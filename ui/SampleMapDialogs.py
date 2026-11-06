from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6 import QtWidgets as QtW

import Functions.SQLUtils as SQLUtils
import Functions.Text_manipulations as TxM
import logger_setup
from Functions.Alter_database import convert_gps_location
from Functions.Check_triggers import validate_insert, update_modified_timestamp
from Functions.Database_manager import update_database
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Widget_classes import show_loading_dialog
from ui.AddTreeTags import AddTreeTags

SAMPLE_TAG_TABLES = {key.split('.')[0]: schema for key, schema in SQLUtils.tree_tables_schema.items()
                     if schema['bridge_table'].startswith('Samples_')}
"""Samples tree tags (AgeSignatures, Regions, RockTypes, SampleContexts, SamplingMethods, Settings, Units) and their
bridge tables, taken from SQLUtils.tree_tables_schema"""

GPS_COLUMNS = ['GPSLatDeg', 'GPSLatMin', 'GPSLatSec', 'GPSLatDirectionID', 'GPSLonDeg', 'GPSLonMin', 'GPSLonSec',
               'GPSLonDirectionID', 'GPSUTMZone', 'GPSUTMN', 'GPSUTME', 'GPSElev', 'GPSElevError', 'GPSElevUnitID',
               'GPSFormatID']
"""All GPSLocations input columns; check_gps_format_insert expects every one to be present"""

DD_FORMAT_ID = 1
"""GPSFormats 'DD +/-' (first entry of SQLUtils.gps_formats); map picks are stored as signed decimal degrees"""


def bind(value):
    return QtC.QVariant() if value == 'NULL' else value


def update_if_no_savepoints():
    if not SavepointManager.get_instance().active_savepoints():
        if not update_database():
            logger_setup.get_logger().critical('Error updating and displaying the database')


class MapAddSampleDialog(QtW.QDialog):
    """Add a sample at a location picked on the map. Coordinates are stored as GPSFormatID 1 (DD +/-)."""

    def __init__(self, parent, lat: float, lon: float):
        super().__init__(parent)
        self.setWindowTitle('Add sample at location')
        self.setModal(True)
        self.sample_id = None

        self.name_lineEdit = QtW.QLineEdit()
        self.igsn_lineEdit = QtW.QLineEdit()
        self.description_textEdit = QtW.QPlainTextEdit()
        self.description_textEdit.setFixedHeight(70)
        self.lat_spinBox = self.coordinate_box(90, lat)
        self.lon_spinBox = self.coordinate_box(180, lon)
        number = QtG.QDoubleValidator()
        number.setLocale(QtC.QLocale.c())
        self.elev_lineEdit = QtW.QLineEdit()
        self.elev_lineEdit.setValidator(number)
        self.elev_error_lineEdit = QtW.QLineEdit()
        self.elev_error_lineEdit.setValidator(number)
        self.elev_unit_comboBox = QtW.QComboBox()
        query = QtS.QSqlQuery('SELECT DistanceUnitID, DistanceUnitAbbreviation FROM DistanceUnits')
        while query.next():
            self.elev_unit_comboBox.addItem(query.value(1), query.value(0))
        self.elev_unit_comboBox.setCurrentText('m')

        form = QtW.QFormLayout(self)
        form.addRow('Sample name*', self.name_lineEdit)
        form.addRow('Sample IGSN', self.igsn_lineEdit)
        form.addRow('Latitude (DD)', self.lat_spinBox)
        form.addRow('Longitude (DD)', self.lon_spinBox)
        form.addRow('Elevation', self.elev_lineEdit)
        form.addRow('Elevation error', self.elev_error_lineEdit)
        form.addRow('Elevation unit', self.elev_unit_comboBox)
        form.addRow('Description', self.description_textEdit)
        buttons = QtW.QDialogButtonBox(QtW.QDialogButtonBox.StandardButton.Ok | QtW.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.add_sample)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    @staticmethod
    def coordinate_box(limit: float, value: float) -> QtW.QDoubleSpinBox:
        box = QtW.QDoubleSpinBox()
        box.setLocale(QtC.QLocale.c())
        box.setRange(-limit, limit)
        box.setDecimals(6)
        box.setValue(value)
        return box

    def existing_gps_id(self, gps_values: list):
        """GPSLocationID with identical stored values, if one exists (NULL-safe comparison)."""
        query = QtS.QSqlQuery()
        query.prepare(f'SELECT GPSLocationID FROM GPSLocations WHERE {" AND ".join(f"{c} IS ?" for c in GPS_COLUMNS)}')
        for value in gps_values:
            query.addBindValue(bind(value))
        if query.exec() and query.next():
            return query.value(0)
        return None

    def add_sample(self):
        name = self.name_lineEdit.text().strip()
        if not name:
            logger_setup.get_logger().error('Sample name is required')
            return
        elev = self.elev_lineEdit.text().strip()
        elev_error = self.elev_error_lineEdit.text().strip()
        gps_values = ['NULL'] * len(GPS_COLUMNS)
        gps_values[GPS_COLUMNS.index('GPSLatDeg')] = round(self.lat_spinBox.value(), 6)
        gps_values[GPS_COLUMNS.index('GPSLonDeg')] = round(self.lon_spinBox.value(), 6)
        gps_values[GPS_COLUMNS.index('GPSFormatID')] = DD_FORMAT_ID
        if elev:
            gps_values[GPS_COLUMNS.index('GPSElev')] = float(elev)
            gps_values[GPS_COLUMNS.index('GPSElevUnitID')] = self.elev_unit_comboBox.currentData()
        if elev_error:
            gps_values[GPS_COLUMNS.index('GPSElevError')] = float(elev_error)

        create_savepoint('before_map_add_sample')
        error, header = validate_insert('GPSLocations', GPS_COLUMNS, gps_values, DD_FORMAT_ID)
        if error:
            logger_setup.get_logger().error(f'Invalid GPS input: {error}')
            rollback_savepoint('before_map_add_sample')
            return

        query = QtS.QSqlQuery()
        gps_id = self.existing_gps_id(gps_values)
        if gps_id:
            logger_setup.get_logger().info(f'GPS location already exists with ID {gps_id}')
        else:
            query.prepare(f'INSERT INTO GPSLocations ({", ".join(GPS_COLUMNS)}) VALUES ({", ".join("?" * len(GPS_COLUMNS))})')
            for value in gps_values:
                query.addBindValue(bind(value))
            if not query.exec():
                logger_setup.get_logger().critical('Error inserting GPS location')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                rollback_savepoint('before_map_add_sample')
                return
            gps_id = query.lastInsertId()
            if not convert_gps_location(gps_id):
                logger_setup.get_logger().error(f'Error converting GPS location {gps_id}')
                rollback_savepoint('before_map_add_sample')
                return

        sample_columns = ['SampleName', 'SampleIGSN', 'SampleGPSLocationID', 'SampleDescription']
        sample_values = [name, self.igsn_lineEdit.text().strip() or 'NULL', gps_id,
                         self.description_textEdit.toPlainText().strip() or 'NULL']
        error, header = validate_insert('Samples', sample_columns, sample_values, None)
        if error:
            logger_setup.get_logger().error(error)
            rollback_savepoint('before_map_add_sample')
            return
        query.prepare(f'INSERT INTO Samples ({", ".join(sample_columns)}) VALUES (?, ?, ?, ?)')
        for value in sample_values:
            query.addBindValue(bind(value))
        if not query.exec():
            error = query.lastError().text()
            if 'UNIQUE constraint failed' in error:
                logger_setup.get_logger().error('Sample name and IGSN must be unique (case insensitive)')
            else:
                logger_setup.get_logger().critical('Error inserting sample')
            logger_setup.get_logger().debug(f'Error: {error}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            rollback_savepoint('before_map_add_sample')
            return
        self.sample_id = query.lastInsertId()
        release_savepoint('before_map_add_sample')
        logger_setup.get_logger().info(f'Added sample {name} (SampleID {self.sample_id}) at GPSLocationID {gps_id}')
        update_if_no_savepoints()
        self.accept()


class BulkTagDialog(QtW.QDialog):
    """
    Add or remove Samples tree tags across a group of samples. All changes are held in a savepoint until Finish;
    Cancel or closing rolls them back. New tags are created with AddTreeTags.
    """

    def __init__(self, parent, sample_ids: list):
        super().__init__(parent)
        self.setWindowTitle(f'Edit tags for {len(sample_ids)} samples')
        self.setModal(True)
        self.resize(480, 560)
        self.sample_ids = list(sample_ids)
        self.updated = False

        self.table_comboBox = QtW.QComboBox()
        for table in SAMPLE_TAG_TABLES:
            self.table_comboBox.addItem(TxM.add_spaces_camel(table), table)
        self.filter_lineEdit = QtW.QLineEdit()
        self.filter_lineEdit.setPlaceholderText('Filter tags')
        self.tags_treeWidget = QtW.QTreeWidget()
        self.tags_treeWidget.setHeaderLabels(['Tag', 'Selected samples'])
        self.tags_treeWidget.setSelectionMode(QtW.QAbstractItemView.SelectionMode.ExtendedSelection)

        new_button = QtW.QPushButton('New tag...')
        add_button = QtW.QPushButton('Add to selected samples')
        remove_button = QtW.QPushButton('Remove from selected samples')
        finish_button = QtW.QPushButton('Finish')
        cancel_button = QtW.QPushButton('Cancel')
        new_button.clicked.connect(self.new_tag)
        add_button.clicked.connect(lambda: self.apply(True))
        remove_button.clicked.connect(lambda: self.apply(False))
        finish_button.clicked.connect(self.finish)
        cancel_button.clicked.connect(self.reject)

        edit_buttons = QtW.QHBoxLayout()
        for button in (new_button, add_button, remove_button):
            edit_buttons.addWidget(button)
        close_buttons = QtW.QHBoxLayout()
        close_buttons.addStretch()
        close_buttons.addWidget(cancel_button)
        close_buttons.addWidget(finish_button)
        layout = QtW.QVBoxLayout(self)
        layout.addWidget(self.table_comboBox)
        layout.addWidget(self.filter_lineEdit)
        layout.addWidget(self.tags_treeWidget)
        layout.addLayout(edit_buttons)
        layout.addLayout(close_buttons)

        create_savepoint('before_map_tags')
        self.table_comboBox.currentIndexChanged.connect(self.load_tags)
        self.filter_lineEdit.textChanged.connect(self.filter_tags)
        self.load_tags()

    @property
    def table(self) -> str:
        return self.table_comboBox.currentData()

    @property
    def schema(self) -> dict:
        return SAMPLE_TAG_TABLES[self.table]

    def load_tags(self):
        """Build the tag tree with the count of selected samples carrying each tag."""
        s = self.schema
        parent_row_column = s['name_column'].replace('Name', 'ParentRow')
        sample_ids = ', '.join(str(int(sample_id)) for sample_id in self.sample_ids)
        query = QtS.QSqlQuery()
        if not query.exec(f'''SELECT t.{s["id_column"]}, t.{s["parent_column"]}, t.{s["name_column"]}, COUNT(b.SampleID)
                              FROM {self.table} t
                              LEFT JOIN {s["bridge_table"]} b ON b.{s["bridge_to_column"]} = t.{s["id_column"]}
                                  AND b.{s["bridge_from_column"]} IN ({sample_ids})
                              GROUP BY t.{s["id_column"]}
                              ORDER BY t.{s["parent_column"]}, t.{parent_row_column}'''):
            logger_setup.get_logger().critical(f'Error loading {self.table}')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            return
        rows = []
        while query.next():
            rows.append((query.value(0), None if query.isNull(1) else query.value(1), query.value(2), query.value(3)))
        self.tags_treeWidget.clear()
        items = {}
        for tag_id, parent_id, name, count in rows:
            item = QtW.QTreeWidgetItem([name, f'{count}/{len(self.sample_ids)}'])
            item.setData(0, QtC.Qt.ItemDataRole.UserRole, tag_id)
            items[tag_id] = item
        for tag_id, parent_id, name, count in rows:
            if parent_id in items:
                items[parent_id].addChild(items[tag_id])
            else:
                self.tags_treeWidget.addTopLevelItem(items[tag_id])
        self.tags_treeWidget.expandAll()
        self.tags_treeWidget.resizeColumnToContents(0)
        self.filter_tags(self.filter_lineEdit.text())

    def filter_tags(self, text: str):
        def visible(item: QtW.QTreeWidgetItem) -> bool:
            child_visible = any([visible(item.child(i)) for i in range(item.childCount())])
            shown = child_visible or text.casefold() in item.text(0).casefold()
            item.setHidden(not shown)
            return shown
        for i in range(self.tags_treeWidget.topLevelItemCount()):
            visible(self.tags_treeWidget.topLevelItem(i))

    def apply(self, add: bool):
        """Add (INSERT OR IGNORE) or remove the selected tags for every selected sample."""
        tag_ids = [item.data(0, QtC.Qt.ItemDataRole.UserRole) for item in self.tags_treeWidget.selectedItems()]
        if not tag_ids:
            return
        s = self.schema
        query = QtS.QSqlQuery()
        if add:
            query.prepare(f'INSERT OR IGNORE INTO {s["bridge_table"]} ({s["bridge_from_column"]}, {s["bridge_to_column"]}) '
                          f'VALUES (?, ?)')
        else:
            query.prepare(f'DELETE FROM {s["bridge_table"]} '
                          f'WHERE {s["bridge_from_column"]} = ? AND {s["bridge_to_column"]} = ?')
        create_savepoint('before_map_tag_apply')
        for tag_id in tag_ids:
            for sample_id in self.sample_ids:
                query.bindValue(0, sample_id)
                query.bindValue(1, tag_id)
                if not query.exec():
                    logger_setup.get_logger().critical(f'Error {"adding" if add else "removing"} {self.table} tags')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    rollback_savepoint('before_map_tag_apply')
                    return
        update_modified_timestamp('Samples', self.sample_ids)
        release_savepoint('before_map_tag_apply')
        logger_setup.get_logger().info(f'{"Added" if add else "Removed"} {self.table} {tag_ids} '
                                       f'{"to" if add else "from"} {len(self.sample_ids)} samples')
        self.updated = True
        self.load_tags()

    def new_tag(self):
        show_loading_dialog('Loading', f'Opening add window for {self.table}...')
        dialog = AddTreeTags(self, self.table)
        dialog.exec()
        if dialog.updated:
            self.updated = True
            self.load_tags()

    def finish(self):
        release_savepoint('before_map_tags')
        update_if_no_savepoints()
        self.accept()

    def reject(self):
        if self.updated:
            response = QtW.QMessageBox.question(self, 'Discard changes', 'Discard all tag changes?')
            if response != QtW.QMessageBox.StandardButton.Yes:
                return
        rollback_savepoint('before_map_tags')
        super().reject()

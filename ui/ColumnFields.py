import time

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS

import logger_setup
from Functions.Widget_classes import (
    TreeModel, populate_combo_box, CheckableComboBox, get_headers, populate_many_combo_checks, add_tree_popup,
    save_expanded_state, get_name_from_id, find_tree_model, get_view_from_table, show_loading_dialog,
    close_loading_dialog, FocusGroupBox, set_comboBox_text, update_modified_timestamp
)
from Functions import SQLUtils
from Functions.Settings_manager import SettingsManager

settings = SettingsManager().settings
from Functions.Database_views import ViewQuery
from Functions.Check_triggers import validate_update
from ui.EditTable import EditTable
from ui.EditTree import EditTree
from ui.AddTags import AddTags
from ui.AddTreeTags import AddTreeTags

class ColumnFields(QtW.QWidget):
    def __init__(self, sample_ids: list, parent=None):
        super().__init__(parent)
        if not sample_ids:
            return
        self.checked_sample_list = sample_ids

        self.groupBox = FocusGroupBox(self)
        self.groupBox.setTitle('Column')
        self.groupBox.setSizePolicy(QtW.QSizePolicy.Policy.Preferred, QtW.QSizePolicy.Policy.Preferred)
        self.groupBox.setObjectName('column_groupBox')
        self.groupBox_layout = QtW.QVBoxLayout()
        self.layout = QtW.QVBoxLayout(self)
        self.column_name_label = QtW.QLabel('Column Name:')
        self.column_name_label.setSizePolicy(QtW.QSizePolicy.Policy.Fixed, QtW.QSizePolicy.Policy.Preferred)
        self.column_name_comboBox = CheckableComboBox()
        self.column_name_comboBox.setSizePolicy(QtW.QSizePolicy.Policy.Preferred, QtW.QSizePolicy.Policy.Fixed)
        self.column_name_comboBox.setObjectName("column_name_comboBox")
        self.height_depth_label = QtW.QLabel('Height/Depth:')
        self.height_depth_label.setSizePolicy(QtW.QSizePolicy.Policy.Fixed, QtW.QSizePolicy.Policy.Preferred)
        self.height_depth_lineEdit = QtW.QLineEdit()
        self.height_depth_lineEdit.setSizePolicy(QtW.QSizePolicy.Policy.Expanding, QtW.QSizePolicy.Policy.Fixed)
        self.height_depth_lineEdit.setObjectName("height_depth_lineEdit")
        self.height_depth_error_label = QtW.QLabel('±')
        self.height_depth_error_label.setSizePolicy(QtW.QSizePolicy.Policy.Fixed, QtW.QSizePolicy.Policy.Preferred)
        self.height_depth_error_lineEdit = QtW.QLineEdit()
        self.height_depth_error_lineEdit.setSizePolicy(QtW.QSizePolicy.Policy.Expanding, QtW.QSizePolicy.Policy.Fixed)
        self.height_depth_error_lineEdit.setObjectName("height_depth_error_lineEdit")
        self.height_depth_unit_comboBox = QtW.QComboBox()
        self.height_depth_unit_comboBox.setSizePolicy(QtW.QSizePolicy.Policy.Fixed, QtW.QSizePolicy.Policy.Fixed)
        self.height_depth_unit_comboBox.setMaximumWidth(80)
        self.height_depth_unit_comboBox.setObjectName("height_depth_unit_comboBox")
        self.name_layout = QtW.QHBoxLayout()
        self.height_depth_layout = QtW.QHBoxLayout()

        self.name_layout.addWidget(self.column_name_label)
        self.name_layout.addWidget(self.column_name_comboBox)
        self.height_depth_layout.addWidget(self.height_depth_label)
        self.height_depth_layout.addWidget(self.height_depth_lineEdit)
        self.height_depth_layout.addWidget(self.height_depth_error_label)
        self.height_depth_layout.addWidget(self.height_depth_error_lineEdit)
        self.height_depth_layout.addWidget(self.height_depth_unit_comboBox)
        self.groupBox_layout.addLayout(self.name_layout)
        self.groupBox_layout.addLayout(self.height_depth_layout)
        self.groupBox.setLayout(self.groupBox_layout)
        self.layout.addWidget(self.groupBox)
        self.setLayout(self.layout)

        self.lost_widget = None
        self.column_name_comboBox.lineEdit().setPlaceholderText("Name of column, core, etc.")

        self.populate_dropdowns()
        self.populate_fields()
        self.set_validators()
        self.connect_signals()
        self.updated = False

        self.column_name_comboBox.add_triggered.connect(self.add_popup)
        self.column_name_comboBox.edit_triggered.connect(self.edit_popup)

        self.focus_timer = QtC.QTimer(self)
        self.focus_timer.setSingleShot(True)
        self._isApplicationFocused = True
        QtW.QApplication.instance().installEventFilter(self)

    def populate_dropdowns(self):
        start_populate_dropdown_time = time.time()
        logger_setup.get_logger().info("Populating dropdowns")
        show_loading_dialog('Loading', 'Populating dropdowns...')
        column_cols = settings.value('column_view_columns')
        query_args = {'show_columns': column_cols}
        view_query = ViewQuery('Columns', False, **query_args)
        column_query = view_query.table_query
        populate_combo_box(self.column_name_comboBox,
                           **{'table': 'Columns', 'query': column_query, 'column': 'ColumnName'})
        self.column_name_comboBox.model_modifiable = True
        self.column_name_comboBox.enable_context_menu(True)
        self.column_name_comboBox.set_single_click(True)
        populate_combo_box(self.height_depth_unit_comboBox,
                           **{'table': 'DistanceUnits', 'column': 'DistanceUnitAbbreviation'})

        self.column_name_comboBox.view().setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        end_populate_dropdown_time = time.time()
        close_loading_dialog('Loading', 'Populating dropdowns...')
        logger_setup.get_logger().info(
            f"Populated dropdowns in {end_populate_dropdown_time - start_populate_dropdown_time} seconds")
        logger_setup.get_logger().info("Dropdowns populated")

    def populate_fields(self):
        logger_setup.get_logger().info("Populating fields")
        start_populate_fields_time = time.time()
        headers = get_headers('Samples')
        if len(self.checked_sample_list) > 1:
            sample_query = f'SELECT * FROM Samples WHERE SampleID in {tuple(self.checked_sample_list)}'
        elif len(self.checked_sample_list) == 1:
            sample_query = f'SELECT * FROM Samples WHERE SampleID = {self.checked_sample_list[0]}'
        else:
            sample_query = f'SELECT * FROM Samples WHERE SampleID IS NULL'
        self.samples_table = QtS.QSqlQueryModel()
        self.samples_table.setQuery(sample_query)
        while self.samples_table.canFetchMore():
            self.samples_table.fetchMore()
        if self.samples_table.rowCount() == 0:
            logger_setup.get_logger().info("No samples to populate")
            self.clear_fields()
            return
        for header in headers:
            values = [self.samples_table.record(row).value(header) for row in range(self.samples_table.rowCount())]
            if len(set(values)) == 1 and not values[0]:
                # If all values are the same and empty, add an empty string
                text = ""
            elif len(set(values)) == 1 and values[0]:
                # If all values are the same and not empty, add the value
                text = values[0]
            else:
                # If values are different, add '-'
                text = "-"
            if 'ColumnID' in header:
                if text is None or text == '':
                    set_comboBox_text(self.column_name_comboBox, "")
                elif text == "-":
                    partially_checked_ids = set(value for value in values if value != "" )
                    self.column_name_comboBox.source_model().update_model_checks(set(), set(partially_checked_ids))
                else:
                    column_id = text
                    self.column_name_comboBox.source_model().update_model_checks({column_id}, set())
            elif 'HeightDepthError' in header and 'Calculated' not in header:
                if text is None or text == '':
                    self.height_depth_error_lineEdit.setText("")
                else:
                    self.height_depth_error_lineEdit.setText(f"{text}")
            elif 'HeightDepthUnit' in header:
                if text is None or text == '':
                    set_comboBox_text(self.height_depth_unit_comboBox,
                                      settings.value('heightdepth_unit_abbreviation'))
                elif text == "-":
                    set_comboBox_text(self.height_depth_unit_comboBox, text)
                else:
                    unit_id = text
                    text = get_name_from_id('DistanceUnits', unit_id)
                    set_comboBox_text(self.height_depth_unit_comboBox, text)
            elif 'HeightDepth' in header and 'Calculated' not in header:
                if text is None or text == '':
                    self.height_depth_lineEdit.setText("")
                else:
                    self.height_depth_lineEdit.setText(str(text))

        end_populate_fields_time = time.time()
        logger_setup.get_logger().info(
            f"Populated fields in {end_populate_fields_time - start_populate_fields_time} seconds")
        logger_setup.get_logger().info("Fields populated")

    def set_validators(self):
        height_depth_float_validator = QtG.QDoubleValidator()
        height_depth_float_validator.setNotation(QtG.QDoubleValidator.Notation.StandardNotation)
        self.height_depth_lineEdit.setPlaceholderText("e.g. 0.0")
        self.height_depth_lineEdit.setValidator(height_depth_float_validator)
        self.height_depth_lineEdit.setToolTip("Enter a numeric value")

        self.height_depth_error_lineEdit.setPlaceholderText("e.g. 0.0")
        self.height_depth_error_lineEdit.setValidator(height_depth_float_validator)
        self.height_depth_error_lineEdit.setToolTip("Enter a numeric value")

    def clear_fields(self):
        self.column_name_comboBox.clear_all_checks()
        self.height_depth_lineEdit.clear()
        self.height_depth_error_lineEdit.clear()
        self.height_depth_unit_comboBox.setCurrentText(settings.value('heightdepth_unit_abbreviation'))

    def eventFilter(self, obj, event):
        if event.type() == QtC.QEvent.Type.ApplicationDeactivate:
            self._isApplicationFocused = False
        elif event.type() == QtC.QEvent.Type.ApplicationActivate:
            self._isApplicationFocused = True
        # print(f"Event filter: {event.type()}, {obj}")
        return super().eventFilter(obj, event)

    def check_focus(self):
        if not self.groupBox.edited:
            for child in self.groupBox.findChildren(QtW.QWidget):
                if child.hasFocus():
                    logger_setup.get_logger().info(f"Child {child.objectName()} has focus")
                    self.groupBox.set_edited(child)
                    break
        self.groupBox.clearFocus()
        if self.groupBox.edited:
            logger_setup.get_logger().info(f"GPS was edited")
            self.update_column_info()

    def focus_lost_delay(self):
        if self._isApplicationFocused:
            logger_setup.get_logger().info("Column group box focus lost")
            self.lost_widget = self.sender()
            logger_setup.get_logger().info(f'Focus lost on {self.lost_widget.objectName()}')
            self.focus_timer.timeout.connect(self.update_column_info)
            self.focus_timer.start(100)

    def connect_signals(self):
        # Connect signals and slots
        self.disconnect_signals()
        logger_setup.get_logger().info("Connecting signals")
        self.groupBox.focusLost.connect(self.focus_lost_delay)
        self.groupBox.connect_child_signals()

    def disconnect_signals(self):
        logger_setup.get_logger().info("Disconnecting signals")
        try:
            self.column_name_comboBox.currentTextChanged.disconnect()
        except TypeError:
            pass
        try:
            self.groupBox.focusLost.disconnect()
        except TypeError:
            pass
        try:
            self.height_depth_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass
        try:
            self.height_depth_error_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass
        try:
            self.height_depth_unit_comboBox.currentTextChanged.disconnect()
        except TypeError:
            pass

    def update_column_info(self):
        logger_setup.get_logger().info("Update column height called")
        try:
            self.groupBox.focusLost.disconnect()
        except TypeError:
            pass
        if len(self.checked_sample_list) == 0:
            logger_setup.get_logger().info("No samples selected")
            return False
        start_update_column_height_time = time.time()
        query = QtS.QSqlQuery()
        if not query.exec(
                f"SELECT ColumnID FROM Columns WHERE ColumnName = '{self.column_name_comboBox.currentText()}'"):
            logger_setup.get_logger().critical(
                f"Failed to select ColumnID for {self.column_name_comboBox.currentText()}")
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            return False
        query.next()
        column_id = query.value(0)
        if not query.exec(
                f"SELECT DistanceUnitID FROM DistanceUnits WHERE DistanceUnitAbbreviation = '{self.height_depth_unit_comboBox.currentText()}'"):
            logger_setup.get_logger().critical(
                f"Failed to select DistanceUnitID for {self.height_depth_unit_comboBox.currentText()}")
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            return False
        query.next()
        unit_id = query.value(0)
        if len(self.checked_sample_list) == 1:
            where_sql = f'SampleID = {self.checked_sample_list[0]}'
        else:
            where_sql = f'SampleID IN {tuple(self.checked_sample_list)}'
        error, column = validate_update('Samples',
                                        ['SampleColumnID', 'HeightDepth', 'HeightDepthError', 'HeightDepthUnitID'],
                                        [column_id, self.height_depth_lineEdit.text(),
                                         self.height_depth_error_lineEdit.text(), unit_id], where_sql)
        if error:
            logger_setup.get_logger().error(f"Error: {error}")
            self.groupBox.setFocus()
            return False
        query.prepare(f'''UPDATE Samples SET SampleColumnID = :columnID, HeightDepth = :height, 
                            HeightDepthError = :error, HeightDepthUnitID = :unitID WHERE {where_sql}''')
        query.bindValue(":columnID", column_id)
        query.bindValue(":height", self.height_depth_lineEdit.text())
        query.bindValue(":error", self.height_depth_error_lineEdit.text())
        query.bindValue(":unitID", unit_id)
        if not query.exec():
            logger_setup.get_logger().critical(f"Failed to update column information")
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            return False
        update_modified_timestamp('Samples', self.checked_sample_list)
        self.updated = True
        end_update_column_height_time = time.time()
        logger_setup.get_logger().info(
            f"Updated column height in {end_update_column_height_time - start_update_column_height_time} seconds")
        return True

    def update_list(self, sample_ids):
        logger_setup.get_logger().info(f"Populating column fields for Samples with sample IDs {sample_ids}")
        self.checked_sample_list = sample_ids
        if len(self.checked_sample_list) == 0:
            # No samples selected, clear fields and disable groups
            self.clear_fields() # Also disconnects signals
            self.connect_signals()
        else:
            self.clear_fields() # Also disconnects signals
            self.populate_dropdowns()
            self.populate_fields()

    def add_popup(self, combo: QtW.QComboBox, action: QtG.QAction | None = None):
        combo.blockSignals(True)
        logger_setup.get_logger().info(f"Add popup called")
        try:
            model = combo.source_model()
        except AttributeError:
            model = combo.model()
        if isinstance(combo.view(), QtW.QTreeView):
            if not isinstance(model, TreeModel):
                model, indexes = find_tree_model(model, None)
            if model:
                table = model.table
            else:
                logger_setup.get_logger().critical(f"Error adding new item")
                logger_setup.get_logger().debug(f"Error: No tree model found")
                combo.blockSignals(False)
                return
        else:
            table = model.tableName()
        dlg = None
        if table in SQLUtils.user_viewable_trees:
            save_expanded_state(table, combo.view())
            dlg_args = add_tree_popup(combo.view(), action)
            show_loading_dialog('Loading', f'Opening add window for {table}...')
            if dlg_args:
                dlg = AddTreeTags(self, table, **dlg_args)
            else:
                dlg = AddTreeTags(self, table)
        else:
            show_loading_dialog('Loading', f'Opening add window for {table}...')
            dlg = AddTags(self, table)
        if not dlg:
            combo.blockSignals(False)
            return
        logger_setup.get_logger().info(f"Showing {table} add dialog")
        dlg.exec()
        if dlg.updated:
            self.updated = True
            # Update this combo box
            populate_combo_box(combo, **{'table': table})
            populate_many_combo_checks(f'Samples_{table}', combo, self.checked_sample_list)
            combo.blockSignals(False)
        else:
            combo.blockSignals(False)
            return

    def edit_popup(self):
        logger_setup.get_logger().info(f'Edit popup called')
        combo: QtW.QComboBox = self.sender()
        try:
            model = combo.source_model()
        except AttributeError:
            model = combo.model()
        if isinstance(combo.view(), QtW.QTreeView):
            if not isinstance(model, TreeModel):
                model, indexes = find_tree_model(model, None)
            if model:
                table = model.table
            else:
                logger_setup.get_logger().critical(f"Error editing table")
                logger_setup.get_logger().debug(f"Error: No tree model found")
                return
        elif isinstance(model, QtC.QSortFilterProxyModel):
            model = model.sourceModel()
            table = model.tableName()
        else:
            table = combo.model().tableName()
        combo.blockSignals(True)
        dlg = None
        if table in SQLUtils.user_viewable_trees:
            dlg = EditTree(self, table)
        elif table != get_view_from_table(table):
            from ui.EditView import EditView
            dlg = EditView(self, table)
        else:
            dlg = EditTable(self, table)
        if dlg is None:
            combo.blockSignals(False)
            return
        logger_setup.get_logger().info(f"Showing {table} edit dialog")
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
            # Update this combo box
            populate_combo_box(combo, **{'table': table})
            populate_many_combo_checks(f'Samples_{table}', combo, self.checked_sample_list)
        combo.blockSignals(False)
# from operator import itemgetter

import PyQt6
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6.uic import loadUi
from Functions.Widget_classes import (set_table, set_comboBox_text, SQLiteTableModel, populate_combo_box, get_headers,
    return_number)
from Functions.Settings_manager import settings
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Check_triggers import validate_insert, validate_update, update_modified_timestamp
from Functions.Alter_database import convert_gps_location
import Functions.Database_views as DB_views
import time
import logger_setup

class GPSFields(QtW.QWidget):
    def __init__(self, table: str, item_ids: list | None, parent=None):
        super().__init__(parent)

        logger_setup.get_logger().info('Starting GPSFields')
        gps_ui_file = "ui/GPSFields.ui"
        loadUi(gps_ui_file, self)
        self.table = table
        if self.table == 'Columns':
            self.table_gps_id_header = 'ColumnBaseGPSID'
            self.item_id_header = 'ColumnID'
            self.item_edit_view = 'ColumnEditView'
            self.item_view_gps_header = 'ColumnGPSLocationID'
            self.other_table = 'Samples'
            self.other_table_gps_id_header = 'SampleGPSLocationID'
            self.other_table_id_header = 'SampleID'
            self.other_edit_view = 'SampleEditView'
        elif self.table == 'Samples':
            self.table_gps_id_header = 'SampleGPSLocationID'
            self.item_id_header = 'SampleID'
            self.item_edit_view = 'SampleEditView'
            self.item_view_gps_header = 'SampleGPSLocationID'
            self.other_table = 'Columns'
            self.other_table_gps_id_header = 'ColumnBaseGPSID'
            self.other_table_id_header = 'ColumnID'
            self.other_edit_view = 'ColumnEditView'
        else:
            raise ValueError('Table must be either "Columns" or "Samples"')
        self.item_ids = item_ids
        self.updated = False
        self.errmsg = QtW.QMessageBox(self)
        self.focus_timer = QtC.QTimer(self)
        self.focus_timer.setSingleShot(True)
        self.focus_timer.timeout.connect(self.update_gps)
        self._isApplicationFocused = True
        QtW.QApplication.instance().installEventFilter(self)

        self.item_model = None
        self.gps_format_model = QtS.QSqlTableModel()
        self.gps_location_model = QtS.QSqlTableModel()
        self.direction_unit_model = QtS.QSqlTableModel()
        self.lat_direction_model = QtS.QSqlTableModel()
        self.lon_direction_model = QtS.QSqlTableModel()
        self.distance_unit_model = QtS.QSqlTableModel()
        self.elevation_unit_model = QtS.QSqlTableModel()

        self.gps_location_ids = ""
        self.lost_group_box = None

        self.populate_dropdowns()
        self.populate_fields()
        self.connect_signals()

    def update_list(self, item_ids):
        self.item_ids = item_ids
        self.clear_fields()
        self.disconnect_text_signals()
        self.populate_fields()
        self.connect_signals()

    def populate_dropdowns(self):
        start_populate_dropdowns_time = time.time()
        set_table(self.gps_format_model, 'GPSFormats')
        set_table(self.gps_location_model, 'GPSLocations')
        set_table(self.direction_unit_model, 'DirectionUnits')
        # set_table(self.lat_direction_model, 'DirectionUnits')
        # set_table(self.lon_direction_model, 'DirectionUnits')
        # set_table(self.elevation_unit_model, 'DistanceUnits')

        elevation_unit_abbreviation = settings.value('elevation_unit_abbreviation')
        gps_format_abbreviation = settings.value('gps_format_abbreviation')

        populate_combo_box(self.gps_format_comboBox, **{'table': 'GPSFormats', 'column': 'GPSFormatAbbreviation'})
        self.gps_format_comboBox.setCurrentIndex(-1)
        populate_combo_box(self.lat_comboBox, **{'table': 'DirectionUnits', 'column': 'DirectionUnitAbbreviation'})
        self.lat_direction_model = self.lat_comboBox.model()
        self.lat_direction_model.setFilter('DirectionUnitAbbreviation = "N" OR DirectionUnitAbbreviation = "S"')
        populate_combo_box(self.lon_comboBox, **{'table': 'DirectionUnits', 'column': 'DirectionUnitAbbreviation'})
        self.lon_direction_model = self.lon_comboBox.model()
        self.lon_direction_model.setFilter('DirectionUnitAbbreviation = "E" OR DirectionUnitAbbreviation = "W"')
        populate_combo_box(self.elevation_unit_comboBox, **{'table': 'DistanceUnits', 'column': 'DistanceUnitAbbreviation'})
        self.elevation_unit_model = self.elevation_unit_comboBox.model()
        self.elevation_unit_comboBox.setCurrentText(elevation_unit_abbreviation)
        end_populate_dropdowns_time = time.time()
        logger_setup.get_logger().info(f"Populated GPS dropdowns in {end_populate_dropdowns_time - start_populate_dropdowns_time} seconds")

    def check_focus(self):
        if not self.latlon_groupBox.any_child_has_focus() and self.latlon_groupBox.edited:
            self.latlon_groupBox.focusLost.emit()
        elif not self.utm_groupBox.any_child_has_focus() and self.utm_groupBox.edited:
            self.utm_groupBox.focusLost.emit()
        elif not self.elev_groupBox.any_child_has_focus() and self.elev_groupBox.edited:
            self.elev_groupBox.focusLost.emit()

    def eventFilter(self, obj, event):
        if event.type() == QtC.QEvent.Type.ApplicationDeactivate:
            self._isApplicationFocused = False
        elif event.type() == QtC.QEvent.Type.ApplicationActivate:
            self._isApplicationFocused = True
        return super().eventFilter(obj, event)

    def connect_signals(self):
        self.gps_format_comboBox.currentTextChanged.connect(self.display_gps)
        self.latlon_groupBox.connect_child_signals()
        self.latlon_groupBox.focusLost.connect(self.focus_lost_delay)
        self.utm_groupBox.connect_child_signals()
        self.utm_groupBox.focusLost.connect(self.focus_lost_delay)
        self.elev_groupBox.connect_child_signals()
        self.elev_groupBox.focusLost.connect(self.focus_lost_delay)

    def focus_lost_delay(self):
        if self._isApplicationFocused:
            self.lost_group_box = self.sender()
            self.focus_timer.start(100)

    def disconnect_text_signals(self):
        self.latlon_groupBox.disconnect_child_signals()
        self.utm_groupBox.disconnect_child_signals()
        self.elev_groupBox.disconnect_child_signals()
        try:
            self.gps_format_comboBox.currentTextChanged.disconnect(self.display_gps)
        except TypeError:
            pass

    def populate_fields(self):
        logger_setup.get_logger().info('Populating GPS fields')
        start_populate_fields_time = time.time()
        reset_fields = False  # Reset the GPS fields if there are no samples to populate
        column_names = get_headers('GPSLocations')
        if len(self.item_ids) > 1:
            query_where_str = f' WHERE {self.item_id_header} IN {tuple(self.item_ids)}'
        elif len(self.item_ids) == 1:
            query_where_str = f' WHERE {self.item_id_header} = {self.item_ids[0]}'
        else:
            query_where_str = ''
        self.item_model = QtS.QSqlQueryModel()
        self.item_model.setQuery(f'SELECT {self.item_view_gps_header} FROM {self.item_edit_view}{query_where_str}')
        logger_setup.get_logger().info(f'Set {self.table} model query')
        if self.item_model.rowCount() == 0:
            logger_setup.get_logger().info("No samples to populate")
            reset_fields = True
            empty_gps = True
        if not reset_fields:
            empty_gps = False
            gps_ids = []
            for row in range(self.item_model.rowCount()):
                id_value = self.item_model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole)
                if id_value == '':
                    empty_gps = True
                if id_value and isinstance(id_value, int) and id_value not in gps_ids:
                    gps_ids.append(self.item_model.index(row, 0).data())
            if len(gps_ids) == 0:
                logger_setup.get_logger().info("No GPS locations associated with the samples, so reset fields")
                reset_fields = True
            elif len(set(gps_ids)) == 1:
                self.gps_location_model.setFilter(f"GPSLocationID = {gps_ids[0]}")
            elif len(set(gps_ids)) > 1:
                self.gps_location_model.setFilter(f"GPSLocationID in {tuple(gps_ids)}")
            self.gps_location_model.select()
            if self.gps_location_model.rowCount() == 0:
                logger_setup.get_logger().info(f"Could not find GPS location with ID {gps_ids}, so reset fields")
                reset_fields = True
        for header in column_names:
            logger_setup.get_logger().info(f'Populating {header}')
            if reset_fields:
                text = ""
            else:
                values = []
                for row in range(self.gps_location_model.rowCount()):
                    data = self.gps_location_model.index(row, self.gps_location_model.record().indexOf(header)).data()
                    if data:
                        values.append(self.gps_location_model.index(row, self.gps_location_model.record().indexOf(header)).data())
                    else:
                        values.append("")
                if len(set(values)) == 1 and not values[0]:
                    # If all values are the same and empty, text is an empty string
                    text = ""
                elif len(set(values)) == 1 and values[0] and not empty_gps:
                    # If all values are the same and not empty, and no items are missing GPS, text is the value
                    text = values[0]
                elif empty_gps:
                    # Some items have GPS with values and some don't, so text is "-"
                    text = "-"
                else:
                    # Values are all different, text is '-'
                    text = "-"
            if 'GPSLocationID' in header:
                if text and text != "-":
                    self.gps_location_ids = text
                else:
                    self.gps_location_ids = ""
            elif 'LatDeg' in header:
                if not text:
                    self.lat_deg_lineEdit.setText('')
                else:
                    self.lat_deg_lineEdit.setText(f"{text}")
            elif 'LatMin' in header:
                if not text:
                    self.lat_min_lineEdit.setText('')
                else:
                    self.lat_min_lineEdit.setText(f"{text}")
            elif 'LatSec' in header:
                if not text:
                    self.lat_sec_lineEdit.setText('')
                else:
                    self.lat_sec_lineEdit.setText(f"{text}")
            elif 'LatDir' in header:
                if not text:
                    set_comboBox_text(self.lat_comboBox, '')
                else:
                    # text is the ID, so we need to get the index in the model
                    # combo_index = self.lat_comboBox.currentIndex()
                    # for row in range(self.lat_direction_model.rowCount()):
                    #     if self.lat_direction_model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole) == text:
                    #         combo_index = row
                    #         break
                    # self.lat_comboBox.setCurrentIndex(combo_index)
                    if isinstance(text, int):
                        self.lat_comboBox.setCurrentIndex(text-1)
                    else:
                        self.lat_comboBox.setCurrentText(text)
            elif 'LonDeg' in header:
                if not text:
                    self.lon_deg_lineEdit.setText('')
                else:
                    self.lon_deg_lineEdit.setText(f"{text}")
            elif 'LonMin' in header:
                if not text:
                    self.lon_min_lineEdit.setText('')
                else:
                    self.lon_min_lineEdit.setText(f"{text}")
            elif 'LonSec' in header:
                if not text:
                    self.lon_sec_lineEdit.setText('')
                else:
                    self.lon_sec_lineEdit.setText(f"{text}")
            elif 'LonDir' in header:
                if not text:
                    set_comboBox_text(self.lon_comboBox, '')
                else:
                    # text is the ID, so we need to get the index in the model
                    # combo_index = self.lon_comboBox.currentIndex()
                    # for row in range(self.lon_direction_model.rowCount()):
                    #     if self.lon_direction_model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole) == text:
                    #         combo_index = row
                    #         break
                    # self.lon_comboBox.setCurrentIndex(combo_index)
                    if isinstance(text, int):
                        # The lat_comboBox has the first two items as "N" and "S", so we need to subtract 3 from the ID to get "E" or "W"
                        self.lon_comboBox.setCurrentIndex(text-3)
                    else:
                        self.lon_comboBox.setCurrentText(text)
            elif 'UTMZone' in header:
                if not text:
                    self.utm_zone_lineEdit.setText('')
                else:
                    self.utm_zone_lineEdit.setText(f"{text}")
            elif 'UTMN' in header:
                if not text:
                    self.utm_n_lineEdit.setText('')
                else:
                    self.utm_n_lineEdit.setText(f"{text}")
            elif 'UTME' in header:
                if not text:
                    self.utm_e_lineEdit.setText('')
                else:
                    self.utm_e_lineEdit.setText(f"{text}")
            elif 'ElevError' in header and 'Calculated' not in header:
                if not text:
                    self.elevation_error_lineEdit.setText('')
                else:
                    self.elevation_error_lineEdit.setText(f"{text}")
            elif 'ElevUnit' in header:
                if not text:
                    set_comboBox_text(self.elevation_unit_comboBox, settings.value('elevation_unit_abbreviation'))
                else:
                    # text is the ID, so we need to get the index in the model
                    # combo_index = self.elevation_unit_comboBox.currentIndex()
                    # for row in range(self.elevation_unit_model.rowCount()):
                    #     if self.elevation_unit_model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole) == text:
                    #         combo_index = row
                    #         break
                    # self.elevation_unit_comboBox.setCurrentIndex(combo_index)
                    if isinstance(text, int):
                        self.elevation_unit_comboBox.setCurrentIndex(text-1)
                    else:
                        self.elevation_unit_comboBox.setCurrentText(text)
            elif 'Elev' in header and 'Calculated' not in header:
                if not text:
                    self.elevation_lineEdit.setText('')
                else:
                    self.elevation_lineEdit.setText(f"{text}")
            elif 'GPSFormat' in header:
                if not text:
                    if self.gps_format_comboBox.currentIndex() == -1:
                        # If nothing has been selected yet, set it to the default
                        set_comboBox_text(self.gps_format_comboBox, settings.value('gps_format_abbreviation'))
                else:
                    # text is the ID, so we need to get the index in the model
                    # combo_index = self.gps_format_comboBox.currentIndex()
                    # for row in range(self.gps_format_model.rowCount()):
                    #     if self.gps_format_model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole) == text:
                    #         combo_index = row
                    #         break
                    # self.gps_format_comboBox.setCurrentIndex(combo_index)
                    if isinstance(text, int):
                        self.gps_format_comboBox.setCurrentIndex(text-1)
                    else:
                        self.gps_format_comboBox.setCurrentText(text)
        end_populate_fields_time = time.time()
        logger_setup.get_logger().info(f"Populated GPS fields in {end_populate_fields_time - start_populate_fields_time} seconds")
        self.display_gps()

    def display_gps(self):
        current_gps_format = self.gps_format_comboBox.currentText()
        if current_gps_format == '':
            # Show all gps fields
            self.utm_groupBox.show()
            self.latlon_groupBox.show()
            self.lat_min_lineEdit.show()
            self.lon_min_lineEdit.show()
            self.lat_min_label.show()
            self.lon_min_label.show()
            self.lat_sec_lineEdit.show()
            self.lon_sec_lineEdit.show()
            self.lat_sec_label.show()
            self.lon_sec_label.show()
            self.lat_comboBox.show()
            self.lon_comboBox.show()
        elif current_gps_format == 'UTM':
            self.utm_groupBox.show()
            self.latlon_groupBox.hide()
        else:
            self.utm_groupBox.hide()
            self.latlon_groupBox.show()
            self.lat_deg_lineEdit.show()
            self.lon_deg_lineEdit.show()
            self.lat_deg_label.show()
            self.lon_deg_label.show()
            if 'M' in current_gps_format:
                self.lat_min_lineEdit.show()
                self.lon_min_lineEdit.show()
                self.lat_min_label.show()
                self.lon_min_label.show()
                if 'MS' in current_gps_format:
                    self.lat_sec_lineEdit.show()
                    self.lon_sec_lineEdit.show()
                    self.lat_sec_label.show()
                    self.lon_sec_label.show()
                else:
                    self.lat_sec_lineEdit.hide()
                    self.lon_sec_lineEdit.hide()
                    self.lat_sec_label.hide()
                    self.lon_sec_label.hide()
            else:
                self.lat_min_lineEdit.hide()
                self.lon_min_lineEdit.hide()
                self.lat_min_label.hide()
                self.lon_min_label.hide()
                self.lat_sec_lineEdit.hide()
                self.lon_sec_lineEdit.hide()
                self.lat_sec_label.hide()
                self.lon_sec_label.hide()
            if '+/-' in current_gps_format:
                self.lat_comboBox.hide()
                self.lon_comboBox.hide()
            elif 'NSEW' in current_gps_format:
                self.lat_comboBox.show()
                self.lon_comboBox.show()

    def update_gps(self):
        if not self.lost_group_box.edited:
            logger_setup.get_logger().info(f"GPS fields not edited")
            return
        logger_setup.get_logger().info('Update_gps called. Collecting input values.')
        if len(self.item_ids) == 0:
            logger_setup.get_logger().info(f"No samples to update")
            return
        create_savepoint('before_update')
        gps_format_abbreviation = self.gps_format_comboBox.currentText()
        self.gps_format_model.setFilter(f"GPSFormatAbbreviation = '{gps_format_abbreviation}'")
        gps_format_id = self.gps_format_model.data(self.gps_format_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
        self.gps_format_model.setFilter('')  # Clear the filter
        if 'D' in gps_format_abbreviation:
            lat_deg = return_number(self.lat_deg_lineEdit.text())
            if not lat_deg:
                lat_deg = 'Null'
            lon_deg = return_number(self.lon_deg_lineEdit.text())
            if not lon_deg:
                lon_deg = 'Null'
            if 'M' in gps_format_abbreviation:
                lat_min = return_number(self.lat_min_lineEdit.text())
                if not lat_min:
                    lat_min = 'Null'
                lon_min = return_number(self.lon_min_lineEdit.text())
                if not lon_min:
                    lon_min = 'Null'
                if 'S' in gps_format_abbreviation:
                    lat_sec = return_number(self.lat_sec_lineEdit.text())
                    if not lat_sec:
                        lat_sec = 'Null'
                    lon_sec = return_number(self.lon_sec_lineEdit.text())
                    if not lon_sec:
                        lon_sec = 'Null'
                else:
                    lat_sec = 'Null'
                    lon_sec = 'Null'
            else:
                lat_min = 'Null'
                lon_min = 'Null'
                lat_sec = 'Null'
                lon_sec = 'Null'
            if '+/-' in gps_format_abbreviation:
                lat_dir = 'Null'
                lon_dir = 'Null'
            elif ' NSEW' in gps_format_abbreviation:
                lat_dir = self.lat_comboBox.currentText()
                lon_dir = self.lon_comboBox.currentText()
                if not lat_dir:
                    lat_dir = 'Null'
                else:
                    self.direction_unit_model.setFilter(f"DirectionUnitAbbreviation = '{lat_dir}'")
                    lat_dir = self.direction_unit_model.data(self.direction_unit_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
                if not lon_dir:
                    lon_dir = 'Null'
                else:
                    self.direction_unit_model.setFilter(f"DirectionUnitAbbreviation = '{lon_dir}'")
                    lon_dir = self.direction_unit_model.data(self.direction_unit_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            utm_zone = 'Null'
            utm_n = 'Null'
            utm_e = 'Null'
        elif gps_format_abbreviation == 'UTM':
            lat_deg = 'Null'
            lat_min = 'Null'
            lat_sec = 'Null'
            lat_dir = 'Null'
            lon_deg = 'Null'
            lon_min = 'Null'
            lon_sec = 'Null'
            lon_dir = 'Null'
            utm_zone = return_number(self.utm_zone_lineEdit.text())
            if not utm_zone:
                utm_zone = 'Null'
            utm_n = return_number(self.utm_n_lineEdit.text())
            if not utm_n:
                utm_n = 'Null'
            utm_e = return_number(self.utm_e_lineEdit.text())
            if not utm_e:
                utm_e = 'Null'
        elevation = return_number(self.elevation_lineEdit.text())
        if not elevation:
            elevation = 'Null'
        elevation_error = return_number(self.elevation_error_lineEdit.text())
        if not elevation_error:
            elevation_error = 'Null'
        elevation_unit = self.elevation_unit_comboBox.currentText()
        if not elevation_unit:
            elevation_unit = 'Null'
        else:
            self.elevation_unit_model.setFilter(f"DistanceUnitAbbreviation = '{elevation_unit}'")
            elevation_unit = self.elevation_unit_model.data(self.elevation_unit_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)

        query = QtS.QSqlQuery()
        gps_to_delete = []
        gps_id = None
        gps_columns = ['GPSLatDeg', 'GPSLatMin', 'GPSLatSec', 'GPSLatDirectionID', 'GPSLonDeg', 'GPSLonMin',
                       'GPSLonSec', 'GPSLonDirectionID', 'GPSUTMZone', 'GPSUTMN', 'GPSUTME', 'GPSElev',
                       'GPSElevError', 'GPSElevUnitID', 'GPSFormatID']
        gps_values = [lat_deg, lat_min, lat_sec, lat_dir, lon_deg, lon_min, lon_sec, lon_dir,
                      utm_zone, utm_n, utm_e, elevation, elevation_error, elevation_unit, gps_format_id]
        duplicate_id = self.check_existing_gps(gps_columns, gps_values)
        if duplicate_id:
            logger_setup.get_logger().info(f"GPS location already exists with ID {duplicate_id}. Updating.")
            gps_id = duplicate_id
        if len(self.item_ids) > 1:
            self.item_model = SQLiteTableModel(f"SELECT {self.item_view_gps_header} FROM {self.item_edit_view} WHERE {self.item_id_header} in {tuple(self.item_ids)}")
        elif len(self.item_ids) == 1:
            self.item_model = SQLiteTableModel(f"SELECT {self.item_view_gps_header} FROM {self.item_edit_view} WHERE {self.item_id_header} = {self.item_ids[0]}")
        gps_ids = []
        for row in range(self.item_model.rowCount()):
            id_value = self.item_model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole)
            if id_value and isinstance(id_value, int) and id_value not in gps_ids:
                gps_ids.append(self.item_model.index(row, 0).data())
        qgps_columns = ', '.join(gps_columns)
        qgps_values = ', '.join(str(v) for v in gps_values)
        if len(gps_ids) > 0:
            logger_setup.get_logger().info(f"Checking {len(gps_ids)} GPS locations associated with the {self.table}")
            for gps in gps_ids:
                self.item_model = SQLiteTableModel(f"SELECT {self.item_id_header} FROM {self.item_edit_view} WHERE {self.table_gps_id_header} = {gps}")
                other_item_model = QtS.QSqlQueryModel()
                other_item_model.setQuery(f"SELECT {self.other_table_id_header} FROM {self.other_edit_view} WHERE {self.other_table_gps_id_header} = {gps}")
                if self.item_model.rowCount() == 0 and other_item_model.rowCount() == 0:
                    logger_setup.get_logger().info(f"GPS location {gps} is not associated with any other samples or columns")
                    if not gps_id:
                        # Choose the first GPS location to update and delete the rest that will be unused
                        gps_id = gps
                    elif gps != gps_id:
                        gps_to_delete.append(gps)
        if not gps_id:
            logger_setup.get_logger().info(f"Adding a new GPS location.")
            error, header = validate_insert('GPSLocations', gps_columns, gps_values, gps_format_id)
            if error:
                logger_setup.get_logger().error(f"Invalid GPS input: {error}")
                rollback_savepoint('before_update')
                return

            if not query.exec(f'''INSERT INTO GPSLocations ({qgps_columns}) VALUES ({qgps_values})'''):
                logger_setup.get_logger().critical(f"Error inserting GPS location")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                rollback_savepoint('before_update')
                return
            logger_setup.get_logger().info(f"Inserted new GPS location")
            gps_id = query.lastInsertId()
        else:
            if not query.exec(f"SELECT {qgps_columns} FROM GPSLocations WHERE GPSLocationID = {gps_id}"):
                logger_setup.get_logger().error(f"Error getting current values for GPS")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                rollback_savepoint('before_update')
                return
            query.next()
            existing_values = [query.value(i) for i in range(query.record().count())]
            for s in existing_values:
                index = existing_values.index(s)
                if not s:
                    s = 'Null'
                    existing_values[index] = s
            if existing_values != gps_values:
                logger_setup.get_logger().info(f"GPS location {gps_id} has different values than the input. Updating.")
                error, header = validate_update('GPSLocations', gps_columns, gps_values, f'GPSFormatID = {gps_format_id}')
                if error:
                    logger_setup.get_logger().error(f"Invalid GPS input: {error}")
                    rollback_savepoint('before_update')
                    return
                logger_setup.get_logger().info(f"Valid GPS information")
                if not query.exec(f'''UPDATE GPSLocations SET ({qgps_columns}) = ({qgps_values}) WHERE GPSLocationID = {gps_to_update[0]}'''):
                    logger_setup.get_logger().critical(f"Error updating GPS")
                    logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                    logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                    rollback_savepoint('before_update')
                    return
                update_modified_timestamp('GPSLocations', gps_id)
                logger_setup.get_logger().info(f"Updated GPSLocationID {gps_id}")
        if len(gps_to_delete) > 0:
            if not query.exec(f'DELETE FROM GPSLocations WHERE GPSLocationID in {tuple(gps_to_delete)}'):
                logger_setup.get_logger().critical(f"Error deleting unused GPS")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                rollback_savepoint('before_update')
                return
            logger_setup.get_logger().info(f"Deleted unused GPSLocationIDs {gps_to_delete}")
        if not convert_gps_location(gps_id):
            logger_setup.get_logger().error(f"Error converting GPS location {gps_id}")
            rollback_savepoint('before_update')
            return
        for item_id in self.item_ids:
            if not query.exec(f'''UPDATE {self.table} SET {self.table_gps_id_header} = {gps_id} WHERE {self.item_id_header} = {item_id}'''):
                logger_setup.get_logger().critical(f"Error updating GPS for selected {self.table}")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                rollback_savepoint('before_update')
                return
            update_modified_timestamp(self.table, [item_id])
            logger_setup.get_logger().info(f"Updated {self.item_id_header} {item_id} with GPSLocationID {gps_id}")
        self.updated = True
        logger_setup.get_logger().info('Update_gps finished')
        release_savepoint('before_update')
        self.lost_group_box.reset_edited()
        self.lost_group_box = None
        return True

    def check_existing_gps(self, gps_columns, gps_values):
        """
        Check if the GPS values already exist in the database.
        :param gps_columns: list of column names
        :param gps_values: list of values to check
        :return: existing GPSLocationID if the values already exist, None otherwise
        """
        query = QtS.QSqlQuery()
        conditions = []
        for i in range(len(gps_columns)):
            if gps_values[i] != 'Null':
                conditions.append(f"{gps_columns[i]} = :{gps_columns[i]}")
            else:
                conditions.append(f"{gps_columns[i]} IS NULL")
        sql_where = " AND ".join(conditions)
        sql_query = f"SELECT GPSLocationID FROM GPSLocations WHERE {sql_where}"
        query.prepare(sql_query)
        for i in range(len(gps_columns)):
            if gps_values[i] != 'Null':
                query.bindValue(f":{gps_columns[i]}", gps_values[i])
        if not query.exec():
            logger_setup.get_logger().critical('Error checking for duplicates', self)
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {sql_query}\n{gps_values}")
            return None
        if query.next():
            existing_gps_id = query.value(0)
            logger_setup.get_logger().info(f"Found existing GPSLocationID {existing_gps_id} with values {gps_values}")
            return existing_gps_id
        else:
            logger_setup.get_logger().info(f"No existing GPSLocationID found with values {gps_values}")
            return None


    def clear_fields(self):
        self.disconnect_text_signals()
        self.lat_deg_lineEdit.clear()
        self.lat_min_lineEdit.clear()
        self.lat_sec_lineEdit.clear()
        self.lon_deg_lineEdit.clear()
        self.lon_min_lineEdit.clear()
        self.lon_sec_lineEdit.clear()
        self.utm_zone_lineEdit.clear()
        self.utm_n_lineEdit.clear()
        self.utm_e_lineEdit.clear()
        self.elevation_lineEdit.clear()
        self.elevation_error_lineEdit.clear()
        # self.gps_format_comboBox.setCurrentIndex(-1)
        self.lat_comboBox.setCurrentIndex(-1)
        self.lon_comboBox.setCurrentIndex(-1)
        self.elevation_unit_comboBox.setCurrentIndex(-1)
        self.connect_signals()
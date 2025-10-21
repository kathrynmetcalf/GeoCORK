# from operator import itemgetter
import os
import sys

import PyQt6
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6.uic import loadUi
from Functions.Widget_classes import (set_table, set_comboBox_text, SQLiteTableModel, populate_combo_box, get_headers,
                                      return_number, delete_data, show_loading_dialog, close_loading_dialog)
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Check_triggers import validate_insert, validate_update, update_modified_timestamp
from Functions.Alter_database import convert_gps_location
import Functions.Database_views as DB_views
import time
import logger_setup

class GPSFields(QtW.QWidget):
    def __init__(self, table: str, item_ids: list | None, parent=None):
        super().__init__(parent)
        show_loading_dialog('Loading', 'Loading GPS Fields...')
        logger_setup.get_logger().info('Starting GPSFields')
        start_gps_time = time.time()
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "GPSFields.ui")
        loadUi(sources_ui_file, self)

        self.table = table
        if self.table == 'Columns':
            self.table_gps_id_header = 'ColumnBaseGPSID'
            self.item_id_header = 'ColumnID'
            self.item_view_gps_header = 'ColumnGPSLocationID'
            self.other_table = 'Samples'
            self.other_table_gps_id_header = 'SampleGPSLocationID'
            self.other_table_id_header = 'SampleID'
        elif self.table == 'Samples':
            self.table_gps_id_header = 'SampleGPSLocationID'
            self.item_id_header = 'SampleID'
            self.item_view_gps_header = 'SampleGPSLocationID'
            self.other_table = 'Columns'
            self.other_table_gps_id_header = 'ColumnBaseGPSID'
            self.other_table_id_header = 'ColumnID'
        else:
            raise ValueError('Table must be either "Columns" or "Samples"')
        self.item_ids = item_ids
        self.updated = False
        self.initial_values = []
        self.errmsg = QtW.QMessageBox(self)
        self.focus_timer = QtC.QTimer(self)
        self.focus_timer.setSingleShot(True)
        self.focus_timer.timeout.connect(self.update_gps)
        self._isApplicationFocused = True
        QtW.QApplication.instance().installEventFilter(self)

        self.item_model = QtS.QSqlQueryModel()
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
        close_loading_dialog('Loading', 'Loading GPS Fields...')
        logger_setup.get_logger().info(f'Finished GPSFields initialization in {time.time() - start_gps_time} seconds')

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
        self.gps_format_comboBox.setCurrentText(gps_format_abbreviation)
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
        logger_setup.get_logger().info(f"Checking GPS field focus...")
        if self.latlon_groupBox.any_child_has_focus() or self.latlon_groupBox.edited:
            if not self.latlon_groupBox.edited:
                for child in self.latlon_groupBox.findChildren(QtW.QWidget):
                    if child.hasFocus():
                        logger_setup.get_logger().info(f"Child {child.objectName()} has focus")
                        self.latlon_groupBox.set_edited(child)
                        break
            self.latlon_groupBox.clearFocus()
            if self.latlon_groupBox.edited:
                logger_setup.get_logger().info(f"GPS was edited")
                self.lost_group_box = self.latlon_groupBox
                self.update_gps()
        elif self.utm_groupBox.any_child_has_focus() or self.utm_groupBox.edited:
            if not self.utm_groupBox.edited:
                for child in self.utm_groupBox.findChildren(QtW.QWidget):
                    if child.hasFocus():
                        logger_setup.get_logger().info(f"Child {child.objectName()} has focus")
                        self.utm_groupBox.set_edited(child)
                        break
            self.utm_groupBox.clearFocus()
            if self.utm_groupBox.edited:
                logger_setup.get_logger().info(f"GPS was edited")
                self.lost_group_box = self.utm_groupBox
                self.update_gps()
        elif self.elev_groupBox.any_child_has_focus() or self.elev_groupBox.edited:
            if not self.elev_groupBox.edited:
                for child in self.elev_groupBox.findChildren(QtW.QWidget):
                    if child.hasFocus():
                        logger_setup.get_logger().info(f"Child {child.objectName()} has focus")
                        self.elev_groupBox.set_edited(child)
                        break
            self.elev_groupBox.clearFocus()
            if self.elev_groupBox.edited:
                logger_setup.get_logger().info(f"GPS was edited")
                self.lost_group_box = self.elev_groupBox
                self.update_gps()

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
        logger_setup.get_logger().info(f"Focus lost delay called")
        if self._isApplicationFocused:
            self.lost_group_box = self.sender()
            logger_setup.get_logger().info(f"Lost focus from {self.lost_group_box.objectName()}. Starting timer.")
            self.focus_timer.start(200)

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
            query_where_str = f' WHERE {self.item_id_header} IS NULL'
        self.item_model = QtS.QSqlQueryModel()
        self.item_model.setQuery(f'SELECT {self.table_gps_id_header} FROM {self.table}{query_where_str}')
        while self.item_model.canFetchMore():
            self.item_model.fetchMore()
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
            # logger_setup.get_logger().info(f'Populating {header}')
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
                if text is None or text == '':
                    self.lat_deg_lineEdit.setText('')
                else:
                    self.lat_deg_lineEdit.setText(f"{text}")
            elif 'LatMin' in header:
                if text is None or text == '':
                    self.lat_min_lineEdit.setText('')
                else:
                    self.lat_min_lineEdit.setText(f"{text}")
            elif 'LatSec' in header:
                if text is None or text == '':
                    self.lat_sec_lineEdit.setText('')
                else:
                    self.lat_sec_lineEdit.setText(f"{text}")
            elif 'LatDir' in header:
                if text is None or text == '':
                    set_comboBox_text(self.lat_comboBox, '')
                else:
                    if isinstance(text, int):
                        self.lat_comboBox.setCurrentIndex(text-1)
                    else:
                        self.lat_comboBox.setCurrentText(text)
            elif 'LonDeg' in header:
                if text is None or text == '':
                    self.lon_deg_lineEdit.setText('')
                else:
                    self.lon_deg_lineEdit.setText(f"{text}")
            elif 'LonMin' in header:
                if text is None or text == '':
                    self.lon_min_lineEdit.setText('')
                else:
                    self.lon_min_lineEdit.setText(f"{text}")
            elif 'LonSec' in header:
                if text is None or text == '':
                    self.lon_sec_lineEdit.setText('')
                else:
                    self.lon_sec_lineEdit.setText(f"{text}")
            elif 'LonDir' in header:
                if text is None or text == '':
                    set_comboBox_text(self.lon_comboBox, '')
                else:
                    if isinstance(text, int):
                        # The lat_comboBox has the first two items as "N" and "S", so we need to subtract 3 from the ID to get "E" or "W"
                        self.lon_comboBox.setCurrentIndex(text-3)
                    else:
                        self.lon_comboBox.setCurrentText(text)
            elif 'UTMZone' in header:
                if text is None or text == '':
                    self.utm_zone_lineEdit.setText('')
                else:
                    self.utm_zone_lineEdit.setText(f"{text}")
            elif 'UTMN' in header:
                if text is None or text == '':
                    self.utm_n_lineEdit.setText('')
                else:
                    self.utm_n_lineEdit.setText(f"{text}")
            elif 'UTME' in header:
                if text is None or text == '':
                    self.utm_e_lineEdit.setText('')
                else:
                    self.utm_e_lineEdit.setText(f"{text}")
            elif 'ElevError' in header and 'Calculated' not in header:
                if text is None or text == '':
                    self.elevation_error_lineEdit.setText('')
                else:
                    self.elevation_error_lineEdit.setText(f"{text}")
            elif 'ElevUnit' in header:
                if text is None or text == '':
                    set_comboBox_text(self.elevation_unit_comboBox, settings.value('elevation_unit_abbreviation'))
                else:
                    if isinstance(text, int):
                        self.elevation_unit_comboBox.setCurrentIndex(text-1)
                    else:
                        self.elevation_unit_comboBox.setCurrentText(text)
            elif 'Elev' in header and 'Calculated' not in header:
                if text is None or text == '':
                    self.elevation_lineEdit.setText('')
                else:
                    self.elevation_lineEdit.setText(f"{text}")
            elif 'GPSFormat' in header:
                if text is None or text == '':
                    if self.gps_format_comboBox.currentIndex() == -1:
                        # If nothing has been selected yet, set it to the default
                        set_comboBox_text(self.gps_format_comboBox, settings.value('gps_format_abbreviation'))
                else:
                    if isinstance(text, int):
                        self.gps_format_comboBox.setCurrentIndex(text-1)
                    else:
                        self.gps_format_comboBox.setCurrentText(text)
        self.initial_values = self.get_values()[1]
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

    def get_values(self):
        gps_columns = ['GPSLatDeg', 'GPSLatMin', 'GPSLatSec', 'GPSLatDirectionID', 'GPSLonDeg', 'GPSLonMin',
                       'GPSLonSec', 'GPSLonDirectionID', 'GPSUTMZone', 'GPSUTMN', 'GPSUTME', 'GPSElev',
                       'GPSElevError', 'GPSElevUnitID', 'GPSFormatID']
        gps_format_abbreviation = self.gps_format_comboBox.currentText()
        if gps_format_abbreviation == '-' or gps_format_abbreviation == '':
            lat_deg = return_number(self.lat_deg_lineEdit.text())
            if not lat_deg:
                lat_deg = 'NULL'
            lat_min = return_number(self.lat_min_lineEdit.text())
            if not lat_min:
                lat_min = 'NULL'
            lat_sec = return_number(self.lat_sec_lineEdit.text())
            if not lat_sec:
                lat_sec = 'NULL'
            lon_deg = return_number(self.lon_deg_lineEdit.text())
            if not lon_deg:
                lon_deg = 'NULL'
            lon_min = return_number(self.lon_min_lineEdit.text())
            if not lon_min:
                lon_min = 'NULL'
            lon_sec = return_number(self.lon_sec_lineEdit.text())
            if not lon_sec:
                lon_sec = 'NULL'
            lat_dir = self.lat_comboBox.currentText()
            lon_dir = self.lon_comboBox.currentText()
            if not lat_dir:
                lat_dir = 'NULL'
            else:
                self.direction_unit_model.setFilter(f"DirectionUnitAbbreviation = '{lat_dir}'")
                lat_dir = self.direction_unit_model.data(self.direction_unit_model.index(0, 0),
                                                         QtC.Qt.ItemDataRole.DisplayRole)
            if not lon_dir:
                lon_dir = 'NULL'
            else:
                self.direction_unit_model.setFilter(f"DirectionUnitAbbreviation = '{lon_dir}'")
                lon_dir = self.direction_unit_model.data(self.direction_unit_model.index(0, 0),
                                                         QtC.Qt.ItemDataRole.DisplayRole)
            utm_zone = return_number(self.utm_zone_lineEdit.text())
            if not utm_zone:
                utm_zone = 'NULL'
            utm_n = return_number(self.utm_n_lineEdit.text())
            if not utm_n:
                utm_n = 'NULL'
            utm_e = return_number(self.utm_e_lineEdit.text())
            if not utm_e:
                utm_e = 'NULL'
            if gps_format_abbreviation == '':
                gps_format_id = 'NULL'
            elif gps_format_abbreviation == '-':
                gps_format_id = '-'
        else:
            self.gps_format_model.setFilter(f"GPSFormatAbbreviation = '{gps_format_abbreviation}'")
            gps_format_id = self.gps_format_model.data(self.gps_format_model.index(0, 0),
                                                       QtC.Qt.ItemDataRole.DisplayRole)
        self.gps_format_model.setFilter('')  # Clear the filter
        if 'D' in gps_format_abbreviation:
            lat_deg = return_number(self.lat_deg_lineEdit.text())
            if not lat_deg:
                lat_deg = 'NULL'
            lon_deg = return_number(self.lon_deg_lineEdit.text())
            if not lon_deg:
                lon_deg = 'NULL'
            if 'M' in gps_format_abbreviation:
                lat_min = return_number(self.lat_min_lineEdit.text())
                if not lat_min:
                    lat_min = 'NULL'
                lon_min = return_number(self.lon_min_lineEdit.text())
                if not lon_min:
                    lon_min = 'NULL'
                if 'S' in gps_format_abbreviation:
                    lat_sec = return_number(self.lat_sec_lineEdit.text())
                    if not lat_sec:
                        lat_sec = 'NULL'
                    lon_sec = return_number(self.lon_sec_lineEdit.text())
                    if not lon_sec:
                        lon_sec = 'NULL'
                else:
                    lat_sec = 'NULL'
                    lon_sec = 'NULL'
            else:
                lat_min = 'NULL'
                lon_min = 'NULL'
                lat_sec = 'NULL'
                lon_sec = 'NULL'
            if '+/-' in gps_format_abbreviation:
                lat_dir = 'NULL'
                lon_dir = 'NULL'
            elif ' NSEW' in gps_format_abbreviation:
                lat_dir = self.lat_comboBox.currentText()
                lon_dir = self.lon_comboBox.currentText()
                if not lat_dir:
                    lat_dir = 'NULL'
                else:
                    self.direction_unit_model.setFilter(f"DirectionUnitAbbreviation = '{lat_dir}'")
                    lat_dir = self.direction_unit_model.data(self.direction_unit_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
                if not lon_dir:
                    lon_dir = 'NULL'
                else:
                    self.direction_unit_model.setFilter(f"DirectionUnitAbbreviation = '{lon_dir}'")
                    lon_dir = self.direction_unit_model.data(self.direction_unit_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            utm_zone = 'NULL'
            utm_n = 'NULL'
            utm_e = 'NULL'
        elif gps_format_abbreviation == 'UTM':
            lat_deg = 'NULL'
            lat_min = 'NULL'
            lat_sec = 'NULL'
            lat_dir = 'NULL'
            lon_deg = 'NULL'
            lon_min = 'NULL'
            lon_sec = 'NULL'
            lon_dir = 'NULL'
            utm_zone = return_number(self.utm_zone_lineEdit.text())
            if not utm_zone:
                utm_zone = 'NULL'
            utm_n = return_number(self.utm_n_lineEdit.text())
            if not utm_n:
                utm_n = 'NULL'
            utm_e = return_number(self.utm_e_lineEdit.text())
            if not utm_e:
                utm_e = 'NULL'
        elevation = return_number(self.elevation_lineEdit.text())
        if not elevation:
            elevation = 'NULL'
        elevation_error = return_number(self.elevation_error_lineEdit.text())
        if not elevation_error:
            elevation_error = 'NULL'
        elevation_unit = self.elevation_unit_comboBox.currentText()
        if not elevation_unit:
            elevation_unit = 'NULL'
        else:
            self.elevation_unit_model.setFilter(f"DistanceUnitAbbreviation = '{elevation_unit}'")
            elevation_unit = self.elevation_unit_model.data(self.elevation_unit_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
        gps_values = [lat_deg, lat_min, lat_sec, lat_dir, lon_deg, lon_min, lon_sec, lon_dir,
                      utm_zone, utm_n, utm_e, elevation, elevation_error, elevation_unit, gps_format_id]
        return gps_columns, gps_values

    def update_gps(self):
        logger_setup.get_logger().info('Update_gps called when focus timer timed out')
        if not self.lost_group_box.edited:
            logger_setup.get_logger().info(f"GPS fields not edited")
            return
        show_loading_dialog('Updating', 'Updating GPS...')
        logger_setup.get_logger().info('Update_gps called. Collecting input values.')
        if len(self.item_ids) == 0:
            logger_setup.get_logger().info(f"No samples to update")
            close_loading_dialog('Updating', 'Updating GPS...')
            return
        gps_columns, gps_values = self.get_values()
        if gps_values == self.initial_values:
            logger_setup.get_logger().info(f"GPS fields not edited")
            close_loading_dialog('Updating', 'Updating GPS...')
            return
        format_index = gps_columns.index('GPSFormatID')
        gps_format_id = gps_values[format_index]
        if gps_format_id in ('-', '', 'NULL') and gps_values != self.initial_values:
            logger_setup.get_logger().error(f"Must set a single GPS format to update location data")
        elif '-' not in gps_values:
            if not self.update_single_gps(gps_columns, gps_values, self.item_ids):
                close_loading_dialog('Updating', 'Updating GPS...')
                return
        else:
            if not self.update_multiple_gps(gps_columns, gps_values):
                close_loading_dialog('Updating', 'Updating GPS...')
                return
        self.lost_group_box.reset_edited()
        self.lost_group_box = None
        self.initial_values = gps_values
        close_loading_dialog('Updating', 'Updating GPS...')

    def update_multiple_gps(self, gps_columns, gps_values):
        """
        Update the selected samples with multiple GPS locations. Only certain GPS columns will be updated.
        :param gps_columns: list of column names
        :param gps_values:  list of values to insert
        :return: True if the update was successful, False otherwise
        """
        # Do not edit those columns and do not look for duplicate
        update_columns = []
        update_values = []
        for column, value in zip(gps_columns, gps_values):
            if value != '-':
                update_columns.append(column)
                update_values.append(value)
        self.item_model.setQuery(
            f'''SELECT {self.table_gps_id_header}, {self.item_id_header} FROM {self.table} WHERE {self.item_id_header} 
                in {tuple(self.item_ids)}''')
        while self.item_model.canFetchMore():
            self.item_model.fetchMore()
        ids_to_update = {}
        for row in range(self.item_model.rowCount()):
            gps_id = self.item_model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole)
            item_id = self.item_model.index(row, 1).data(QtC.Qt.ItemDataRole.DisplayRole)
            if gps_id and isinstance(gps_id, int) and item_id and isinstance(item_id, int):
                if gps_id not in ids_to_update.keys():
                    ids_to_update[gps_id] = [item_id]
                else:
                    ids_to_update[gps_id].append(item_id)
        query = QtS.QSqlQuery()
        if len(ids_to_update) == 0:
            logger_setup.get_logger().info(f"No {self.table} to update")
            return True
        # Get the gps_columns not in update_columns
        unaffected_columns = [gps_columns[i] for i in range(len(gps_columns)) if gps_columns[i] not in update_columns]
        logger_setup.get_logger().info(f"Updating {len(ids_to_update)} GPS locations")
        create_savepoint('before_update')
        delete_gps = True
        for value in gps_values[0:13]:
            if value != 'NULL':
                delete_gps = False
                break
        if delete_gps:
            return self.delete_gps(list(set(ids_to_update.keys())), list(set(ids_to_update.values())))
        for gps_id in ids_to_update:
            item_ids = ids_to_update[gps_id]
            query.prepare(f'''SELECT {', '.join(unaffected_columns)} FROM GPSLocations WHERE GPSLocationID = {gps_id}''')
            if not query.exec():
                logger_setup.get_logger().critical(f"Error getting current values for GPS")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                rollback_savepoint('before_update')
                return
            if not query.next():
                logger_setup.get_logger().critical(f"GPS location {gps_id} not found")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                return
            existing_values = [query.value(i) for i in range(query.record().count())]
            for row in range(len(gps_columns)):
                if gps_columns[row] in unaffected_columns:
                    existing_value = existing_values[unaffected_columns.index(gps_columns[row])]
                    if existing_value is None or existing_value == '':
                        existing_value = 'NULL'
                    gps_values[row] = existing_value
            if not self.update_single_gps(gps_columns, gps_values, item_ids):
                return

    def update_single_gps(self, gps_columns, gps_values, item_ids: list):
        """
        Update the selected samples with a single GPS location
        :param gps_columns: list of column names
        :param gps_values: list of values to insert
        """
        query = QtS.QSqlQuery()
        gps_to_delete = []
        gps_id = None
        format_index = gps_columns.index('GPSFormatID')
        gps_format_id = gps_values[format_index]
        delete_gps = True
        for value in gps_values[0:13]:
            if value != 'NULL':
                delete_gps = False
                break
        create_savepoint('before_update')
        duplicate_id = self.check_existing_gps(gps_columns, gps_values)
        if duplicate_id:
            if delete_gps:
                return self.delete_gps([duplicate_id], item_ids)
            logger_setup.get_logger().info(f"GPS location already exists with ID {duplicate_id}. Updating.")
            gps_id = duplicate_id
        else:
            if len(item_ids) > 1:
                self.item_model.setQuery(f"SELECT {self.table_gps_id_header} FROM {self.table} WHERE {self.item_id_header} in {tuple(item_ids)}")
            elif len(item_ids) == 1:
                self.item_model.setQuery(f"SELECT {self.table_gps_id_header} FROM {self.table} WHERE {self.item_id_header} = {item_ids[0]}")
            while self.item_model.canFetchMore():
                self.item_model.fetchMore()
            gps_ids = []
            for row in range(self.item_model.rowCount()):
                id_value = self.item_model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole)
                if id_value and isinstance(id_value, int) and id_value not in gps_ids:
                    gps_ids.append(self.item_model.index(row, 0).data())
            qgps_columns = ', '.join(gps_columns)
            qgps_values = ', '.join(str(v) for v in gps_values)
            if len(gps_ids) > 0:
                if delete_gps:
                    return self.delete_gps(gps_ids, item_ids)
                logger_setup.get_logger().info(f"Checking {len(gps_ids)} GPS locations associated with the {self.table}")
                if len(self.item_ids) > 1:
                    item_where = f"IN {tuple(self.item_ids)}"
                elif len(self.item_ids) == 1:
                    item_where = f"{self.item_ids[0]}"
                for gps in gps_ids:
                    self.item_model.setQuery(f"SELECT {self.item_id_header} FROM {self.table} WHERE {self.table_gps_id_header} = {gps} AND {self.item_id_header} IS NOT {item_where}")
                    while self.item_model.canFetchMore():
                        self.item_model.fetchMore()
                    other_item_model = QtS.QSqlQueryModel()
                    other_item_model.setQuery(f"SELECT {self.other_table_id_header} FROM {self.other_table} WHERE {self.other_table_gps_id_header} = {gps}")
                    while other_item_model.canFetchMore():
                        other_item_model.fetchMore()
                    if self.item_model.rowCount() == 0 and other_item_model.rowCount() == 0:
                        logger_setup.get_logger().info(f"GPS location {gps} is not associated with any other samples or columns")
                        if not gps_id:
                            # Choose the first GPS location to update and delete the rest that will be unused
                            gps_id = gps
                        elif gps != gps_id:
                            gps_to_delete.append(gps)
        if not gps_id:
            if delete_gps:
                rollback_savepoint('before_update')
                return False
            logger_setup.get_logger().info(f"Adding a new GPS location.")
            error, header = validate_insert('GPSLocations', gps_columns, gps_values, gps_format_id)
            if error:
                logger_setup.get_logger().error(f"Invalid GPS input: {error}")
                rollback_savepoint('before_update')
                return False

            if not query.exec(f'''INSERT INTO GPSLocations ({qgps_columns}) VALUES ({qgps_values})'''):
                logger_setup.get_logger().critical(f"Error inserting GPS location")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                rollback_savepoint('before_update')
                return False
            logger_setup.get_logger().info(f"Inserted new GPS location")
            gps_id = query.lastInsertId()
        else:
            if not query.exec(f"SELECT {qgps_columns} FROM GPSLocations WHERE GPSLocationID = {gps_id}"):
                logger_setup.get_logger().error(f"Error getting current values for GPS")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                rollback_savepoint('before_update')
                return False
            query.next()
            existing_values = [query.value(i) for i in range(query.record().count())]
            for s in existing_values:
                index = existing_values.index(s)
                if not s:
                    s = 'NULL'
                    existing_values[index] = s
            if existing_values != gps_values:
                if delete_gps:
                    return self.delete_gps([gps_id], item_ids)
                logger_setup.get_logger().info(f"GPS location {gps_id} has different values than the input. Updating.")
                error, header = validate_update('GPSLocations', gps_columns, gps_values, f'GPSFormatID = {gps_format_id}')
                if error:
                    logger_setup.get_logger().error(f"Invalid GPS input: {error}")
                    rollback_savepoint('before_update')
                    return False
                logger_setup.get_logger().info(f"Valid GPS information")
                if not query.exec(f'''UPDATE GPSLocations SET ({qgps_columns}) = ({qgps_values}) WHERE GPSLocationID = {gps_id}'''):
                    logger_setup.get_logger().critical(f"Error updating GPS")
                    logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                    logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                    rollback_savepoint('before_update')
                    return False
                update_modified_timestamp('GPSLocations', [gps_id])
                logger_setup.get_logger().info(f"Updated GPSLocationID {gps_id}")
        if len(gps_to_delete) > 0:
            if not delete_data('GPSLocations', gps_to_delete):
                logger_setup.get_logger().critical(f"Error deleting unused GPS")
                rollback_savepoint('before_update')
                return False
            logger_setup.get_logger().info(f"Deleted unused GPSLocationIDs {gps_to_delete}")
        if not convert_gps_location(gps_id):
            logger_setup.get_logger().error(f"Error converting GPS location {gps_id}")
            rollback_savepoint('before_update')
            return False
        for item_id in item_ids:
            if not query.exec(f'''UPDATE {self.table} SET {self.table_gps_id_header} = {gps_id} WHERE {self.item_id_header} = {item_id}'''):
                logger_setup.get_logger().critical(f"Error updating GPS for selected {self.table}")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                rollback_savepoint('before_update')
                return False
            update_modified_timestamp(self.table, [item_id])
            logger_setup.get_logger().info(f"Updated {self.item_id_header} {item_id} with GPSLocationID {gps_id}")
        self.updated = True
        logger_setup.get_logger().info('Update_gps finished')
        release_savepoint('before_update')
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
            if gps_values[i] != 'NULL':
                conditions.append(f"{gps_columns[i]} = :{gps_columns[i]}")
            else:
                conditions.append(f"{gps_columns[i]} IS NULL")
        sql_where = " AND ".join(conditions)
        sql_query = f"SELECT GPSLocationID FROM GPSLocations WHERE {sql_where}"
        query.prepare(sql_query)
        for i in range(len(gps_columns)):
            if gps_values[i] != 'NULL':
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


    def delete_gps(self, gps_ids: list, item_ids: list):
        # Check if the gps id is associated with other database items
        if len(gps_ids) == 0 or None in gps_ids:
            logger_setup.get_logger().critical('No GPS IDs to update')
            return False
        if len(item_ids) == 0 or None in item_ids:
            logger_setup.get_logger().critical(f'No {self.table} to update')
            return False
        logger_setup.get_logger().info(f"Checking if GPS location is associated with other entries in {self.table}")
        if len(item_ids) > 1:
            sql_where = f"NOT IN {tuple(item_ids)}"
        else:
            sql_where = f"IS NOT {item_ids[0]}"
        other_items = False
        for gps_id in gps_ids:
            self.item_model.setQuery(
                    f"SELECT {self.item_id_header} FROM {self.table} WHERE {self.table_gps_id_header} = {gps_id} AND {self.item_id_header} {sql_where}")
            while self.item_model.canFetchMore():
                self.item_model.fetchMore()
            other_item_model = QtS.QSqlQueryModel()
            other_item_model.setQuery(
                    f"SELECT {self.other_table_id_header} FROM {self.other_table} WHERE {self.other_table_gps_id_header} = {gps_id}")
            while other_item_model.canFetchMore():
                other_item_model.fetchMore()
            if self.item_model.rowCount() > 0 or other_item_model.rowCount() > 0:
                other_items = True
        if not other_items:
            logger_setup.get_logger().info(
                    f"GPS locations {gps_ids} are not associated with any other samples or columns")
            msg = f"Are you sure you want to delete the GPS for the selected {self.table}?"
            msg_box = QtW.QMessageBox()
            msg_box.setText(msg)
            msg_box.setWindowTitle('Delete GPS')
            msg_box.setIcon(QtW.QMessageBox.Icon.Question)
            msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
            response = msg_box.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                logger_setup.get_logger().info(f"Deleting GPS ID {gps_id}")
                query = QtS.QSqlQuery()
                if len(gps_ids) > 1:
                    gps_where = f"IN {tuple(gps_ids)}"
                else:
                    gps_where = f"IS {gps_ids[0]}"
                query.prepare(f"DELETE FROM GPSLocations WHERE GPSLocationID {gps_where}")
                if not query.exec():
                    logger_setup.get_logger().critical('Error deleting GPS ID', self)
                    logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                    logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                    rollback_savepoint('before_update')
                    return False
                else:
                    logger_setup.get_logger().info('Deleted GPS ID', self)
                    self.updated = True
                    release_savepoint('before_update')
                    return True
            else:
                logger_setup.get_logger().info(f"Canceled deletion of GPS")
                rollback_savepoint('before_update')
                return False
        else:
            logger_setup.get_logger().info(f"GPS locations {gps_ids} associated with other items in the database")
            msg = f"The GPS is associated with other items in the database. Do you want to delete the GPS for all items or remove it from the selected items only?"
            msg_box = QtW.QMessageBox()
            msg_box.setText(msg)
            msg_box.setWindowTitle('Delete GPS')
            msg_box.setIcon(QtW.QMessageBox.Icon.Question)
            cancel_button = QtW.QPushButton('Cancel')
            delete_all_button = QtW.QPushButton(f'Delete From All')
            delete_selected_button = QtW.QPushButton(f'Delete From Selected Only')
            msg_box.addButton(cancel_button, QtW.QMessageBox.ButtonRole.RejectRole)
            msg_box.addButton(delete_all_button, QtW.QMessageBox.ButtonRole.AcceptRole)
            msg_box.addButton(delete_selected_button, QtW.QMessageBox.ButtonRole.ActionRole)
            msg_box.exec()
            response = msg_box.clickedButton()
            if response == QtW.QMessageBox.ButtonRole.RejectRole:
                rollback_savepoint('before_update')
                return False
            elif response == QtW.QMessageBox.ButtonRole.AcceptRole:
                logger_setup.get_logger().info(f"Deleting GPS ID {gps_id}")
                query = QtS.QSqlQuery()
                query.prepare(f"DELETE FROM GPSLocations WHERE GPSLocationID = {gps_id}")
                if not query.exec():
                    logger_setup.get_logger().critical('Error deleting GPS ID', self)
                    logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                    logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                    rollback_savepoint('before_update')
                    return False
                else:
                    logger_setup.get_logger().info('Deleted GPS ID', self)
                    self.updated = True
                    release_savepoint('before_update')
                    return True
            elif response == QtW.QMessageBox.ButtonRole.ActionRole:
                logger_setup.get_logger().info(f"Removing GPS ID {gps_id} from {len(item_ids)} {self.table}")
                sql_where = sql_where.replace('NOT ','')
                query = QtS.QSqlQuery()
                query.prepare(f"UPDATE {self.table} SET ({self.table_gps_id_header}) VALUES (NULL) WHERE {sql_where}")
                if not query.exec():
                    logger_setup.get_logger().critical('Error removing GPS ID from selected items', self)
                    logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                    logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                    rollback_savepoint('before_update')
                    return False
                else:
                    logger_setup.get_logger().info('Removed GPS ID', self)
                    self.updated = True
                    release_savepoint('before_update')
                    return True


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
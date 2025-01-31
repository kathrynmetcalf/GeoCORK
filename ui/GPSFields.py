# from operator import itemgetter

import PyQt6
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6.uic import loadUi
from Functions.Table_classes import set_table, set_comboBox_text, SQLiteTableModel
from Functions.Settings_manager import settings
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Check_triggers import validate_insert, validate_update, update_modified_timestamp
import Functions.Database_views as DB_views

class GPSFields(QtW.QWidget):
    def __init__(self, table: str, item_ids: list | None, parent=None):
        super().__init__(parent)

        gps_ui_file = "ui/GPSFields.ui"
        loadUi(gps_ui_file, self)
        self.table = table
        if self.table == 'Columns':
            self.table_gps_id_header = 'ColumnBaseGPSID'
            self.item_id_header = 'ColumnID'
            self.item_ifnull_query = DB_views.ColumnIfNullQuery()
            self.other_table = 'Samples'
            self.other_table_gps_id_header = 'SampleGPSLocationID'
            self.other_table_id_header = 'SampleID'
            self.other_ifnull_view = 'SampleIfNullView'
        elif self.table == 'Samples':
            self.table_gps_id_header = 'SampleGPSLocationID'
            self.item_id_header = 'SampleID'
            self.item_ifnull_query = DB_views.SampleIfNullQuery()
            self.other_table = 'Columns'
            self.other_table_gps_id_header = 'ColumnBaseGPSID'
            self.other_table_id_header = 'ColumnID'
            self.other_ifnull_view = 'ColumnIfNullView'
        else:
            raise ValueError('Table must be either "Columns" or "Samples"')
        self.item_ids = item_ids
        self.updated = False
        self.errmsg = QtW.QMessageBox(self)

        self.item_model = QtS.QSqlTableModel()
        self.full_item_model = QtS.QSqlTableModel()
        self.gps_format_model = QtS.QSqlTableModel()
        self.gps_location_model = QtS.QSqlTableModel()
        self.direction_unit_model = QtS.QSqlTableModel()
        self.lat_direction_model = QtS.QSqlTableModel()
        self.lon_direction_model = QtS.QSqlTableModel()
        self.distance_unit_model = QtS.QSqlTableModel()
        self.elevation_unit_model = QtS.QSqlTableModel()

        self.gps_location_ids = ""

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
        set_table(self.gps_format_model, 'GPSFormats')
        set_table(self.gps_location_model, 'GPSLocations')
        set_table(self.direction_unit_model, 'DirectionUnits')
        set_table(self.lat_direction_model, 'DirectionUnits')
        self.lat_direction_model.setFilter('DirectionUnitAbbreviation = "N" OR DirectionUnitAbbreviation = "S"')
        self.lon_direction_model = set_table(self.lon_direction_model, 'DirectionUnits')
        self.lon_direction_model.setFilter('DirectionUnitAbbreviation = "E" OR DirectionUnitAbbreviation = "W"')
        self.elevation_unit_model = set_table(self.elevation_unit_model, 'DistanceUnits')

        elevation_unit_id = settings.value('elevation_unit_id')
        gps_format_id = settings.value('gps_format_id')
        self.gps_format_comboBox.setModel(self.gps_format_model)
        self.gps_format_comboBox.setModelColumn(self.gps_format_model.record().indexOf('GPSFormatAbbreviation'))
        self.gps_format_comboBox.setCurrentIndex(gps_format_id - 1)
        self.lat_comboBox.setModel(self.lat_direction_model)
        self.lat_comboBox.setModelColumn(self.lat_direction_model.record().indexOf('DirectionUnitAbbreviation'))
        self.lon_comboBox.setModel(self.lon_direction_model)
        self.lon_comboBox.setModelColumn(self.lon_direction_model.record().indexOf('DirectionUnitAbbreviation'))
        self.elevation_unit_comboBox.setModel(self.elevation_unit_model)
        self.elevation_unit_comboBox.setModelColumn(self.elevation_unit_model.record().indexOf('DistanceUnitAbbreviation'))
        self.elevation_unit_comboBox.setCurrentIndex(elevation_unit_id - 1)

    def connect_signals(self):
        self.gps_format_comboBox.currentTextChanged.connect(self.display_gps)
        self.latlon_groupBox.connect_child_signals()
        self.latlon_groupBox.focusLost.connect(self.update_gps)
        self.utm_groupBox.connect_child_signals()
        self.utm_groupBox.focusLost.connect(self.update_gps)
        self.elev_groupBox.connect_child_signals()
        self.elev_groupBox.focusLost.connect(self.update_gps)

    def disconnect_text_signals(self):
        self.latlon_groupBox.disconnect_child_signals()
        self.utm_groupBox.disconnect_child_signals()
        self.elev_groupBox.disconnect_child_signals()
        try:
            self.gps_format_comboBox.currentTextChanged.disconnect(self.display_gps)
        except TypeError:
            pass

    def populate_fields(self):
        if len(self.item_ids) > 1:
            item_ifnull_model = SQLiteTableModel(f'{self.item_ifnull_query} WHERE {self.table}.{self.item_id_header} in {tuple(self.item_ids)}')
        elif len(self.item_ids) == 1:
            item_ifnull_model = SQLiteTableModel(f'{self.item_ifnull_query} WHERE {self.table}.{self.item_id_header} = {self.item_ids[0]}')
        else:
            item_ifnull_model = SQLiteTableModel(f'{self.item_ifnull_query}')
        if item_ifnull_model.rowCount() == 0:
            self.errmsg.setText(f'Error: No GPS location found for the selected {self.table.lower()}')
            self.errmsg.exec()
            return
        text_values = []
        headers = []
        for col in range(item_ifnull_model.columnCount()):
            # If there is only one value concatenated in the column, add it to the list, otherwise add '-'
            text = item_ifnull_model._data[0][col]
            header = item_ifnull_model._headers[col]
            header = header.split('ifnull(')[1].split(',"Null')[0]
            headers.append(header)
            if ',' in text:
                if 'Description' in header:
                    text_values.append(text)
                else:
                    text_values.append('-')
            elif text == 'Null':
                text_values.append('')
            else:
                text_values.append(text)
        if len(text_values) > 0 and self.table == 'Columns':
            for header in headers:
                if 'GPSLocationID' in header:
                    self.gps_location_ids = text_values[headers.index(header)]
                elif 'LatDeg' in header:
                    self.lat_deg_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'LatMin' in header:
                    self.lat_min_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'LatSec' in header:
                    self.lat_sec_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'LatDir' in header:
                    set_comboBox_text(self.lat_comboBox, text_values[headers.index(header)])
                elif 'LonDeg' in header:
                    self.lon_deg_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'LonMin' in header:
                    self.lon_min_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'LonSec' in header:
                    self.lon_sec_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'LonDir' in header:
                    set_comboBox_text(self.lon_comboBox, text_values[headers.index(header)])
                elif 'UTMZone' in header:
                    self.utm_zone_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'UTMN' in header:
                    self.utm_n_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'UTME' in header:
                    self.utm_e_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'ElevError' in header:
                    self.elevation_error_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'ElevationUnit' in header:
                    set_comboBox_text(self.elevation_unit_comboBox, text_values[headers.index(header)])
                elif 'Elev' in header:
                    self.elevation_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'GPSFormat' in header:
                    set_comboBox_text(self.gps_format_comboBox, text_values[headers.index(header)])
        elif len(text_values) > 0 and self.table == 'Samples':
            for header in headers:
                if 'GPSLocationID' in header:
                    self.gps_location_ids = text_values[headers.index(header)]
                elif 'LatDeg' in header:
                    self.lat_deg_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'LatMin' in header:
                    self.lat_min_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'LatSec' in header:
                    self.lat_sec_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'LatDir' in header:
                    set_comboBox_text(self.lat_comboBox, text_values[headers.index(header)])
                elif 'LonDeg' in header:
                    self.lon_deg_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'LonMin' in header:
                    self.lon_min_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'LonSec' in header:
                    self.lon_sec_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'LonDir' in header:
                    set_comboBox_text(self.lon_comboBox, text_values[headers.index(header)])
                elif 'UTMZone' in header:
                    self.utm_zone_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'UTMN' in header:
                    self.utm_n_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'UTME' in header:
                    self.utm_e_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'ElevError' in header:
                    self.elevation_error_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'Elev' in header:
                    self.elevation_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'ElevationUnit' in header:
                    set_comboBox_text(self.elevation_unit_comboBox, text_values[headers.index(header)])
                elif 'GPSFormat' in header:
                    set_comboBox_text(self.gps_format_comboBox, text_values[headers.index(header)])
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
                if 'S' in current_gps_format:
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
        print('Update_gps called')
        if len(self.item_ids) > 0:
            create_savepoint('before_update')
            gps_format_abbreviation = self.gps_format_comboBox.currentText()
            self.gps_format_model.setFilter(f"GPSFormatAbbreviation = '{gps_format_abbreviation}'")
            gps_format_id = self.gps_format_model.data(self.gps_format_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            self.gps_format_model.setFilter('')  # Clear the filter
            if 'D' in gps_format_abbreviation:
                lat_deg = self.lat_deg_lineEdit.text()
                lon_deg = self.lon_deg_lineEdit.text()
                if 'M' in gps_format_abbreviation:
                    lat_min = self.lat_min_lineEdit.text()
                    lon_min = self.lon_min_lineEdit.text()
                    if 'S' in gps_format_abbreviation:
                        lat_sec = self.lat_sec_lineEdit.text()
                        lon_sec = self.lon_sec_lineEdit.text()
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
                    self.direction_unit_model.setFilter(f"DirectionUnitAbbreviation = '{lat_dir}'")
                    lat_dir = self.direction_unit_model.data(self.direction_unit_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
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
                utm_zone = self.utm_zone_lineEdit.text()
                utm_n = self.utm_n_lineEdit.text()
                utm_e = self.utm_e_lineEdit.text()
            elevation = self.elevation_lineEdit.text()
            elevation_error = self.elevation_error_lineEdit.text()
            elevation_unit = self.elevation_unit_comboBox.currentText()
            if not elevation:
                elevation = 'Null'
            if not elevation_error:
                elevation_error = 'Null'
            if not elevation_unit:
                elevation_unit = 'Null'
            else:
                self.elevation_unit_model.setFilter(f"DistanceUnitAbbreviation = '{elevation_unit}'")
                elevation_unit = self.elevation_unit_model.data(self.elevation_unit_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)

            if len(self.item_ids) > 1:
                self.item_model.setFilter(f"{self.item_id_header} in {tuple(self.item_ids)}")
            elif len(self.item_ids) == 1:
                self.item_model.setFilter(f"{self.item_id_header} = {self.item_ids[0]}")
            gps_ids = []
            for row in range(self.item_model.rowCount()):
                if self.item_model.index(row, 3).data() != 'Null':
                    gps_ids.append(self.item_model.index(row, 3).data())
            query = QtS.QSqlQuery()
            gps_columns = ['GPSLatDeg', 'GPSLatMin', 'GPSLatSec', 'GPSLatDirectionID', 'GPSLonDeg', 'GPSLonMin',
                           'GPSLonSec', 'GPSLonDirectionID', 'GPSUTMZone', 'GPSUTMN', 'GPSUTME', 'GPSElev',
                           'GPSElevError', 'GPSElevUnitID', 'GPSFormatID']
            qgps_columns = ', '.join(gps_columns)
            gps_values = [f'{lat_deg}', f'{lat_min}', f'{lat_sec}', f'{lat_dir}', f'{lon_deg}', f'{lon_min}',
                          f'{lon_sec}', f'{lon_dir}', f'{utm_zone}', f'{utm_n}', f'{utm_e}', f'{elevation}',
                          f'{elevation_error}', f'{elevation_unit}', f'{gps_format_id}']
            qgps_values = ', '.join(gps_values)
            gps_to_delete = []
            gps_to_update = []
            if len(gps_ids) > 0:
                for gps in gps_ids:
                    self.item_model.setFilter(f"{self.table_gps_id_header} = {gps}")
                    other_item_model = QtS.QSqlTableModel()
                    other_item_model.setFilter(f"{self.other_table_gps_id_header} = {gps}")
                    items_with_gps = []
                    for row in range(self.item_model.rowCount()):
                        if self.item_model.index(row, 0).data() not in self.item_ids:
                            items_with_gps.append(self.item_model.index(row, 0).data())
                    if len(items_with_gps) == 0 and other_item_model.rowCount() == 0:
                        # There are no other samples or columns with this GPS location
                        if len(gps_to_update) == 0:
                            # Choose the first GPS location to update and delete the rest that will be unused
                            gps_to_update.append(gps)
                        else:
                            gps_to_delete.append(gps)
                if len(gps_to_update) == 0:
                    # All gps are associated with other samples or columns, so create a new one
                    error, header = validate_insert('GPSLocations', gps_columns, gps_values, gps_format_id)
                    if error:
                        errtxt = error
                        print(errtxt)
                        rollback_savepoint('before_update')
                        return
                    if not query.exec(f'''INSERT INTO GPSLocations ({qgps_columns}) = (qgps_values)'''):
                        errtxt = query.lastError().text()
                        print(errtxt)
                        rollback_savepoint('before_update')
                        return
                    gps_id = query.lastInsertId()
                else:
                    if not query.exec(f"SELECT {qgps_columns} FROM GPSLocations WHERE GPSLocationID = {gps_to_update[0]}"):
                        errtxt = query.lastError().text()
                        self.errmsg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        return
                    query.next()
                    existing_values = [query.value(i) for i in range(query.record().count())]
                    if existing_values != gps_values:
                        error, header = validate_update('GPSLocations', gps_columns, gps_values, gps_format_id)
                        if error:
                            errtxt = error
                            print(errtxt)
                            rollback_savepoint('before_update')
                            return
                        if not query.exec(f'''UPDATE GPSLocations SET ({qgps_columns}) = ({qgps_values}) WHERE GPSLocationID = {gps_to_update[0]}'''):
                            errtxt = query.lastError().text()
                            print(errtxt)
                            rollback_savepoint('before_update')
                            return
                        update_modified_timestamp('GPSLocations', gps_to_update)
                        gps_id = gps_to_update[0]
                    else:
                        gps_id = gps_to_update[0]
                    if len(gps_to_delete) > 0:
                        if not query.exec(f'DELETE FROM GPSLocations WHERE GPSLocationID in {tuple(gps_to_delete)}'):
                            errtxt = query.lastError().text()
                            print(errtxt)
                            rollback_savepoint('before_update')
                        return
            else:
                # There are no GPS locations associated with the samples or columns
                error, header = validate_insert('GPSLocations', gps_columns, gps_values, gps_format_id)
                if error:
                    errtxt = error
                    print(errtxt)
                    rollback_savepoint('before_update')
                    return
                if not query.exec(f'''INSERT INTO GPSLocations ({qgps_columns}) VALUES({qgps_values})'''):
                    errtxt = query.lastError().text()
                    print(errtxt)
                    rollback_savepoint('before_update')
                    return
                gps_id = query.lastInsertId()
            for item_id in self.item_ids:
                if not query.exec(f'''UPDATE {self.table} SET {self.table_gps_id_header} = {gps_id} WHERE {self.item_id_header} = {item_id}'''):
                    errtxt = query.lastError().text()
                    print(errtxt)
                    rollback_savepoint('before_update')
                    return
                update_modified_timestamp(self.table, [item_id])
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
        self.gps_format_comboBox.setCurrentIndex(-1)
        self.lat_comboBox.setCurrentIndex(-1)
        self.lon_comboBox.setCurrentIndex(-1)
        self.elevation_unit_comboBox.setCurrentIndex(-1)
        self.connect_signals()
import csv
import html
import json
import math
import os
import sys

from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6 import QtWidgets as QtW
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QWidget

import Functions.GPS_conversions as GPS
import Functions.SQLUtils as SQLUtils
import Functions.Text_manipulations as TxM
import logger_setup
from Functions.Settings_manager import SettingsManager
from ui.PlotDialog import PlotDialog
from ui.SampleInformation import SampleInformation
from ui.SampleMapDialogs import SAMPLE_TAG_TABLES, MapAddSampleDialog, BulkTagDialog

settings = SettingsManager().settings

BASEMAPS = {'Terrain': 'terrain', 'Satellite': 'satellite', 'OpenStreetMap': 'openmap', 'Macrostrat': 'macrostrat'}
"""Display name: key used by setBasemap() in SampleMap.html"""

GPS_RAW_COLUMNS = ['GPSLatDeg', 'GPSLatMin', 'GPSLatSec', 'GPSLatDirectionID', 'GPSLonDeg', 'GPSLonMin',
                   'GPSLonSec', 'GPSLonDirectionID', 'GPSUTMZone', 'GPSUTME', 'GPSUTMN']
"""Stored (reported) GPSLocations columns. Decimal degrees are derived from these, since CalculatedLat/CalculatedLon
only exist when the user's GPS display format is lat/lon."""

TABLE_COLUMNS = (['SampleName', 'SampleIGSN', 'Latitude', 'Longitude', 'GPSSampleLocationCalculated', 'SampleElevation']
                 + [schema['name_column'] for schema in SAMPLE_TAG_TABLES.values()] + ['SampleDescription'])
"""Columns shown in the selection table and written to CSV"""


def sample_location_sql() -> str:
    """
    One row per located sample: SQLUtils sample/GPS columns, raw GPS fields, and concatenated Samples tree tags.
    """
    tag_columns = [
        f'REPLACE(GROUP_CONCAT(DISTINCT {table}.{schema["name_column"]}), ",", "; ") AS {schema["name_column"]}'
        for table, schema in SAMPLE_TAG_TABLES.items()]
    columns = ([SQLUtils.qsample_id, SQLUtils.qsample_name, SQLUtils.qigsn, SQLUtils.qsample_description,
                SQLUtils.qgps, SQLUtils.qsample_elev_display]
               + [f'SampleGPS.{column} AS {column}' for column in GPS_RAW_COLUMNS] + tag_columns)
    joins = SQLUtils.get_join_from_table('', ['GPSLocations'] + list(SAMPLE_TAG_TABLES))
    return (f'SELECT {", ".join(columns)}\nFROM Samples\n{joins}'
            f'WHERE Samples.SampleGPSLocationID IS NOT NULL\nGROUP BY Samples.SampleID')


def _degrees(deg, minutes, seconds, direction_id):
    """Degrees/minutes/seconds with sign or DirectionUnitID to signed decimal degrees."""
    if deg is None or deg == '':
        return None
    deg = float(deg)
    value = abs(deg) + float(minutes or 0) / 60 + float(seconds or 0) / 3600
    if math.copysign(1, deg) < 0 or (
            direction_id and GPS.convert_direction_id_to_abbreviation(direction_id) in ('S', 'W')):
        return -value
    return value


def decimal_degrees(row: dict):
    """Signed decimal degrees from the stored GPSLocations values of any GPSFormat."""
    lat = _degrees(row['GPSLatDeg'], row['GPSLatMin'], row['GPSLatSec'], row['GPSLatDirectionID'])
    lon = _degrees(row['GPSLonDeg'], row['GPSLonMin'], row['GPSLonSec'], row['GPSLonDirectionID'])
    if (lat is None or lon is None) and row['GPSUTMZone'] and row['GPSUTME'] is not None and row['GPSUTMN'] is not None:
        result = GPS.convert_utm_to_dd(str(row['GPSUTMZone']), float(row['GPSUTME']), float(row['GPSUTMN']))
        if isinstance(result, tuple) and result[0] != '':
            lat, lon = result[0][0], result[1][0]
    return lat, lon


def tooltip_html(row: dict) -> str:
    lines = [f'<b>{html.escape(str(row["SampleName"]))}</b>']
    if row['SampleIGSN']:
        lines.append(f'<b>IGSN:</b> {html.escape(str(row["SampleIGSN"]))}')
    lines.append(f'{row["Latitude"]:.5f}, {row["Longitude"]:.5f}')
    if row['GPSSampleLocationCalculated']:
        lines.append(f'<b>Location:</b> {html.escape(str(row["GPSSampleLocationCalculated"]))}')
    if row['SampleElevation']:
        lines.append(f'<b>Elevation:</b> {html.escape(row["SampleElevation"])}')
    for table, schema in SAMPLE_TAG_TABLES.items():
        if row[schema['name_column']]:
            lines.append(f'<b>{TxM.add_spaces_camel(table)}:</b> {html.escape(str(row[schema["name_column"]]))}')
    if row['SampleDescription']:
        lines.append(f'<b>Description:</b> <i>{html.escape(str(row["SampleDescription"])[:150])}</i>')
    return '<br>'.join(lines)


class MapBridge(QtC.QObject):
    """QWebChannel object exposed to SampleMap.html as `bridge`."""
    ready = QtC.pyqtSignal()
    selection_changed = QtC.pyqtSignal(list)
    location_picked = QtC.pyqtSignal(float, float)

    @QtC.pyqtSlot()
    def pageReady(self):
        self.ready.emit()

    @QtC.pyqtSlot(str)
    def selectionChanged(self, ids: str):
        self.selection_changed.emit(json.loads(ids))

    @QtC.pyqtSlot(float, float)
    def locationPicked(self, lat: float, lon: float):
        self.location_picked.emit(lat, lon)

    @QtC.pyqtSlot(str)
    def openUrl(self, url: str):
        if url.startswith(('https://', 'http://')):
            QtG.QDesktopServices.openUrl(QtC.QUrl(url))


class SampleMapWindow(QtW.QMainWindow):
    """
    Interactive map of sample locations. Reads Samples/GPSLocations live from the open database, supports hover
    information, click/box/lasso selection, viewing/editing/exporting the selection, adding samples at picked
    locations, and bulk add/remove of Samples tree tags.
    """
    open_samples_requested = QtC.pyqtSignal(list)
    """Emitted with selected SampleIDs; connect in GeoCORKMain to open_tab"""

    def __init__(self, parent=None, startup_sample_ids: list[int] = None):
        super().__init__(parent)
        logger_setup.get_logger().info('Starting SampleMapWindow')
        self.setWindowTitle('Sample Map')
        self.resize(1200, 800)
        self.samples: dict[int, dict] = {}
        self.selected_ids: list[int] = []
        self.startup_sample_ids = []
        self.page_ready = False
        self.plot_dialog: PlotDialog | None = None

        self.view = QWebEngineView(self)
        # A file:// page needs both: remote for tiles/CDN, file for sibling resources (remote alone disables file)
        self.view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        self.view.page().profile().setHttpUserAgent(f'GeoCORK/{settings.value("default_geocork_version")}')
        self.bridge = MapBridge(self)
        self.channel = QWebChannel(self)
        self.channel.registerObject('bridge', self.bridge)
        self.view.page().setWebChannel(self.channel)
        self.setCentralWidget(self.view)

        self.bridge.ready.connect(self.on_page_ready)
        self.bridge.selection_changed.connect(self.set_selected)
        self.bridge.location_picked.connect(self.add_sample_at)

        self.build_toolbar()
        self.build_selection_dock()

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.view.load(QtC.QUrl.fromLocalFile(os.path.join(base_path, 'SampleMap.html')))
        if startup_sample_ids:
            self.select_samples(startup_sample_ids)

    def js(self, function: str, *args):
        if self.page_ready:
            self.view.page().runJavaScript(f'{function}({", ".join(json.dumps(arg) for arg in args)})')

    def build_toolbar(self):
        bar = self.addToolBar('Map')
        bar.setMovable(False)
        self.basemap_comboBox = QtW.QComboBox()
        self.basemap_comboBox.addItems(BASEMAPS)
        self.basemap_comboBox.setCurrentText(settings.value('map_basemap', 'Terrain'))
        self.basemap_comboBox.currentTextChanged.connect(self.set_basemap)
        bar.addWidget(self.basemap_comboBox)
        bar.addSeparator()
        modes = QtG.QActionGroup(self)
        for label, mode in (('Pan', 'pan'), ('Box select', 'box'), ('Lasso select', 'lasso'),
                            ('Add new sample to location', 'pick')):
            action = bar.addAction(label, lambda checked=False, m=mode: self.js('setMode', m))
            action.setCheckable(True)
            action.setChecked(mode == 'pan')
            modes.addAction(action)
        bar.addSeparator()
        bar.addAction('Zoom to all', lambda: self.js('fitTo', []))
        bar.addAction('Zoom to selection', lambda: self.js('fitTo', self.selected_ids))
        bar.addAction('Clear selection', lambda: self.set_selected([], push=True))
        bar.addAction('Refresh', self.refresh_all)
        bar.addSeparator()
        bar.addAction('Plots...', self.show_plots)
        bar.addSeparator()
        bar.addAction('ArcGIS API key...', self.set_api_key)

    def build_selection_dock(self):
        self.model = QtG.QStandardItemModel(0, len(TABLE_COLUMNS))
        self.model.setHorizontalHeaderLabels([TxM.add_spaces_camel(column) for column in TABLE_COLUMNS])
        self.table_view = QtW.QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_view.setSelectionBehavior(QtW.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.doubleClicked.connect(
            lambda index: self.js('flyTo', index.data(QtC.Qt.ItemDataRole.UserRole)))

        buttons = QtW.QHBoxLayout()
        self.selection_buttons = []
        for label, slot in (('Edit information...', self.edit_information), ('Edit tags...', self.edit_tags),
                            # ('Open in GeoCORK', lambda: self.open_samples_requested.emit(self.selected_ids)),
                            ('Open in exporter', self.open_in_expoter)):
            button = QtW.QPushButton(label)
            button.clicked.connect(slot)
            button.setEnabled(False)
            buttons.addWidget(button)
            self.selection_buttons.append(button)

        panel = QtW.QWidget()
        layout = QtW.QVBoxLayout(panel)
        layout.addWidget(self.table_view)
        layout.addLayout(buttons)
        self.dock = QtW.QDockWidget('Selected samples (0)', self)
        self.dock.setWidget(panel)
        self.dock.setFeatures(QtW.QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(QtC.Qt.DockWidgetArea.BottomDockWidgetArea, self.dock)

    def on_page_ready(self):
        self.page_ready = True
        self.set_basemap(self.basemap_comboBox.currentText())
        self.refresh()
        if self.startup_sample_ids:
            self.select_samples(self.startup_sample_ids)
            self.startup_sample_ids = []
        else:
            self.js('fitTo', [])

    def select_samples(self, sample_ids: list):
        """Select and zoom to SampleIDs from elsewhere in GeoCORK. Safe to call before the page has loaded and on an
        already-open window; IDs are coerced to int to match the SampleID keys in self.samples."""
        sample_ids = [int(sample_id) for sample_id in sample_ids]
        if not self.page_ready:
            self.startup_sample_ids = sample_ids  # applied in on_page_ready once samples are loaded
            return
        self.set_selected(sample_ids, push=True)
        dropped = set(sample_ids) - set(self.selected_ids)
        if dropped:
            logger_setup.get_logger().warning(f'SampleIDs {sorted(dropped)} not mapped: no GPS location or location '
                                              f'could not be resolved to decimal degrees')
        self.js('fitTo', self.selected_ids)
        self.show()
        self.raise_()
        self.activateWindow()

    def set_basemap(self, name: str):
        settings.setValue('map_basemap', name)
        self.js('setBasemap', BASEMAPS[name], settings.value('arcgis_api_key', ''))

    def set_api_key(self):
        key, ok = QtW.QInputDialog.getText(
            self, 'ArcGIS API key',
            'API key for the ArcGIS Static Basemap Tiles service.\nLeave blank to use the legacy Esri tiles.',
            QtW.QLineEdit.EchoMode.Password, settings.value('arcgis_api_key', ''))
        if ok:
            settings.setValue('arcgis_api_key', key.strip())
            self.set_basemap(self.basemap_comboBox.currentText())

    def refresh(self):
        """Reload sample locations from the database and redraw markers, keeping the current selection."""
        query = QtS.QSqlQuery()
        if not query.exec(sample_location_sql()):
            logger_setup.get_logger().critical('Error loading sample locations')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            return
        fields = [query.record().fieldName(i) for i in range(query.record().count())]
        self.samples = {}
        unresolved = 0
        while query.next():
            row = {field: None if query.isNull(i) else query.value(i) for i, field in enumerate(fields)}
            lat, lon = decimal_degrees(row)
            if lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
                unresolved += 1
                continue
            row['Latitude'], row['Longitude'] = round(lat, 6), round(lon, 6)
            elevation = row['SampleElevation']
            row['SampleElevation'] = None if not elevation or elevation.startswith('±') else elevation.replace('± ',
                                                                                                               ' ')
            self.samples[row['SampleID']] = row
        self.js('loadSamples', [{'id': sample_id, 'lat': row['Latitude'], 'lon': row['Longitude'],
                                 'html': tooltip_html(row)} for sample_id, row in self.samples.items()])
        self.set_selected(self.selected_ids, push=True)
        message = f'{len(self.samples)} samples mapped'
        if unresolved:
            message += f'; {unresolved} with GPS locations that could not be resolved to decimal degrees'
        self.statusBar().showMessage(message)

    def set_selected(self, sample_ids: list, push: bool = False):
        selected_ids = [sample_id for sample_id in sample_ids if sample_id in self.samples]
        if self.plot_dialog and selected_ids != self.selected_ids:
            self.plot_dialog.set_samples(selected_ids)
        self.selected_ids = selected_ids
        if push:
            self.js('setSelection', self.selected_ids)
        self.model.removeRows(0, self.model.rowCount())
        for sample_id in self.selected_ids:
            items = []
            for column in TABLE_COLUMNS:
                value = self.samples[sample_id][column]
                item = QtG.QStandardItem('' if value is None else str(value))
                item.setData(sample_id, QtC.Qt.ItemDataRole.UserRole)
                items.append(item)
            self.model.appendRow(items)
        self.table_view.resizeColumnsToContents()
        self.dock.setWindowTitle(f'Selected samples ({len(self.selected_ids)})')
        for button in self.selection_buttons:
            button.setEnabled(bool(self.selected_ids))

    def refresh_all(self):
        """Reload map samples and discard cached plot data."""
        self.refresh()
        if self.plot_dialog:
            self.plot_dialog.reload()

    def show_plots(self):
        if self.plot_dialog is None:
            self.plot_dialog = PlotDialog(self)
        self.plot_dialog.set_samples(self.selected_ids)
        self.plot_dialog.show()
        self.plot_dialog.raise_()

    def edit_information(self):
        SampleInformation(self, list(self.selected_ids)).exec()
        self.refresh_all()

    def edit_tags(self):
        if BulkTagDialog(self, self.selected_ids).exec() == QtW.QDialog.DialogCode.Accepted:
            self.refresh_all()

    def add_sample_at(self, lat: float, lon: float):
        dialog = MapAddSampleDialog(self, lat, lon)
        if dialog.exec() == QtW.QDialog.DialogCode.Accepted:
            self.refresh()
            self.set_selected([dialog.sample_id], push=True)
        self.js('clearPick')

    def open_in_expoter(self):
        main_widget, export_widget = None, None
        for widget in QApplication.topLevelWidgets():
            if widget.inherits("QMainWindow") and widget.objectName() == 'GeoCORKMain':
                main_widget = widget
                export_widget = widget.findChild(QWidget, 'ExportWidget')
        if not export_widget:
            logger_setup.get_logger().error('Export tab not found')
            return
        logger_setup.get_logger().info(f'Exporting {len(self.selected_ids)} samples to Exporter')
        # Switch first so showEvent populates the samples combo on first use, then apply the checks
        main_widget.switch_to_export_tab()
        export_widget.set_checked_samples(self.selected_ids)
        main_widget.raise_()
        main_widget.activateWindow()

    def changeEvent(self, event: QtC.QEvent):
        """Re-read the database when the window regains focus so edits made elsewhere in GeoCORK appear."""
        if event.type() == QtC.QEvent.Type.ActivationChange and self.isActiveWindow():
            self.refresh()
        super().changeEvent(event)
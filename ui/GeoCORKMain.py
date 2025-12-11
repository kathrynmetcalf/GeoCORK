import os
import sys
import time
from datetime import datetime

from PyQt6 import QtGui as QtG
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import QPoint, QSize, QStandardPaths
from PyQt6.QtGui import QAction
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import QMenu, QFileDialog, QProgressDialog
from PyQt6.uic import loadUi
from tzlocal import get_localzone

import logger_setup
import ui.ImportWizard
import ui.New_reference
from Functions import Savepoint_manager
from Functions.BackupDatabase import BackupThread
from Functions.Database_manager import update_database, turn_on_foreign_keys
from Functions.LoadingDialog_manager import LoadingDialogManager
from Functions.Savepoint_manager import SavepointManager
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.Text_manipulations import shrink_home, expand_home
from Functions.Widget_classes import PartiallyCloseableTabWidget
from Functions.Widget_classes import get_name_from_id, close_loading_dialog
from ui.DisplayTables import DisplayTables
from ui.ExportWidget import ExportWidget
from ui.Filters import Filters
from ui.SampleInformation import SampleInformation
from ui.Settings import SettingsDialog
from ui.ViewDataTab import ViewDataTab


# import Select_Database as sd  # Eventually get database file from initial dialog


class GeoCORK(QtW.QMainWindow):
    def __init__(self, landingpage):
        super().__init__()
        logger_setup.get_logger().info("Starting the main window")
        # Define any variables here

        self.loading_manager = LoadingDialogManager.get_instance()

        blank_schema_file = "Reference/GeoCORK_v1-0.db"
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        base_path = os.path.normpath(base_path)
        sources_ui_file = fr'{os.path.join(base_path, "GeoCORKMain.ui")}'
        sources_ui_file = os.path.normpath(sources_ui_file)
        self.loadWindowState()
        loadUi(sources_ui_file, self)
        self.setObjectName('GeoCORKMain')

        self.landingpage = landingpage
        self.db = QSqlDatabase()
        self.db_file = self.landingpage.get_filename()
        self.update_window_title()
        self.recent_files = settings.value("ui/LandingPage/recentlist", defaultValue=[], type=list)
        self.recent_files = self.recent_files[0:5]
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('File')
        actionNew = QtG.QAction('New', self)
        actionNew.setShortcut(QtG.QKeySequence('Ctrl+N'))
        actionOpen = QtG.QAction('Open', self)
        actionOpen.setShortcut(QtG.QKeySequence('Ctrl+O'))
        self.menuRecent = QMenu('Recent', self)
        self.update_recent_files_menu()
        actionImport = QtG.QAction('Import', self)
        actionImport.setShortcut(QtG.QKeySequence('Ctrl+I'))
        actionSettings = QtG.QAction('Settings', self)
        actionSettings.setShortcut(QtG.QKeySequence('Ctrl+,'))
        actionSettings.setMenuRole(QtG.QAction.MenuRole.PreferencesRole)
        actionCreateBackup = QtG.QAction('Create Backup', self)
        actionRestoreBackup = QtG.QAction('Restore Backup', self)
        actionExport = QtG.QAction('Export', self)
        actionExport.setShortcut(QtG.QKeySequence('Ctrl+E'))
        actionQuit = QtG.QAction('Quit', self)
        actionQuit.setShortcut(QtG.QKeySequence('Ctrl+Q'))
        file_menu.addActions([actionNew, actionOpen, actionImport])
        file_menu.addSeparator()
        file_menu.addMenu(self.menuRecent)
        file_menu.addSeparator()
        file_menu.addAction(actionSettings)
        file_menu.addSeparator()
        file_menu.addActions([actionCreateBackup, actionRestoreBackup, actionExport])
        file_menu.addSeparator()
        file_menu.addAction(actionQuit)

        settings.setValue('db_file', self.db_file)
        logger_setup.get_logger().info(f"Setting database file to: {self.db_file}")
        if '/' in self.db_file:
            self.db_name: str = self.db_file.split('/')[-1]
        elif '\\' in self.db_file:
            self.db_name: str = self.db_file.split('\\')[-1]
        if self.db.isOpen():
            if self.db.open():
                logger_setup.get_logger().info(f"Database opened successfully")
                self.setWindowTitle(f"GeoCORK - {self.db_name}")
            else:
                logger_setup.get_logger().critical('Database could not be opened')
                return
        else:
            logger_setup.get_logger().info(f"Database already opened")

        if not turn_on_foreign_keys():
            return

        SettingsManager().set_db_file(self.db_name)
        self.savepoint_manager = Savepoint_manager.SavepointManager().get_instance()
        self.msg = QtW.QMessageBox(self)

        # if not update_database():
        #     logger_setup.get_logger().critical('Error updating and displaying database')
        #     self.close()

        self.tabWidget: PartiallyCloseableTabWidget
        self.tabWidget.set_permanent_tabs(['Data Tables', 'Filters', 'Export'])
        self.tabWidget.addTab(DisplayTables(self), 'Data Tables')
        self.tabWidget.addTab(Filters(self), 'Filters')
        self.tabWidget.addTab(ExportWidget(self), 'Export')

        # todo: figure out how to add a divider between the permanent tabs and the user-added tabs, rather than
        #  always moving the permanent tabs to the left upon changes
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.tabCloseRequested.connect(self.close_tab)
        self.tabWidget.currentChanged.connect(self.on_tab_changed)

        actionOpen.triggered.connect(self.landingpage.showFileDialog)
        actionCreateBackup.triggered.connect(self.create_backup)
        actionRestoreBackup.triggered.connect(self.restore_backup)
        actionImport.triggered.connect(self.show_import_wizard_dialog)
        actionSettings.triggered.connect(self.show_settings_dialog)
        actionExport.triggered.connect(self.switch_to_export_tab)
        actionQuit.triggered.connect(self.close)
        actionNew.triggered.connect(self.new_database)

        self.loading_manager.close_loading_dialog('Opening',
                                              f'Opening {self.db_name}... \n(GeoCORK may be slower for large databases)')
        self.showMaximized()
        self.show()

    def cancel_open(self, title, message):
        close_loading_dialog(title, message)
        self.close()

    def update_recent_files_menu(self):
        """Refresh the recent files menu."""
        self.menuRecent.clear()
        if self.recent_files:
            for file_path in self.recent_files:
                action = QAction(shrink_home(file_path), self)
                action.triggered.connect(lambda checked, path=file_path: self.open_recent_file(path))
                self.menuRecent.addAction(action)
        else:
            empty_action = QAction("(No recent files)", self)
            empty_action.setEnabled(False)
            self.menuRecent.addAction(empty_action)

    def open_recent_file(self, file_path):
        """Simulate opening a recent file."""
        self.update_recent_files_menu()
        self.landingpage.selected_files = expand_home(file_path)
        settings.setValue('db_file', expand_home(file_path))
        self.landingpage.db = None
        self.landingpage.open_geo_cork()

    def new_database(self):
        file_name, _ = QFileDialog.getSaveFileName(
            None,
            "Save Database File",
            "",
            "Database Files (*.db)"
        )
        if not file_name:
            return

        # Ensure the filename ends with .db
        if not file_name.lower().endswith(".db"):
            if '.' in file_name:
                # If there's already an extension, replace it with .db
                file_name = file_name.split('.')[0] + ".db"

        self.landingpage.selected_files = file_name
        if self.landingpage.selected_files not in self.landingpage.list_recents:
            self.landingpage.list_recents.insert(0, self.landingpage.selected_files)  # Add the new database to the top of the list
            settings.setValue("ui/LandingPage/recentlist", self.landingpage.list_recents)
        self.landingpage.db = None
        self.landingpage.open_about_db()
        self.landingpage.open_geo_cork()

    def update_window_title(self):
        query = QSqlQuery('Select Name From About WHERE AboutID=1')
        if query.exec():
            if query.next():
                self.setWindowTitle(f'GeoCORK Database: {query.value(0)}            file: {self.db_file}')

    def show_settings_dialog(self):
        dlg = SettingsDialog()
        dlg.exec()
        if dlg.updated:
            if not update_database():
                logger_setup.get_logger().critical('Error updating and displaying database')
                self.close()
            self.update_window_title()
            # Refresh the active tab
            self.refresh()
        else:
            return

    def show_import_wizard_dialog(self):
        """
        Opens a file dialog to select a file to import
        Executes the import wizard with that file
        :return:
        """

        import_wizard = ui.ImportWizard.ImportWizardDialog(None)
        import_wizard.data_imported.connect(self.refresh)
        import_wizard.show()

    def refresh(self):
        """
        Refreshes the current tab if it is a data table, view data tab, or export tab
        :return:
        """
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == 'Data Tables':
            self.tabWidget.widget(self.tabWidget.currentIndex()).display_table()
        elif ' : ' in self.tabWidget.tabText(self.tabWidget.currentIndex()):
            self.tabWidget.widget(self.tabWidget.currentIndex()).display_table()
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == 'Export':
            self.tabWidget.widget(self.tabWidget.currentIndex()).refresh_widget()

    def switch_to_export_tab(self):
        self.tabWidget.setCurrentIndex(2)

    def create_backup(self):
        logger_setup.get_logger().info(f'Creating backup of {self.db_name}:')
        local_timezone = get_localzone()
        current_time = datetime.now(local_timezone)
        formatted_timestamp = current_time.strftime('%Y-%m-%d %H.%M.%S')

        backup_file = (QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation) +
                       rf"/backups/{self.db_name.replace('.db', '')}/{os.path.basename(self.db_file).replace('.db', '')}-{formatted_timestamp}.db")

        backup_dir = os.path.dirname(backup_file)
        if backup_dir and not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)

        logger_setup.get_logger().info(f'Backing up to {backup_file}')

        if not SavepointManager.get_instance().active_savepoints():
            self.progressBar = QProgressDialog()
            self.progressBar.setLabelText('Backing up database...')
            self.progressBar.setCancelButtonText(None)
            self.progressBar.show()

            # Create and start the backup thread
            self.thread = BackupThread(self.db_file, backup_file)
            self.thread.progress_updated.connect(self.progressBar.setValue)
            self.thread.start()

        else:
            logger_setup.get_logger().critical('Uncommitted changes: cannot backup\nPlease commit or discard changes before creating a backup.')
            logger_setup.get_logger().debug(f"Savepoints: {SavepointManager.get_instance().active_savepoints_names()}")

    def restore_backup(self):
        logger_setup.get_logger().info(f'Restoring backup to {self.db_name}:')

        backup_file = (QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation) +
                       rf"/backups/{self.db_name.replace('.db', '')}/")

        backup_dir = os.path.dirname(backup_file)
        if backup_dir and not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)

        backup_file, _ = QFileDialog(self).getOpenFileName(self, "Select Database File", backup_dir,
                                                           "Database Files (*.db)")

        if backup_file:
            if not SavepointManager.get_instance().active_savepoints():
                self.landingpage.restore_backup(self.db_file, backup_file)

    def edit_sample_information(self, sample_ids: list[int]):
        """
        Opens the sample information dialog for the given sample IDs
        :param sample_ids: The IDs of the samples to edit
        :return:
        """
        self.loading_manager.show_loading_dialog('Loading', 'Opening Sample Information window...')
        sample_ids = list(set(sample_ids))
        dlg = SampleInformation(self, sample_ids)
        dlg.exec()
        if dlg.updated:
            if self.tabWidget.currentIndex() == 0:
                self.tabWidget.widget(0).display_table()

    def on_tab_changed(self, index):
        """
        When the tab is changed, check if the tab is a temporary table
        If it is, refresh the table
        :param index: The index of the tab that was changed
        :return:
        """
        logger_setup.get_logger().debug(f'Tab changed to {self.tabWidget.tabText(index)}')
        ## This is taking too long, so the user should use the refresh button as needed
        # if self.tabWidget.tabText(index) not in self.tabWidget.permanent_tabs:
        #     self.tabWidget.widget(index).display_table()

    def open_tab(self, parent_ids: list[int], parent_type: str, child_type: str):
        """
        Opens a tab with the given parent ID and parent type
        :param parent_ids: The list of parent IDs
        :param parent_type: The type of the parent
        :param child_type: The type of the child
        :return:
        """
        logger_setup.get_logger().info(
            f'Opening tab with parent ID {parent_ids} and parent type {parent_type} and child type {child_type}')
        start_open_tab_time = time.time()
        if not parent_ids:
            return
        self.tabWidget: PartiallyCloseableTabWidget
        for p_id in parent_ids:
            if parent_type not in ['Samples', 'Aliquots', 'Grains', 'Spots']:
                logger_setup.get_logger().critical(f'Parent type {parent_type} not recognized')
                return
            parent_name = get_name_from_id(parent_type, p_id)
            if child_type not in ['Aliquots', 'Grains', 'Spots', 'UPbAnalyses']:
                logger_setup.get_logger().critical(f'Child type {child_type} not recognized')
                return
            label = f'{parent_type} {parent_name}: {child_type}'
            self.loading_manager.show_loading_dialog('Loading',
                                                     f'Loading {parent_type} {parent_name}: {child_type}...')
            tab = ViewDataTab(p_id, parent_type, child_type, label)
            tab.setUpdatesEnabled(False)
            start_add_tab_time = time.time()
            self.tabWidget.addTab(tab, label)
            logger_setup.get_logger().debug(f'Time to add tab: {time.time() - start_add_tab_time}')
            tab.setUpdatesEnabled(True)
        end_open_tab_time = time.time()
        logger_setup.get_logger().info(f'Time to open tab: {end_open_tab_time - start_open_tab_time}')

    def close_tab(self, index):
        self.tabWidget: PartiallyCloseableTabWidget
        if index not in self.tabWidget.permanent_tabs:
            self.tabWidget.removeTab(index)
            if self.tabWidget.currentIndex() == index:
                self.tabWidget.setCurrentIndex(index - 1)

    def saveWindowState(self):
        settings.setValue("ui/GeoChronMain/pos", self.pos())
        settings.setValue("ui/GeoChronMain/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/GeoChronMain/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/GeoChronMain/size", defaultValue=QSize(810, 569)))

    def closeEvent(self, event):
        self.saveWindowState()

        logger_setup.get_logger().info(f"Current databases open {QSqlDatabase().connectionNames()}")
        if 'qt_sql_default_connection' in QSqlDatabase().connectionNames():
            if not self.db.commit():
                if 'transaction is active' in self.db.lastError().text():
                    logger_setup.get_logger().critical(
                        f'Database is open but a transaction is active: {self.db.lastError().text()}')
                else:
                    if "Driver not loaded" not in self.db.lastError().text():
                        logger_setup.get_logger().critical(f'Database error: {self.db.lastError().text()}')
            self.db.close()
            self.db.removeDatabase('qt_sql_default_connection')
            logger_setup.get_logger().info(f"Current databases open {QSqlDatabase().connectionNames()}")
        else:
            logger_setup.get_logger().info('Database not open')
        self.landingpage.show()
        super().closeEvent(event)

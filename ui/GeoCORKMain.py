import os
import sys

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6.QtCore import QPoint, QSize

from PyQt6.uic import loadUi
import Functions.Database_views as DB_views
import Functions.Widget_classes as WC
import logger_setup
from Functions import SQLUtils
from Functions import Savepoint_manager
from Functions.Settings_manager import settings
from Functions.Database_manager import update_database
import ui.import_wizard
import ui.New_reference
from ui.SampleInformation import SampleInformation

from ui.Settings import SettingsDialog
from ui.ExportWidget import ExportWidget
from ui.DisplayTables import DisplayTables
from ui.Filters import Filters
from ui.ViewDataTab import ViewDataTab
from Functions.Widget_classes import PartiallyCloseableTabWidget
import time

# import Select_Database as sd  # Eventually get database file from initial dialog


class GeoCORK(QtW.QMainWindow):
    def __init__(self, landingpage):
        super().__init__()
        logger_setup.get_logger().info("Starting the main window")
        # Define any variables here
        self.landingpage = landingpage

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('File')
        actionNew = QtG.QAction('New', self)
        actionNew.setShortcut(QtG.QKeySequence('Ctrl+N'))
        actionOpen = QtG.QAction('Open', self)
        actionOpen.setShortcut(QtG.QKeySequence('Ctrl+O'))
        actionRecent = QtG.QAction('Recent', self)
        actionImport = QtG.QAction('Import', self)
        actionImport.setShortcut(QtG.QKeySequence('Ctrl+I'))
        actionSettings = QtG.QAction('Settings', self)
        actionSettings.setShortcut(QtG.QKeySequence('Ctrl+,'))
        actionSettings.setMenuRole(QtG.QAction.MenuRole.PreferencesRole)
        actionCreateBackup = QtG.QAction('Create Backup', self)
        actionRestoreBackup = QtG.QAction('Restore Backup', self)
        actionExport = QtG.QAction('Export', self)
        actionQuit = QtG.QAction('Quit', self)
        actionQuit.setShortcut(QtG.QKeySequence('Ctrl+Q'))
        file_menu.addActions([actionNew, actionOpen, actionRecent, actionImport, actionSettings,
                                   actionCreateBackup, actionRestoreBackup, actionExport, actionQuit])
        file_menu.insertSeparator(actionSettings)
        file_menu.insertSeparator(actionCreateBackup)
        file_menu.insertSeparator(actionQuit)

        self.db = QtS.QSqlDatabase.addDatabase('QSQLITE')
        self.db_file = self.landingpage.get_filename()

        settings.setValue('db_file', self.db_file)
        logger_setup.get_logger().info(f"Setting database file to: {self.db_file}")
        self.db.setDatabaseName(self.db_file)
        if self.db.open():
            logger_setup.get_logger().info(f"Database opened successfully")
            if '/' in self.db_file:
                self.setWindowTitle(f"GeoCORK - {self.db_file.split('/')[-1]}")
            elif '\\' in self.db_file:
                self.setWindowTitle(f"GeoCORK - {self.db_file.split('\\')[-1]}")
        else:
            logger_setup.get_logger().critical('Database could not be opened')
            return
        self.loadWindowState()

        blank_schema_file = "Reference/GeoCORK_v1-0.db"
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        base_path = os.path.normpath(base_path)
        sources_ui_file = fr'{os.path.join(base_path, "GeoCORKMain.ui")}'
        sources_ui_file = os.path.normpath(sources_ui_file)

        loadUi(sources_ui_file, self)

        savepoint_manager = Savepoint_manager.SavepointManager()
        self.savepoint_manager = savepoint_manager.get_instance()
        self.msg = QtW.QMessageBox(self)

        # self.db = Database_converter.check_database_schema(self.db, blank_schema_file)
        update_database()

        self.tabWidget: PartiallyCloseableTabWidget
        self.tabWidget.set_permanent_tabs(['Data Tables', 'Filters', 'Export'])
        self.tabWidget.addTab(DisplayTables(self), 'Data Tables')
        self.tabWidget.addTab(Filters(self), 'Filters')
        self.tabWidget.addTab(ExportWidget(self), 'Export')

        # todo: figure out how to add a divider between the permanent tabs and the user-added tabs
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.tabCloseRequested.connect(self.close_tab)
        self.tabWidget.currentChanged.connect(self.on_tab_changed)

        actionOpen.triggered.connect(self.landingpage.showFileDialog)
        actionRecent.triggered.connect(self.landingpage.new_database_dialog)
        # actionCreateBackup.triggered.connect(self.create_backup)
        # actionRestoreBackup.triggered.connect(self.restore_backup)
        actionImport.triggered.connect(self.show_import_wizard_dialog)
        actionSettings.triggered.connect(self.show_settings_dialog)
        actionExport.triggered.connect(ExportWidget)
        actionQuit.triggered.connect(self.close)

        self.show()

    def show_settings_dialog(self):
        dlg = SettingsDialog()
        dlg.exec()
        update_database()
        # If the active tab is a data table, refresh it
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == 'Data Tables':
            self.tabWidget.widget(self.tabWidget.currentIndex()).display_table()

    def show_import_wizard_dialog(self):
        """
        Opens a file dialog to select a file to import
        Executes the import wizard with that file
        :return:
        """

        import_wizard = ui.import_wizard.ImportWizardDialog()
        import_wizard.data_imported.connect(self.edit_sample_information)
        import_wizard.show()


    def edit_sample_information(self, sample_ids: list[int]):
        """
        Opens the sample information dialog for the given sample IDs
        :param sample_ids: The IDs of the samples to edit
        :return:
        """
        dlg = SampleInformation(self, sample_ids)
        dlg.exec()

    def on_tab_changed(self, index):
        """
        When the tab is changed, check if the tab is a temporary table
        If it is, refresh the table
        :param index: The index of the tab that was changed
        :return:
        """
        logger_setup.get_logger().debug(f'Tab changed to {self.tabWidget.tabText(index)}')
        if self.tabWidget.tabText(index) not in self.tabWidget.permanent_tabs:
            self.tabWidget.widget(index).display_table()

    def open_tab(self, parent_id: list[int], parent_type: str, child_type: str):
        """
        Opens a tab with the given parent ID and parent type
        :param parent_id: The ID of the parent
        :param parent_type: The type of the parent
        :param child_type: The type of the child
        :return:
        """
        logger_setup.get_logger().info(f'Opening tab with parent ID {parent_id} and parent type {parent_type} and child type {child_type}')
        start_open_tab_time = time.time()
        if not parent_id:
            return
        self.tabWidget: PartiallyCloseableTabWidget
        for p_id in parent_id:
            if parent_type == 'Sample':
                parent_name = WC.get_name_from_id('Samples', p_id)
            elif parent_type == 'Aliquot':
                parent_name = WC.get_name_from_id('Aliquots', p_id)
            elif parent_type == 'Spot':
                parent_name = WC.get_name_from_id('Spots', p_id)
            else:
                print("Error: Invalid parent type")
                return
            if child_type == 'Aliquot':
                child_label = 'Aliquots'
            elif child_type == 'Spot':
                child_label = 'Spots'
            elif child_type == 'UPbAnalysis':
                child_label = 'U-Pb Analyses'
            else:
                print("Error: Invalid child type")
                return
            tab = ViewDataTab(p_id, parent_type, child_type)
            self.tabWidget.addTab(tab, f'{parent_type} {parent_name}: {child_label}')
        end_open_tab_time = time.time()
        logger_setup.get_logger().info(f'Time to open tab: {end_open_tab_time - start_open_tab_time}')

    def close_tab(self, index):
        self.tabWidget: PartiallyCloseableTabWidget
        if index not in self.tabWidget.permanent_tabs:
            self.tabWidget.removeTab(index)
            self.tabWidget.setCurrentIndex(index-1)

    def saveWindowState(self):
        settings.setValue("ui/GeoChronMain/pos", self.pos())
        settings.setValue("ui/GeoChronMain/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/GeoChronMain/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/GeoChronMain/size", defaultValue=QSize(810, 569)))

    def closeEvent(self, event):
        # if self.table in self.dbtree_list:
        #     TrC.save_expanded_state(self.table, self.tree_proxy_model, self.dbTable_treeView)
        self.saveWindowState()
        # print(f"Closing with active savepoints: {self.savepoint_manager.active_savepoints()}")
        self.savepoint_manager.reset()
        if self.db.isOpen():
            if not self.db.commit():
                if 'no transaction is active' not in self.db.lastError().text():
                    logger_setup.get_logger().critical(
                        f'Database is open but a transaction is active: {self.db.lastError().text()}')
            self.db.close()
        self.landingpage.show()
        super().closeEvent(event)
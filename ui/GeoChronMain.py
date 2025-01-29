import os
import sys

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import QPoint, QSize

from PyQt6.uic import loadUi
import Functions.Database_views as DB_views
import Functions.Table_classes as TbC
from Functions import SQLUtils
from Functions import Savepoint_manager
from Functions.Settings_manager import settings
from Functions.Database_manager import update_database
import ui.import_wizard
import ui.New_reference

from ui.Settings import SettingsDialog
from ui.ExportWidget import ExportWidget
from ui.DisplayTables import DisplayTables
from ui.Filters import Filters
from ui.ViewDataTab import ViewDataTab
from Functions.Widget_classes import PartiallyCloseableTabWidget
import time

# import Select_Database as sd  # Eventually get database file from initial dialog


class GeoChron(QtW.QMainWindow):
    def __init__(self, landingpage):
        super().__init__()
        # Define any variables here
        self.landingpage = landingpage
        self.db = QtS.QSqlDatabase.addDatabase('QSQLITE')
        self.db_file = self.landingpage.get_filename()
        self.db.setDatabaseName(self.db_file)
        ok = self.db.open()
        print("Database is open: " + str(ok))
        self.loadWindowState()

        blank_schema_file = "Reference/GeoCORK_v1-0.db"
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        base_path = os.path.normpath(base_path)
        sources_ui_file = fr'{os.path.join(base_path, "GeochronMain.ui")}'
        sources_ui_file = os.path.normpath(sources_ui_file)

        loadUi(sources_ui_file, self)

        savepoint_manager = Savepoint_manager.SavepointManager()
        self.savepoint_manager = savepoint_manager.get_instance()
        self.msg = QtW.QMessageBox(self)
        # self.switch_to_table()

        # self.db = Database_converter.check_database_schema(self.db, blank_schema_file)
        update_database()
        create_view_begin = time.time()
        print("Creating views")
        DB_views.create_all_views()
        create_view_end = time.time()
        print(f"Create views time: {create_view_end - create_view_begin}")

        self.actionImport.triggered.connect(self.show_import_wizard_dialog)
        self.actionSettings.triggered.connect(self.show_settings_dialog)
        self.actionNew.triggered.connect(self.show_settings_dialog)

        self.tabWidget: PartiallyCloseableTabWidget
        self.tabWidget.set_permanent_tabs(['Data Tables', 'Filters', 'Export'])
        self.tabWidget.addTab(DisplayTables(self), 'Data Tables')
        self.tabWidget.addTab(Filters(self), 'Filters')
        self.tabWidget.addTab(ExportWidget(self), 'Export')
        # todo: figure out how to add a divider between the permanent tabs and the user-added tabs
        # todo: make the permanent tabs unmovable, current workaround is reordering everything after a mouse release event
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.tabCloseRequested.connect(self.close_tab)

        self.show()

    def show_settings_dialog(self):
        dlg = SettingsDialog()
        dlg.exec()
        update_database()

    def show_import_wizard_dialog(self):
        """
        Opens a file dialog to select a file to import
        Executes the import wizard with that file
        :return:
        """

        import_wizard = ui.import_wizard.ImportWizardDialog()
        import_wizard.show()


    def drop_views(self):
        """
        Drop all views in the database
        :return:
        """
        for view in SQLUtils.views:
            output = DB_views.drop_view(view)
            if output is not None and output.type == str:
                errtxt = output
                self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def open_tab(self, parent_id: int, parent_type: str, child_type: str):
        """
        Opens a tab with the given parent ID and parent type
        :param parent_id: The ID of the parent
        :param parent_type: The type of the parent
        :param child_type: The type of the child
        :return:
        """
        if not parent_id:
            return
        self.tabWidget: PartiallyCloseableTabWidget
        if parent_type == 'Sample':
            parent_name = TbC.get_name_from_id('Samples', parent_id)
        elif parent_type == 'Aliquot':
            parent_name = TbC.get_name_from_id('Aliquots', parent_id)
        elif parent_type == 'Spot':
            parent_name = TbC.get_name_from_id('Spots', parent_id)
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
        self.tabWidget.addTab(ViewDataTab(parent_id, parent_type, child_type), f'{parent_type} {parent_name}: {child_label}')

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
                    print(self.db.lastError().text())
            self.db.close()
        self.landingpage.show()
        super().closeEvent(event)
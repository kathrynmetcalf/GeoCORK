import sys
from pathlib import Path
import sqlite3
import re
from random import sample

# import pandas as pd
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import Qt, QEventLoop, QStandardPaths, QPoint, QSettings, QSize
from PyQt6.QtWidgets import QFileDialog, QWidget, QPushButton, QTabWidget

from PyQt6.uic import loadUi
import Functions.Create_database as Create_db
import Functions.Alter_database as Alter_db
import Functions.Database_views as DB_views
import Functions.Table_classes as TbC
import Functions.Tree_classes as TrC
import Functions.Text_manipulations as TxM
from Functions import SQLUtils
from Functions import Database_manager
from Functions import Database_converter
from Functions.Settings_manager import settings
import ui.import_wizard
import ui.New_reference
from Functions.Database_views import drop_view
from ui.Settings import SettingsDialog
from ui.ExportWidget import ExportWidget
from ui.DisplayTables import DisplayTables
from ui.Filters import Filters
from ui.ViewDataTab import ViewDataTab
from Functions.Tree_classes import TreeSortFilterProxyModel
from Functions.Widget_classes import PartiallyCloseableTabWidget
# from ui.EditTags import EditTags
from ui.EditSampleTable import EditSampleTable
from ui.EditTable import EditTable
from ui.EditTree import EditTree
from ui.AddTags import AddTags
from ui.Filters import QueryBuilder
from ui.SampleInformation import  SampleInformation
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
        sources_ui_file = "ui/GeochronMain.ui"
        loadUi(sources_ui_file, self)

        savepoint_manager = Database_manager.SavepointManager()
        self.savepoint_manager = savepoint_manager.get_instance()
        self.msg = QtW.QMessageBox(self)
        # self.switch_to_table()

        # self.db = Database_converter.check_database_schema(self.db, blank_schema_file)
        Create_db.create_tables()
        self.drop_views()
        Alter_db.settings_reset()
        create_view_begin = time.time()
        print("Creating views")
        DB_views.create_all_views()
        create_view_end = time.time()
        print(f"Create views time: {create_view_end - create_view_begin}")
        #list of all user-viewable tables in the database
        # self.user_view_tables = SQLUtils.user_viewable_tables
        # #list of tables to display as a tree structure
        # self.dbtree_list = SQLUtils.user_viewable_trees
        # self.dbtable_list = [table for table in self.user_view_tables if table not in self.dbtree_list]


        # self.ui_widgets()

        # Set up models
        # self.sample_proxy_model = QtC.QSortFilterProxyModel()
        # self.model = TbC.DisplayRoundedModel()
        # self.query_model = TbC.DisplayRoundedQueryModel()
        # self.tree_model = TrC.TreeModel()
        # self.tree_proxy_model = TreeSortFilterProxyModel(view=self.dbTable_treeView)
        # self.table_proxy_model = TbC.ReadableProxyModel()
        # self.table = ''
        # self.display_table_list()

        # Display the selected table
        # self.dbTable_comboBox.currentIndexChanged.connect(self.display_table)

        # Signal for search bar
        # self.search_lineEdit.textChanged.connect(self.search)
        # Signal for clicked add button in main window
        # self.actionImport.triggered.connect(self.show_import_wizard_dialog)
        # Signal for clicked edit button
        # self.edit_pushButton.clicked.connect(self.edit_popup)
        # Signal for clicked edit samples button
        # self.edit_samples_pushButton.clicked.connect(self.edit_samples_popup)
        # Context menu for table and tree views
        # self.dbTable_tableView.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        # self.dbTable_tableView.customContextMenuRequested.connect(self.show_context_menu)
        # self.dbTable_treeView.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        # self.dbTable_treeView.customContextMenuRequested.connect(self.show_context_menu)

        self.tabWidget: PartiallyCloseableTabWidget
        self.tabWidget.set_permanent_tabs(['Data Tables', 'Filters', 'Export'])
        self.tabWidget.addTab(DisplayTables(self), 'Data Tables')
        self.tabWidget.addTab(Filters(self), 'Filters')
        self.tabWidget.addTab(ExportWidget(self), 'Export')
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.tabCloseRequested.connect(self.close_tab)

        # If the platform is MacOS, connect to the preferences action
        if sys.platform == "darwin":
            self.menuBar().isNativeMenuBar()
            self.settings_action = QtG.QAction("Settings", self)
            self.settings_action.setMenuRole(QtG.QAction.MenuRole.PreferencesRole)
            self.settings_action.triggered.connect(self.show_settings_dialog)
            self.menuBar().addAction(self.settings_action)

        self.show()

    # def closeEvent(self, a0):
    #     self.landingpage.show()
    #     self.saveWindowState()
    #     super().closeEvent(a0)

    def show_settings_dialog(self):
        dlg = SettingsDialog()
        dlg.exec()

    # def ui_widgets(self):
    #     self.dbTable_tableView: QtW.QTableView
    #     self.dbTable_treeView: QtW.QTreeView
    #     self.dbTable_comboBox: QtW.QComboBox
    #     self.search_lineEdit: QtW.QLineEdit
    #     self.add_pushButton: QtW.QPushButton
    #     self.submitall_pushButton: QtW.QPushButton
    #     self.status_label: QtW.QLabel
    #     self.db_stackedWidget: QtW.QStackedWidget
    #     self.case_checkBox: QtW.QCheckBox
    #
    # def switch_to_table(self):
    #     """
    #     Sets the current widget to a table view
    #     :return:
    #     """
    #     self.db_stackedWidget: QtW.QStackedWidget
    #     self.db_stackedWidget.setCurrentWidget(self.db_table)
    #
    # def switch_to_tree(self):
    #     """
    #     Sets the current widget to a tree view
    #     :return:
    #     """
    #     self.db_stackedWidget: QtW.QStackedWidget
    #     self.db_stackedWidget.setCurrentWidget(self.db_tree)

    def show_import_wizard_dialog(self):
        """
        Opens a file dialog to select a file to import
        Executes the import wizard with that file
        :return:
        """
        try:
            home_dir = str(Path.home()) + r'\Downloads'
            fname = QFileDialog.getOpenFileName(self, 'Open file', home_dir)
            import_wizard = ui.import_wizard.ImportWizardDialog(fname[0], self.db_file)
            import_wizard.exec()
        except FileNotFoundError:
            print("No file selected")

    # def display_table_list(self):
    #     """
    #     Populates the tables combo box with the editable tables
    #     Displays the default table
    #     :return:
    #     """
    #     self.dbTable_comboBox: QtW.QComboBox
    #     self.dbTable_comboBox.addItems(self.user_view_tables)
    #     self.previous_table = ''
    #     self.dbTable_comboBox.setCurrentText('Samples')
    #     self.display_table()
    #
    # def display_table(self):
    #     """
    #     Displays the selected table
    #     :return:
    #     """
    #     # if not self.db.isOpen():
    #     #     print("Database is not open")
    #     #     return
    #     self.edit_pushButton: QPushButton
    #     self.dbTable_tableView: QtW.QTableView
    #     self.dbTable_treeView: QtW.QTreeView
    #     self.dbTable_comboBox: QtW.QComboBox
    #     self.add_pushButton: QtW.QPushButton
    #     self.case_checkBox: QtW.QCheckBox
    #     table = self.dbTable_comboBox.currentText()
    #     self.table = TxM.remove_spaces(table)
    #     # If moving from a tree table, save the expanded state first
    #     if self.previous_table in self.dbtree_list and self.previous_table != self.table:
    #         TrC.save_expanded_state(self.previous_table, self.tree_proxy_model, self.dbTable_treeView)
    #     self.previous_table = self.table
    #
    #     if self.table in self.dbtree_list:
    #         self.switch_to_tree()
    #         self.edit_samples_pushButton.hide()
    #         self.model = QtS.QSqlTableModel()
    #         self.model.setTable(table)
    #         self.model.select()
    #
    #         self.tree_model = TrC.TreeModel(self.model, None)
    #         self.tree_proxy_model.setSourceModel(self.tree_model)
    #         # self.edit_pushButton.clicked.connect(lambda: self.edit_popup(self.model))
    #
    #         self.dbTable_treeView.setModel(self.tree_proxy_model)
    #         self.dbTable_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
    #         self.dbTable_treeView.hideColumn(1)  # don't show ID column
    #         self.dbTable_treeView.hideColumn(2)  # don't show parent ID column
    #         self.dbTable_treeView.hideColumn(3)  # don't show parent row column
    #         # Keep the tree sorted as dictated by the database
    #         self.dbTable_treeView.setSortingEnabled(False)
    #         # if self.table == 'Ages':
    #             # self.dbTable_treeView.hideColumn(6)  # don't show created column
    #             # self.dbTable_treeView.hideColumn(7)  # don't show modified column
    #             # self.dbTable_treeView.sortByColumn(4, Qt.SortOrder(0))
    #         self.dbTable_treeView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
    #         TrC.restore_expanded_state(table, self.tree_proxy_model, self.dbTable_treeView)
    #     elif self.table in self.dbtable_list:
    #         self.switch_to_table()
    #         if self.table == 'Samples':
    #             self.query_model.setQuery('SELECT * FROM SampleView')
    #             self.table_proxy_model.setSourceModel(self.query_model)
    #             self.edit_samples_pushButton.show()
    #         else:
    #             self.edit_samples_pushButton.hide()
    #             if self.table == 'Columns':
    #                 self.query_model.setQuery('SELECT * FROM ColumnView')
    #                 self.table_proxy_model.setSourceModel(self.query_model)
    #             else:
    #                 self.model.setTable(table)
    #                 self.model.select()
    #                 self.table_proxy_model.setSourceModel(self.model)
    #         # for col in range(self.table_proxy_model.columnCount()):
    #         #     header = self.table_proxy_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
    #         #     if 'ID' in header and col != 0:
    #         #         # Leave ID in the first column but remove it for foreign key references
    #         #         header = header.replace('ID', '')
    #         #     header = TxM.add_spaces_camel(header)
    #         #     self.table_proxy_model.setHeaderData(col, QtC.Qt.Orientation.Horizontal, header, QtC.Qt.ItemDataRole.DisplayRole)
    #         # if self.case_checkBox.isChecked():
    #         #     self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseSensitive)
    #         # else:
    #         #     self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
    #         self.table_proxy_model.setFilterKeyColumn(-1)  # search all columns
    #         self.dbTable_tableView.setModel(self.table_proxy_model)
    #         self.dbTable_tableView.hideColumn(0)  # don't show ID column
    #         self.dbTable_tableView.resizeColumnsToContents()
    #         self.dbTable_tableView.setSortingEnabled(True)
    #         self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
    #         self.dbTable_tableView.verticalHeader().hide()
    #     else:
    #         print("Error: Tried to switch to a table with no table or tree..Don't know how it got here")
    #
    #     self.edit_pushButton.setText(f"Edit {table}")
    #
    # def search(self):
    #     """
    #     Search the current table for the text in the search box
    #     Check if the case-sensitive box is checked or not
    #     :return:
    #     """
    #     self.search_lineEdit: QtW.QLineEdit
    #     self.dbtable_comboBox: QtW.QComboBox
    #     # if self.case_checkBox.isChecked():
    #     #     self.sample_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseSensitive)
    #     #     self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseSensitive)
    #     #     self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseSensitive)
    #     # else:
    #
    #     # self.sample_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
    #     # self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
    #     # self.tree_proxy_model.setRecursiveFilteringEnabled(True)
    #     # self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
    #     search_expression = QtC.QRegularExpression(self.search_lineEdit.text())
    #     if self.table == 'Samples':
    #         self.sample_proxy_model.setFilterRegularExpression(search_expression)
    #     elif self.table in self.dbtree_list:
    #         self.tree_proxy_model.setFilterRegularExpression(search_expression)
    #         if search_expression != "":
    #             self.dbTable_treeView.expandAll()
    #     else:
    #         self.table_proxy_model.setFilterRegularExpression(search_expression)
    #
    # def show_context_menu(self, pos):
    #     """
    #     Show a context menu when right-clicking on a table or tree view
    #     :param pos: The position of the mouse click
    #     :return:
    #     """
    #     self.dbTable_tableView: QtW.QTableView
    #     self.dbTable_treeView: QtW.QTreeView
    #     tree_menu = TrC.TreeContextMenu()
    #     table_menu = QtW.QMenu()
    #     edit_action = table_menu.addAction('Edit')
    #     add_action = table_menu.addAction('Add')
    #     if self.table in self.dbtree_list:
    #         if self.table == 'Ages':
    #             tree_menu.set_view(self.dbTable_treeView, False, False, False)
    #         else:
    #             tree_menu.set_view(self.dbTable_treeView, False)
    #         action = tree_menu.exec(self.dbTable_tableView.viewport().mapToGlobal(pos))
    #         if action:
    #             self.tree_context_menu(action)
    #     elif self.table == 'Samples':
    #         view_data_menu = table_menu.addMenu('View Data')
    #         view_aliquot_action = view_data_menu.addAction('View Aliquots')
    #         view_spot_action = view_data_menu.addAction('View Spots')
    #         view_upb_analyses_action = view_data_menu.addAction('View U-Pb Analyses')
    #         action = table_menu.exec(self.dbTable_tableView.viewport().mapToGlobal(pos))
    #         if action:
    #             # get the row that was right-clicked
    #             index = self.dbTable_tableView.indexAt(pos)
    #             parent_id = self.table_proxy_model.data(self.table_proxy_model.index(index.row(), 0), QtC.Qt.ItemDataRole.DisplayRole)
    #             if action == view_aliquot_action:
    #                 self.open_tab(parent_id, 'Sample', 'Aliquot')
    #             elif action == view_spot_action:
    #                 self.open_tab(parent_id, 'Sample', 'Spot')
    #             elif action == view_upb_analyses_action:
    #                 self.open_tab(parent_id, 'Sample', 'UPbAnalysis')
    #             else:
    #                 self.table_context_menu(action)
    #     else:
    #         action = table_menu.exec(self.dbTable_tableView.viewport().mapToGlobal(pos))
    #         if action:
    #             self.table_context_menu(action)
    #
    # def tree_context_menu(self, action: QtG.QAction):
    #     """
    #     Context menu for tree views
    #     :param action: The action selected from the context menu
    #     :return:
    #     """
    #     if action.text() == 'Edit':
    #         self.edit_popup()
    #     elif 'Add' in action.text() or 'Insert' in action.text():
    #         self.add_popup(action)
    #     elif 'Expand' in action.text() or 'Collapse' in action.text():
    #         TrC.expand_collapse(self.dbTable_treeView, action)
    #
    # def edit_popup(self):
    #     if self.table == 'Samples':
    #         dlg = EditSampleTable(self.db, self.model)
    #     elif self.table == 'Aliquots' or self.table == 'Spots' or self.table == 'UPbData':
    #         return
    #     elif self.table in self.dbtree_list:
    #         TrC.save_expanded_state(self.table, self.tree_proxy_model, self.dbTable_treeView)
    #         dlg = EditTree(self.db, self.model, self.table)
    #     else:
    #         dlg = EditTable(self.table)
    #     dlg.exec()
    #     self.display_table()
    #
    # def edit_samples_popup(self):
    #     selected_samples = []
    #     self.dbTable_tableView: QtW.QTableView
    #     # Add the sample ID for any rows that are selected
    #     selected_indexes = self.dbTable_tableView.selectedIndexes()
    #     for index in selected_indexes:
    #         id_index = index.siblingAtColumn(0)
    #         selected_samples.append(id_index.data(QtC.Qt.ItemDataRole.DisplayRole))
    #     dlg = SampleInformation(self, selected_samples)
    #     dlg.exec()
    #     self.display_table()
    #
    # def add_popup(self, action: QtG.QAction | None = None):
    #     dlg = None
    #     dlg_args = None
    #     if self.table in self.dbtree_list:
    #         TrC.save_expanded_state(self.table, self.tree_proxy_model, self.dbTable_treeView)
    #         indexes = self.dbTable_treeView.selectedIndexes()
    #         item_ids, parent_ids, parent_rows = TrC.get_selected_ids(self.tree_proxy_model, indexes)
    #         if action:
    #             if action.text() == 'Insert above':
    #                 row = parent_rows[0]
    #                 parent_id = parent_ids[0]
    #                 dlg_args = (None, parent_id, row)
    #                 # dlg = EditTree.add_popup(EditTree(self.db, self.tree_model.source_model, self.dbTable_comboBox.currentText()), None, parent_id, row)
    #             elif action.text() == 'Insert below':
    #                 row = parent_rows[0] + 1
    #                 parent_id = parent_ids[0]
    #                 dlg_args = (None, parent_id, row)
    #                 # dlg = EditTree.add_popup(EditTree(self.db, self.tree_model.source_model, self.dbTable_comboBox.currentText()), None, parent_id, row)
    #             elif action.text() == 'Add child':
    #                 parent_id = item_ids[0]
    #                 dlg_args = (None, parent_id)
    #                 # dlg = EditTree.add_popup(EditTree(self.db, self.tree_model.source_model, self.dbTable_comboBox.currentText()), None, parent_id)
    #             elif action.text() == 'Add parent':
    #                 dlg_args = (item_ids, parent_ids, parent_rows)
    #                 # dlg = EditTree.add_parent(item_ids, parent_ids, parent_rows)
    #             elif action.text() == 'Add to end':
    #                 dlg_args = (None, None)
    #         if dlg_args:
    #             dlg = EditTree(self.db, self.tree_model.source_model, self.dbTable_comboBox.currentText())
    #     else:
    #         dlg = EditTable(self.table)
    #     if not dlg:
    #         return
    #     dlg.add_popup(*dlg_args)
    #     self.display_table()

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
        insert_index = self.tabWidget.count() - 2
        self.tabWidget.insertTab(insert_index, ViewDataTab(parent_id, parent_type, child_type), f'{parent_type} {parent_name}: {child_label}')

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
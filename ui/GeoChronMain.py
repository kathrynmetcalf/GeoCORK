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
import Functions.Table_classes as TbC
import Functions.Tree_classes as TrC
import Functions.Text_manipulations as TxM
import ui.import_wizard
import ui.New_source
from ui.ExportWidget import ExportWidget
from Functions.Tree_classes import TreeSortFilterProxyModel
from ui.EditTags import EditTags
from ui.EditSampleTable import EditSampleTable
from ui.EditTable import EditTable
from ui.EditTree import EditTree
from ui.AddTags import AddTags
from ui.Filters import QueryBuilder
from ui.SampleInformation import  SampleInformation


# import Select_Database as sd  # Eventually get database file from initial dialog


class GeoChron(QtW.QMainWindow):
    def __init__(self, landingpage):
        super().__init__()
        # Define any variables here
        self.landingpage = landingpage
        self.db = QtS.QSqlDatabase.addDatabase('QSQLITE')
        self.db_file = self.landingpage.get_filename()
        self.db.setDatabaseName(self.db_file)
        self.settings = QSettings("CSUF", "GeoChron")
        ok = self.db.open()
        print("Database is open: " + str(ok))
        self.loadWindowState()

        sources_ui_file = "ui/GeochronMain.ui"
        loadUi(sources_ui_file, self)

        self.switch_to_table()

        Create_db.create_tables(self.db_file)
        #list of all user-viewable tables in the database
        self.user_view_tables = ['Ages', 'Age Signatures', 'Aliquots', 'Aliquot Context', 'Columns', 'Lab Facilities', 'Instruments',
                        'Regions', 'Rock Types', 'Sample Contexts', 'Samples', 'Sampling Methods', 'Settings', 'Sources',
                        'Spot Compositions', 'Spot Contexts', 'UPb Data', 'Analysis Methods', 'Units']
        #list of tables to display as a tree structure
        self.dbtree_list = ['Ages', 'AgeSignatures', 'AliquotContexts', 'Regions', 'RockTypes', 'SampleContexts',
                       'SamplingMethods', 'Settings', 'SpotCompositions', 'SpotContexts', 'Units']
        self.dbtable_list = ['Aliquots', 'Columns', 'LabFacilities', 'Instruments', 'Sources', 'UPbData',
                            'AnalysisMethods']

        self.ui_widgets()

        # Set up models
        self.sample_model = QtS.QSqlQueryModel()
        self.sample_proxy_model = QtC.QSortFilterProxyModel()
        self.model = QtS.QSqlTableModel()
        self.tree_model = TrC.TreeModel()
        self.tree_proxy_model = TreeSortFilterProxyModel(view=self.dbTable_treeView)
        self.table_proxy_model = QtC.QSortFilterProxyModel()
        self.display_table_list()

        # Display the selected table
        self.dbTable_comboBox.currentIndexChanged.connect(self.display_table)

        # Signal for search bar
        self.search_lineEdit.textChanged.connect(self.search)
        # Signal for clicked add button in main window
        self.actionImport.triggered.connect(self.show_import_wizard_dialog)
        # Signal for clicked edit button
        self.edit_pushButton.clicked.connect(self.edit_popup)
        # Signal for clicked edit samples button
        self.edit_samples_pushButton.clicked.connect(self.edit_samples_popup)
        # End widgets here # show the window when done, used for making a top-level window

        self.tabWidget: QTabWidget
        self.querybuilder = QueryBuilder(self)
        self.tabWidget.addTab(ExportWidget(self), 'Export')
        self.querybuilder.setLayout(self.horizontalLayout_2)
        self.horizontalLayout_2.addWidget(self.querybuilder)


        self.show()

    def closeEvent(self, a0):
        self.landingpage.show()
        self.saveWindowState()
        """When the main window is closing, drop all the views except the SampleView"""
        view_list = QtS.QSqlQuery('''SELECT name FROM sqlite_schema WHERE type = "view"''')
        while view_list.next():
            view = view_list.value(0)
            if view != 'SampleView':
                # if the view is not SampleView, drop it
                query = QtS.QSqlQuery()
                query.prepare(f'''DROP VIEW IF EXISTS {view}''')
                if query.exec():
                    print(f'Successfully dropped {view}')
        super().closeEvent(a0)

    # Define any methods here

    def ui_widgets(self):
        self.dbTable_tableView: QtW.QTableView
        self.dbTable_treeView: QtW.QTreeView
        self.dbTable_comboBox: QtW.QComboBox
        self.search_lineEdit: QtW.QLineEdit
        self.add_pushButton: QtW.QPushButton
        self.submitall_pushButton: QtW.QPushButton
        self.status_label: QtW.QLabel
        self.db_stackedWidget: QtW.QStackedWidget
        self.case_checkBox: QtW.QCheckBox

    def switch_to_table(self):
        """
        Sets the current widget to a table view
        :return:
        """
        self.db_stackedWidget: QtW.QStackedWidget
        self.db_stackedWidget.setCurrentWidget(self.db_table)
        
    def switch_to_tree(self):
        """
        Sets the current widget to a tree view
        :return:
        """
        self.db_stackedWidget: QtW.QStackedWidget
        self.db_stackedWidget.setCurrentWidget(self.db_tree)

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

    def display_table_list(self):
        """
        Populates the tables combo box with the editable tables
        Displays the default table
        :return:
        """
        self.dbTable_comboBox: QtW.QComboBox
        self.dbTable_comboBox.addItems(self.user_view_tables)
        self.previous_table = ''
        self.dbTable_comboBox.setCurrentText('Samples')
        # self.display_table()

    def display_table(self):
        """
        Displays the selected table
        :return:
        """
        self.edit_pushButton: QPushButton
        self.dbTable_tableView: QtW.QTableView
        self.dbTable_treeView: QtW.QTreeView
        self.dbTable_comboBox: QtW.QComboBox
        self.add_pushButton: QtW.QPushButton
        self.case_checkBox: QtW.QCheckBox
        table_name = self.dbTable_comboBox.currentText()
        # Remove spaces from display names
        table = TxM.remove_spaces(table_name)
        # If moving from a tree table, save the expanded state first
        if self.previous_table in self.dbtree_list and self.previous_table != table:
            TrC.save_expanded_state(self.previous_table, self.tree_proxy_model, self.dbTable_treeView, self.settings)
        self.previous_table = table

        # self.edit_pushButton.clicked.connect(lambda: self.edit_popup(self.sample_model))
        # self.edit_pushButton.clicked.disconnect()
        if table == 'Samples':
            self.switch_to_table()
            self.edit_samples_pushButton.show()
            query = TbC.SampleTableModel().setupQuery()
            self.sample_model.setQuery(QtS.QSqlQuery(query, self.db))
            # self.edit_pushButton.clicked.connect(lambda: self.edit_popup(self.sample_model))
            # view = "SampleView"
            # self.sample_proxy_model.setTable(view)
            # self.sample_proxy_model.select()
            for col in range(self.sample_model.columnCount()):
                header = TxM.add_spaces_camel(
                    self.sample_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
                self.sample_model.setHeaderData(col, QtC.Qt.Orientation.Horizontal, header, QtC.Qt.ItemDataRole.DisplayRole)

            self.sample_proxy_model.setSourceModel(self.sample_model)
            self.sample_proxy_model.setFilterKeyColumn(-1)  # search all columns
            self.dbTable_tableView.setModel(self.sample_proxy_model)
            self.dbTable_tableView.hideColumn(0)  # don't show ID column
            self.dbTable_tableView.resizeColumnsToContents()
            self.dbTable_tableView.setSortingEnabled(True)
            self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
        elif table in self.dbtree_list:
            self.switch_to_tree()
            self.edit_samples_pushButton.hide()
            self.model.setTable(table)
            self.model.select()

            self.tree_model = TrC.TreeModel(self.model, None)
            self.tree_proxy_model.setSourceModel(self.tree_model)
            # self.edit_pushButton.clicked.connect(lambda: self.edit_popup(self.model))

            self.dbTable_treeView.setModel(self.tree_proxy_model)
            self.dbTable_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
            self.dbTable_treeView.hideColumn(1)  # don't show ID column
            self.dbTable_treeView.hideColumn(2)  # don't show parent ID column
            self.dbTable_treeView.hideColumn(3)  # don't show parent row column
            # Keep the tree sorted as dictated by the database
            self.dbTable_treeView.setSortingEnabled(False)
            # if table == 'Ages':
                # self.dbTable_treeView.hideColumn(6)  # don't show created column
                # self.dbTable_treeView.hideColumn(7)  # don't show modified column
                # self.dbTable_treeView.sortByColumn(4, Qt.SortOrder(0))
            self.dbTable_treeView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
            TrC.restore_expanded_state(table, self.tree_proxy_model, self.dbTable_treeView, self.settings)
        elif table in self.dbtable_list:
            self.switch_to_table()
            self.edit_samples_pushButton.hide()
            self.model.setTable(table)
            self.model.select()
            # self.edit_pushButton.clicked.connect(lambda: self.edit_popup(self.model))
            for col in range(self.model.columnCount()):
                header = TxM.add_spaces_camel(self.model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
                self.model.setHeaderData(col, QtC.Qt.Orientation.Horizontal, header, QtC.Qt.ItemDataRole.DisplayRole)
            self.table_proxy_model.setSourceModel(self.model)
            # if self.case_checkBox.isChecked():
            #     self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseSensitive)
            # else:
            #     self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
            self.table_proxy_model.setFilterKeyColumn(-1)  # search all columns
            self.dbTable_tableView.setModel(self.table_proxy_model)
            self.dbTable_tableView.hideColumn(0)  # don't show ID column
            # self.dbTable_tableView.hideColumn(3)  # don't show created column
            # self.dbTable_tableView.hideColumn(4)  # don't show modified column
            self.dbTable_tableView.resizeColumnsToContents()
            self.dbTable_tableView.setSortingEnabled(True)
            self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)

        else:
            print("Error: Tried to switch to a table with no table or tree..Don't know how it got here")

        self.edit_pushButton.setText(f"Edit {table_name}")

    def search(self):
        """
        Search the current table for the text in the search box
        Check if the case-sensitive box is checked or not
        :return:
        """
        self.search_lineEdit: QtW.QLineEdit
        self.dbtable_comboBox: QtW.QComboBox
        # if self.case_checkBox.isChecked():
        #     self.sample_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseSensitive)
        #     self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseSensitive)
        #     self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseSensitive)
        # else:

        # self.sample_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        # self.treWe_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        # self.tree_proxy_model.setRecursiveFilteringEnabled(True)
        # self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        search_expression = QtC.QRegularExpression(self.search_lineEdit.text())
        table_name = self.dbTable_comboBox.currentText()
        # Remove spaces from display names
        table = table_name.replace(" ", "")
        if table == 'Samples':
            self.sample_proxy_model.setFilterRegularExpression(search_expression)
        elif table in self.dbtree_list:
            self.tree_proxy_model.setFilterRegularExpression(search_expression)
            if search_expression is not "":
                self.dbTable_treeView.expandAll()
        else:
            self.table_proxy_model.setFilterRegularExpression(search_expression)

    def get_existing(self, field, table):
        """
        Get all the entries for the selected field in the selected table
        Parameters
        ----------
        field: column name
        table: database table name

        Returns
        -------
        existing: list of the existing entries
        """
        conn = sqlite3.connect(self.db_file)
        with conn:
            c = conn.cursor()
            sql = f'''SELECT {field} FROM {table}'''
            if c.execute(sql):
                existing = c.fetchall()
                return existing

    def edit_popup(self):
        table_name = self.dbTable_comboBox.currentText()
        table = TxM.remove_spaces(table_name)
        if table_name == 'Samples':
            dlg = EditSampleTable(self.db, self.sample_model)
        elif table_name == 'Aliquots' or table_name == 'Spots' or table_name == 'UPb Data':
            return
        elif table in self.dbtree_list:
            dlg = EditTree(self.db, self.model, table_name)
        else:
            dlg = EditTable(self.db, self.model, table_name)
        dlg.exec()
        self.display_table()

    def edit_samples_popup(self):
        selected_samples = []
        self.dbTable_tableView: QtW.QTableView
        # Add the sample ID for any rows that are selected
        selected_indexes = self.dbTable_tableView.selectedIndexes()
        for index in selected_indexes:
            id_index = index.siblingAtColumn(0)
            selected_samples.append(id_index.data(QtC.Qt.ItemDataRole.DisplayRole))
        dlg = SampleInformation(self, selected_samples)
        dlg.exec()
        self.display_table()

    def saveWindowState(self):
        self.settings.setValue("ui/GeoChronMain/pos", self.pos())
        self.settings.setValue("ui/GeoChronMain/size", self.size())

    def loadWindowState(self):
        self.move(self.settings.value("ui/GeoChronMain/pos", defaultValue=QPoint(410, 241)))
        self.resize(self.settings.value("ui/GeoChronMain/size", defaultValue=QSize(810, 569)))

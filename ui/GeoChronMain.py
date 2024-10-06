import sys
from pathlib import Path
import sqlite3
import re
# import pandas as pd
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import Qt, QEventLoop, QStandardPaths, QPoint, QSettings, QSize
from PyQt6.QtWidgets import QFileDialog, QWidget

from PyQt6.uic import loadUi
import Functions.Create_database as Create_db
import Functions.Tree_classes as TrC
import Functions.Group_classes as GC
import Functions.Text_manipulations as TxM
import ui.import_wizard
import ui.New_source
from Functions.Tree_classes import TreeModel
from ui.EditTags import EditTags
from ui.EditTable import EditTable
from ui.EditTree import EditTree
from ui.AddTags import AddTags
from ui.Filters import QueryBuilder


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

        self.loadWindowState()
        # Define any widgets here

        sources_ui_file = "ui/GeochronMain.ui"
        loadUi(sources_ui_file, self)

        self.sample_model = QtS.QSqlQueryModel()
        self.aliquot_model = QtS.QSqlQueryModel()
        self.spot_model = QtS.QSqlQueryModel()
        self.model = QtS.QSqlTableModel()
        self.tree_model = TrC.TreeModel
        self.sample_proxy_model = QtC.QSortFilterProxyModel()
        self.table_proxy_model = QtC.QSortFilterProxyModel()
        self.tree_proxy_model = QtC.QSortFilterProxyModel()
        self.delegate = QtS.QSqlRelationalDelegate()
        self.status_bar = QtW.QStatusBar()
        # self.status_bar.show()

        self.settings = QtC.QSettings('User', 'Geochron')
        self.switch_to_table()

        Create_db.create_tables(self.db_file)
        self.dbtable_list = ['Ages', 'Age Signatures', 'Aliquots', 'Aliquot Context', 'Columns', 'Lab Facilities', 'Instruments',
                        'Regions', 'Rock Types', 'Sample Context', 'Samples', 'Sampling Methods', 'Settings', 'Sources',
                        'Spot Compositions', 'Spot Context', 'UPb Data', 'Analysis Methods', 'Units']
        self.dbtree_list = ['Ages', 'AgeSignatures', 'AliquotContext', 'Regions', 'RockTypes', 'SampleContext',
                       'SamplingMethods', 'Settings', 'SpotCompositions', 'SpotContext', 'Units']
        self.display_table_list()

        self.ui_widgets()

        # Display the selected table
        self.dbTable_comboBox.activated.connect(self.display_table)

        # Signal for search bar
        self.search_lineEdit.textChanged.connect(self.search)
        # Signal for clicked add button in main window
        self.edit_pushButton.clicked.connect(self.edit_popup)
        self.actionImport.triggered.connect(self.show_import_wizard_dialog)
        # End widgets here # show the window when done, used for making a top-level window

        self.querybuilder = QueryBuilder(self)
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

    def open_db(self):
        """
        Opens a file dialog to select an existing database file, must be in the format .db
        :return: database file name with path
        """
        home_dir = str(Path.home())
        db_file = QFileDialog.getOpenFileName(self, 'Open file', home_dir, 'db(*.db)')
        return db_file[0]

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
        home_dir = str(Path.home()) + '\Downloads'
        fname = QFileDialog.getOpenFileName(self, 'Open file', home_dir)
        import_wizard = ui.import_wizard.ImportWizardDialog(fname[0], self.db_file)
        #todo fix crash on cancel file dialog
        import_wizard.exec()

    def display_table_list(self):
        """
        Populates the tables combo box with the editable tables
        Displays the default table
        :return:
        """
        self.dbTable_comboBox: QtW.QComboBox
        self.dbTable_comboBox.addItems(self.dbtable_list)
        self.previous_table = ''
        self.dbTable_comboBox.setCurrentText('Samples')
        self.display_table()

    def display_table(self):
        """
        Displays the selected table
        :return:
        """
        if self.previous_table in self.dbtree_list:
            TrC.save_expanded_state(self.previous_table, self.tree_proxy_model, self.dbTable_treeView, self.settings)
        self.dbTable_tableView: QtW.QTableView
        self.dbTable_treeView: QtW.QTreeView
        self.dbTable_comboBox: QtW.QComboBox
        self.add_pushButton: QtW.QPushButton
        self.case_checkBox: QtW.QCheckBox
        table_name = self.dbTable_comboBox.currentText()
        # Remove spaces from display names
        table = TxM.remove_spaces(table_name)
        self.previous_table = table
        if table == 'Samples':
            self.switch_to_table()
            view = "SampleView"
            self.model.setTable(view)
            self.model.select()
            for col in range(self.model.columnCount()):
                header = TxM.add_spaces_camel(
                    self.model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
                self.model.setHeaderData(col, QtC.Qt.Orientation.Horizontal, header, QtC.Qt.ItemDataRole.DisplayRole)
            self.sample_proxy_model.setSourceModel(self.model)
            self.sample_proxy_model.setFilterKeyColumn(-1)  # search all columns
            self.dbTable_tableView.setModel(self.sample_proxy_model)
            self.dbTable_tableView.hideColumn(0)  # don't show ID column
            self.dbTable_tableView.resizeColumnsToContents()
            self.dbTable_tableView.setSortingEnabled(True)
            self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
        elif table in self.dbtree_list:
            self.switch_to_tree()
            self.model.setTable(table)
            self.model.select()
            # for col in range(self.model.columnCount()):
            #     header = TxM.add_spaces_camel(self.model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            #     self.model.setHeaderData(col, QtC.Qt.Orientation.Horizontal, header, QtC.Qt.ItemDataRole.DisplayRole)
            self.tree_model = TrC.TreeModel(self.model, None)

            self.tree_proxy_model.setSourceModel(self.tree_model)
            self.tree_proxy_model.setFilterKeyColumn(-1)  # search all columns
            self.dbTable_treeView.setModel(self.tree_proxy_model)
            TrC.restore_expanded_state(table, self.tree_proxy_model, self.dbTable_treeView, self.settings)
            self.dbTable_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
            self.dbTable_treeView.hideColumn(1)  # don't show ID column
            self.dbTable_treeView.hideColumn(2)  # don't show parent ID column
            self.dbTable_treeView.hideColumn(3)  # don't show parent row column
            self.dbTable_treeView.setSortingEnabled(False)
            if table == 'Ages':
                self.dbTable_treeView.hideColumn(5)  # don't show created column
                self.dbTable_treeView.hideColumn(6)  # don't show modified column
                # self.dbTable_treeView.sortByColumn(4, Qt.SortOrder(0))
            self.dbTable_treeView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
        else:
            self.switch_to_table()
            self.model.setTable(table)
            self.model.select()
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
        self.sample_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.tree_proxy_model.setRecursiveFilteringEnabled(True)
        self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        search_expression = QtC.QRegularExpression(self.search_lineEdit.text())
        table_name = self.dbTable_comboBox.currentText()
        # Remove spaces from display names
        table = table_name.replace(" ", "")
        if table == 'Samples':
            self.sample_proxy_model.setFilterRegularExpression(search_expression)
        elif table in self.dbtree_list:
            self.tree_proxy_model.setFilterRegularExpression(search_expression)
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
            dlg = EditTable(self.db, self.sample_model, table_name)
        elif table_name == 'Aliquots' or table_name == 'Spots' or table_name == 'UPb Data':
            return
        elif table in self.dbtree_list:
            dlg = EditTree(self.db, self.model, table_name)
        else:
            dlg = EditTable(self.db, self.model, table_name)
        dlg.exec()
        self.display_table()

    def saveWindowState(self):
        self.settings.setValue("ui/GeoChronMain/pos", self.pos())
        self.settings.setValue("ui/GeoChronMain/size", self.size())

    def loadWindowState(self):
        self.move(self.settings.value("ui/GeoChronMain/pos", defaultValue=QPoint(410, 241)))
        self.resize(self.settings.value("ui/GeoChronMain/size", defaultValue=QSize(810, 569)))

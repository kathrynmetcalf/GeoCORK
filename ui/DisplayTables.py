import sqlite3
import os
import sys
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import Qt, QEventLoop, QStandardPaths, QPoint, QSettings, QSize, QAbstractTableModel, QTimer
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtWidgets import QFileDialog, QWidget, QPushButton, QTabWidget, QTableWidgetItem, QTableWidget, QTreeView

from PyQt6.uic import loadUi
from Functions.Widget_classes import (
    TreeSortFilterProxyModel, DisplayRoundedModel, DisplayRoundedQueryModel, SQLiteTableModel, WordWrapDelegate,
    save_expanded_state, restore_expanded_state, expand_collapse, get_selected_tree_ids, TreeContextMenu, TreeModel,
    ReadableProxyModel
)
import Functions.Text_manipulations as TxM
from Functions import SQLUtils
from Functions import Savepoint_manager
from Functions.Database_manager import update_database
from Functions.Settings_manager import settings
# from Functions.Widget_classes import add_popup_dialog
from ui.EditSampleTable import EditSampleTable
from ui.EditTable import EditTable
from ui.EditTree import EditTree
from ui.AddTags import AddTags
from ui.AddTreeTags import AddTreeTags
from ui.New_reference import NewReference
from ui.SampleInformation import  SampleInformation
import time

class DisplayTables(QtW.QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        # Load the ui file
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "DisplayTables.ui")
        loadUi(sources_ui_file, self)

        # Retrieve the main window
        for widget in QtW.QApplication.topLevelWidgets():
            if widget.inherits("QMainWindow"):
                self.main_window = widget
                break

        # Retrieve the savepoint manager
        savepoint_manager = Savepoint_manager.SavepointManager()
        self.savepoint_manager = savepoint_manager.get_instance()

        # Message box for any popup messages
        self.msg = QtW.QMessageBox(self)

        # List of all user-viewable tables in the database
        self.user_view_tables = SQLUtils.user_viewable_tables
        # List of tables to display as a tree structure
        self.dbtree_list = SQLUtils.user_viewable_trees
        self.dbtable_list = [table for table in self.user_view_tables if table not in self.dbtree_list]

        self.sample_proxy_model = QtC.QSortFilterProxyModel()
        self.model = DisplayRoundedModel()
        self.query_model = DisplayRoundedQueryModel()
        self.tree_model = TreeModel()
        self.tree_proxy_model = TreeSortFilterProxyModel(view=self.dbTable_treeView)
        self.table_proxy_model = ReadableProxyModel()
        self.table = ''
        self.show_cols = []
        self.switch_to_table()
        self.display_table_list()

        self.connect_signals()

    def connect_signals(self):
        # Signal for table combo box
        self.dbTable_comboBox.currentIndexChanged.connect(self.display_table)
        # Signal for search bar
        self.search_lineEdit.textChanged.connect(self.search)
        # Signal for clicked edit button
        self.edit_pushButton.clicked.connect(self.edit_popup)
        # Signal for clicked edit samples button
        self.edit_samples_pushButton.clicked.connect(lambda: self.edit_samples_popup('edit_pushButton'))
        # Context menu for table and tree views
        self.dbTable_tableView.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.dbTable_tableView.customContextMenuRequested.connect(self.show_context_menu)
        self.dbTable_treeView.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.dbTable_treeView.customContextMenuRequested.connect(self.show_context_menu)

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
        self.display_table()

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
        table = self.dbTable_comboBox.currentText()
        self.table = TxM.remove_spaces(table)
        # If moving from a tree table, save the expanded state first
        if self.previous_table in self.dbtree_list and self.previous_table != self.table:
            save_expanded_state(self.previous_table, self.tree_proxy_model, self.dbTable_treeView)
        self.previous_table = self.table

        if self.table in self.dbtree_list:
            self.switch_to_tree()
            self.edit_samples_pushButton.hide()
            self.model = QtS.QSqlTableModel()
            self.model.setTable(table)
            self.model.select()

            self.tree_model = TreeModel(self.model, None)
            self.tree_proxy_model.setSourceModel(self.tree_model)
            # self.edit_pushButton.clicked.connect(lambda: self.edit_popup(self.model))

            self.dbTable_treeView.setModel(self.tree_proxy_model)
            self.dbTable_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
            self.dbTable_treeView.hideColumn(1)  # don't show ID column
            self.dbTable_treeView.hideColumn(2)  # don't show parent ID column
            self.dbTable_treeView.hideColumn(3)  # don't show parent row column
            # Keep the tree sorted as dictated by the database
            self.dbTable_treeView.setSortingEnabled(False)
            self.dbTable_treeView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
            restore_expanded_state(table, self.tree_proxy_model, self.dbTable_treeView)
            self.dbTable_treeView: QTreeView
        elif self.table in self.dbtable_list:
            self.switch_to_table()
            if self.table == 'Samples':
                self.show_cols = settings.value('sample_view_columns')
                self.show_cols = ', '.join(self.show_cols)
                model = SQLiteTableModel(f'SELECT {self.show_cols} FROM SampleView')
                # model = SQLiteTableModel(f'SELECT * FROM SampleView')

                self.table_proxy_model.setSourceModel(model)
                self.edit_samples_pushButton.show()
                # # Signal for double-clicked on table-view
                # self.dbTable_tableView.doubleClicked.connect(self.edit_samples_popup('double-clicked'))
            else:
                self.edit_samples_pushButton.hide()
                if self.table == 'Columns':
                    self.show_cols = settings.value('column_view_columns')
                    self.show_cols = ', '.join(self.show_cols)
                    model = SQLiteTableModel(f'SELECT {self.show_cols} FROM ColumnView')
                    # model = SQLiteTableModel(f'SELECT * FROM ColumnView')
                    self.table_proxy_model.setSourceModel(model)
                elif self.table == 'References':
                    self.show_cols = settings.value('reference_view_columns')
                    self.show_cols = ', '.join(self.show_cols)
                    model = SQLiteTableModel(f'SELECT {self.show_cols} FROM ReferenceView')
                    # model = SQLiteTableModel(f'SELECT * FROM ReferenceView')
                    self.table_proxy_model.setSourceModel(model)
                else:
                    self.model.setTable(table)
                    self.model.select()
                    self.table_proxy_model.setSourceModel(self.model)
            # if self.case_checkBox.isChecked():
            #     self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseSensitive)
            # else:
            #     self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)

            self.dbTable_tableView.setWordWrap(True)
            self.dbTable_tableView.setTextElideMode(Qt.TextElideMode.ElideNone)  # Prevent text truncation
            self.dbTable_tableView.setItemDelegate(WordWrapDelegate(self.dbTable_tableView))

            self.table_proxy_model.setFilterKeyColumn(-1)  # search all columns
            self.dbTable_tableView.setModel(self.table_proxy_model)
            self.dbTable_tableView.hideColumn(0)  # don't show ID column
            self.dbTable_tableView.resizeColumnsToContents()
            self.dbTable_tableView.setSortingEnabled(True)
            self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.dbTable_tableView.verticalHeader().hide()

            # Optimize window resizing
            self.resize_timer = QTimer()
            self.resize_timer.setSingleShot(True)
            self.resize_timer.timeout.connect(self.resizeRowsOptimized)

            # Connect resizing events
            self.dbTable_tableView.horizontalHeader().sectionResized.connect(self.optimizeVerticalResize)
            self.dbTable_tableView.verticalHeader().sectionResized.connect(self.optimizeVerticalResize)
        else:
            print("Error: Tried to switch to a table with no table or tree..Don't know how it got here")

        self.edit_pushButton.setText(f"Edit {table}")

    def optimizeVerticalResize(self, logical_index, old_size, new_size):
        """Trigger a delayed row height update when the user resizes the window vertically."""
        self.resize_timer.start(250)  # Add a slight delay to avoid excessive updates

    def resizeRowsOptimized(self):
        """Resize rows only when resizing stops."""
        self.dbTable_tableView.resizeRowsToContents()
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
        # self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        # self.tree_proxy_model.setRecursiveFilteringEnabled(True)
        # self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        search_expression = QtC.QRegularExpression(self.search_lineEdit.text())
        if self.table == 'Samples':
            self.sample_proxy_model.setFilterRegularExpression(search_expression)
        elif self.table in self.dbtree_list:
            self.tree_proxy_model.setFilterRegularExpression(search_expression)
            if search_expression != "":
                self.dbTable_treeView.expandAll()
        else:
            self.table_proxy_model.setFilterRegularExpression(search_expression)

    def show_context_menu(self, pos):
        """
        Show a context menu when right-clicking on a table or tree view
        :param pos: The position of the mouse click
        :return:
        """
        self.dbTable_tableView: QtW.QTableView
        self.dbTable_treeView: QtW.QTreeView
        tree_menu = TreeContextMenu()
        table_menu = QtW.QMenu()
        edit_action = table_menu.addAction('Edit')
        add_action = table_menu.addAction('Add')
        if self.table in self.dbtree_list:
            if self.table == 'Ages':
                tree_menu.set_view(self.dbTable_treeView, False, False, False)
            else:
                tree_menu.set_view(self.dbTable_treeView, False)
            action = tree_menu.exec(self.dbTable_tableView.viewport().mapToGlobal(pos))
            if action:
                self.tree_context_menu(action)
        elif self.table == 'Samples':
            view_data_menu = table_menu.addMenu('View Data')
            view_aliquot_action = view_data_menu.addAction('View Aliquots')
            view_spot_action = view_data_menu.addAction('View Spots')
            view_upb_analyses_action = view_data_menu.addAction('View U-Pb Analyses')
            action = table_menu.exec(self.dbTable_tableView.viewport().mapToGlobal(pos))
            if action:
                # get the row that was right-clicked
                parent_ids = []
                if self.dbTable_tableView.selectionModel().hasSelection():
                        for index in self.dbTable_tableView.selectionModel().selectedIndexes():
                            parent_id = self.table_proxy_model.data(self.table_proxy_model.index(index.row(), 0), QtC.Qt.ItemDataRole.DisplayRole)
                            parent_ids.append(str(parent_id))


                # index = self.dbTable_tableView.indexAt(pos)
                # parent_id = self.table_proxy_model.data(self.table_proxy_model.index(index.row(), 0), QtC.Qt.ItemDataRole.DisplayRole)
                if action == view_aliquot_action:
                    self.main_window.open_tab(parent_ids, 'Sample', 'Aliquot')
                elif action == view_spot_action:
                    self.main_window.open_tab(parent_ids, 'Sample', 'Spot')
                elif action == view_upb_analyses_action:
                    self.main_window.open_tab(parent_ids, 'Sample', 'UPbAnalysis')
                else:
                    self.table_context_menu(action)
        else:
            action = table_menu.exec(self.dbTable_tableView.viewport().mapToGlobal(pos))
            if action:
                self.table_context_menu(action)

    def tree_context_menu(self, action: QtG.QAction):
        """
        Context menu for tree views
        :param action: The action selected from the context menu
        :return:
        """
        if action.text() == 'Edit':
            self.edit_popup()
        elif 'Add' in action.text() or 'Insert' in action.text():
            self.add_popup(action)
        elif 'Expand' in action.text() or 'Collapse' in action.text():
            expand_collapse(self.dbTable_treeView, action)

    def table_context_menu(self, action: QtG.QAction):
        """
        Context menu for table views
        :param action: The action selected from the context menu
        :return:
        """
        if action.text() == 'Edit':
            if self.table == 'Samples':
                self.edit_samples_popup('edit_context_menu')
            else:
                self.edit_popup()
        elif 'Add' in action.text() or 'Insert' in action.text():
            self.add_popup(action)

    def edit_popup(self):
        if self.table == 'Samples':
            dlg = EditSampleTable(self.model)
        elif self.table == 'Aliquots' or self.table == 'Spots' or self.table == 'UPbData':
            return
        elif self.table in self.dbtree_list:
            save_expanded_state(self.table, self.tree_proxy_model, self.dbTable_treeView)
            dlg = EditTree(self.table)
        else:
            dlg = EditTable(self.table)
        dlg.exec()
        update_database()
        self.display_table()

    def edit_samples_popup(self, text=None):
        print(f'edit_samples_popup called with {text}')
        if self.table != 'Samples':
            return
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

    def add_popup(self, action: QtG.QAction | None = None):
        dlg = None
        dlg_args = None
        if self.table in self.dbtree_list:
            save_expanded_state(self.table, self.tree_proxy_model, self.dbTable_treeView)
            indexes = self.dbTable_treeView.selectedIndexes()
            item_ids, parent_ids, parent_rows = get_selected_tree_ids(self.tree_proxy_model, indexes)
            if action:
                if action.text() == 'Insert above':
                    row = parent_rows[0]
                    parent_id = parent_ids[0]
                    dlg_args = (self.table, parent_id, row)
                elif action.text() == 'Insert below':
                    row = parent_rows[0] + 1
                    parent_id = parent_ids[0]
                    dlg_args = (None, parent_id, row)
                elif action.text() == 'Add child':
                    parent_id = item_ids[0]
                    dlg_args = (None, parent_id)
                elif action.text() == 'Add parent':
                    dlg_args = (item_ids, parent_ids, parent_rows)
                elif action.text() == 'Add to end':
                    dlg_args = (None, None)
            if dlg_args:
                dlg = AddTreeTags(self.table, *dlg_args)
        else:
            dlg = AddTags(self.table)
        if not dlg:
            return
        dlg.exec()
        update_database()
        self.display_table()

    def closeEvent(self, event):
        if self.table in self.dbtree_list:
            save_expanded_state(self.table, self.tree_proxy_model, self.dbTable_treeView)
        event.accept()
        super().closeEvent(event)
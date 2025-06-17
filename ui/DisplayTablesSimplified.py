import os
import os
import sys

from PyQt6 import QtCore as QtC
from PyQt6 import QtSql as QtS
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import QPushButton, QTreeView
from PyQt6.uic import loadUi

import Functions.Text_manipulations as TxM
import logger_setup
from Functions import SQLUtils
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.Widget_classes import (
    TreeSortFilterProxyModel, DisplayRoundedModel, DisplayRoundedQueryModel, SQLiteTableModel, WordWrapDelegate,
    save_expanded_state, restore_expanded_state, TreeModel,
    ReadableProxyModel, get_view_from_table
)
from Functions.Database_views import ViewQuery


class DisplayTablesSimplified(QtW.QWidget):
    def __init__(self, parent, db_file: str):
        super().__init__(parent)
        # logger_setup.get_logger().info("Starting the display tables window")
        self.setObjectName('database_tab')

        self.db_file = db_file

        if 'temp' in QSqlDatabase().connectionNames():
            QSqlDatabase().removeDatabase('temp')

        self.database = QSqlDatabase().addDatabase('QSQLITE', 'temp')
        self.database.setDatabaseName(self.db_file)
        self.database.open()
        # Load the ui file
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "DisplayTablesSimplified.ui")
        loadUi(sources_ui_file, self)


        # List of all user-viewable tables in the database
        self.user_view_tables = SQLUtils.export_database_tables_viewable
        # List of tables to display as a tree structure
        self.dbtree_list = SQLUtils.user_viewable_trees
        self.dbtree_list.append('Aliquots')
        self.dbtable_list = [table for table in self.user_view_tables if table not in self.dbtree_list]

        self.sample_proxy_model = ReadableProxyModel()
        self.model = DisplayRoundedModel(db=self.database)
        self.query_model = DisplayRoundedQueryModel(db=self.database)
        self.tree_model = TreeModel(db=self.database)
        self.tree_proxy_model = ReadableProxyModel()
        self.table_proxy_model = ReadableProxyModel()
        self.table = ''
        self.show_cols = []
        self.db_stackedWidget: QtW.QStackedWidget
        # logger_setup.get_logger().info("Adding the frozen table view")
        # self.dbFrozen_tableView = FrozenTableView()
        # self.db_stackedWidget.addWidget(self.dbFrozen_tableView)
        self.switch_to_table()
        self.display_table_list()

        self.connect_signals()

    def connect_signals(self):
        # Signal for table combo box
        self.dbTable_comboBox.currentIndexChanged.connect(self.display_table)

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

        self.dbTable_tableView: QtW.QTableView
        self.dbTable_treeView: QtW.QTreeView
        self.dbTable_comboBox: QtW.QComboBox
        table = self.dbTable_comboBox.currentText()
        self.table = TxM.remove_spaces(table)
        if not self.table:
            logger_setup.get_logger().warning('No table selected to display')
            return
        logger_setup.get_logger().info(f'Displaying {self.table}')
        # If moving from a tree table, save the expanded state first
        if self.previous_table in self.dbtree_list and self.previous_table != self.table:
            save_expanded_state(self.previous_table, self.dbTable_treeView)
        self.previous_table = self.table

        if self.table in self.dbtree_list:
            logger_setup.get_logger().info(f'Switching to tree view for {self.table}')
            self.switch_to_tree()
            self.database.open()
            if get_view_from_table(self.table) != self.table:
                # This table requires a more complex query to view
                show_columns = settings.valeu(SQLUtils.view_setting_dict[get_view_from_table(self.table)])
                query_args = {'show_columns': show_columns}
                view_query = ViewQuery(self.table, False, **query_args)
                table_query = view_query.table_query
            else:
                table_query = f'SELECT * FROM {table}'
            self.model = SQLiteTableModel(table_query, self.db_file)
            if self.model.last_error:
                logger_setup.get_logger().critical(f'Error loading {self.table}')
                return

            self.tree_model = TreeModel(source_model=self.model, db=self.database)
            self.tree_proxy_model.setSourceModel(self.tree_model)

            self.dbTable_treeView: QTreeView
            self.dbTable_treeView.setModel(self.tree_proxy_model)
            self.dbTable_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
            self.dbTable_treeView.hideColumn(1)  # don't show ID column
            self.dbTable_treeView.hideColumn(2)  # don't show parent ID column
            self.dbTable_treeView.hideColumn(3)  # don't show parent row column
            # Keep the tree sorted as dictated by the database
            self.dbTable_treeView.setSortingEnabled(False)
            self.dbTable_treeView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.dbTable_treeView.expandAll()
            self.dbTable_treeView: QTreeView
        elif self.table in self.dbtable_list:
            self.switch_to_table()
            if self.table != get_view_from_table(self.table):
                # This table requires a more complex query to view
                show_columns = settings.value(SQLUtils.view_setting_dict[get_view_from_table(self.table)])
                query_args = {'show_columns': show_columns}
                view_query = ViewQuery(self.table, False, **query_args)
                table_query = view_query.table_query
            else:
                table_query = f'SELECT * FROM {table}'
            self.model = SQLiteTableModel(table_query, database=self.db_file)
            if self.model.last_error:
                logger_setup.get_logger().critical(f'Error loading {self.table}')
                return
            self.table_proxy_model.setSourceModel(self.model)

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

        search_expression = QtC.QRegularExpression(self.search_lineEdit.text())
        if self.table == 'Samples':
            self.sample_proxy_model.setFilterRegularExpression(search_expression)
        elif self.table in self.dbtree_list:
            self.tree_proxy_model.setFilterRegularExpression(search_expression)
            if search_expression != "":
                self.dbTable_treeView.expandAll()
        else:
            self.table_proxy_model.setFilterRegularExpression(search_expression)

    def closeEvent(self, event):
        if self.table in self.dbtree_list:
            save_expanded_state(self.table, self.dbTable_treeView)
        event.accept()
        super().closeEvent(event)
import re
import os
import sys
import webbrowser

import qtawesome
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6.QtCore import Qt, QTimer, QRegularExpression
from PyQt6.QtWidgets import QPushButton, QTableWidgetItem, QLineEdit

from PyQt6.uic import loadUi
from Functions.Widget_classes import (
    TreeSortFilterProxyModel, DisplayRoundedModel, DisplayRoundedQueryModel, SQLiteTableModel, save_expanded_state,
    expand_collapse, TreeContextMenu, TreeModel, ReadableProxyModel, add_tree_popup, FrozenTableView, get_name_column,
    get_headers, get_total_records, get_record_row, close_loading_dialog, show_loading_dialog, columns_as_list,
    TableToolTipModel, get_id_from_name, scroll_to_record, get_view_from_table, TrackExpandedTreeView
)
import Functions.Text_manipulations as TxM
from Functions import SQLUtils
from Functions import Savepoint_manager
from Functions.Database_manager import update_database
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.Database_views import ViewQuery
from ui.EditView import EditView
from ui.EditTable import EditTable
from ui.EditTree import EditTree
from ui.AddTags import AddTags
from ui.AddTreeTags import AddTreeTags
from ui.New_reference import NewReference
from ui.SampleInformation import SampleInformation
import logger_setup
import time


class DisplayTables(QtW.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        logger_setup.get_logger().info("Starting the display tables window")

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
        self.name_completer = QtW.QCompleter()

        # List of all user-viewable tables in the database
        self.user_view_tables = SQLUtils.user_viewable_tables
        # List of tables to display as a tree structure
        self.dbtree_list = SQLUtils.user_viewable_trees
        self.dbtable_list = [table for table in self.user_view_tables if table not in self.dbtree_list]

        self.model = DisplayRoundedModel()
        self.query_model = DisplayRoundedQueryModel()
        self.tree_model = TreeModel()
        self.tree_proxy_model = TreeSortFilterProxyModel()
        self.table_proxy_model = ReadableProxyModel()
        self.table = ''
        self.previous_table = ''
        self.name_column = None
        self.name_header = None
        self.show_cols = []
        self.timer = QTimer()
        self.db_stackedWidget: QtW.QStackedWidget
        self.switch_to_table()

        # Pagination variables
        self.show_per_page_comboBox: QtW.QComboBox
        self.show_per_page_comboBox.addItems(['10', '25', '50', '100', '250', '500', '1000'])
        self.current_page: int = 0
        self.rows_per_page: int = settings.value('show_per_page')
        self.show_per_page_comboBox.setCurrentText(str(self.rows_per_page))
        self.total_records: int = 0

        self.display_table_list()

        self.connect_signals()

    def set_go_to_completer(self):
        # Populate the value input with a completer based on the selected attribute

        sql_query = f'SELECT DISTINCT {self.name_header} FROM "{self.table}"'
        logger_setup.get_logger().debug(f'SQL command: {sql_query}')
        all_names = columns_as_list(sql_query, [self.name_header])[0]
        if not all_names:
            return
        list_model = QtC.QStringListModel(sorted(all_names, key=str.casefold))
        list_proxy_model = ReadableProxyModel()
        list_proxy_model.setSourceModel(list_model)
        self.name_completer.setModel(list_proxy_model)
        self.name_completer.setFilterMode(QtC.Qt.MatchFlag.MatchContains)
        self.name_completer.setCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.name_completer.setModelSorting(QtW.QCompleter.ModelSorting.CaseInsensitivelySortedModel)
        self.name_completer.setCompletionMode(QtW.QCompleter.CompletionMode.PopupCompletion)

        self.goto_line_edit: QLineEdit
        self.goto_line_edit.setCompleter(self.name_completer)

    def connect_signals(self):
        # Signal for table combo box
        self.dbTable_comboBox.currentIndexChanged.connect(self.display_table)
        # Signal for search bar
        self.search_lineEdit.returnPressed.connect(self.search)
        # Signal for clicked edit button
        self.edit_pushButton.clicked.connect(self.edit_popup)
        # Signal for clicked edit samples button
        self.edit_samples_pushButton.clicked.connect(lambda: self.edit_samples_popup('edit_pushButton'))
        # Context menu for table and tree views
        self.dbTable_tableView.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.dbTable_tableView.frozen_table_view.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.dbTable_tableView.customContextMenuRequested.connect(self.show_context_menu)
        self.dbTable_tableView.frozen_table_view.customContextMenuRequested.connect(self.show_context_menu)
        self.dbTable_treeView.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.dbTable_treeView.customContextMenuRequested.connect(self.show_context_menu)

        self.goto_line_edit.returnPressed.connect(self.go_to_record)
        self.prev_button.clicked.connect(self.previous_page)
        self.next_button.clicked.connect(self.next_page)
        self.show_per_page_comboBox.currentIndexChanged.connect(self.change_rows_per_page)

        self.refresh_button.setIcon(qtawesome.icon('fa6s.rotate-right', color='green', scale_factor=1.2))
        self.refresh_button.clicked.connect(self.display_table)

    def display_table(self):
        """
        Displays the selected table
        :return:
        """
        self.edit_pushButton: QPushButton
        self.dbTable_tableView: QtW.QTableView
        self.dbTable_treeView: TrackExpandedTreeView
        self.dbTable_comboBox: QtW.QComboBox
        self.add_pushButton: QtW.QPushButton
        table = self.dbTable_comboBox.currentText()
        self.table = TxM.remove_spaces(table)

        logger_setup.get_logger().info(f'Displaying {get_total_records(self.table, '')} {self.table}')
        if self.table != get_view_from_table(self.table):
            if settings.value('show_items_missing_data'):
                msg = f'Loading related data for {self.table}...\n\nSettings to speed up loading:\n- Hide items with missing data\n- Reduce the columns shown'
            else:
                msg = f'Loading related data for {self.table}...\n\nSettings to speed up loading:\n- Reduce the columns shown'
        else:
            msg = f'Displaying {get_total_records(self.table, '')} {self.table}...'
        show_loading_dialog('Loading', msg)
        start_display_time = time.time()
        # If moving from a tree table, save the expanded state first
        if self.previous_table in self.dbtree_list and self.previous_table != self.table and self.model.rowCount() > 0:
            save_expanded_state(self.previous_table, self.dbTable_treeView)
        if self.table in self.dbtree_list:
            logger_setup.get_logger().info(f'Switching to tree view for {self.table}')
            start_display_tree_time = time.time()
            self.dbTable_treeView: TrackExpandedTreeView
            self.switch_to_tree()
            self.edit_samples_pushButton.hide()
            self.model = SQLiteTableModel(f'SELECT * FROM {self.table}')
            if self.model.last_error:
                logger_setup.get_logger().critical(f'Error displaying {self.table}')
                close_loading_dialog('Loading', msg)
                self.parent().close()
            self.total_records = self.model.rowCount()
            self.tree_model = TreeModel(self.model, None)
            self.tree_proxy_model.setSourceModel(self.tree_model)
            self.tree_proxy_model.setFilterKeyColumn(-1)
            # self.edit_pushButton.clicked.connect(lambda: self.edit_popup(self.model))

            self.dbTable_treeView.setModel(self.tree_proxy_model)
            self.dbTable_treeView.setUniformRowHeights(True)
            logger_setup.get_logger().info(
                f'Populated tree view in {time.time() - start_display_tree_time:.2f} seconds')
            self.dbTable_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
            self.dbTable_treeView.hideColumn(1)  # don't show ID column
            self.dbTable_treeView.hideColumn(2)  # don't show parent ID column
            self.dbTable_treeView.hideColumn(3)  # don't show parent row column
            if isinstance(self.dbTable_treeView.model(), TreeSortFilterProxyModel):
                self.dbTable_treeView.model().update_visible_columns()
            # Keep the tree sorted as dictated by the database
            self.dbTable_treeView.setSortingEnabled(False)
            self.dbTable_treeView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.dbTable_treeView.setTextElideMode(Qt.TextElideMode.ElideNone)  # Prevent text truncation

            self.name_column = get_name_column(get_view_from_table(self.table))
            self.name_header = self.model.headerData(self.name_column, QtC.Qt.Orientation.Horizontal,
                                                     QtC.Qt.ItemDataRole.DisplayRole)
            self.set_go_to_completer()
            logger_setup.get_logger().info(f'Displaying {self.name_header}')

            # Optimize window resizing
            self.resize_timer = QTimer()
            self.resize_timer.setSingleShot(True)
            self.resize_timer.timeout.connect(self.resizeRowsOptimized)

            # Connect resizing events
            self.dbTable_treeView.header().sectionResized.connect(self.optimizeVerticalResize)

            start_column_resize_time = time.time()
            for column in range(self.tree_proxy_model.columnCount()):
                self.dbTable_treeView.resizeColumnToContents(column)
                if self.dbTable_treeView.columnWidth(column) > 400:
                    self.dbTable_treeView.setColumnWidth(column, 400)
            logger_setup.get_logger().info(f'Resized columns in {time.time() - start_column_resize_time} seconds')

            self.page_info_label.setText(f'{self.total_records} {self.table}')

            logger_setup.get_logger().info(
                f'Set up tree view for {self.table} in {time.time() - start_display_tree_time} seconds')

        elif self.table in self.dbtable_list:
            logger_setup.get_logger().info(f'Switching to table view for {self.table}')
            self.switch_to_table()
            # Reset column sorting indicator
            self.dbTable_tableView.horizontalHeader().setSortIndicator(-1, QtC.Qt.SortOrder.AscendingOrder)
            self.name_column = get_name_column(get_view_from_table(self.table))
            id_header = get_headers(self.table)[0]
            if self.table != get_view_from_table(self.table):
                # This table requires a more complex query to view
                self.show_cols = settings.value(SQLUtils.view_setting_dict[get_view_from_table(self.table)])
                self.name_header = self.show_cols[self.name_column]
                query_args = {'show_columns': self.show_cols,
                              'limit': f'LIMIT {self.rows_per_page} OFFSET {self.current_page * self.rows_per_page}',
                              'group_col': f'{id_header}', 'order_col': f'{self.name_header}'}
                view_query = ViewQuery(self.table, False, **query_args)
                table_query = view_query.table_query
            else:
                self.show_cols = '*'
                self.name_header = get_headers(self.table)[self.name_column]
                table = self.table
                table_query = f'''SELECT {self.show_cols} FROM {table} GROUP BY {id_header} ORDER BY {self.name_header} 
                                LIMIT {self.rows_per_page} OFFSET {self.current_page * self.rows_per_page}'''
            if self.table == 'Samples':
                self.edit_samples_pushButton.show()
            else:
                self.edit_samples_pushButton.hide()
            # logger_setup.get_logger().debug(f'SQL query: {table_query}')
            try:
                self.model = SQLiteTableModel(table_query, view_query=view_query)
            except NameError:
                # There is no view_query, so just use the table query
                self.model = SQLiteTableModel(table_query)
            close_loading_dialog('Loading', msg)
            if self.model.last_error is not None:
                logger_setup.get_logger().critical(f'Error displaying {self.table}')
                close_loading_dialog('Loading', msg)
                self.parent().close()
            self.dbTable_tableView.setSortingEnabled(True)
            self.model.set_table(self.table)
            self.table_proxy_model.setSourceModel(self.model)
            self.table_proxy_model.setFilterKeyColumn(-1)  # search all columns
            # Sort the table by the name column
            proxy_name_column = None
            for column in range(self.table_proxy_model.columnCount()):
                header = self.model.headerData(column, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
                if header == self.name_header:
                    proxy_name_column = column
                    break
            if proxy_name_column:
                self.table_proxy_model.sort(proxy_name_column, QtC.Qt.SortOrder.AscendingOrder)
            self.dbTable_tableView: FrozenTableView
            self.dbTable_tableView.setSelectionBehavior(QtW.QAbstractItemView.SelectionBehavior.SelectRows)
            self.dbTable_tableView.frozen_table_view.setSelectionBehavior(QtW.QAbstractItemView.SelectionBehavior.SelectRows)

            self.dbTable_tableView.setModel(self.table_proxy_model)
            self.dbTable_tableView.hideColumn(0)  # don't show ID column
            # self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.dbTable_tableView.verticalHeader().hide()

            self.name_header = self.model.headerData(self.name_column, QtC.Qt.Orientation.Horizontal,
                                                     QtC.Qt.ItemDataRole.DisplayRole)
            if table == 'References':
                try:
                    self.dbTable_tableView.doubleClicked.disconnect()
                except TypeError:
                    pass
                self.dbTable_tableView.doubleClicked.connect(self.open_doi_link)
            self.set_go_to_completer()

            # Optimize window resizing
            self.resize_timer = QTimer()
            self.resize_timer.setSingleShot(True)
            self.resize_timer.timeout.connect(self.resizeRowsOptimized)

            # Connect resizing events
            self.dbTable_tableView.horizontalHeader().sectionResized.connect(self.optimizeVerticalResize)
            self.dbTable_tableView.verticalHeader().sectionResized.connect(self.optimizeVerticalResize)

            self.total_records = get_total_records(self.table)
            if (self.current_page + 1) * self.rows_per_page > self.total_records:
                self.page_info_label.setText(
                    f'{self.current_page * self.rows_per_page + 1}-{self.total_records} of {self.total_records}')
            else:
                self.page_info_label.setText(
                    f'{self.current_page * self.rows_per_page + 1}-{(self.current_page + 1) * self.rows_per_page} of '
                    f'{self.total_records}')

            self.dbTable_tableView.resizeColumnsToContents()
            for column in range(self.table_proxy_model.columnCount()):
                if self.dbTable_tableView.columnWidth(column) > 400:
                    self.dbTable_tableView.setColumnWidth(column, 400)

        else:
            logger_setup.get_logger().error(f"Error {self.table}: Tried to switch to a table with no table or tree...")
            self.parent().close()

        self.edit_pushButton.setText(f"Edit {self.table}")
        self.goto_line_edit.clear()
        self.goto_line_edit.setPlaceholderText(f'Go to {self.name_header}...')
        self.previous_table = self.table
        self.search_lineEdit.setText("")
        self.search()
        close_loading_dialog('Loading', msg)
        logger_setup.get_logger().info(f'Displayed {self.table} in {time.time() - start_display_time} seconds')

    def edit_samples_popup(self, text=None):
        # print(f'edit_samples_popup called with {text}')
        if self.table != 'Samples':
            return
        selected_samples = []
        self.dbTable_tableView: QtW.QTableView
        # Add the sample ID for any rows that are selected
        if self.dbTable_tableView.selectedIndexes():
            selected_indexes = self.dbTable_tableView.selectedIndexes()
        else:
            logger_setup.get_logger().error("Select rows to edit")
            return
        for index in selected_indexes:
            id_index = index.siblingAtColumn(0)
            sample_id = id_index.data(QtC.Qt.ItemDataRole.DisplayRole)
            if sample_id and sample_id not in selected_samples:
                selected_samples.append(sample_id)
        show_loading_dialog('Loading', f'Opening Sample Information window...')
        dlg = SampleInformation(self, selected_samples)
        dlg.exec()
        if dlg.updated:
            if not update_database():
                logger_setup.get_logger().critical(f'Error updating and displaying database')
                self.parent().close()
            self.display_table()

    def edit_popup(self):
        show_loading_dialog('Loading', f'Opening edit window for {self.table}...')
        view_tables = ['Samples', 'Aliquots', 'Spots', 'UPbAnalyses', 'Columns', 'References']
        if self.table in view_tables:
            dlg = EditView(self, self.table)
        elif self.table in self.dbtree_list:
            if self.model.rowCount() > 0:
                save_expanded_state(self.table, self.dbTable_treeView)
            dlg = EditTree(self, self.table)
        else:
            dlg = EditTable(self, self.table)
        dlg.exec()
        if dlg.updated:
            if not update_database():
                logger_setup.get_logger().critical(f'Error updating and displaying database')
                self.parent().close()
            self.display_table()

    def add_popup(self, action: QtG.QAction | None = None):
        dlg = None
        show_loading_dialog('Loading', f'Opening add window for {self.table}...')
        if self.table in self.dbtree_list and self.model.rowCount() > 0:
            save_expanded_state(self.table, self.dbTable_treeView)
            dlg_args = add_tree_popup(self.dbTable_treeView, action)
            if dlg_args:
                dlg = AddTreeTags(self, self.table, **dlg_args)
        elif self.table in ['References', '"References"']:
            table = 'References'
            show_loading_dialog('Loading', f'Opening add window for {table}...')
            dlg = NewReference(self)
        else:
            dlg = AddTags(self, self.table)
        if not dlg:
            return
        dlg.exec()
        if dlg.updated:
            if not update_database():
                logger_setup.get_logger().critical(f'Error updating and displaying database')
                self.parent().close()
            self.display_table()

    def open_doi_link(self, item: QTableWidgetItem):
        self.dbTable_tableView: FrozenTableView
        if self.dbTable_tableView.model().headerData(item.column(), Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) == "DOI":
            text:str = item.data(Qt.ItemDataRole.DisplayRole)
            if text.startswith('doi:'):
                text = text.replace('doi:','')

            doi_regex = re.compile(r"^(10\.\d{4,9}\/[-._;()\/:A-Z0-9]+)$", re.IGNORECASE)

            if re.match(doi_regex, text):
                if 'doi.org/' not in text:
                    if 'http://' not in text and 'https://' not in text:
                        text = 'https://doi.org/' + text
                    webbrowser.open(text)
                else:
                    webbrowser.open(text)

    def show_context_menu(self, pos):
        """
        Show a context menu when right-clicking on a table or tree view
        :param pos: The position of the mouse click
        :return:
        """
        self.dbTable_tableView: QtW.QTableView
        self.dbTable_treeView: TrackExpandedTreeView
        tree_menu = TreeContextMenu()
        table_menu = QtW.QMenu()
        edit_action = table_menu.addAction('Edit')
        if self.table != 'Samples':
            add_action = table_menu.addAction('Add')
        else:
            add_action = None
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
            view_grain_action = view_data_menu.addAction('View Grains')
            view_spot_action = view_data_menu.addAction('View Spots')
            view_upb_analyses_action = view_data_menu.addAction('View U-Pb Analyses')
            view_geochem_analyses_action = view_data_menu.addAction('View GeoChemical Analyses')
            action = table_menu.exec(self.dbTable_tableView.viewport().mapToGlobal(pos))
            if action:
                # get the row that was right-clicked
                parent_ids = []
                if self.dbTable_tableView.selectedIndexes():
                    selected_indexes = self.dbTable_tableView.selectedIndexes()
                else:
                    logger_setup.get_logger().error("Select row")
                    return
                for index in selected_indexes:
                    parent_id = self.table_proxy_model.data(self.table_proxy_model.index(index.row(), 0),
                                                            QtC.Qt.ItemDataRole.DisplayRole)
                    if str(parent_id) not in parent_ids:
                        parent_ids.append(str(parent_id))

                # index = self.dbTable_tableView.indexAt(pos)
                # parent_ids = self.table_proxy_model.data(self.table_proxy_model.index(index.row(), 0), QtC.Qt.ItemDataRole.DisplayRole)
                if action == view_aliquot_action:
                    self.main_window.open_tab(parent_ids, 'Samples', 'Aliquots')
                elif action == view_grain_action:
                    self.main_window.open_tab(parent_ids, 'Samples', 'Grains')
                elif action == view_spot_action:
                    self.main_window.open_tab(parent_ids, 'Samples', 'Spots')
                elif action == view_upb_analyses_action:
                    self.main_window.open_tab(parent_ids, 'Samples', 'UPbAnalyses')
                elif action == view_geochem_analyses_action:
                    self.main_window.open_tab(parent_ids, 'Samples', 'GeoChemicalAnalyses')
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

    def cancel_dlg(self, dlg):
        dlg = None
        self.display_table()

    def optimizeVerticalResize(self, logical_index, old_size, new_size):
        """Trigger a delayed row height update when the user resizes the window vertically."""
        self.resize_timer.start(100)  # Add a slight delay to avoid excessive updates

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

        search_expression = QtC.QRegularExpression(self.search_lineEdit.text(),
                                                   options=QRegularExpression.PatternOption.CaseInsensitiveOption)
        if self.table in self.dbtree_list:
            self.tree_proxy_model.setRecursiveFilteringEnabled(True)
            self.tree_proxy_model.setFilterRegularExpression(search_expression)
            if self.search_lineEdit.text() != "":
                self.dbTable_treeView.expandAll()
        else:
            self.table_proxy_model.setFilterRegularExpression(search_expression)

    def display_table_list(self):
        """
        Populates the tables combo box with the editable tables
        Displays the default table
        :return:
        """
        self.dbTable_comboBox: QtW.QComboBox
        self.dbTable_comboBox.setModel(TableToolTipModel())
        self.dbTable_comboBox.addItems(self.user_view_tables)
        self.previous_table = ''
        self.dbTable_comboBox.setCurrentText('Samples')
        self.display_table()

    def change_rows_per_page(self):
        """
        Slot to change the number of rows displayed per page
        """
        self.rows_per_page = int(self.show_per_page_comboBox.currentText())
        self.current_page = 0
        self.display_table()

    def next_page(self):
        """
        Slot to move to the next page for the displayed table
        """
        if (self.current_page + 1) * self.rows_per_page < self.total_records:
            self.current_page += 1
            self.display_table()

    def previous_page(self):
        """
        Slot to move to the previous page for the displayed table
        """
        if self.current_page > 0:
            self.current_page -= 1
            self.display_table()

    def go_to_record(self):
        """
        Slot to go to a specific record display name for the displayed table.
        """
        try:
            record_name = self.goto_line_edit.text()
            self.goto_line_edit.setText('')
            if record_name == "":
                return
            record_id = get_id_from_name(self.table, record_name)
            if not record_id:
                logger_setup.get_logger().error(f'Could not find record ID for record name: {record_name}')
                return
            row = get_record_row(self.table, record_id)

            if row != -1:
                new_page = row // self.rows_per_page
                if self.current_page != new_page:
                    self.current_page = new_page
                    self.display_table()
                if self.table in self.dbtable_list:
                    scroll_to_record(record_id, self.dbTable_tableView)
                elif self.table in self.dbtree_list:
                    scroll_to_record(record_id, self.dbTable_treeView)
            else:
                logger_setup.get_logger().critical(f"Record {self.name_header} not found: {record_name}")
        except Exception as e:
            logger_setup.get_logger().critical(f"Invalid Record {self.name_header}: {record_name}")
            logger_setup.get_logger().debug(f'Error: {e}')

        self.goto_line_edit.setText('')

    def switch_to_table(self):
        """
        Sets the current widget to a table view
        :return:
        """
        self.db_stackedWidget: QtW.QStackedWidget
        self.db_stackedWidget.setCurrentWidget(self.db_table)
        self.prev_button: QtW.QPushButton
        self.next_button: QtW.QPushButton
        self.page_info_label: QtW.QLabel
        self.show_per_page_comboBox: QtW.QComboBox
        self.prev_button.show()
        self.next_button.show()
        # self.page_info_label.show()
        self.show_per_page_comboBox.show()
        self.show_per_page_label.show()
        self.goto_line_edit.show()

    def switch_to_tree(self):
        """
        Sets the current widget to a tree view
        :return:
        """
        self.db_stackedWidget: QtW.QStackedWidget
        self.db_stackedWidget.setCurrentWidget(self.db_tree)
        self.prev_button: QtW.QPushButton
        self.next_button: QtW.QPushButton
        self.page_info_label: QtW.QLabel
        self.show_per_page_comboBox: QtW.QComboBox
        self.prev_button.hide()
        self.next_button.hide()
        # self.page_info_label.hide()
        self.show_per_page_comboBox.hide()
        self.show_per_page_label.hide()
        self.goto_line_edit.hide()

    def cancel_display(self, title, message):
        close_loading_dialog(title, message)
        self.dbTable_comboBox.setCurrentText(self.previous_table)
        self.display_table()

    def closeEvent(self, event):
        if self.table in self.dbtree_list and self.model.rowCount() > 0:
            save_expanded_state(self.table, self.dbTable_treeView)
        event.accept()
        super().closeEvent(event)

import os
import re
import sys
import time
import webbrowser

from PyQt6 import QtCore as QtC, QtWidgets, QtGui, QtCore
from PyQt6 import QtSql as QtS
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import QPoint, QSize, QTimer, Qt, QRegularExpression, QAbstractItemModel, QModelIndex
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtWidgets import QWidget, QTableView, QTreeView, QComboBox, QPushButton, QMessageBox, \
    QCompleter, QLineEdit, QStackedWidget, QTableWidgetItem
from PyQt6.uic import loadUi

import Functions.Text_manipulations as TxM
import logger_setup
from Functions.Database_manager import update_database
from Functions import SQLUtils
from Functions.SQLUtils import user_viewable_tables
from Functions.Widget_classes import SQLiteTableModel, TreeSortFilterProxyModel, save_expanded_state, TreeModel, \
    WordWrapDelegate, get_name_column, ReadableProxyModel, get_id_from_name, get_record_index, column_as_list, \
    get_view_name_column
from Functions.Widget_classes import get_headers
from ui.SampleInformation import SampleInformation
from Functions.Settings_manager import settings
from Functions.LoadingDialog_manager import LoadingDialogManager
from ui.EditTable import EditTable
from ui.EditTree import EditTree
from ui.EditView import EditView
from ui.EditTreeView import EditTreeView


class DataViewerWidget(QWidget):
    def __init__(self, query_builder, ids_to_show: set, table_type):
        start_time = time.time()
        super().__init__(parent=None)
        self.query_builder = query_builder

        self.loading_manager = LoadingDialogManager.get_instance()

        self.data_table = table_type
        self.data_filtered_table = 'RockTypes' # default to rocktypes

        self.current_selection = []

        self.data_ids_to_show = ids_to_show
        self.data_filtered_ids_to_show = set()

        self.data_table_model = None
        self.data_filtered_table_model = None

        self.data_table_proxy_model = ReadableProxyModel()
        self.data_filtered_table_proxy_model = ReadableProxyModel()

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "DataViewerWidget.ui")
        loadUi(sources_ui_file, self)

        self.loadWindowState()

        # Remove Samples from user-viewable tables
        items = SQLUtils.user_viewable_tables.copy()
        items.remove('Samples')
        self.dbTable_comboBox_2.addItems(items)
        self.dbTable_comboBox_2.setCurrentText(self.data_filtered_table)

        self.dbTable_comboBox.addItems(['Samples', 'Aliquots', 'Spots', 'UPbAnalyses'])
        self.dbTable_comboBox.setCurrentText(self.data_table)

        self.dbTable_comboBox.currentTextChanged.connect(self.data_table_switcher)

        # Display filtered table for the first time
        self.dbTable_comboBox_2.currentTextChanged.connect(self.display_table_with_data_filter)

        self.dbTable_tableView_2.doubleClicked.connect(self.open_doi_link)
        # Pagination variables
        # todo add rows_per_page combobox and signals to connect to settings values
        # self.show_per_page_comboBox.addItems(['10', '25', '50', '100', '250', '500', '1000'])
        # self.rows_per_page: int = settings.value('show_per_page')
        # self.show_per_page_comboBox.setCurrentText(str(self.rows_per_page))
        self.current_page_1 = 0
        self.rows_per_page_1 = 2000
        self.total_records_1 = self.get_total_records_1()

        self.current_page_2 = 0
        self.rows_per_page_2 = 2000
        self.total_records_2 = self.get_total_records_2(self.dbTable_comboBox_2)

        self.goto_line_edit.returnPressed.connect(self.go_to_record_1)
        self.goto_line_edit_2.returnPressed.connect(self.go_to_record_2)

        self.prev_button.clicked.connect(self.previous_page_1)
        self.next_button.clicked.connect(self.next_page_1)

        self.prev_button_2.clicked.connect(self.previous_page_2)
        self.next_button_2.clicked.connect(self.next_page_2)

        self.edit_pushButton.clicked.connect(
            lambda: self.edit_popup(self.dbTable_tableView, self.dbTable_treeView, self.data_table_proxy_model,
                                    self.dbTable_comboBox))

        self.search_lineEdit.returnPressed.connect(lambda: self.search(self.search_lineEdit, self.data_table_proxy_model))

        self.selectionTimer = QTimer()
        self.selectionTimer.setSingleShot(True)
        self.selectionTimer.timeout.connect(self.display_table_with_data_filter)
        self.display_data_table()

        self.show()
        end_time = time.time()
        logger_setup.get_logger().info(f'Displayed filtered view in {end_time - start_time} seconds')

    # creates ids_to_show string in format (id1, id2, id3, ...)
    # ids_to_show is a filtered list of ids to show in the table
    # can be either from Samples, Aliquots, Spots, or UPbData
    @property
    def sql_data_ids_to_show(self) -> str:
        if not self.data_ids_to_show:
            return '()'
        elif len(self.data_ids_to_show) == 1:
            return f'= {str(list(self.data_ids_to_show)[0])}'
        else:
            return f'IN ({", ".join([str(i) for i in self.data_ids_to_show])})'

    @property
    def sql_data_filtered_ids_to_show(self) -> str:
        if not self.data_filtered_ids_to_show:
            return 'IN ()'
        elif len(self.data_filtered_ids_to_show) == 1:
            return f'= {str(list(self.data_filtered_ids_to_show)[0])}'
        else:
            return f'IN ({", ".join([str(i) for i in self.data_filtered_ids_to_show])})'

    def data_table_switcher(self):
        new_table = self.dbTable_comboBox.currentText()
        filtered_ids = self.query_builder.get_filtered_ids(new_table)
        if filtered_ids is None:
            logger_setup.get_logger().critical(
                f'No matching Spots for given filter(s)')
            self.dbTable_comboBox.setText(self.data_table)
            return
        else:
            if len(set(filtered_ids)) > 1000:
                if not self.view_many_results(len(set(filtered_ids))):
                    return
            self.setWindowTitle(f'Filtered {self.data_table} View')
            self.data_table = new_table
            self.data_ids_to_show = set(filtered_ids)
            self.display_data_table()

    def view_many_results(self, number: int) -> bool:
        """
        Prompts the user if they want to view many results. If they do, it returns True, otherwise False.
        :param number: number of filtered ids
        :return: bool
        """
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle('Many results')
        msg.setText(f'Would you like to view {number} results? This may take a while to load.')
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        reply = msg.exec()
        if reply == QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

    def display_data_table(self):
        """
        Displays the sample table
        :return:
        """
        if not self.data_table:
            logger_setup.get_logger().info(f'No table selected to display')
            return

        self.loading_manager.show_loading_dialog('Loading', f'Displaying {self.data_table}...')
        self.data_table_model = None
        self.data_table_proxy_model = None

        if self.data_table != 'Aliquots':
            self.switch_to_table(self.db_stackedWidget)
            self.total_records_1 = self.get_total_records_1()
            offset = self.current_page_1 * self.rows_per_page_1

            match self.data_table:
                case 'Samples':
                    table = 'SampleView'
                    show_cols = ', '.join(settings.value('sample_view_columns'))
                    self.data_table_model = SQLiteTableModel(
                        f'SELECT {show_cols} FROM {table} WHERE SampleID {self.sql_data_ids_to_show} ORDER BY SampleName LIMIT {self.rows_per_page_1} OFFSET {offset}')
                case 'Spots':
                    table = 'SpotView'
                    show_cols = ', '.join(settings.value('spot_view_columns'))
                    self.data_table_model = SQLiteTableModel(
                        f'SELECT {show_cols} FROM {table} WHERE SpotID {self.sql_data_ids_to_show} ORDER BY SampleName LIMIT {self.rows_per_page_1} OFFSET {offset}')
                case 'UPbAnalyses':
                    table = 'UPbView'
                    show_cols = ', '.join(settings.value('upb_analysis_view_columns'))
                    self.data_table_model = SQLiteTableModel(
                        f'SELECT {show_cols} FROM {table} WHERE UPbAnalysisID {self.sql_data_ids_to_show} ORDER BY SampleName LIMIT {self.rows_per_page_1} OFFSET {offset}')
                case _:
                    logger_setup.get_logger().critical(
                        f"Error {self.data_table}: Tried to switch to a table with no table or tree...")
                    return

            name_column = get_view_name_column(table)
            if name_column is not None:
                name_header = self.data_table_model.headerData(get_view_name_column(table), QtC.Qt.Orientation.Horizontal,
                                           QtC.Qt.ItemDataRole.DisplayRole)
                self.set_go_to_completer(self.goto_line_edit, name_header, table)

            self.data_table_proxy_model = ReadableProxyModel()
            self.data_table_proxy_model.setSourceModel(self.data_table_model)
            self.data_table_proxy_model.setFilterKeyColumn(-1)  # search all columns

            self.dbTable_tableView.setModel(self.data_table_proxy_model)
            self.dbTable_tableView.setSortingEnabled(True)
            self.dbTable_tableView.setWordWrap(True)
            self.dbTable_tableView.setTextElideMode(Qt.TextElideMode.ElideNone)  # Prevent text truncation
            self.dbTable_tableView.setItemDelegate(WordWrapDelegate(self.dbTable_tableView))
            self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.dbTable_tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
            self.dbTable_tableView.verticalHeader().hide()

            self.hide_columns(self.dbTable_tableView, table)

            self.dbTable_tableView.resizeColumnsToContents()
            for column in range(self.data_table_proxy_model.columnCount()):
                if self.dbTable_tableView.columnWidth(column) > 400:
                    self.dbTable_tableView.setColumnWidth(column, 400)

            # Update page info label
            start_record = offset + 1
            end_record = min(offset + self.rows_per_page_1, self.total_records_1)
            self.page_info_label.setText(
                f"Showing records {start_record} - {end_record} of {self.total_records_1}")

            self.dbTable_tableView.setSizeAdjustPolicy(
                QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
            if get_view_name_column(table) is not None:
                self.data_table_proxy_model.sort(get_view_name_column(table), QtC.Qt.SortOrder.AscendingOrder)

        elif self.data_table == 'Aliquots':
            if self.data_table not in SQLUtils.user_viewable_trees:
                logger_setup.get_logger().critical(f"Error {self.data_table}: Tried to display a table as a tree...")
                return
            if self.data_table == 'Aliquots':
                table = 'AliquotView'
                self.switch_to_tree(self.db_stackedWidget)
                show_cols = ', '.join(settings.value('aliquot_view_columns'))
                model = SQLiteTableModel(
                    f'SELECT {show_cols} FROM {table} WHERE AliquotID {self.sql_data_ids_to_show} ORDER BY SampleName')
            else:
                logger_setup.get_logger().info(f"Passed a tree that is not Aliquots")
                return

            self.data_table_model = TreeModel(model, self)

            # proxy_model = ReadableProxyModel()
            # proxy_model.setSourceModel(self.data_table_model)
            self.data_table_proxy_model = TreeSortFilterProxyModel(view=self.dbTable_treeView)
            self.data_table_proxy_model.setSourceModel(self.data_table_model)
            # self.data_table_proxy_model.sort(5, QtC.Qt.SortOrder.AscendingOrder)
            self.dbTable_treeView.setModel(self.data_table_proxy_model)
            self.dbTable_treeView.expandAll()

            self.dbTable_treeView.setSortingEnabled(False)
            self.dbTable_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
            self.dbTable_treeView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.hide_columns(self.dbTable_treeView, table)
            for column in range(self.data_table_proxy_model.columnCount()):
                self.dbTable_treeView.resizeColumnToContents(column)
        else:
            logger_setup.get_logger().critical(
                f"Error {self.data_table}: Tried to switch to a table with no table or tree...")

        self.edit_pushButton.setText(f"Edit {self.data_table}")

        if self.data_table == 'Aliquots':
            self.dbTable_treeView.selectionModel().selectionChanged.connect(self.on_select_changed)
        else:
            self.dbTable_tableView.selectionModel().selectionChanged.connect(self.on_select_changed)

        self.loading_manager.close_loading_dialog('Loading', f'Displaying {self.data_table}...')

    def on_select_changed(self):
        """
        This method is called whenever the selection changes.
        It restarts the timer to batch rapid selection changes.
        """
        # Restart the timer every time the selection changes
        self.selectionTimer.start(250)  # Delay in milliseconds

    def display_table_with_data_filter(self):
        """
        Displays the selected table
        :return:
        """
        if self.data_table == 'Aliquots':
            data_filter = self.dbTable_treeView
        else:
            data_filter = self.dbTable_tableView

        if ((self.current_selection == data_filter.selectionModel().selectedIndexes()) and
            (not data_filter.selectionModel().hasSelection())):
            return
        elif not data_filter.selectionModel().hasSelection():
            return
        else:
            self.current_selection = data_filter.selectionModel().selectedIndexes()
        self.data_filtered_table_model = None
        self.data_filtered_table_proxy_model = None

        self.edit_pushButton_2.setText(f"Edit {self.dbTable_comboBox_2.currentText()}")
        self.data_filtered_table = TxM.remove_spaces(self.dbTable_comboBox_2.currentText())
        if self.data_filtered_table == 'Ages':
            self.edit_pushButton_2.hide()
        else:
            self.edit_pushButton_2.show()
        show_cols = ['*']
        if self.data_filtered_table == "References":
            self.data_filtered_table = 'ReferenceView'
            show_cols = settings.value('reference_view_columns')
        elif self.data_filtered_table == 'Columns':
            self.data_filtered_table = 'ColumnView'
            show_cols = settings.value('column_view_columns')

        selected_data_filter_ids = set()

        self.current_selection = data_filter.selectionModel().selectedIndexes()
        if self.data_table == 'Aliquots':
            id_column = 1
        else:
            id_column = 0

        proxy = self.data_table_proxy_model  # proxy on the view
        source = self.data_table_model  # underlying model

        sel_model = data_filter.selectionModel()

        # We already know the column the IDs live in → ask the selection model for
        # exactly those indexes. Works for both QTableView and QTreeView.
        for proxy_row_idx in sel_model.selectedRows():  # works for table + tree
            if hasattr(proxy_row_idx, "siblingAtColumn"):  # PyQt ≥ 6.5
                proxy_id_idx = proxy_row_idx.siblingAtColumn(id_column)
            else:  # PyQt ≤ 6.4
                proxy_id_idx = proxy.index(
                    proxy_row_idx.row(), id_column, proxy_row_idx.parent()
                )
            if not proxy_id_idx.isValid():
                continue

            source_idx: QModelIndex = proxy.mapToSource(proxy_id_idx)

            # read the value from the source model (DisplayRole = user‑visible text)
            value = source.data(source_idx, Qt.ItemDataRole.DisplayRole)
            if value is not None:
                selected_data_filter_ids.add(str(value))

        # `selected_data_filter_ids` now contains ONLY the IDs the user selected

        if self.data_filtered_table in SQLUtils.as_table_dict.values():
            for key, value in SQLUtils.as_table_dict.items():
                if value == self.data_filtered_table:
                    as_table = key
                    break
        else:
            as_table = self.data_filtered_table

        table_condition = ''
        if self.data_filtered_table == 'ReferenceView':
            sql_table = 'UPbReferenceView'
        elif self.data_filtered_table == 'RejectionReasons':
            sql_table = 'UPbRejectionReasons'
        else:
            sql_table = as_table

        sql_columns = ', '.join(f'{sql_table}.{column}' for column in show_cols)
        sql = f'SELECT DISTINCT {sql_columns} FROM Samples '
        sql += SQLUtils.get_join_from_table("", [sql_table] + [self.data_table])
        if selected_data_filter_ids:
            if len(selected_data_filter_ids) > 1:
                sql_selected_data_filter_ids = f'IN ({", ".join([str(i) for i in selected_data_filter_ids])})'
            else:
                sql_selected_data_filter_ids = f'= {str(list(selected_data_filter_ids)[0])}'
            match self.data_table:
                case 'Samples':
                    table_condition = f"WHERE Samples.SampleID {sql_selected_data_filter_ids}"
                case 'Aliquots':
                    table_condition = f"WHERE Aliquots.AliquotID {sql_selected_data_filter_ids}"
                case 'Spots':
                    table_condition = f"WHERE Spots.SpotID {sql_selected_data_filter_ids}"
                case 'UPbAnalyses':
                    table_condition = f"WHERE UPbAnalyses.UPbAnalysisID {sql_selected_data_filter_ids}"
        else:
            return

        sql += table_condition
        logger_setup.get_logger().debug(f'Distinct Filtered Selection SQL Command: {sql}')

        query = QSqlQuery()
        # Execute the query
        logger_setup.get_logger().info(
            f'Displaying table with selection-based filter')
        if query.exec(sql):
            self.data_filtered_ids_to_show = set()
            while query.next():  # Iterate through all results
                row_id = query.value(0)
                if row_id is not None and row_id != '':
                    self.data_filtered_ids_to_show.add(str(row_id))
        else:
            logger_setup.get_logger().critical(
                f'Error in displaying table with selection-based filter')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL command: {sql}')

        # Update the id_condition attribute

        try:
            self.search_lineEdit_2.editingFinsihed.disconnect()
        except:
            pass
        try:
            self.edit_pushButton_2.clicked.disconnect()
        except:
            pass

        sql_columns = ', '.join(f'{self.data_filtered_table}.{column}' for column in show_cols)
        if self.data_filtered_table in SQLUtils.user_viewable_trees:
            self.switch_to_tree_2(self.db_stackedWidget_2)
            id_col_name = get_headers(self.data_filtered_table)[0]
            where_sql = f"""{id_col_name} IN (WITH RECURSIVE ParentTree AS
                                        (SELECT {', '.join(show_cols)} FROM {self.data_filtered_table}
                                        WHERE {id_col_name} {self.sql_data_filtered_ids_to_show}
                                        UNION ALL
                                        SELECT {sql_columns} FROM {self.data_filtered_table}
                                        INNER JOIN ParentTree ON {self.data_filtered_table}.{id_col_name} = ParentTree.Parent{id_col_name})
                                        SELECT {id_col_name} FROM ParentTree)"""
            sql_query = f"""SELECT {sql_columns} FROM {self.data_filtered_table} WHERE {where_sql}"""
            source_model = SQLiteTableModel(sql_query)

            logger_setup.get_logger().debug(f'SQL command: {sql_query}')

            self.data_filtered_table_model = TreeModel(source_model, self)

            self.data_filtered_table_proxy_model = ReadableProxyModel()
            self.data_filtered_table_proxy_model.setSourceModel(self.data_filtered_table_model)
            tree_proxy_model = TreeSortFilterProxyModel(view=self.dbTable_treeView_2)
            tree_proxy_model.setSourceModel(self.data_filtered_table_proxy_model)
            self.dbTable_treeView_2.setModel(tree_proxy_model)
            self.dbTable_treeView_2.expandAll()

            self.dbTable_treeView_2.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
            self.dbTable_treeView_2.hideColumn(1)  # don't show ID column
            self.dbTable_treeView_2.hideColumn(2)  # don't show parent ID column
            self.dbTable_treeView_2.hideColumn(3)  # don't show parent row column
            # self.dbTable_treeView_2.hideColumn(4)  # don't show sample ID column
            self.dbTable_treeView_2.setSortingEnabled(False)

            self.search_lineEdit_2.returnPressed.connect(
                lambda: self.search(self.search_lineEdit_2, tree_proxy_model, self.dbTable_treeView_2))

            self.edit_pushButton_2.clicked.connect(
                lambda: self.edit_popup(self.dbTable_tableView_2, self.dbTable_treeView_2, tree_proxy_model,
                                        self.dbTable_comboBox_2))

        elif self.data_filtered_table in SQLUtils.user_viewable_tables or 'View' in self.data_filtered_table:
            self.switch_to_table_2(self.db_stackedWidget_2)
            offset = self.current_page_2 * self.rows_per_page_2

            sql_query = f"""SELECT * FROM {self.data_filtered_table} WHERE 
                                    {get_headers(self.data_filtered_table)[0]} {self.sql_data_filtered_ids_to_show}
                                    ORDER BY {get_headers(self.data_filtered_table)[0]} LIMIT {self.rows_per_page_2} OFFSET {offset}"""

            logger_setup.get_logger().debug(f'SQL query: {sql_query}')
            self.data_filtered_table_model = SQLiteTableModel(sql_query)

            self.data_filtered_table_proxy_model = ReadableProxyModel()
            self.data_filtered_table_proxy_model.setSourceModel(self.data_filtered_table_model)

            if self.data_table == 'Samples':
                table = 'SampleView'
            elif self.data_table == 'Spots':
                table = 'SpotView'
            elif self.data_table == 'UPbAnalyses':
                table = 'UPbView'
            else:
                table = self.data_table

            self.data_filtered_table_proxy_model.setFilterKeyColumn(-1)  # search all columns
            self.dbTable_tableView_2.setModel(self.data_filtered_table_proxy_model)
            self.dbTable_tableView_2.hideColumn(0)  # don't show ID column
            self.dbTable_tableView_2.verticalHeader().setVisible(False)
            self.dbTable_tableView_2.resizeColumnsToContents()
            self.dbTable_tableView_2.setSortingEnabled(True)
            self.dbTable_tableView_2.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.data_filtered_table_proxy_model.sort(get_view_name_column(table), QtC.Qt.SortOrder.AscendingOrder)

            self.search_lineEdit_2.returnPressed.connect(
                lambda: self.search(self.search_lineEdit_2, self.data_filtered_table_proxy_model))
            self.edit_pushButton_2.clicked.connect(
                lambda: self.edit_popup(self.dbTable_tableView_2, self.dbTable_treeView_2, self.data_filtered_table_proxy_model,
                                        self.dbTable_comboBox_2))

            logger_setup.get_logger().info('Sucessfully displayed table with selection-based filter')
        else:
            logger_setup.get_logger().critical(
                f"Error {self.data_filtered_table}: Tried to switch to a table with no table or tree..Don't know how it got here")

    def edit_popup(self, dbTable_tableView, dbTable_treeView, tree_proxy_model, dbTable_comboBox):
        dbTable_comboBox: QComboBox
        table_name = dbTable_comboBox.currentText()
        table = TxM.remove_spaces(table_name)
        view_tables = ['Samples', 'Aliquots', 'Spots', 'UPbAnalyses', 'Columns', 'References']
        if table_name in view_tables:
            ids = self.data_ids_to_show
            if table_name == 'Aliquots':
                # Ask the user which sample they want to edit
                sample_names = []
                query = QSqlQuery()
                for aliquot_id in self.data_ids_to_show:
                    if not query.exec(f'SELECT SampleID FROM Aliquots WHERE AliquotID = {aliquot_id}'):
                        logger_setup.get_logger().critical(f'Error fetching SampleID')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        return
                    if query.next():
                        sample_id = query.value(0)
                        if not query.exec(f'SELECT SampleName FROM Samples WHERE SampleID = {sample_id}'):
                            logger_setup.get_logger().critical(f'Error fetching SampleName')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                            return
                        if query.next():
                            sample_name = query.value(0)
                            if sample_name not in sample_names:
                                sample_names.append(sample_name)
                sample_name, ok = QtW.QInputDialog.getItem(self, "Select Sample",
                                                           "Edit aliquots of selected sample:", sample_names, 0, False)
                if not ok:
                    logger_setup.get_logger().info(f'User cancelled sample selection')
                    return
                if not query.exec(f'SELECT SampleID FROM Samples WHERE SampleName = "{sample_name}"'):
                    logger_setup.get_logger().critical(f'Error fetching SampleID')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    return
                if not query.next():
                    logger_setup.get_logger().critical(f'No SampleID found for the selected sample')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    return
                sample_id = query.value(0)
                if not query.exec(f'SELECT AliquotID FROM Aliquots WHERE SampleID = {sample_id}'):
                    logger_setup.get_logger().critical(f'Error fetching AliquotID')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    return
                ids = []
                while query.next():
                    if query.value(0) in self.data_ids_to_show:
                        ids.append(query.value(0))
                if not ids:
                    logger_setup.get_logger().critical(f'No AliquotIDs found for the selected sample')
                    return
                dlg_args = {'parent_id': sample_id, 'parent_type': 'Sample', 'table_item_ids': ids}
                dlg = EditTreeView(self, table, **dlg_args)
            else:
                dlg_args = {'table_item_ids': ids}
                dlg = EditView(self, table, **dlg_args)
        elif table in SQLUtils.user_viewable_trees:
            save_expanded_state(table_name, tree_proxy_model, dbTable_treeView)
            self.loading_manager.show_loading_dialog('Loading', f'Opening edit window for {table}...')
            dlg = EditTree(self, table)
        else:
            self.loading_manager.show_loading_dialog('Loading', f'Opening edit window for {table}...')
            dlg = EditTable(self, table)
        dlg.exec()
        if dlg.updated:
            if not update_database():
                logger_setup.get_logger().critical(f'Error updating and displaying the database')
                self.close()

            self.display_data_table()

            self.edit_pushButton: QPushButton
            self.edit_pushButton.clearMask()

    def edit_samples_popup(self, table_name):
        if table_name != 'Samples':
            return
        selected_samples = []

        # Add the sample ID for any rows that are selected
        selected_indexes = self.dbTable_tableView.selectedIndexes()
        for index in selected_indexes:
            id_index = index.siblingAtColumn(0)
            selected_samples.append(id_index.data(QtC.Qt.ItemDataRole.DisplayRole))
        dlg = SampleInformation(self, selected_samples)
        dlg.exec()
        if not update_database():
            logger_setup.get_logger().critical(f'Error updating and displaying the database')
            self.close()

    def open_doi_link(self, item: QTableWidgetItem):
        if self.dbTable_tableView_2.model().headerData(item.column(), Qt.Orientation.Horizontal,
                                                     Qt.ItemDataRole.DisplayRole) == "DOI":
            text: str = item.data(Qt.ItemDataRole.DisplayRole)
            if text.startswith('doi:'):
                text = text.replace('doi:', '')

            doi_regex = re.compile(r"^(10\.\d{4,9}\/[-._;()\/:A-Z0-9]+)$", re.IGNORECASE)

            if re.match(doi_regex, text):
                if 'doi.org/' not in text:
                    if 'http://' not in text and 'https://' not in text:
                        text = 'https://doi.org/' + text
                    webbrowser.open(text)
                else:
                    webbrowser.open(text)

    def set_go_to_completer(self, lineedit: QLineEdit, name_header, table):
        # Populate the value input with a completer based on the selected attribute
        name_completer = QCompleter(parent=lineedit)
        query = QSqlQuery()
        match self.data_table:
            case 'Samples':
                sql_query = f'SELECT DISTINCT {name_header} FROM SampleView WHERE SampleID {self.sql_data_ids_to_show}'
            case 'Spots':
                sql_query = f'SELECT DISTINCT {name_header} FROM SpotView WHERE SpotID {self.sql_data_ids_to_show}'
            case 'UPbAnalyses':
                sql_query = f'SELECT DISTINCT {name_header} FROM UPbView WHERE UPbAnalysisID {self.sql_data_ids_to_show}'
            case '"References"':
                sql_query = f'SELECT DISTINCT {name_header} FROM ReferenceView WHERE ReferenceID {self.sql_data_ids_to_show}'
            case 'Columns':
                sql_query = f'SELECT DISTINCT {name_header} FROM ColumnView WHERE ColumnID {self.sql_data_ids_to_show}'
            case _:
                sql_query = f'SELECT DISTINCT {name_header} FROM "{table}" WHERE {get_headers(table)[0]} {self.sql_data_ids_to_show}'

        logger_setup.get_logger().debug(f'SQL command: {sql_query}')
        all_names = column_as_list(sql_query, name_header)
        if not all_names:
            return
        values = set(all_names)
        name_completer.setModel(QtC.QStringListModel(values))
        name_completer.setFilterMode(QtC.Qt.MatchFlag.MatchContains)
        name_completer.setCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        name_completer.setCompletionMode(QtW.QCompleter.CompletionMode.PopupCompletion)

        lineedit.setCompleter(name_completer)

    def hide_columns(self, db_view, table):
        hidden_columns = []
        match table:
            case 'SampleView':
                hidden_columns = [0]  # don't show SampleID column
            case 'AliquotView':
                hidden_columns = [1, 2, 3, 4]  # don't show AliquotID, ParentAliquotID, AliquotParentRow, SampleID
            case 'SpotView':
                hidden_columns = [0, 1, 2]  # don't show SpotID, SampleID, AliquotID
            case 'UPbView':
                hidden_columns = [0, 1, 2, 3]  # don't show UPbAnalysisID, SampleID, AliquotID, SpotID
        for column in range(db_view.model().columnCount()):
            if column in hidden_columns:
                db_view.hideColumn(column)
            else:
                db_view.showColumn(column)

    def search(self, search_lineEdit, proxy_model, dbTable_treeView=None):
        """
        Search the current table for the text in the search box
        Check if the case-sensitive box is checked or not
        :return:
        """
        search_lineEdit: QtW.QLineEdit
        search_expression = QtC.QRegularExpression(search_lineEdit.text(),
                                                   options=QRegularExpression.PatternOption.CaseInsensitiveOption)
        proxy_model.setFilterRegularExpression(search_expression)
        if dbTable_treeView is not None:
            dbTable_treeView.expandAll()

    def next_page_1(self):
        """
        Slot to move to the next page for the sample table
        """
        if (self.current_page_1 + 1) * self.rows_per_page_1 < self.total_records_1:
            self.current_page_1 += 1
            self.display_data_table()

    def previous_page_1(self):
        """
        Slot to move to the previous page for the sample table
        """
        if self.current_page_1 > 0:
            self.current_page_1 -= 1
            self.display_data_table()

    def next_page_2(self):
        """
        Slot to move to the next page for the filtered table
        """
        if (self.current_page_2 + 1) * self.rows_per_page_2 < self.total_records_2:
            self.current_page_2 += 1
            self.display_table_with_data_filter()

    def previous_page_2(self):
        """
        Slot to move to the previous page for the filtered table
        """
        if self.current_page_2 > 0:
            self.current_page_2 -= 1
            self.display_table_with_data_filter()

    def go_to_record_1(self):
        """
        Slot to go to a specific record ID for the sample table.
        """
        try:
            record_name = self.goto_line_edit.text()
            if record_name == "":
                return
            record_id = get_id_from_name(self.dbTable_comboBox.currentText(), record_name)
            if not record_id:
                logger_setup.get_logger().error(f'Could not find record ID for record name: {record_name}')
                return
            index = get_record_index(self.dbTable_comboBox.currentText(), record_id)

            if index != -1:
                new_page = index // self.rows_per_page_1
                if self.current_page_1 == new_page:
                    QMessageBox.information(self, 'Record Found', 'Record already displayed')
                else:
                    self.current_page_1 = new_page
                    self.display_data_table()
                self.goto_line_edit.setText('')

            else:
                logger_setup.get_logger().critical(f"Record {self.name_header} not found: {self.goto_line_edit.text()}")
        except Exception as e:
            logger_setup.get_logger().critical(f"Invalid Record {self.name_header}: {self.goto_line_edit.text()}")
            logger_setup.get_logger().debug(f'Error: {e}')

    def go_to_record_2(self):
        """
        Slot to go to a specific record ID for the filter table
        """
        try:
            record_name = self.goto_line_edit_2.text()
            if record_name == "":
                return
            record_id = get_id_from_name(self.dbTable_comboBox_2.currentText(), record_name)
            if not record_id:
                logger_setup.get_logger().error(f'Could not find record ID for record name: {record_name}')
                return
            index = get_record_index(self.dbTable_comboBox_2.currentText(), record_id)

            if index != -1:
                new_page = index // self.rows_per_page_2
                if self.current_page_2 == new_page:
                    QMessageBox.information(self, 'Record Found', 'Record already displayed')
                else:
                    self.current_page_2 = new_page
                    self.display_table_with_data_filter()
                self.goto_line_edit_2.setText('')

            else:
                logger_setup.get_logger().critical(f"Record {self.name_header} not found: {self.goto_line_edit.text()}")
        except Exception as e:
            logger_setup.get_logger().critical(f"Invalid Record {self.name_header}: {self.goto_line_edit.text()}")
            logger_setup.get_logger().debug(f'Error: {e}')

    def get_total_records_1(self) -> int:
        """
        Get the total number of records in the Samples table
        """
        query = QSqlQuery()

        sql_query = f"SELECT COUNT(*) FROM {self.data_table} WHERE {get_headers(self.data_table)[0]} {self.sql_data_ids_to_show}"

        # Execute the query
        logger_setup.get_logger().info(f'Fetching total records for the table type: {self.data_table}')
        logger_setup.get_logger().debug(f'SQL command: {sql_query}')
        if not query.exec(sql_query):
            # Handle query execution error
            logger_setup.get_logger().critical(
                f'Error fetching total records: {query.lastError().text()}')
            logger_setup.get_logger().critical(f'SQL command: {sql_query}')
            return 0

        # Fetch the count
        if query.next():
            return query.value(0)

        return 0

    def get_total_records_2(self, dbTable_comboBox) -> int:
        """
        Get the total number of records in the Samples table
        """
        query = QSqlQuery()
        sql_query = f"SELECT COUNT(*) FROM {self.data_filtered_table} WHERE {get_headers(self.data_filtered_table)[0]} {self.sql_data_filtered_ids_to_show}"

        # Execute the query
        logger_setup.get_logger().info(f'Fetching total records for the table type: {self.data_filtered_table}')
        logger_setup.get_logger().debug(f'SQL command: {sql_query}')
        if not query.exec(sql_query):
            # Handle query execution error
            logger_setup.get_logger().critical(
                f'Error fetching total records: {query.lastError().text()}')
            logger_setup.get_logger().critical(f'SQL command: {sql_query}')
            return 0

        # Fetch the count
        if query.next():
            return query.value(0)

        return 0

    def get_record_index(self, record_id, dbTable_comboBox):
        """
        Get the index of a specific record ID
        """
        table_name = dbTable_comboBox.currentText()
        table = TxM.remove_spaces(table_name)
        query = QSqlQuery()

        # Construct the SQL query
        base_id_column = get_headers(table)[0]
        sql_query = f"""
                SELECT row_number 
                FROM (
                    SELECT ROW_NUMBER() OVER (ORDER BY {base_id_column}) AS row_number, {base_id_column} 
                    FROM {table} 
                    WHERE {base_id_column} {self.data_ids_to_show}
                ) 
                WHERE {base_id_column} = :record_id
            """

        # Prepare and bind parameters
        query.prepare(sql_query)
        query.bindValue(":record_id", record_id)

        logger_setup.get_logger().info('Getting the record index for record ID: {record_id}')
        logger_setup.get_logger().debug(f'SQL command: {sql_query}')
        # Execute the query
        if not query.exec():
            # Handle query execution error
            logger_setup.get_logger().critical(
                f'Error fetching records index: {query.lastError().text()}')
            logger_setup.get_logger().critical(f'SQL command: {sql_query}')
            return -1

        # Fetch the result
        if query.next():
            return query.value(0) - 1  # Convert to zero-based index

        return -1

    def switch_to_table(self, stacked_widget: QStackedWidget):
        """
        Sets the current widget to a table view
        :return:
        """
        stacked_widget.setCurrentIndex(0)
        self.page_info_label.show()
        self.prev_button.show()
        self.next_button.show()
        self.goto_line_edit.show()

    def switch_to_tree(self, stacked_widget: QStackedWidget):
        """
        Sets the current widget to a tree view
        :return:
        """
        stacked_widget.setCurrentIndex(1)
        self.page_info_label.hide()
        self.prev_button.hide()
        self.next_button.hide()
        self.goto_line_edit.hide()

    def switch_to_table_2(self, stacked_widget: QStackedWidget):
        """
        Sets the current widget to a table view
        :return:
        """
        stacked_widget.setCurrentIndex(0)
        self.page_info_label_2.show()
        self.prev_button_2.show()
        self.next_button_2.show()
        self.goto_line_edit_2.show()

    def switch_to_tree_2(self, stacked_widget: QStackedWidget):
        """
        Sets the current widget to a tree view
        :return:
        """
        stacked_widget.setCurrentIndex(1)
        self.page_info_label_2.hide()
        self.prev_button_2.hide()
        self.next_button_2.hide()
        self.goto_line_edit_2.hide()

    def saveWindowState(self):
        settings.setValue("ui/DataviewWidget/pos", self.pos())
        settings.setValue("ui/DataviewWidget/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/DataviewWidget/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/DataviewWidget/size", defaultValue=QSize(810, 569)))

    def closeEvent(self, a0):
        self.saveWindowState()
        super().closeEvent(a0)

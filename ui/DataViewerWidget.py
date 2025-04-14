import os
import sys
import time

from PyQt6 import QtCore as QtC, QtWidgets
from PyQt6 import QtSql as QtS
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import QPoint, QSize, QTimer, Qt, QRegularExpression
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtWidgets import QWidget, QTableView, QTreeView, QComboBox, QPushButton, QMessageBox, \
    QCompleter, QLineEdit, QStackedWidget
from PyQt6.uic import loadUi

import Functions.Text_manipulations as TxM
import logger_setup
from Functions.Database_manager import update_database
from Functions import SQLUtils
from Functions.Widget_classes import SQLiteTableModel, TreeSortFilterProxyModel, save_expanded_state, TreeModel, \
    WordWrapDelegate, get_name_column, ReadableProxyModel, get_id_from_name, get_record_index
from ui.SampleInformation import SampleInformation
from Functions.Settings_manager import settings
from Functions.LoadingDialog_manager import LoadingDialogManager
from ui.EditTable import EditTable
from ui.EditTree import EditTree
from ui.EditView import EditView
from ui.EditTreeView import EditTreeView


class DataViewerWidget(QWidget):
    def __init__(self, ids_to_show, table_type):

        start_time = time.time()
        super().__init__()
        self.loading_manager = LoadingDialogManager.get_instance()
        self.table_type = table_type
        self.ids_to_show = '('

        # creates ids_to_show string in format (id1, id2, id3, ...)
        # ids_to_show is a filtered list of ids to show in the table
        # can be either from Samples, Aliquots, Spots, or UPbData
        if len(ids_to_show) > 0:
            id_str = ", ".join([str(i) for i in ids_to_show])
            self.ids_to_show += id_str
            self.ids_to_show += ")"

        self.loadWindowState()

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "DataViewerWidget.ui")
        loadUi(sources_ui_file, self)

        self.id_condition = '()'

        self.current_selection = []
        self.current_table = ""

        self.dbTable_comboBox_2.addItems(SQLUtils.user_viewable_tables)

        match self.table_type:
            case 'Samples':
                self.dbTable_comboBox.addItem('Samples')
            case 'Aliquots':
                self.dbTable_comboBox.addItem('Aliquots')
            case 'Spots':
                self.dbTable_comboBox.addItem('Spots')
            case 'UPbAnalyses':
                self.dbTable_comboBox.addItem('UPbAnalyses')

        self.proxy_model = ReadableProxyModel

        # todo future implementation for dynamically switching between these tables
        # self.dbTable_comboBox.addItems(['Samples', 'Aliquots', 'Spots', 'UPbAnalyses'])
        # self.dbTable_comboBox.currentTextChanged.connect(lambda: self.display_data_table(self.db_stackedWidget, self.dbTable_tableView,
        #                                                                                  self.dbTable_comboBox, self.edit_pushButton))

        # Display filtered table for the first time
        self.dbTable_comboBox_2.currentTextChanged.connect(self.display_table_with_data_filter)

        # Pagination variables
        # todo add rows_per_page combobox and signals to connect to settings values
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
            lambda: self.edit_popup(self.dbTable_tableView, self.dbTable_treeView, self.proxy_model,
                                    self.dbTable_comboBox))

        self.search_lineEdit.returnPressed.connect(lambda: self.search(self.search_lineEdit, self.proxy_model))

        self.selectionTimer = QTimer()
        self.selectionTimer.setSingleShot(True)
        self.selectionTimer.timeout.connect(self.display_table_with_data_filter)
        self.display_data_table()
        if self.table_type == 'Aliquots':
            self.dbTable_treeView.selectionModel().selectionChanged.connect(self.on_select_changed)
        else:
            self.dbTable_tableView.selectionModel().selectionChanged.connect(self.on_select_changed)

        self.show()
        end_time = time.time()
        logger_setup.get_logger().info(f'Displayed filtered view in {end_time - start_time} seconds')

    def display_data_table(self):
        """
        Displays the sample table
        :return:
        """
        if not self.table_type:
            logger_setup.get_logger().info(f'No table selected to display')
            return

        self.loading_manager.show_loading_dialog('Loading', f'Displaying {self.table_type}...')

        if self.table_type != 'Aliquots':
            self.switch_to_table(self.db_stackedWidget)
            self.total_records_1 = self.get_total_records_1()
            offset = self.current_page_1 * self.rows_per_page_1

            match self.table_type:
                case 'Samples':
                    table = 'SampleView'
                    show_cols = ', '.join(settings.value('sample_view_columns'))
                    model = SQLiteTableModel(
                        f'SELECT {show_cols} FROM {table} WHERE SampleID IN {self.ids_to_show} ORDER BY SampleName LIMIT {self.rows_per_page_1} OFFSET {offset}')
                case 'Spots':
                    table = 'SpotView'
                    show_cols = ', '.join(settings.value('spot_view_columns'))
                    model = SQLiteTableModel(
                        f'SELECT {show_cols} FROM {table} WHERE SpotID IN {self.ids_to_show} ORDER BY SampleName LIMIT {self.rows_per_page_1} OFFSET {offset}')
                case 'UPbAnalyses':
                    table = 'UPbView'
                    show_cols = ', '.join(settings.value('upb_analysis_view_columns'))
                    model = SQLiteTableModel(
                        f'SELECT {show_cols} FROM {table} WHERE UPbAnalysisID IN {self.ids_to_show} ORDER BY SampleName LIMIT {self.rows_per_page_1} OFFSET {offset}')
                case _:
                    logger_setup.get_logger().critical(
                        f"Error {self.table_type}: Tried to switch to a table with no table or tree...")
                    return

            name_header = model.headerData(get_name_column(self.table_type) - 1, QtC.Qt.Orientation.Horizontal,
                                           QtC.Qt.ItemDataRole.DisplayRole)
            self.set_go_to_completer(self.goto_line_edit, name_header, table)

            self.proxy_model = ReadableProxyModel()
            self.proxy_model.setSourceModel(model)
            self.proxy_model.setFilterKeyColumn(-1)  # search all columns

            self.dbTable_tableView.setModel(self.proxy_model)
            self.dbTable_tableView.setSortingEnabled(True)
            self.dbTable_tableView.setWordWrap(True)
            self.dbTable_tableView.setTextElideMode(Qt.TextElideMode.ElideNone)  # Prevent text truncation
            self.dbTable_tableView.setItemDelegate(WordWrapDelegate(self.dbTable_tableView))
            self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.dbTable_tableView.verticalHeader().hide()

            self.hide_columns(self.dbTable_tableView, table)

            self.dbTable_tableView.resizeColumnsToContents()
            for column in range(self.proxy_model.columnCount()):
                if self.dbTable_tableView.columnWidth(column) > 400:
                    self.dbTable_tableView.setColumnWidth(column, 400)

            # Update page info label
            start_record = offset + 1
            end_record = min(offset + self.rows_per_page_1, self.total_records_1)
            self.page_info_label.setText(
                f"Showing records {start_record} - {end_record} of {self.total_records_1}")

            self.dbTable_tableView.setSizeAdjustPolicy(
                QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        elif self.table_type == 'Aliquots':
            if self.table_type not in SQLUtils.user_viewable_trees:
                logger_setup.get_logger().critical(f"Error {self.table_type}: Tried to display a table as a tree...")
                return
            if self.table_type == 'Aliquots':
                table = 'AliquotView'
                self.switch_to_tree(self.db_stackedWidget)
                show_cols = ', '.join(settings.value('aliquot_view_columns'))
                source_model = SQLiteTableModel(
                    f'SELECT {show_cols} FROM {table} WHERE AliquotID IN {self.ids_to_show} ORDER BY SampleName')
                model = TreeModel(source_model)
                self.proxy_model = ReadableProxyModel()
                self.proxy_model.setSourceModel(model)
            else:
                logger_setup.get_logger().info(f"Passed a tree that is not Aliquots")
                return

            self.dbTable_treeView.setModel(self.proxy_model)
            self.dbTable_treeView.setSortingEnabled(False)
            self.dbTable_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
            self.dbTable_treeView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.hide_columns(self.dbTable_treeView, table)
            for column in range(self.proxy_model.columnCount()):
                self.dbTable_treeView.resizeColumnToContents(column)
        else:
            logger_setup.get_logger().critical(
                f"Error {self.table_type}: Tried to switch to a table with no table or tree...")

        self.edit_pushButton.setText(f"Edit {self.table_type}")

        self.loading_manager.close_loading_dialog('Loading', f'Displaying {self.table_type}...')

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
        table = TxM.remove_spaces(self.dbTable_comboBox_2.currentText())
        if table == "References":
            table = '"References"'

        if self.table_type == 'Aliquots':
            data_filter = self.dbTable_treeview
            db_view: QTreeView = self.dbTable_treeView_2
        else:
            data_filter = self.dbTable_tableView
            db_view: QTableView = self.dbTable_tableView_2

        if db_view is None:
            return

        condition_ids = []
        ids_to_show = []

        if data_filter.selectionModel().hasSelection():
            if self.current_selection != data_filter.selectionModel().selectedIndexes():
                self.current_selection = data_filter.selectionModel().selectedIndexes()
                self.current_table = self.dbTable_comboBox_2.currentText()
                for index in data_filter.selectionModel().selectedIndexes():
                    condition_id = data_filter.model().index(index.row(), 0).data()
                    condition_ids.append(str(condition_id))

                if table in SQLUtils.as_table_dict.values():
                    for key, value in SQLUtils.as_table_dict.items():
                        if value == table:
                            as_table = key
                            break
                else:
                    as_table = table

                table_condition = ''
                sql = f'SELECT DISTINCT {as_table if as_table != '"References"' else "UPbReferences"}.* FROM Samples '
                sql += SQLUtils.get_join_from_table("", [table] + [self.table_type])
                if condition_ids:
                    match self.table_type:
                        case 'Samples':
                            table_condition = f" WHERE Samples.SampleID IN ({', '.join(condition_ids)})"
                        case 'Aliquots':
                            table_condition = f" WHERE Aliquots.AliquotID IN ({', '.join(condition_ids)})"
                        case 'Spots':
                            table_condition = f" WHERE Spots.SpotID IN ({', '.join(condition_ids)})"
                        case 'UPbAnalyses':
                            table_condition = f" WHERE UPbAnalyses.UPbAnalysisID IN ({', '.join(condition_ids)})"

                sql += table_condition
                logger_setup.get_logger().debug(f'Distinct Filtered Selection SQL Command: {sql}')

                query = QSqlQuery()
                ids_to_show = []
                # Execute the query
                logger_setup.get_logger().info(
                    f'Displaying table with selection-based filter')
                logger_setup.get_logger().debug(f'SQL command: {sql}')
                if query.exec(sql):
                    while query.next():  # Iterate through all results
                        row_id = query.value(0)
                        if row_id is not None and row_id != '':
                            ids_to_show.append(str(row_id))
                else:
                    logger_setup.get_logger().critical(
                        f'Error in displaying table with selection-based filter: {query.lastError().text()}')
                    logger_setup.get_logger().critical(f'SQL command: {sql}')

                # Update the id_condition attribute

                self.id_condition = f'({", ".join(ids_to_show)}'
                self.id_condition = self.id_condition + ')'
            try:
                self.search_lineEdit_2.editingFinsihed.disconnect()
            except:
                pass
            try:
                self.edit_pushButton_2.clicked.disconnect()
            except:
                pass

            if table in SQLUtils.user_viewable_trees:
                self.switch_to_tree_2(self.db_stackedWidget_2)
                model = QtS.QSqlTableModel()
                model.setTable(table)
                model.select()

                model.setFilter(f'{table[0:-1]}ID  IN ( '
                                f'WITH RECURSIVE ParentTree AS '
                                f'(SELECT * FROM {table} '
                                f'WHERE {table[0:-1]}ID IN {self.id_condition} '
                                f'UNION ALL '
                                f'SELECT {table}.* FROM {table} '
                                f'INNER JOIN ParentTree ON {table}.{table[0:-1]}ID = ParentTree.Parent{table[0:-1]}ID) '
                                f'SELECT {table[0:-1]}ID FROM ParentTree) ')
                tree_model = TreeModel(model, self)

                self.dbTable_treeView_2.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
                self.dbTable_treeView_2.hideColumn(1)  # don't show ID column
                self.dbTable_treeView_2.hideColumn(2)  # don't show parent ID column
                self.dbTable_treeView_2.hideColumn(3)  # don't show parent row column
                # self.dbTable_treeView_2.hideColumn(4)  # don't show sample ID column
                self.dbTable_treeView_2.setSortingEnabled(False)

                self.proxy_model = ReadableProxyModel()
                self.proxy_model.setSourceModel(tree_model)
                tree_proxy_model = TreeSortFilterProxyModel(view=self.dbTable_treeView_2)
                tree_proxy_model.setSourceModel(self.proxy_model)
                self.dbTable_treeView_2.setModel(tree_proxy_model)
                self.dbTable_treeView_2.expandAll()

                self.search_lineEdit_2.returnPressed.connect(
                    lambda: self.search(self.search_lineEdit_2, tree_proxy_model, self.dbTable_treeView_2))

                self.edit_pushButton_2.clicked.connect(
                    lambda: self.edit_popup(self.dbTable_tableView_2, self.dbTable_treeView_2, tree_proxy_model,
                                            self.dbTable_comboBox_2))

            elif table in SQLUtils.user_viewable_tables or table == '"References"':
                self.switch_to_table_2(self.db_stackedWidget_2)
                offset = self.current_page_2 * self.rows_per_page_2
                model = QtS.QSqlQueryModel()
                self.proxy_model = ReadableProxyModel()

                # todo would be nice to switch these table[0:-1] entries and LabFac UPbAnalys to be a dict lookup from SQLUtils
                if table == "LabFacilities":
                    model.setQuery(
                        f"SELECT * FROM {table} WHERE LabFacilityID IN {self.id_condition} ORDER BY LabFacilityID LIMIT {self.rows_per_page_2} OFFSET {offset}")
                elif table == "UPbAnalyses":
                    model.setQuery(
                        f"SELECT * FROM {table} WHERE UPbAnalysisID IN {self.id_condition} ORDER BY UPbAnalysisID LIMIT {self.rows_per_page_2} OFFSET {offset}")
                elif table == '"References"' or table == 'References' or table == 'UPbReferences':
                    model.setQuery(
                        f'SELECT * FROM "References" WHERE ReferenceID IN {self.id_condition} ORDER BY ReferenceID LIMIT {self.rows_per_page_2} OFFSET {offset}')
                else:
                    model.setQuery(
                        f"SELECT * FROM {table} WHERE {table[0:-1]}ID IN {self.id_condition} ORDER BY {table[0:-1]}ID LIMIT {self.rows_per_page_2} OFFSET {offset}")

                self.proxy_model.setFilterKeyColumn(-1)  # search all columns
                self.dbTable_tableView_2.setModel(self.proxy_model)
                self.dbTable_tableView_2.hideColumn(0)  # don't show ID column
                self.dbTable_tableView_2.verticalHeader().setVisible(False)
                self.dbTable_tableView_2.resizeColumnsToContents()
                self.dbTable_tableView_2.setSortingEnabled(True)
                self.dbTable_tableView_2.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)

                self.search_lineEdit_2.returnPressed.connect(
                    lambda: self.search(self.search_lineEdit_2, self.proxy_model))
                self.edit_pushButton_2.clicked.connect(
                    lambda: self.edit_popup(self.dbTable_tableView_2, self.dbTable_treeView_2, self.proxy_model,
                                            self.dbTable_comboBox_2))

                logger_setup.get_logger().info('Sucessfully displayed table with selection-based filter')
            else:
                logger_setup.get_logger().critical(
                    f"Error {table}: Tried to switch to a table with no table or tree..Don't know how it got here")

    def edit_popup(self, dbTable_tableView, dbTable_treeView, tree_proxy_model, dbTable_comboBox):
        dbTable_comboBox: QComboBox
        table_name = dbTable_comboBox.currentText()
        table = TxM.remove_spaces(table_name)
        view_tables = ['Samples', 'Aliquots', 'Spots', 'UPbAnalyses', 'Columns', 'References']
        if table_name in view_tables:
            id_str = self.ids_to_show.replace('(', '').replace(')', '')
            ids = id_str.split(', ')
            ids = list(map(int, ids))  # Convert all IDs to integers
            if table_name == 'Aliquots':
                # Ask the user which sample they want to edit
                sample_names = []
                query = QSqlQuery()
                for aliquot_id in list(eval(self.ids_to_show)):
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
                    if query.value(0) in list(eval(self.ids_to_show)):
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
            update_database()

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
        update_database()

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

    def set_go_to_completer(self, lineedit: QLineEdit, name_header, table):
        # Populate the value input with a completer based on the selected attribute
        name_completer = QCompleter(parent=lineedit)
        query = QSqlQuery()
        sql_query = f'SELECT DISTINCT {name_header} FROM "{table}"'
        logger_setup.get_logger().debug(f'SQL command: {sql_query}')
        if not query.exec(sql_query):
            logger_setup.get_logger().critical(f'Error creating the completer for input')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        values = set()
        while query.next():
            values.add(query.value(0))
        name_completer.setModel(QtC.QStringListModel(values))
        name_completer.setFilterMode(QtC.Qt.MatchFlag.MatchContains)
        name_completer.setCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        name_completer.setCompletionMode(QtW.QCompleter.CompletionMode.PopupCompletion)

        lineedit.setCompleter(name_completer)

    def hide_columns(self, db_view, table):
        match table:
            case 'SampleView':
                db_view.hideColumn(0)  # don't show SampleID column
            case 'AliquotView':
                db_view.hideColumn(1)  # don't show AliquotID
                db_view.hideColumn(2)  # don't show ParentAliquotID
                db_view.hideColumn(3)  # don't show AliquotParentRow
                db_view.hideColumn(4)  # don't show SampleID
            case 'SpotView':
                db_view.hideColumn(0)  # don't show SpotID
                db_view.hideColumn(1)  # don't show SampleID
                db_view.hideColumn(2)  # don't show AliquotID
            case 'UPbView':
                db_view.hideColumn(0)  # don't show UPbAnalysisID
                db_view.hideColumn(1)  # don't show SampleID
                db_view.hideColumn(2)  # don't show AliquotID
                db_view.hideColumn(3)  # don't show SpotID

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
        table = TxM.remove_spaces(self.dbTable_comboBox.currentText())
        query = QSqlQuery()
        sql_query = ""

        # Construct the query based on the table
        if table == "LabFacilities":
            sql_query = f"SELECT COUNT(*) FROM {table} WHERE LabFacilityID IN {self.ids_to_show}"
        elif table == "UPbAnalyses":
            sql_query = f"SELECT COUNT(*) FROM {table} WHERE UPbAnalysisID IN {self.ids_to_show}"
        else:
            sql_query = f"SELECT COUNT(*) FROM {table} WHERE {table[:-1]}ID IN {self.ids_to_show}"

        # Execute the query
        logger_setup.get_logger().info(f'Fetching total records for the table type: {self.table_type}')
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
        table_name = dbTable_comboBox.currentText()
        table = TxM.remove_spaces(table_name)
        query = QSqlQuery()
        sql_query = ""

        # Construct the query based on the table
        if table == "LabFacilities":
            sql_query = f"SELECT COUNT(*) FROM {table} WHERE LabFacilityID IN {self.id_condition}"
        elif table == "UPbAnalyses":
            sql_query = f"SELECT COUNT(*) FROM {table} WHERE UPbAnalysisID IN {self.id_condition}"
        else:
            sql_query = f"SELECT COUNT(*) FROM {table} WHERE {table[:-1]}ID IN {self.id_condition}"

        # Execute the query
        logger_setup.get_logger().info(f'Fetching total records for the table type: {self.table_type}')
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
        base_id_column = f"{table[:-1]}ID"
        sql_query = f"""
                SELECT row_number 
                FROM (
                    SELECT ROW_NUMBER() OVER (ORDER BY {base_id_column}) AS row_number, {base_id_column} 
                    FROM {table} 
                    WHERE {base_id_column} IN {self.ids_to_show}
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

    def saveWindowState(self):
        settings.setValue("ui/DataviewWidget/pos", self.pos())
        settings.setValue("ui/DataviewWidget/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/DataviewWidget/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/DataviewWidget/size", defaultValue=QSize(810, 569)))

    def closeEvent(self, a0):
        self.saveWindowState()
        super().closeEvent(a0)

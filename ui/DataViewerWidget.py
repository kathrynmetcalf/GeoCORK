import os
import sys

from PyQt6 import QtCore as QtC
from PyQt6 import QtSql as QtS
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import QPoint, QSettings, QSize, QSortFilterProxyModel, QTimer
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtWidgets import QWidget, QTableView, QTreeView, QComboBox, QPushButton, QPlainTextEdit
from PyQt6.uic import loadUi

import Functions.Text_manipulations as TxM
import logger_setup
from Functions.Database_manager import update_database
from Functions import SQLUtils
from Functions.Widget_classes import SQLiteTableModel, TreeSortFilterProxyModel, save_expanded_state, TreeModel
from ui.SampleInformation import SampleInformation
from Functions.Settings_manager import settings
from ui.EditTable import EditTable
from ui.EditTree import EditTree
from ui.EditView import EditView


class DataViewerWidget(QWidget):
    def __init__(self, ids_to_show, table_type):
        super().__init__()
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

        # self.switch_to_table(self.db_stackedWidget)
        # self.switch_to_table(self.db_stackedWidget_2)

        self.dbTable_comboBox_2.addItems(SQLUtils.user_viewable_tables)

        if self.table_type == 'Samples':
            self.dbTable_comboBox.addItem('Samples')
        elif self.table_type == 'Aliquots':
            self.dbTable_comboBox.addItem('Aliquots')
        elif self.table_type == 'Spots':
            self.dbTable_comboBox.addItem('Spots')
        elif self.table_type == 'UPbAnalyses':
            self.dbTable_comboBox.addItem('UPbAnalyses')
        # todo future implementation for dynamically switching between these tables

        # Pagination variables
        self.current_page_1 = 0
        self.rows_per_page_1 = 2000
        self.total_records_1 = self.get_total_records_1()

        self.current_page_2 = 0
        self.rows_per_page_2 = 2000
        self.total_records_2 = self.get_total_records_2(self.dbTable_comboBox_2)

        self.goto_line_edit.textChanged.connect(self.go_to_record_1)
        self.goto_line_edit_2.textChanged.connect(self.go_to_record_2)

        # display sample table information first time
        self.display_sample_table(self.db_stackedWidget, self.dbTable_tableView,
                                  self.dbTable_comboBox, self.edit_pushButton)

        self.dbTable_comboBox.currentTextChanged.connect(lambda: self.display_sample_table(self.db_stackedWidget, self.dbTable_tableView,
                                  self.dbTable_comboBox, self.edit_pushButton))
        # todo the showing records and next/previous pages are broken and not updating

        # Display filtered table for the first time
        self.dbTable_comboBox_2.currentTextChanged.connect(lambda: self.display_table_with_sample_filter(
            self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2, self.dbTable_comboBox_2,
            self.edit_pushButton_2, self.dbTable_tableView, self.table_type))

        self.dbTable_tableView: QTableView

        # Connect buttons to their respective functions
        self.prev_button.clicked.connect(lambda: self.previous_page_1(self.db_stackedWidget, self.dbTable_tableView,
                                                                      self.dbTable_comboBox, self.edit_pushButton))
        self.next_button.clicked.connect(lambda: self.next_page_1(self.db_stackedWidget, self.dbTable_tableView,
                                                                  self.dbTable_comboBox, self.edit_pushButton))

        self.prev_button_2.clicked.connect(
            (lambda: self.previous_page_2(self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2,
                                          self.dbTable_comboBox_2,
                                          self.edit_pushButton_2, self.dbTable_tableView, self.table_type)))
        self.next_button_2.clicked.connect(
            (lambda: self.next_page_2(self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2,
                                      self.dbTable_comboBox_2,
                                      self.edit_pushButton_2, self.dbTable_tableView, self.table_type)))

        self.show()

    def closeEvent(self, a0):
        self.saveWindowState()
        super().closeEvent(a0)

    def next_page_1(self, db_stackedWidget, dbTable_tableView, dbTable_comboBox, edit_pushButton):
        """
        Slot to move to the next page for the sample table
        """
        if (self.current_page_1 + 1) * self.rows_per_page_1 < self.total_records_1:
            self.current_page_1 += 1
            self.display_sample_table(
                db_stackedWidget, dbTable_tableView, dbTable_comboBox, edit_pushButton)

    def previous_page_1(self, db_stackedWidget, dbTable_tableView, dbTable_comboBox, edit_pushButton):
        """
        Slot to move to the previous page for the sample table
        """
        if self.current_page_1 > 0:
            self.current_page_1 -= 1
        self.display_sample_table(db_stackedWidget, dbTable_tableView, dbTable_comboBox, edit_pushButton)

    def next_page_2(self, db_stackedWidget, dbTable_tableView, dbTable_treeView, dbTable_comboBox, edit_pushButton,
                    sample_filter, table_type):
        """
        Slot to move to the next page for the filtered table
        """
        if (self.current_page_2 + 1) * self.rows_per_page_2 < self.total_records_2:
            self.current_page_2 += 1
            self.display_table_with_sample_filter(
                db_stackedWidget, dbTable_tableView, dbTable_treeView, dbTable_comboBox, edit_pushButton, sample_filter,
                table_type)

    def previous_page_2(self, db_stackedWidget, dbTable_tableView, dbTable_treeView, dbTable_comboBox, edit_pushButton,
                        sample_filter, table_type):
        """
        Slot to move to the previous page for the filtered table
        """
        if self.current_page_2 > 0:
            self.current_page_2 -= 1
        self.display_table_with_sample_filter(
            db_stackedWidget, dbTable_tableView, dbTable_treeView, dbTable_comboBox, edit_pushButton, sample_filter,
            table_type)

    def go_to_record_1(self):
        """
        Slot to go to a specific record ID for the sample table.
        """
        # todo connect this to a new button.
        try:
            text = self.goto_line_edit.text().strip()
            if not text:
                # QMessageBox.warning(self, "Input Error", "Please enter a record ID.")
                return

            record_id = int(text)
            index = self.get_record_index(record_id, self.dbTable_comboBox)

            if index != -1:
                self.current_page_1 = index // self.rows_per_page_1
                self.display_sample_table(
                    self.db_stackedWidget,
                    self.dbTable_tableView,
                    self.dbTable_comboBox,
                    self.edit_pushButton
                )
            else:
                logger_setup.get_logger().critical(f"Record ID not found: {record_id}")
        except ValueError:
            logger_setup.get_logger().critical(f"Invalid Record ID: {record_id}")

    def go_to_record_2(self):
        """
        Slot to go to a specific record ID for the filter table
        """
        # todo fix, this slot is not connected to a signal
        try:
            record_id = int(self.goto_line_edit_2.plainText())
            index = self.get_record_index(record_id, self.dbTable_comboBox_2)
            if index != -1:
                self.current_page_2 = index // self.rows_per_page_2
                self.display_table_with_sample_filter(self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2,
                                      self.dbTable_comboBox_2,
                                      self.edit_pushButton_2, self.dbTable_tableView, self.table_type)
            else:
                logger_setup.get_logger().critical(f"Record ID not found: {record_id}")
        except ValueError:
            logger_setup.get_logger().critical(f"Invalid Record ID: {record_id}")

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

    def switch_to_table(self, db_stackedWidget):
        """
        Sets the current widget to a table view
        :return:
        """
        db_stackedWidget: QtW.QStackedWidget
        db_stackedWidget.setCurrentIndex(0)

    def switch_to_tree(self, db_stackedWidget):
        """
        Sets the current widget to a tree view
        :return:
        """
        db_stackedWidget: QtW.QStackedWidget
        db_stackedWidget.setCurrentIndex(1)

    def display_sample_table(self, db_stackedWidget, dbTable_tableView, dbTable_comboBox, edit_pushButton):
        """
        Displays the sample table
        :return:
        """
        table_name = dbTable_comboBox.currentText()
        self.total_records_1 = self.get_total_records_1()

        # Remove spaces from display names
        table = TxM.remove_spaces(table_name)
        offset = self.current_page_1 * self.rows_per_page_1

        if table == 'Samples':
            self.switch_to_table(db_stackedWidget)
            show_cols = ', '.join(settings.value('sample_view_columns'))
            query = SQLiteTableModel(
                f'SELECT {show_cols} FROM SampleView WHERE SampleID IN {self.ids_to_show} ORDER BY SampleName LIMIT {self.rows_per_page_1} OFFSET {offset}')

            sample_proxy_model = QtC.QSortFilterProxyModel()
            sample_proxy_model.setSourceModel(query)
            # Signal for clicked add button in main window
            self.edit_pushButton.clicked.connect(
                lambda: self.edit_popup(self.dbTable_tableView, self.dbTable_treeView, sample_proxy_model, self.dbTable_comboBox))

            sample_proxy_model.setFilterKeyColumn(-1)  # search all columns
            dbTable_tableView.setModel(sample_proxy_model)
            dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            # self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.OnManualSubmit)
            # Signal for search bar
            self.search_lineEdit.textChanged.connect(lambda: self.search(self.search_lineEdit, sample_proxy_model))
        elif table == 'Aliquots':
            # todo make aliquots a tree model
            self.switch_to_table(db_stackedWidget)
            show_cols = ', '.join(settings.value('aliquot_view_columns'))
            query = SQLiteTableModel(
                f'SELECT {show_cols} FROM AliquotView WHERE AliquotID IN {self.ids_to_show} ORDER BY SampleName LIMIT {self.rows_per_page_1} OFFSET {offset}')

            aliquot_proxy_model = QtC.QSortFilterProxyModel()
            aliquot_proxy_model.setSourceModel(query)

            self.edit_pushButton.clicked.connect(
                lambda: self.edit_popup(self.dbTable_tableView, self.dbTable_treeView, aliquot_proxy_model,
                                        self.dbtable_comboBox))

            aliquot_proxy_model.setFilterKeyColumn(-1)  # search all columns
            dbTable_tableView.setModel(aliquot_proxy_model)
            dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.hideColumn(1)  # don't show SampleID column
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            # self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.OnManualSubmit)
            self.search_lineEdit.textChanged.connect(lambda: self.search(self.search_lineEdit, aliquot_proxy_model))
        elif table == 'Spots':
            self.switch_to_table(db_stackedWidget)
            show_cols = ', '.join(settings.value('spot_view_columns'))
            query = SQLiteTableModel(
                f'SELECT {show_cols} FROM SpotView WHERE SpotID IN {self.ids_to_show} ORDER BY SampleName LIMIT {self.rows_per_page_1} OFFSET {offset}')

            spot_proxy_model = QtC.QSortFilterProxyModel()
            spot_proxy_model.setSourceModel(query)

            self.edit_pushButton.clicked.connect(
                lambda: self.edit_popup(self.dbTable_tableView, self.dbTable_treeView, spot_proxy_model,
                                        self.dbTable_comboBox))

            spot_proxy_model.setFilterKeyColumn(-1)  # search all columns
            dbTable_tableView.setModel(spot_proxy_model)
            dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.hideColumn(1)  # don't show SampleID column
            dbTable_tableView.hideColumn(2)  # don't show AliquotID column
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            # self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.OnManualSubmit)
            self.search_lineEdit.textChanged.connect(lambda: self.search(self.search_lineEdit, spot_proxy_model))
        elif table == 'UPbAnalyses':
            self.switch_to_table(db_stackedWidget)
            show_cols = ', '.join(settings.value('upb_analysis_view_columns'))
            query = SQLiteTableModel(
                f'SELECT {show_cols} FROM UPbView WHERE UPbAnalysisID IN {self.ids_to_show} ORDER BY SampleName LIMIT {self.rows_per_page_1} OFFSET {offset}')

            upb_proxy_model = QtC.QSortFilterProxyModel()
            upb_proxy_model.setSourceModel(query)
            upb_proxy_model.setFilterKeyColumn(-1)  # search all columns

            self.edit_pushButton.clicked.connect(
                lambda: self.edit_popup(self.dbTable_tableView, self.dbTable_treeView, upb_proxy_model,
                                        self.dbTable_comboBox))

            dbTable_tableView.setModel(upb_proxy_model)
            dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            # self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.OnManualSubmit)
            self.search_lineEdit.textChanged.connect(lambda: self.search(self.search_lineEdit, upb_proxy_model))
        else:
            logger_setup.get_logger().critical(f"Error {table}: Tried to switch to a table with no table or tree...")

        # Update page info label
        start_record = offset + 1
        end_record = min(offset + self.rows_per_page_1, self.total_records_1)
        self.page_info_label.setText(f"Showing records {start_record} - {end_record} of {self.total_records_1}")

        self.selectionTimer = QTimer()
        self.selectionTimer.setSingleShot(True)
        self.selectionTimer.timeout.connect(lambda: self.display_table_with_sample_filter(
            self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2, self.dbTable_comboBox_2,
            self.edit_pushButton_2, self.dbTable_tableView, self.table_type))

        # Connect the selectionChanged signal to the onSelectionChanged method
        self.dbTable_tableView.selectionModel().selectionChanged.connect(self.on_select_changed)

        edit_pushButton.setText(f"Edit {table_name}")

    def on_select_changed(self):
        """
        This method is called whenever the selection changes.
        It restarts the timer to batch rapid selection changes.
        """
        # Restart the timer every time the selection changes
        self.selectionTimer.start(250)  # Delay in milliseconds

    def display_table_with_sample_filter(self, db_stackedWidget, dbTable_tableView, dbTable_treeView,
                                         dbTable_comboBox, edit_pushButton, sample_filter, table_type, selected=None,
                                         deselected=None):
        """
        Displays the selected table
        :return:
        """
        self.dbTable_tableView: QTableView
        dbTable_treeView: QTreeView
        sample_filter: QTableView
        offset = self.current_page_2 * self.rows_per_page_2

        table = TxM.remove_spaces(dbTable_comboBox.currentText())
        if table == "References":
            table = '"References"'

        condition_ids = []
        ids_to_show = []

        if sample_filter.selectionModel().hasSelection():
            if (self.current_selection != self.dbTable_tableView.selectionModel().selectedIndexes()
                    or self.current_table != dbTable_comboBox.currentText()):
                self.current_selection = self.dbTable_tableView.selectionModel().selectedIndexes()
                self.current_table = dbTable_comboBox.currentText()
                for index in self.dbTable_tableView.selectionModel().selectedIndexes():
                    condition_id = sample_filter.model().index(index.row(), 0).data()
                    condition_ids.append(str(condition_id))

                if table in SQLUtils.as_table_dict.values():
                    for key, value in SQLUtils.as_table_dict.items():
                        if value == table:
                            as_table = key
                            break
                else:
                    as_table = table

                table_condition = ''
                sql = f'SELECT DISTINCT {as_table if as_table!='"References"' else "UPbReferences"}.* FROM Samples '
                sql += SQLUtils.get_join_from_table("", [table] + [table_type])
                if condition_ids:
                    if table_type == 'Samples':
                        table_condition = f" WHERE Samples.SampleID IN ({', '.join(condition_ids)})"
                    elif table_type == 'Aliquots':
                        table_condition = f" WHERE Aliquots.AliquotID IN ({', '.join(condition_ids)})"
                    elif table_type == 'Spots':
                        table_condition = f" WHERE Spots.SpotID IN ({', '.join(condition_ids)})"
                    elif table_type == 'UPbAnalyses':
                        table_condition = f" WHERE UPbAnalyses.UPbAnalysisID IN ({', '.join(condition_ids)})"
                    # "(19,39,58)"

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

        if table in SQLUtils.user_viewable_trees:
            self.switch_to_tree(db_stackedWidget)
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
            tree_model = TreeModel(model, None)

            dbTable_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
            dbTable_treeView.hideColumn(1)  # don't show ID column
            dbTable_treeView.hideColumn(2)  # don't show parent ID column
            dbTable_treeView.hideColumn(3)  # don't show parent row column
            dbTable_treeView.setSortingEnabled(True)

            tree_proxy_model = TreeSortFilterProxyModel(view=dbTable_treeView)
            tree_proxy_model.setSourceModel(tree_model)
            dbTable_treeView.setModel(tree_proxy_model)

            self.search_lineEdit_2.textChanged.connect(
                lambda: self.search(self.search_lineEdit_2, tree_proxy_model, dbTable_treeView))

        elif table in SQLUtils.user_viewable_tables or table=='"References"':
            self.switch_to_table(db_stackedWidget)

            model = QtS.QSqlQueryModel()
            table_proxy_model = QSortFilterProxyModel()

            # todo would be nice to switch these table[0:-1] entries and LabFac UPbAnalys to be a dict lookup from SQLUtils
            if table == "LabFacilities":
                model.setQuery(
                    f"SELECT * FROM {table} WHERE LabFacilityID IN {self.id_condition} ORDER BY LabFacilityID LIMIT {self.rows_per_page_2} OFFSET {offset}")
            elif table == "UPbAnalyses":
                model.setQuery(
                    f"SELECT * FROM {table} WHERE UPbAnalysisID IN {self.id_condition} ORDER BY UPbAnalysisID LIMIT {self.rows_per_page_2} OFFSET {offset}")
            elif table == '"References"' or table =='References' or table=='UPbReferences':
                print( f'SELECT * FROM "References" WHERE ReferenceID IN {self.id_condition} ORDER BY ReferenceID LIMIT {self.rows_per_page_2} OFFSET {offset}')
                model.setQuery(
                    f'SELECT * FROM "References" WHERE ReferenceID IN {self.id_condition} ORDER BY ReferenceID LIMIT {self.rows_per_page_2} OFFSET {offset}')
            else:
                model.setQuery(
                    f"SELECT * FROM {table} WHERE {table[0:-1]}ID IN {self.id_condition} ORDER BY {table[0:-1]}ID LIMIT {self.rows_per_page_2} OFFSET {offset}")

            # logger_setup.get_logger().info(f'Setting the model query: {model.query().lastQuery()}')
            for col in range(model.columnCount()):
                header = TxM.add_spaces_camel(
                    model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
                model.setHeaderData(col, QtC.Qt.Orientation.Horizontal, header, QtC.Qt.ItemDataRole.DisplayRole)
            table_proxy_model.setSourceModel(model)

            table_proxy_model.setFilterKeyColumn(-1)  # search all columns
            dbTable_tableView.setModel(table_proxy_model)
            dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.verticalHeader().setVisible(False)
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)

            self.search_lineEdit_2.textChanged.connect(lambda: self.search(self.search_lineEdit_2, table_proxy_model))
            logger_setup.get_logger().info('Sucessfully displayed table with selection-based filter')
        else:
            logger_setup.get_logger().critical(f"Error {table}: Tried to switch to a table with no table or tree..Don't know how it got here")


    def search(self, search_lineEdit, proxy_model, dbTable_treeView=None):
        """
        Search the current table for the text in the search box
        Check if the case-sensitive box is checked or not
        :return:
        """
        search_lineEdit: QtW.QLineEdit
        search_expression = QtC.QRegularExpression(search_lineEdit.text())
        proxy_model.setFilterRegularExpression(search_expression)
        if dbTable_treeView is not None:
            dbTable_treeView.expandAll()

    def edit_popup(self, dbTable_tableView, dbTable_treeView, tree_proxy_model, dbTable_comboBox):
        dbTable_comboBox: QComboBox
        table_name = dbTable_comboBox.currentText()
        table = TxM.remove_spaces(table_name)
        # todo fix this for working with new sample edit view
        view_tables = ['Samples', 'Aliquots', 'Spots', 'UPbAnalyses', 'Columns', 'References']
        if table_name in view_tables:
            id_str = self.ids_to_show.replace('(', '').replace(')', '')
            ids = id_str.split(', ')
            ids = list(map(int, ids))  # Convert all IDs to integers
            dlg_args = {'table_item_ids': ids}
            dlg = EditView(table, **dlg_args)
        elif table_name == 'Aliquots':
            pass
        elif table in SQLUtils.user_viewable_trees:
            save_expanded_state(table_name, tree_proxy_model, dbTable_treeView)
            dlg = EditTree(table)
        else:
            dlg = EditTable(table)
        dlg.exec()
        update_database()

        # update both tables
        self.display_sample_table(self.db_stackedWidget, self.dbTable_tableView,
                                  self.dbTable_comboBox, self.edit_pushButton)

        # Display filtered table for the first time
        self.dbTable_comboBox_2.currentTextChanged.connect(lambda: self.display_table_with_sample_filter(
            self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2, self.dbTable_comboBox_2,
            self.edit_pushButton_2, self.dbTable_tableView, self.table_type))

        self.edit_pushButton: QPushButton
        self.edit_pushButton.clearMask()

    def edit_samples_popup(self, table_name, dbTable_tableView):
        if table_name != 'Samples':
            return
        selected_samples = []
        self.dbTable_tableView: QtW.QTableView
        # Add the sample ID for any rows that are selected
        selected_indexes = dbTable_tableView.selectedIndexes()
        for index in selected_indexes:
            id_index = index.siblingAtColumn(0)
            selected_samples.append(id_index.data(QtC.Qt.ItemDataRole.DisplayRole))
        dlg = SampleInformation(self, selected_samples)
        dlg.exec()
        update_database()

    def saveWindowState(self):
        settings.setValue("ui/DataviewWidget/pos", self.pos())
        settings.setValue("ui/DataviewWidget/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/DataviewWidget/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/DataviewWidget/size", defaultValue=QSize(810, 569)))

import os
import sys

from PyQt6 import QtCore as QtC
from PyQt6 import QtSql as QtS
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import QPoint, QSettings, QSize, QSortFilterProxyModel, QTimer
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtWidgets import QWidget, QTableView, QTreeView, QComboBox
from PyQt6.uic import loadUi

import Functions.Table_classes as TbC
import Functions.Text_manipulations as TxM
import Functions.Tree_classes as TrC
from Functions import SQLUtils
from Functions.Tree_classes import TreeSortFilterProxyModel
from ui.EditTable import EditTable
from ui.EditTree import EditTree


class DataViewerWidget(QWidget):
    def __init__(self, ids_to_show, table_type):
        super().__init__()
        self.table_type = table_type
        self.ids_to_show = '('

        # creates ids_to_show string in format (id1, id2, id3, ...)
        # ids_to_show is a filtered list of ids to show in the table
        # can be either from Samples, Aliquots, Spots, or UPbData
        if len(ids_to_show) > 0:
            for sample in ids_to_show:
                self.ids_to_show += str(sample[0]) + ", "
            self.ids_to_show = self.ids_to_show[0:-2]
            self.ids_to_show += ")"

        # self.db = QtS.QSqlDatabase.addDatabase('QSQLITE')
        # self.db.setDatabaseName(self.db_file)
        self.settings = QSettings("CSUF", "GeoChron")

        # self.db.open()

        self.loadWindowState()

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "DataViewerWidget.ui")
        loadUi(sources_ui_file, self)

        self.id_condition = '()'

        self.current_selection = []
        self.current_table = ""

        self.switch_to_table(self.db_stackedWidget)
        self.switch_to_table(self.db_stackedWidget_2)

        self.dbTable_comboBox_2.addItems(SQLUtils.user_viewable_tables)

        if self.table_type == 'sample':
            self.dbTable_comboBox.addItem('Samples')
        elif self.table_type == 'aliquot':
            self.dbTable_comboBox.addItem('Aliquots')
        elif self.table_type == 'spot':
            self.dbTable_comboBox.addItem('Spots')
        elif self.table_type == 'upbdata':
            self.dbTable_comboBox.addItem('UPbAnalyses')
        # todo future implementation for dynamically switching between these tables

        # Pagination variables
        self.current_page_1 = 0
        self.rows_per_page_1 = 255
        self.total_records_1 = self.get_total_records_1()

        self.current_page_2 = 0
        self.rows_per_page_2 = 255
        self.total_records_2 = self.get_total_records_2(self.dbTable_comboBox_2)

        # display sample table information first time
        self.display_sample_table(self.db_stackedWidget, self.dbTable_tableView,
                                  self.dbTable_comboBox, self.edit_pushButton)

        # Display filtered table for the first time
        self.dbTable_comboBox_2.currentTextChanged.connect(lambda: self.display_table_with_sample_filter(
            self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2, self.dbTable_comboBox_2,
            self.edit_pushButton_2, self.dbTable_tableView, table_type))

        self.dbTable_tableView: QTableView

        # Connect buttons to their respective functions
        self.prev_button.clicked.connect(lambda: self.previous_page_1(self.db_stackedWidget, self.dbTable_tableView,
                                                                      self.dbTable_comboBox, self.edit_pushButton))
        self.next_button.clicked.connect(lambda: self.next_page_1(self.db_stackedWidget, self.dbTable_tableView,
                                                                  self.dbTable_comboBox, self.edit_pushButton))

        self.prev_button_2.clicked.connect(
            (lambda: self.previous_page_2(self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2,
                                          self.dbTable_comboBox_2,
                                          self.edit_pushButton_2, self.dbTable_tableView, table_type)))
        self.next_button_2.clicked.connect(
            (lambda: self.next_page_2(self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2,
                                      self.dbTable_comboBox_2,
                                      self.edit_pushButton_2, self.dbTable_tableView, table_type)))
        # Signal for clicked add button in main window
        self.edit_pushButton.clicked.connect(lambda: self.edit_popup(self.dbTable_comboBox_2.currentText()))
        self.edit_pushButton_2.clicked.connect(lambda: self.edit_popup(self.dbTable_comboBox_2.currentText()))

        self.show()
    # def edit_popup(self, table):
    #     if table == 'Aliquots' or table == 'Spots' or table == 'UPbAnalyses':
    #         return
    #     elif table in SQLUtils.user_viewable_trees:
    #         TrC.save_expanded_state(table, self.dbTable_tableView_2.model(), self.dbTable_tableView_2)
    #         dlg = EditTree(self.dbTable_tableView_2.model().sourceModel(), table)
    #     else:
    #         dlg = EditTable(table)
    #     dlg.exec()
    #     # self.display_table()

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
        Slot to go to a specific record ID for the sample table
        """
        # todo fix, this slot is not connected to a signal
        try:
            record_id = int(self.goto_line_edit_1.text())
            index = self.get_record_index(record_id, self.dbTable_comboBox)
            if index != -1:
                self.current_page_1 = index // self.rows_per_page_1
                self.display_sample_table(
                    self.db_stackedWidget, self.dbTable_tableView, self.dbTable_comboBox, self.edit_pushButton)
            else:
                print("Record ID not found.")
        except ValueError:
            print("Invalid record ID.")

    def go_to_record_2(self, db_stackedWidget, dbTable_tableView, dbTable_treeView, dbTable_comboBox, edit_pushButton,
                       sample_filter, table_type):
        """
        Slot to go to a specific record ID for the filter table
        """
        # todo fix, this slot is not connected to a signal
        try:
            record_id = int(self.goto_line_edit_2.text())
            index = self.get_record_index(record_id, dbTable_comboBox)
            if index != -1:
                self.current_page_2 = index // self.rows_per_page_2
                self.display_table_with_sample_filter(
                    db_stackedWidget, dbTable_tableView, dbTable_treeView, dbTable_comboBox, edit_pushButton,
                    sample_filter,
                    table_type)
            else:
                print("Record ID not found.")
        except ValueError:
            print("Invalid record ID.")

    def get_total_records_1(self):
        """
        Get the total number of records in the Samples table
        """
        table_name = self.dbTable_comboBox.currentText()
        table = TxM.remove_spaces(table_name)
        query = QSqlQuery()
        sql_query = ""

        # Construct the query based on the table
        if table == "LabFacilities":
            sql_query = f"SELECT COUNT(*) FROM {table} WHERE LabFacilityID IN {self.ids_to_show}"
        elif table == "UPbAnalyses":
            sql_query = f"SELECT COUNT(*) FROM UPbAnalyses WHERE UPbAnalysisID IN {self.ids_to_show}"
        else:
            sql_query = f"SELECT COUNT(*) FROM {table} WHERE {table[:-1]}ID IN {self.ids_to_show}"

        # Execute the query
        if not query.exec(sql_query):
            # Handle query execution error
            print("Failed to execute query:", query.lastError().text())
            return 0

        # Fetch the count
        if query.next():
            return query.value(0)

        return 0

    def get_total_records_2(self, dbTable_comboBox):
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
            sql_query = f"SELECT COUNT(*) FROM UPbAnalyses WHERE UPbAnalysisID IN {self.id_condition}"
        else:
            sql_query = f"SELECT COUNT(*) FROM {table} WHERE {table[:-1]}ID IN {self.id_condition}"

        # Execute the query
        if not query.exec(sql_query):
            # Handle query execution error
            print("Failed to execute query:", query.lastError().text())
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

        # Execute the query
        if not query.exec():
            # Handle query execution error
            print("Failed to execute query:", query.lastError().text())
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

        # Remove spaces from display names
        table = TxM.remove_spaces(table_name)
        offset = self.current_page_1 * self.rows_per_page_1
        if table == 'Samples':
            self.switch_to_table(db_stackedWidget)

            # todo very slow because of the sample view
            # todo sample tables across entire db is broken.
            sample_model = TbC.SampleAgeTableModel()
            query = TbC.SampleTableModel().setupQuery(self.ids_to_show, self.rows_per_page_1, offset)
            sample_model.setQuery(QtS.QSqlQuery(query))

            sample_proxy_model = QtC.QSortFilterProxyModel()
            sample_proxy_model.setSourceModel(sample_model)

            sample_proxy_model.setFilterKeyColumn(-1)  # search all columns
            dbTable_tableView.setModel(sample_proxy_model)
            dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            # self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.OnManualSubmit)
            # Signal for search bar
            self.search_lineEdit.textChanged.connect(lambda: self.search(self.search_lineEdit, sample_proxy_model))
        elif table == 'Aliquots':
            self.switch_to_table(db_stackedWidget)

            aliquot_model = TbC.AliquotTableModel()
            query = TbC.AliquotTableModel().setupQuery()
            aliquot_model.setQuery(QtS.QSqlQuery(query))

            aliquot_proxy_model = QtC.QSortFilterProxyModel()
            aliquot_proxy_model.setSourceModel(aliquot_model)

            aliquot_proxy_model.setFilterKeyColumn(-1)  # search all columns
            dbTable_tableView.setModel(aliquot_proxy_model)
            dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            # self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.OnManualSubmit)
            self.search_lineEdit.textChanged.connect(lambda: self.search(self.search_lineEdit, sample_proxy_model))
        elif table == 'Spots':
            self.switch_to_table(db_stackedWidget)
            spot_model = TbC.SpotTableModel()
            query = TbC.AliquotTableModel().setupQuery()
            spot_model.setQuery(QtS.QSqlQuery(query))

            spot_proxy_model = QtC.QSortFilterProxyModel()
            spot_proxy_model.setSourceModel(spot_model)

            spot_proxy_model.setFilterKeyColumn(-1)  # search all columns
            dbTable_tableView.setModel(spot_proxy_model)
            dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            # self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.OnManualSubmit)
            self.search_lineEdit.textChanged.connect(lambda: self.search(self.search_lineEdit, sample_proxy_model))
        elif table == 'UPbAnalyses':
            self.switch_to_table(db_stackedWidget)
            sample_model = QtS.QSqlQueryModel()
            sample_proxy_model = QtC.QSortFilterProxyModel()
            sample_model.setQuery(
                f"SELECT * FROM UPbAnalyses WHERE UPbAnalysisID IN {self.ids_to_show} LIMIT {self.rows_per_page_1} OFFSET {offset}")
            sample_proxy_model.setSourceModel(sample_model)
            sample_proxy_model.setFilterKeyColumn(-1)  # search all columns
            dbTable_tableView.setModel(sample_proxy_model)
            dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            # self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.OnManualSubmit)
            self.search_lineEdit.textChanged.connect(lambda: self.search(self.search_lineEdit, sample_proxy_model))
        else:
            print(f"Error {table}: Tried to switch to a table with no table or tree..Don't know how it got here")

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

        table_name = dbTable_comboBox.currentText()
        table = TxM.remove_spaces(table_name)

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

                table_condition = ''
                sql = f'SELECT DISTINCT {table}.* FROM Samples '
                sql += SQLUtils.get_join_from_table({table})
                if condition_ids:
                    if table_type == 'sample':
                        table_condition = f" WHERE Samples.SampleID IN ({', '.join(condition_ids)})"
                    elif table_type == 'aliquot':
                        table_condition = f" WHERE Aliquots.AliquotID IN ({', '.join(condition_ids)})"
                    elif table_type == 'spot':
                        table_condition = f" WHERE Spots.SpotID IN ({', '.join(condition_ids)})"
                    elif table_type == 'upbdata':
                        table_condition = f" WHERE UPbAnalyses.UPbAnalysisID IN ({', '.join(condition_ids)})"
                    # "(19,39,58)"

                sql += table_condition
                query = QSqlQuery()
                ids_to_show = []

                # Execute the query
                if query.exec(sql):
                    while query.next():  # Iterate through all results
                        row_id = query.value(0)
                        if row_id is not None and row_id is not '':
                            ids_to_show.append(str(row_id))
                else:
                    print(sql)
                    print("Failed to execute query:", query.lastError().text())

                # Update the id_condition attribute

                self.id_condition = f'({", ".join(ids_to_show)}'
                self.id_condition = self.id_condition + ')'
                print(f'id condition: {self.id_condition}')

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
            tree_model = TrC.TreeModel(model, None)

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

        elif table in SQLUtils.user_viewable_tables:
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
            else:
                print(f"SELECT * FROM {table} WHERE {table[0:-1]}ID IN {self.id_condition} ORDER BY {table[0:-1]}ID LIMIT {self.rows_per_page_2} OFFSET {offset}")
                model.setQuery(
                    f"SELECT * FROM {table} WHERE {table[0:-1]}ID IN {self.id_condition} ORDER BY {table[0:-1]}ID LIMIT {self.rows_per_page_2} OFFSET {offset}")
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

        else:
            print(f"Error {table}: Tried to switch to a table with no table or tree..Don't know how it got here")

        # self.total_records_2 = self.get_total_records_2(self.dbTable_comboBox_2)
        # # Update page info label
        # start_record = offset + 1
        # end_record = min(offset + self.rows_per_page_2, self.total_records_2)
        # self.page_info_label_2.setText(f"Showing records {start_record} - {end_record} of {self.total_records_2}")
        # edit_pushButton.setText(f"Edit {table_name}")


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

    def edit_popup(self, db_stackedWidget, dbTable_tableView, dbTable_treeView, dbTable_comboBox, edit_pushButton):
        dbTable_comboBox: QComboBox
        table_name = dbTable_comboBox.currentText()
        table = TxM.remove_spaces(table_name)
        # todo fix this for working with new sample edit view
        if table_name == 'Samples':
            dlg = EditTable(self.db, self.sample_model, table_name)
        elif table_name == 'Aliquots' or table_name == 'Spots' or table_name == 'UPb Data':
            return
        elif table in self.dbtree_list:
            dlg = EditTable(self.db, self.tree_model, table_name)
        else:
            dlg = EditTable(self.db, self.model, table_name)
        dlg.exec()
        self.display_table(db_stackedWidget, dbTable_tableView, dbTable_treeView, dbTable_comboBox, edit_pushButton)

    def saveWindowState(self):
        self.settings.setValue("ui/GeoChronMain/pos", self.pos())
        self.settings.setValue("ui/GeoChronMain/size", self.size())

    def loadWindowState(self):
        self.move(self.settings.value("ui/GeoChronMain/pos", defaultValue=QPoint(410, 241)))
        self.resize(self.settings.value("ui/GeoChronMain/size", defaultValue=QSize(810, 569)))

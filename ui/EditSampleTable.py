import sys
import time
from operator import index

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.uic import loadUi
import Functions.Text_manipulations as TxM
import Functions.Errors as Er
from Functions.Tree_classes import TreeModel, CheckableTreeCombobox, CheckableTreeModel, CheckableTreeView
from Functions.Table_classes import SampleTableModel
import Functions.Text_manipulations as TxM
from ui.AddTags import AddTags
import Functions.Table_classes as TbC

class EditSampleTable(QtW.QDialog):
    def __init__(self, database, sample_model: QtS.QSqlQueryModel):
        super().__init__()

        tags_ui_file = "ui/EditSampleTable.ui"
        loadUi(tags_ui_file, self)
        self.table = 'Samples'
        self.db = database
        self.sample_model = sample_model
        self.table_model = QtS.QSqlTableModel()
        self.combo = CheckableTreeCombobox()
        self.combo_index = QtC.QModelIndex()
        # self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnFieldChange)
        self.filter_proxy_model = QtC.QSortFilterProxyModel()
        self.msg = QtW.QMessageBox(self)
        self.display_table()
        self.createSavepoint()

        self.filter_proxy_model.dataChanged.connect(self.update_model)
        # self.combo.closing.connect(self.destroy_dropdown)
        # self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        self.cancel_pushButton.clicked.connect(self.rollback)
        self.edit_tableView.clicked.connect(self.display_dropdown)

    def update_model(self):
        if not self.sample_model.submitAll():
            errtxt = self.sample_model.lastError().text()
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def createSavepoint(self):
        query = QtS.QSqlQuery(self.db)
        if query.exec('SAVEPOINT before_edit') is False:
            errtxt = Er.savepoint_fail(self.table)
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def releaseSavepoint(self):
        query = QtS.QSqlQuery(self.db)
        if query.exec('RELEASE SAVEPOINT before_edit') is False:
            errtxt = Er.savepoint_release_fail(self.table)
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def get_items(self, table):
        headers = []
        items = []
        query = QtS.QSqlQuery(self.db)
        if query.exec(f"SELECT name from pragma_table_info('{table}')"):
            while query.next():
                headers.append(query.value(0))
            name_header = headers[1]
            if query.exec(f"SELECT {name_header} FROM {table}"):
                while query.next():
                    items.append(query.value(0))
                return items

    def display_table(self):
        self.filter_proxy_model.setSourceModel(self.sample_model)
        self.filter_proxy_model.setFilterKeyColumn(-1)  # search all columns
        self.edit_tableView: QtW.QTableView
        # self.edit_tableView.setModel(self.sample_model)
        self.edit_tableView.setModel(self.filter_proxy_model)
        self.edit_tableView.hideColumn(0)  # don't show ID column
        self.edit_tableView.resizeColumnsToContents()
        self.edit_tableView.setSortingEnabled(True)

    def display_dropdown(self):
        selected_index = self.edit_tableView.selectedIndexes()
        print(f"Clicked column: {selected_index[0].column()}")
        if len(selected_index) == 1:
            if 23 > selected_index[0].column() > 15:
                # Column header is Age Signatures, Sample Context, Rock Types, Regions, Sampling Methods, Settings, or Units
                header = self.filter_proxy_model.headerData(selected_index[0].column(), QtC.Qt.Orientation.Horizontal,
                                                       QtC.Qt.ItemDataRole.DisplayRole)
                if ' ' in header:
                    table = TxM.remove_spaces(header)
                else:
                    table = header
            else:
                return
            self.combo_index = selected_index[0]
            self.combo = CheckableTreeCombobox()
            self.combo.closing.connect(self.destroy_dropdown)
            self.table_model.setTable(table)
            self.table_model.select()
            tree_model = CheckableTreeModel()
            tree_model.setSourceModel(self.table_model)
            row = self.combo_index.row()
            sample_ID = self.filter_proxy_model.index(row, 0).data()
            tree_model.set_sample(sample_ID)
            selected_text = self.combo_index.data(QtC.Qt.ItemDataRole.DisplayRole)
            # print(f"Selected text: {selected_text}")
            self.combo.setModel(tree_model)
            self.combo.set_line_edit_text(selected_text)
            self.edit_tableView.setIndexWidget(self.combo_index, self.combo)
            # print("showing popup")
            self.combo.showPopup()

    def destroy_dropdown(self):
        self.edit_tableView: QtW.QTableView
        if self.combo is not None:
            # print("Start destroying dropdown")
            self.combo.closing.disconnect(self.destroy_dropdown)
            checked_text = self.combo.lineEdit().text()
            checked_list = checked_text.split(',')
            print(f"Checked text: {checked_text}")
            print(f"Checked list: {checked_list}")
            self.combo.model().update_db(checked_list)

            self.verticalLayout.removeWidget(self.combo)
            self.combo.deleteLater()
            self.combo = None

            self.recreate_sample_model()
            # Only update the model if the text has changed
            # previous_text = self.combo_index.data(QtC.Qt.ItemDataRole.DisplayRole)
            # if checked_text != previous_text:
            #     self.recreate_sample_model()
            # self.combo_index = QtC.QModelIndex()

    def recreate_sample_model(self):
        query_start_time = time.time()
        query = SampleTableModel().setupQuery()
        self.sample_model.setQuery(QtS.QSqlQuery(query, self.db))
        query_end_time = time.time()
        print(f"Query time: {query_end_time - query_start_time}")
        for col in range(self.sample_model.columnCount()):
            header = TxM.add_spaces_camel(
                self.sample_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            self.sample_model.setHeaderData(col, QtC.Qt.Orientation.Horizontal, header, QtC.Qt.ItemDataRole.DisplayRole)
        self.display_table()

    # def update_edited_row(self):
    # todo: update the row in the sample table with the new values

    def rollback(self):
        query = QtS.QSqlQuery(self.db)
        if query.exec('ROLLBACK TO SAVEPOINT before_edit') is False:
            errtxt = Er.rollback_fail(self.table)
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
        else:
            self.reject()

    def commit(self):
        self.releaseSavepoint()
        self.msg.information(self, 'Success', 'Changes saved', QtW.QMessageBox.StandardButton.Ok)
        self.close()

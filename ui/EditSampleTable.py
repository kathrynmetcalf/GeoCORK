import sys
from operator import index

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.uic import loadUi
import Functions.Text_manipulations as TxM
import Functions.Errors as Er
from Functions.Tree_classes import TreeModel, TreeCombobox
from ui.AddTags import AddTags
import Functions.Table_classes as TbC

class EditSampleTable(QtW.QDialog):
    def __init__(self, database, model):
        super().__init__()

        # Define any widgets here
        tags_ui_file = "ui/EditSampleTable.ui"
        loadUi(tags_ui_file, self)
        self.table = 'Samples'
        # self.create_comboboxes()
        self.db = database
        self.model = model
        self.table_model = QtS.QSqlTableModel()
        self.combo = TreeCombobox()
        # self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnFieldChange)
        self.filter_proxy_model = QtC.QSortFilterProxyModel()
        self.filter_proxy_model.setSourceModel(self.model)
        self.filter_proxy_model.setFilterKeyColumn(-1)  # search all columns
        self.msg = QtW.QMessageBox(self)
        self.display_table()
        self.createSavepoint()

        self.filter_proxy_model.dataChanged.connect(self.update_model)
        self.combo.closed.connect(self.destroy_combobox)
        # self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        self.cancel_pushButton.clicked.connect(self.rollback)
        self.edit_tableView.clicked.connect(self.display_combobox)

    def update_model(self):
        if not self.model.submitAll():
            errtxt = self.model.lastError().text()
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

    # def create_comboboxes(self):
    #     columns = self.get_items('Columns')
    #     comboColumns = SC.comboList(self, columns)

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
        self.edit_tableView: QtW.QTableView
        self.edit_tableView.setModel(self.model)
        # self.edit_tableView.setModel(self.filter_proxy_model)
        self.edit_tableView.hideColumn(0)  # don't show ID column
        self.edit_tableView.resizeColumnsToContents()
        # columns = self.get_items('Columns')
        # combo_columns = TbC.ComboList(self, columns)
        # index = self.edit_tableView.model().index(0,11)
        # self.edit_tableView.setIndexWidget(index,combo_columns)
        # self.edit_tableView.setSortingEnabled(True)

    def display_combobox(self):
        selected_index = self.edit_tableView.selectedIndexes()
        if len(selected_index) == 1:
            if selected_index[0].column() == 22:
                table = "Units"
                tree_model = TreeModel()
                self.table_model.setTable(table)
                self.table_model.select()
                tree_model.setSourceModel(self.table_model)
                self.combo.setModel(tree_model)
                self.edit_tableView.setIndexWidget(selected_index[0], self.combo)
                self.combo.showPopup()

    def destroy_combobox(self):
        self.layout().removeWidget(self.combo)
        self.combo.deleteLater()
        self.combo = None

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

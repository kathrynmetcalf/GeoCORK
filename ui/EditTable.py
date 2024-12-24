import sys
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.uic import loadUi
import Functions.Text_manipulations as TxM
import Functions.Errors as Er
import Functions.Table_classes as TbC
from ui.AddTags import AddTags

# todo: figure out how to change non-text values to none or null
class EditTable(QtW.QDialog):
    def __init__(self, database, model, table_name):
        super().__init__()

        # Define any widgets here
        tags_ui_file = "ui/EditTable.ui"
        loadUi(tags_ui_file, self)
        self.table = TxM.remove_spaces(table_name)
        if self.table == 'Samples' or self.table == 'Sources' or self.table == 'Aliquots' or self.table == 'UPbData':
            pass
        else:
            self.db = database
            self.model = model
            self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnRowChange)
            self.filter_proxy_model = TbC.VerifiableProxyModel()
            self.filter_proxy_model.setSourceModel(self.model)
            self.filter_proxy_model.setFilterKeyColumn(-1)  # search all columns
            self.msg = QtW.QMessageBox(self)
            self.display_table()
            self.model.submitAll()
            self.createSavepoint()

            self.filter_proxy_model.dataChanged.connect(self.update_model)
            self.add_pushButton.clicked.connect(self.add_popup)
            self.commit_pushButton.clicked.connect(self.commit)
            self.cancel_pushButton.clicked.connect(self.rollback)


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

    def display_table(self):
        self.edit_tableView.setModel(self.model)
        # self.edit_tableView.setModel(self.filter_proxy_model)
        self.edit_tableView.hideColumn(0)  # don't show ID column
        self.edit_tableView.resizeColumnsToContents()
        # self.edit_tableView.setSortingEnabled(True)

    def add_popup(self):
        if self.table == 'Samples' or self.table == 'Sources' or self.table == 'Aliquots' or self.table == 'UPbData':
            pass
        else:
            dlg = AddTags(self.db, self.model, self.table)
            dlg.exec()
            self.display_table()


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

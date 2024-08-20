import sys
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.uic import loadUi
import Functions.Text_manipulations as TxM
import Functions.Errors as Er
from ui.AddTags import AddTags

class EditTable(QtW.QDialog):
    def __init__(self, database, model, table_name):
        super().__init__()

        # Define any widgets here
        tags_ui_file = "EditTable.ui"
        loadUi(tags_ui_file, self)
        self.db = database
        self.model = model
        self.table = TxM.remove_spaces(table_name)
        self.filter_proxy_model = QtC.QSortFilterProxyModel()
        self.filter_proxy_model.setSourceModel(self.model)
        self.filter_proxy_model.setFilterKeyColumn(-1)  # search all columns
        self.errmsg = QtW.QMessageBox(self)

        if self.table == 'Samples' or self.table == 'Sources' or self.table == 'Aliquots' or self.table == 'UPbData':
            pass
        else:
            self.model: QtS.QSqlTableModel

            self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnManualSubmit)

        self.createSavepoint()

        self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        self.apply_pushButton.clicked.connect(self.apply)
        self.cancel_pushButton.clicked.connect(self.rollback)
        self.filter_proxy_model.dataChanged.connect(self.handleDataChanged)


    def createSavepoint(self):
        query = QtS.QSqlQuery(self.db)
        if query.exec('SAVEPOINT before_edit') is False:
            errtxt = Er.savepoint_fail(self.table)
            self.errmsg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def releaseSavepoint(self):
        query = QtS.QSqlQuery(self.db)
        if query.exec('RELEASE SAVEPOINT before_edit') is False:
            errtxt = Er.savepoint_release_fail(self.table)
            self.errmsg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def handleDataChanged(self, index):
        proxy_model = index.model()
        data = proxy_model.data(index)
        print(f'You updated to: {data}')
        if hasattr(proxy_model, 'mapToSource'):
            # The model in the view is a proxy model
            sourceIndex = proxy_model.mapToSource(index)
        if index.isValid():
            source_index = self.filter_proxy_model.mapToSource(index)
            source_model = self.filter_proxy_model.sourceModel()
            row = source_index.row()
            if row == 1 and index.data() is None:
                errtxt = Er.blank_entry('Name')
                self.errmsg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
            else:
                source_model.setData(source_index, index.data(), QtC.Qt.ItemDataRole.EditRole)



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
            self.errmsg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
        else:
            self.reject()

    def apply(self):
        pass

    def commit(self):
        self.accept()


if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QDialog(sys.argv)  # pass command line arguments
    w = EditTable()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

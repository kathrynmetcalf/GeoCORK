import sys
from pathlib import Path
import sqlite3
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6.uic import loadUi
from Functions.Tree_classes import TreeModel
import Functions.Text_manipulations as TxM
import Functions.Errors as Er

class AddTreeTags(QtW.QDialog):
    def __init__(self, database, table: str, parentID=None, parentRow=None):
        super().__init__()

        # Define any widgets here
        tags_ui_file = "AddTreeTags.ui"
        loadUi(tags_ui_file, self)
        self.db = database
        self.table = table
        self.source_model = QtS.QSqlTableModel()
        self.source_model.setTable(self.table)
        self.tree_proxy_model = TreeModel(self.source_model)
        self.filter_proxy_model = QtC.QSortFilterProxyModel()
        self.filter_proxy_model.setSourceModel(self.tree_proxy_model)
        self.table_name = TxM.add_spaces_camel(self.table)
        self.selectTags_label.setText(self.table_name)

        self.errmsg = QtW.QMessageBox(self)
        self.parentID = parentID
        self.parentRow = parentRow

        self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.tree_proxy_model.setFilterKeyColumn(1)   # search first column only, look for distinct names
        self.newName_lineEdit.textChanged.connect(self.tree_proxy_model.setFilterRegularExpression)

        self.display_tags()
        self.createSavepoint()
        self.ok_pushButton.clicked.connect(self.add_tree_tag)
        self.cancel_pushButton.clicked.connect(self.reject)

    def createSavepoint(self):
        query = QtS.QSqlQuery(self.db)
        if query.exec('SAVEPOINT before_add') is False:
            errtxt = Er.savepoint_fail(self.table)
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def releaseSavepoint(self):
        query = QtS.QSqlQuery(self.db)
        if query.exec('RELEASE SAVEPOINT before_add') is False:
            errtxt = Er.savepoint_release_fail(self.table)
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def display_tags(self):
        self.tags_treeView.setModel(self.filter_proxy_model)
        self.tags_treeView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tags_treeView.hideColumn(1)  # Don't show ID column
        self.tags_treeView.hideColumn(2)  # Don't show parent ID column
        self.tags_treeView.hideColumn(3)  # Don't show parent row column
        self.tags_treeView.resizeColumnsToContents()
        self.tags_treeView.horizontalHeader().setDefaultAlignment(QtC.Qt.AlignmentFlag.AlignLeft)
        # query = QtS.QSqlQuery()

        # Get a list of column names for the selected tree
        self.columns = self.tree_proxy_model.proxyHeaders()

        # Get a list of the existing tag names
        # query.prepare(f'SELECT {self.columns[0]} FROM {self.table}')
        # query.exec()
        # while query.next():
        #     self.existing_names.append(query.value(0))
        # completer = QtW.QCompleter(self.existing_names)
        # self.newName_lineEdit.setCompleter(completer)

    # def clear_warning(self):
    #     self.warning_label.hide()

    def add_top_tree_tag(self):
        name = self.newName_lineEdit.text()
        description = self.newDescription_lineEdit.text()
        self.tree_proxy_model.insertItem(name, description, self.parentID, self.parentRow)
        # query = QtS.QSqlQuery()
        # query.prepare(f'INSERT INTO {self.table}({self.columns[1]}, {self.columns[2]}) VALUES(?, ?)')
        # query.addBindValue(name)
        # query.addBindValue(description)
        # if query.exec():
        #     self.model.select()
        #     self.newName_lineEdit.clear()
        #     self.newDescription_lineEdit.clear()
        #     self.display_tags()
        #     self.accept()
        # else:
        #     err = query.lastError().text()
        #     header = TxM.add_spaces_camel(self.columns[1])
        #     if 'UNIQUE constraint failed:' in err:
        #         duplicates = []
        #         for entry in self.existing_names:
        #             if name.casefold() == entry.casefold():
        #                 duplicates.append(entry)
        #         errtxt = Er.duplicate_entry(header, duplicates)
        #         self.errmsg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok, QtW.QMessageBox.StandardButton.Ok)
        #     elif 'CHECK constraint failed:' in err:
        #         errtxt = Er.blank_entry(header)
        #         self.errmsg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok,
        #                              QtW.QMessageBox.StandardButton.Ok)
        #     else:
        #         self.errmsg.critical(self, 'Error', err, QtW.QMessageBox.StandardButton.Ok, QtW.QMessageBox.StandardButton.Ok)

        def update_proxy(self):
            if self.filter_proxy_model.sourceModel() == self.tree_proxy_model:
                self.tree_proxy_model.deleteLater()
            self.tree_proxy_model = TrC.TreeModel(self.model)
            self.tree_proxy_model.dataMoved.connect(self.update_proxy)
            self.filter_proxy_model.setSourceModel(self.tree_proxy_model)
            self.display_tree()

        def rollback(self):
            query = QtS.QSqlQuery(self.db)
            if query.exec('ROLLBACK TO SAVEPOINT before_add') is False:
                errtxt = Er.rollback_fail(self.table)
                self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
            else:
                self.reject()
            # self.model.revertAll()
            self.msg.information(self, 'Cancelled', 'No changes saved', QtW.QMessageBox.StandardButton.Ok)
            self.close()

        # def apply(self):
        #     pass
        #
        def commit(self):
            self.releaseSavepoint()
            self.msg.information(self, 'Success', 'Changes saved', QtW.QMessageBox.StandardButton.Ok)
            self.close()

if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QDialog(sys.argv)  # pass command line arguments
    w = AddTreeTags()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

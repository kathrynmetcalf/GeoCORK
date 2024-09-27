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
import Functions.Tree_classes as TrC

class AddTreeTags(QtW.QDialog):
    def __init__(self, database: QtS.QSqlDatabase, table: str, item_id=None, parent_id=None, parent_row=None):
        super().__init__()

        # Define any widgets here
        tags_ui_file = "AddTreeTags.ui"
        loadUi(tags_ui_file, self)
        self.db = database
        self.table = table
        self.source_model = QtS.QSqlTableModel()
        self.source_model.setTable(self.table)
        self.source_model.select()
        self.id_header = self.source_model.record().fieldName(0)
        self.parent_id_header = self.source_model.record().fieldName(1)
        self.parent_row_header = self.source_model.record().fieldName(2)
        self.tree_model = TreeModel(self.source_model)
        self.tree_proxy_model = QtC.QSortFilterProxyModel()
        self.tree_proxy_model.setSourceModel(self.tree_model)
        self.table_name = TxM.add_spaces_camel(self.table)
        self.selectTags_label.setText(self.table_name)

        self.msg = QtW.QMessageBox(self)
        self.itemID = item_id
        self.parentID = parent_id
        self.parentRow = parent_row

        self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.tree_proxy_model.setFilterKeyColumn(0)   # search first column only, look for distinct names
        self.newName_lineEdit.textChanged.connect(self.search)

        self.clear_warning()
        self.display_tags()
        self.createSavepoint()
        self.tree_model.dataAdded.connect(self.update_proxy)
        self.ok_pushButton.clicked.connect(self.add_tree_tag)
        self.cancel_pushButton.clicked.connect(self.rollback)
        self.finish_pushButton.clicked.connect(self.commit)

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

    def add_label(self):
        query = QtS.QSqlQuery(self.db)
        if self.parentID:
            query.prepare(
            f'SELECT * FROM {self.table} WHERE {self.id_header} = {self.parentID}')
            query.exec()
            query.next()
            parent_name = query.value(3)
        else:
            parent_name = 'top level'
        if self.itemID:
            query.prepare(
            f'SELECT * FROM {self.table} WHERE {self.id_header} = {self.itemID}')
            query.exec()
            query.next()
            item_name = query.value(3)
        else:
            item_name = 'new item'
        if self.parentRow:
            row_name = f'row {self.parentRow + 1}'
        else:
            row_name = 'new row'
        self.adding_label.setText(f'Adding {item_name} to {parent_name} at {row_name}')

    def display_tags(self):
        self.tags_treeView.setModel(self.tree_proxy_model)
        self.tags_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
        self.tags_treeView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tags_treeView.hideColumn(1)  # Don't show ID column
        self.tags_treeView.hideColumn(2)  # Don't show parent ID column
        self.tags_treeView.hideColumn(3)  # Don't show parent row column
        self.add_label()
        # self.tags_treeView.horizontalHeader().setDefaultAlignment(QtC.Qt.AlignmentFlag.AlignLeft)
        # query = QtS.QSqlQuery()

        # Get a list of column names for the selected tree
        # self.columns = self.tree_proxy_model.proxyHeaders()

        # Get a list of the existing tag names
        # query.prepare(f'SELECT {self.columns[0]} FROM {self.table}')
        # query.exec()
        # while query.next():
        #     self.existing_names.append(query.value(0))
        # completer = QtW.QCompleter(self.existing_names)
        # self.newName_lineEdit.setCompleter(completer)

    def clear_warning(self):
        self.warning_label.hide()

    def search(self):
        self.newName_lineEdit: QtW.QLineEdit
        self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.tree_proxy_model.setRecursiveFilteringEnabled(True)
        search_expression = QtC.QRegularExpression(self.newName_lineEdit.text())
        self.tree_proxy_model.setFilterRegularExpression(search_expression)

    def add_tree_tag(self):
        print('ok clicked')
        name = self.newName_lineEdit.text()
        description = self.newDescription_lineEdit.text()
        if self.tree_model.insertItem(name, description, self.parentID, self.parentRow):
            self.update_proxy()
            self.newName_lineEdit.clear()
            self.newDescription_lineEdit.clear()

    def update_proxy(self):
        if self.tree_proxy_model.sourceModel() == self.tree_model:
            self.tree_model.deleteLater()
        self.tree_model = TrC.TreeModel(self.source_model)
        self.tree_model.dataMoved.connect(self.update_proxy)
        self.tree_proxy_model.setSourceModel(self.tree_model)
        self.display_tags()

    def rollback(self):
        query = QtS.QSqlQuery(self.db)
        if query.exec('ROLLBACK TO SAVEPOINT before_add') is False:
            errtxt = Er.rollback_fail(self.table)
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
        else:
            self.reject()
        # self.model.revertAll()
        self.msg.information(self, 'Cancelled', 'No items added', QtW.QMessageBox.StandardButton.Ok)
        self.close()

    def commit(self):
        self.releaseSavepoint()
        self.msg.information(self, 'Success', 'Items added', QtW.QMessageBox.StandardButton.Ok)
        self.close()

if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QDialog(sys.argv)  # pass command line arguments
    w = AddTreeTags()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

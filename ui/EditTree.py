import sys
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.uic import loadUi
import Functions.Text_manipulations as TxM
import Functions.Errors as Er
import Functions.Tree_classes as TrC
from ui.AddTags import AddTags


class EditTree(QtW.QDialog):
    def __init__(self, database, model: QtS.QSqlTableModel, table_name):
        super().__init__()

        # Define any widgets here
        tags_ui_file = "EditTable.ui"
        loadUi(tags_ui_file, self)
        self.db = database
        self.model = model
        self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnFieldChange)
        self.tree_proxy_model = TrC.TreeModel(self.model)
        self.table = TxM.remove_spaces(table_name)
        # self.filter_proxy_model = QtC.QSortFilterProxyModel()
        # self.filter_proxy_model.setSourceModel(self.tree_proxy_model)
        # self.filter_proxy_model.setFilterKeyColumn(-1)  # search all columns

        # self.errmsg = QtW.QMessageBox(self)
        self.display_tree()
        # self.createSavepoint()

        # self.edit_treeView.clicked.connect(self.whichCell)
        # self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        # self.apply_pushButton.clicked.connect(self.apply)
        self.cancel_pushButton.clicked.connect(self.rollback)
        # self.tree_proxy_model.dataChanged.connect(self.handleDataChanged)

    # def createSavepoint(self):
    #     query = QtS.QSqlQuery(self.db)
    #     if query.exec('SAVEPOINT before_edit') is False:
    #         errtxt = Er.savepoint_fail(self.table)
    #         self.errmsg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
    #
    # def releaseSavepoint(self):
    #     query = QtS.QSqlQuery(self.db)
    #     if query.exec('RELEASE SAVEPOINT before_edit') is False:
    #         errtxt = Er.savepoint_release_fail(self.table)
    #         self.errmsg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    # def whichCell(self, index: QtC.QModelIndex):
    #     if index.isValid():
    #         item = self.tree_proxy_model.getItem(index)
    #         source_index = self.tree_proxy_model.mapToSource(index)
    #         print(f'Value in source table is {self.model.data(source_index)}')

    # def handleDataChanged(self, top_left: QtC.QModelIndex, bottom_right: QtC.QModelIndex, roles):
    #     self.tree_proxy_model.inv

            # id_index = self.filter_proxy_model.ind # index of the ID column
            # print(f'The primary key is {self.filter_proxy_model.sibling(row, column, index)}')  # right now getting QModelIndex object instead of ID#
        # if index.isValid():
        #     source_index = self.filter_proxy_model.mapToSource(index)
        #     source_model = self.filter_proxy_model.sourceModel()
        #     if self.table == 'Samples' or self.table == 'Sources' or self.table == 'Aliquots' or self.table == 'UPbData':
        #         pass
        #     elif self.table in self.dbtree_list:
        #         pass
        #     else:
        #         if row == 1 and index.data() is None:
        #             errtxt = Er.blank_entry('Name')
        #             self.errmsg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
        #         else:
        #             source_model.setData(source_index, index.data(), QtC.Qt.ItemDataRole.EditRole)

    def display_tree(self):
        self.edit_treeView.setModel(self.tree_proxy_model)
        self.edit_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
        self.edit_treeView.hideColumn(1)  # don't show ID column
        self.edit_treeView.hideColumn(2)  # don't show parent ID column
        self.edit_treeView.setSortingEnabled(True)

    def add_popup(self):
        if self.table == 'Samples' or self.table == 'Sources' or self.table == 'Aliquots' or self.table == 'UPbData':
            pass
        elif self.table in self.dbtree_list:
            dlg = AddTags(self.db, self.model, self.table)
            dlg.exec()
            self.display_table()
        else:
            dlg = AddTags(self.db, self.model, self.table)
            dlg.exec()
            self.display_table()

    # def contextMenuEvent(self, pos):
    #     self.model: TrC.TreeModel
    #     if (self.model.
    #         ().selection().indexes()):
    #         for i in self.selectionModel().selection().indexes():
    #             row, column = i.row(), i.column()
    #         menu = QtGui.QMenu()
    #         childAction = menu.addAction("Add child")
    #         parentAction = menu.addAction("Add parent")
    #         action = menu.exec_(self.mapToGlobal(pos))
    #         if action == childAction:
    #             # add child
    #         if action == parentAction:
    #             # add parent
    #
    #
    def rollback(self):
        # query = QtS.QSqlQuery(self.db)
        # if query.exec('ROLLBACK TO SAVEPOINT before_edit') is False:
        #     errtxt = Er.rollback_fail(self.table)
        #     self.errmsg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
        # else:
        #     self.reject()
        self.model.revertAll()
        self.close()

    # def apply(self):
    #     pass
    #
    def commit(self):
        self.model.submitAll()


if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QDialog(sys.argv)  # pass command line arguments
    w = EditTree()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

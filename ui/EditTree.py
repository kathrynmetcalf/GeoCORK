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
        tags_ui_file = "EditTree.ui"
        loadUi(tags_ui_file, self)
        self.db = database
        self.model = model
        self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnFieldChange)
        self.tree_proxy_model = TrC.TreeModel(self.model)
        self.table = TxM.remove_spaces(table_name)
        self.filter_proxy_model = QtC.QSortFilterProxyModel()
        self.filter_proxy_model.setSourceModel(self.tree_proxy_model)
        self.filter_proxy_model.setFilterKeyColumn(-1)  # search all columns

        self.msg = QtW.QMessageBox(self)
        self.display_tree()
        self.createSavepoint()

        self.tree_proxy_model.dataMoved.connect(self.update_proxy)
        # self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        self.cancel_pushButton.clicked.connect(self.rollback)

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

    def display_tree(self):
        self.edit_treeView.setModel(self.filter_proxy_model)
        self.edit_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
        self.edit_treeView.hideColumn(1)  # don't show ID column
        self.edit_treeView.hideColumn(2)  # don't show parent ID column
        self.edit_treeView.hideColumn(3)  # don't show parent row column
        self.edit_treeView.setSortingEnabled(False)
        self.edit_treeView.setDragEnabled(True)
        self.edit_treeView.setAcceptDrops(True)
        self.edit_treeView.setDropIndicatorShown(True)
        self.edit_treeView.setDragDropMode(QtW.QAbstractItemView.DragDropMode.InternalMove)
        self.edit_treeView.setDefaultDropAction(QtC.Qt.DropAction.MoveAction)
        self.edit_treeView.setSelectionMode(QtW.QAbstractItemView.SelectionMode.ExtendedSelection)

    def update_proxy(self):
        if self.filter_proxy_model.sourceModel() == self.tree_proxy_model:
            self.tree_proxy_model.deleteLater()
        self.tree_proxy_model = TrC.TreeModel(self.model)
        self.tree_proxy_model.dataMoved.connect(self.update_proxy)
        self.filter_proxy_model.setSourceModel(self.tree_proxy_model)
        self.display_tree()

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


    def rollback(self):
        query = QtS.QSqlQuery(self.db)
        if query.exec('ROLLBACK TO SAVEPOINT before_edit') is False:
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
    w = EditTree()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

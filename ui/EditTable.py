import sys
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.uic import loadUi
import Functions.Text_manipulations as TxM
from ui.AddTags import AddTags

class EditTable(QtW.QDialog):
    def __init__(self, database, model, table_name, tree_list, table_type):
        super().__init__()

        # Define any widgets here
        tags_ui_file = "EditTable.ui"
        loadUi(tags_ui_file, self)
        self.db = database
        self.model = model
        self.dbtree_list = tree_list
        self.table_type = table_type  # table or tree
        self.table = TxM.remove_spaces(table_name)
        self.filter_proxy_model = QtC.QSortFilterProxyModel()
        self.filter_proxy_model.setSourceModel(self.model)
        self.filter_proxy_model.setFilterKeyColumn(-1)  # search all columns

        if self.table_type == 'table':
            self.display_table()
        if self.table_type == 'tree':
            self.display_tree()

        if self.table == 'Samples' or self.table == 'Sources' or self.table == 'Aliquots' or self.table == 'UPbData':
            pass
        elif self.table in self.dbtree_list:
            pass
        else:
            self.model: QtS.QSqlTableModel
            self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnManualSubmit)
            self.model.dataChanged.connect(self.change_notice)

        self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        self.apply_pushButton.clicked.connect(self.apply)
        self.cancel_pushButton.clicked.connect(self.rollback)

    def change_notice(self):
        print('Change detected')

    def display_table(self):
        self.switch_to_table()
        self.edit_tableView.setModel(self.model)
        # self.edit_tableView.setModel(self.filter_proxy_model)
        self.edit_tableView.hideColumn(0)  # don't show ID column
        self.edit_tableView.resizeColumnsToContents()
        # self.edit_tableView.setSortingEnabled(True)

    def display_tree(self):
        self.switch_to_tree()
        self.edit_treeView.setModel(self.filter_proxy_model)
        self.edit_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
        self.edit_treeView.hideColumn(1)  # don't show ID column
        self.edit_treeView.hideColumn(2)  # don't show parent ID column
        self.edit_treeView.setSortingEnabled(True)
    def switch_to_table(self):
        """
        Sets the current widget to a table view
        :return:
        """
        self.edit_stackedWidget.setCurrentWidget(self.edit_table)

    def switch_to_tree(self):
        """
        Sets the current widget to a tree view
        :return:
        """
        self.edit_stackedWidget.setCurrentWidget(self.edit_tree)

    def add_popup(self):
        if self.table == 'Samples' or self.table == 'Sources' or self.table == 'Aliquots' or self.table == 'UPbData':
            pass
        elif self.table in self.dbtree_list:
            dlg = AddTags(self.db, self.tree_model, self.table)
            dlg.exec()
            self.display_table()
        else:
            dlg = AddTags(self.db, self.model, self.table)
            dlg.exec()
            self.display_table()

    def rollback(self):
        self.rejected()

    def apply(self):
        pass

    def commit(self):
        if self.table == 'Samples' or self.table == 'Sources' or self.table == 'Aliquots' or self.table == 'UPbData':
            success = True
        elif self.table in self.dbtree_list:
            success = True
        else:
            success = self.model.submitAll()
            err = self.model.lastError()

        if success:
            self.accept()
        else:
            error_popup = QtW.QErrorMessage()
            error_popup.showMessage(err.text())

if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QDialog(sys.argv)  # pass command line arguments
    w = EditTable()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

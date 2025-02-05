import os
import sys
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.uic import loadUi
from Functions.Settings_manager import settings
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Database_manager import update_database
from Functions.Table_classes import set_table
import Functions.Text_manipulations as TxM
import Functions.Errors as Er
import Functions.Tree_classes as TrC
from ui.AddTreeTags import AddTreeTags


class EditTree(QtW.QDialog):
    def __init__(self, table_name):
        super().__init__()

        # Define any widgets here
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "EditTree.ui")
        loadUi(sources_ui_file, self)

        self.model = QtS.QSqlTableModel()
        set_table(self.model, table_name)
        self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnFieldChange)
        self.tree_model = TrC.TreeModel(self.model)
        self.table = TxM.remove_spaces(table_name)
        self.tree_proxy_model = QtC.QSortFilterProxyModel()
        self.tree_proxy_model.setSourceModel(self.tree_model)
        self.tree_proxy_model.setFilterKeyColumn(-1)  # search all columns

        self.edit_treeView.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.edit_treeView.customContextMenuRequested.connect(self.show_context_menu)

        self.msg = QtW.QMessageBox(self)
        self.display_tree()
        create_savepoint('before_edit')

        self.close_by_dialog = False
        self.search_lineEdit.textChanged.connect(self.search)
        self.tree_model.dataEdited.connect(self.update_proxy)
        self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        self.cancel_pushButton.clicked.connect(self.discard_question)

    def display_tree(self):
        self.edit_treeView.setModel(self.tree_proxy_model)
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
        TrC.restore_expanded_state(self.table, self.tree_proxy_model, self.edit_treeView)

    def search(self):
        self.search_lineEdit: QtW.QLineEdit
        self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.tree_proxy_model.setRecursiveFilteringEnabled(True)
        search_expression = QtC.QRegularExpression(self.search_lineEdit.text())
        self.tree_proxy_model.setFilterRegularExpression(search_expression)

    def show_context_menu(self, pos):
        indexes = self.edit_treeView.selectedIndexes()
        if not indexes:
            return
        item_ids, parent_ids, parent_rows = TrC.get_selected_ids(self.tree_proxy_model, indexes)
        menu = TrC.TreeContextMenu()
        menu.set_view(self.edit_treeView)
        action = menu.exec(self.edit_treeView.viewport().mapToGlobal(pos))
        if action and action.text() == 'Insert above':
            row = parent_rows[0]
            parent_id = parent_ids[0]
            self.add_popup(None, parent_id, row)
        elif action and action.text() == 'Insert below':
            row = parent_rows[0]+1
            parent_id = parent_ids[0]
            self.add_popup(None, parent_id, row)
        elif action and action.text() == 'Add child':
            parent_id = item_ids[0]
            self.add_popup(None, parent_id)
        elif action and action.text() == 'Add parent':
            self.add_parent(item_ids, parent_ids, parent_rows)
        elif action and action.text() == 'Delete':
            if self.delete_question() is True:
                n_item = 0
                for item_id in item_ids:
                    parent_id = parent_ids[n_item]
                    parent_row = parent_rows[n_item]
                    self.tree_model.removeItem(item_id, parent_row, parent_id)
                    n_item += 1
        elif action and ('Expand' in action.text() or 'Collapse' in action.text()):
            TrC.expand_collapse(self.edit_treeView, action)

    def update_proxy(self):
        if self.tree_proxy_model.sourceModel() == self.tree_model:
            self.tree_model.deleteLater()
        self.tree_model = TrC.TreeModel(self.model)
        self.tree_model.dataEdited.connect(self.update_proxy)
        self.tree_proxy_model.setSourceModel(self.tree_model)
        self.display_tree()

    def add_popup(self, item_ID = None, parent_id = None, parent_row = None, add_item: str = 'child', *argv):
        TrC.save_expanded_state(self.table, self.tree_proxy_model, self.edit_treeView)
        if add_item == 'parent':
            new_child_ids = argv[0]
            new_parent_rows = argv[1]
            dlg = AddTreeTags(self.table, add_item, item_ID, parent_id, parent_row, new_child_ids, new_parent_rows)
        else:
            dlg = AddTreeTags(self.table, add_item, item_ID, parent_id, parent_row)
        dlg.exec()
        self.update_proxy()

    def add_parent(self, item_ids: list, parent_ids: list, parent_rows: list):
        TrC.save_expanded_state(self.table, self.tree_proxy_model, self.edit_treeView)
        n_item = 0
        new_child_ids = []
        new_parent_rows = []
        for item in range(len(item_ids)):
            item_id = item_ids[item]
            parent_id = parent_ids[item]
            if not parent_id in item_ids:
                # This is a child of the new parent, not a grandchild or lower
                new_child_ids.append(item_id)
                new_parent_rows.append(n_item)
                n_item += 1
        # Find the top child and get its parent and parent row, that will become the position of the new parent
        output = self.tree_model.top_node(new_child_ids)
        parent_id = output[0]
        row = output[1]
        self.add_popup(None, parent_id, row, 'parent', new_child_ids, new_parent_rows)

    def delete_question(self):
        TrC.save_expanded_state(self.table, self.tree_proxy_model, self.edit_treeView)
        msg_box = QtW.QMessageBox()
        msg_box.setIcon(QtW.QMessageBox.Icon.Question)
        msg_box.setText('Are you sure you want to delete these items and all children?')
        msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

    def discard_question(self):
        msg_box = QtW.QMessageBox()
        msg_box.setIcon(QtW.QMessageBox.Icon.Question)
        msg_box.setText('Are you sure you want to discard all changes?')
        msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            self.rollback()
        else:
            pass

    def rollback(self):
        rollback_savepoint('before_edit')
        TrC.save_expanded_state(self.table, self.tree_proxy_model, self.edit_treeView)
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        release_savepoint('before_edit')
        update_database()
        TrC.save_expanded_state(self.table, self.tree_proxy_model, self.edit_treeView)
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def closeEvent(self, event: QtG.QCloseEvent):
        if not self.close_by_dialog:
            self.discard_question()
            event.ignore()
        else:
            event.accept()

if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QDialog(sys.argv)  # pass command line arguments
    w = EditTree()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

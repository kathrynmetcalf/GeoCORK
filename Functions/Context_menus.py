import PyQt6
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG

def get_selected_ids(selected_model: QtC.QAbstractItemModel | QtC.QAbstractProxyModel, indexes: list):
    item_ids = []
    parent_ids = []
    parent_rows = []
    for index in indexes:
        if index.column() == 0:
            item_id = selected_model.data(index.siblingAtColumn(1), QtC.Qt.ItemDataRole.DisplayRole)
            parent_id = selected_model.data(index.siblingAtColumn(2), QtC.Qt.ItemDataRole.DisplayRole)
            parent_row = selected_model.data(index.siblingAtColumn(3), QtC.Qt.ItemDataRole.DisplayRole)
            item_ids.append(item_id)
            parent_ids.append(parent_id)
            parent_rows.append(parent_row)
    return item_ids, parent_ids, parent_rows

class TreeContextMenu(QtW.QMenu):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.tree_view = None
        self.model = None
        self.indexes = None

    def set_view(self, tree_view: QtW.QTreeView, delete_active: bool = True, add_active: bool = True, edit_active: bool = True):
        self.tree_view = tree_view
        self.model = self.tree_view.model()
        self.indexes = self.tree_view.selectedIndexes()
        item_ids, parent_ids, parent_rows = get_selected_ids(self.model, self.indexes)
        if len(item_ids) == 1:  # only one item selected
            self.add_single_tree_actions(delete_active, add_active, edit_active)
        else:
            self.add_multi_tree_actions(delete_active, add_active, edit_active)
        self.add_expand_collapse_actions()

    def add_single_tree_actions(self, delete_active: bool = True, add_active: bool = True, edit_active: bool = True):
        if edit_active:
            edit_action = self.addAction('Edit')
        if delete_active:
            delete_action = self.addAction('Delete')
        if add_active:
            add_menu = self.addMenu('Add')
            insert_above_action = add_menu.addAction('Insert above')
            insert_below_action = add_menu.addAction('Insert below')
            add_child_action = add_menu.addAction('Add child')
            add_parent_action = add_menu.addAction('Add parent')
            add_end_action = add_menu.addAction('Add to end')

    def add_multi_tree_actions(self, delete_active: bool = True, add_active: bool = True, edit_active: bool = True):
        if edit_active:
            edit_action = self.addAction('Edit')
        if delete_active:
            delete_action = self.addAction('Delete')
        if add_active:
            add_action = self.addAction('Add to end')

    def add_expand_collapse_actions(self):
        expand_menu = self.addMenu('Expand')
        expand_children_action = expand_menu.addAction('Expand children')
        expand_all_children_action = expand_menu.addAction('Expand all children')
        expand_all_action = expand_menu.addAction('Expand all')
        collapse_menu = self.addMenu('Collapse')
        collapse_children_action = collapse_menu.addAction('Collapse children')
        collapse_all_children_action = collapse_menu.addAction('Collapse all children')
        collapse_all_action = collapse_menu.addAction('Collapse all')
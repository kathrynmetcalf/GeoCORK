from datetime import time

from PyQt6 import QtCore
from PyQt6.QtSql import QSqlTableModel, QSqlQueryModel

import logger_setup
from util.widgets.models.CheckableTreeModel import CheckableTreeModel
from util.widgets.models.SQLiteTableModel import SQLiteTableModel
from util.widgets.models.TreeModel import TreeItem


class LazyCheckableTreeModel(CheckableTreeModel):
    """
    A checkable tree model that supports lazy loading of tree items. This model extends CheckableTreeModel to allow for
    dynamic loading of tree items as they are expanded in the view. It overrides the canFetchMore and fetchMore methods
    to load child items on demand, improving performance when dealing with large tree structures. The model maintains a
    set of loaded parent items to track which parent items have already had their children loaded.
    """
    def __init__(self, source_model: QSqlTableModel | QSqlQueryModel | SQLiteTableModel=QSqlTableModel(), parent=None):
        super().__init__(source_model, parent)
        self.loaded_parent_items = set()  # Set to track which parent items have been loaded
        self.loading_children = set()  # Set to prevent multiple simultaneous loads of children for the same parent
        self.first_load = True  # Flag to indicate if this is the first load of the tree model
        self.n_first_load = 500  # Number of children to load for the root item on the first load

    def add_to_tree(self, parent: TreeItem):
        """
        Add child items with unique child IDs to the tree model under the specified parent item. This method iterates
        through the list of child IDs, finds the corresponding records in the source model, and creates
        TreeItem instances for each child. It appends these items to the parent item in the tree structure. This method
        is not recursive.
        :param parent: TreeItem parent to add children to
        :return: None if there are no child IDs
        """
        start_add_time = time.time()
        if parent == self.root_item:
            parent_id = None
        else:
            parent_id = parent.itemData.value(0)
        child_ids = self.parent_to_children.get(parent_id, [])
        if not child_ids or len(child_ids) == parent.childCount():
            # If there are no child IDs for this parent or all child IDs are already loaded in the tree, do not load them again
            return
        if not parent_id:
            if self.first_load:
                # If this is the first load of the tree model, limit to the first 500 children
                child_ids = child_ids[:self.n_first_load]
                self.first_load = False
            else:
                child_ids = child_ids[self.n_first_load:]
        self.loading_children.add(parent)
        for child_id in child_ids:
            record = self.item_data[child_id]
            item = TreeItem(record, parent)
            parent.appendChild(item)
        self.loaded_parent_items.add(parent)
        self.loading_children.remove(parent)
        logger_setup.get_logger().info(f'Added {len(child_ids)} children to the tree in {time.time() - start_add_time} seconds')

    def canFetchMore(self, parent: QtCore.QModelIndex = ...) -> bool:
        """
        Determines whether there are more child items to fetch for the given parent index. This method is used by the view
        to determine if it should call fetchMore to load additional child items when a parent item is expanded. If the
        parent index is valid, it checks if the corresponding parent ID has already been loaded. If not, it returns True
        to indicate that there are more items to fetch.
        :param parent: QModelIndex of the parent item for which to check if more child items can be fetched
        :return: True if there are more child items to fetch for the given parent index, False otherwise
        """
        if not parent.isValid():
            # The root item can always fetch more if it has children that haven't been loaded yet
            return None in self.parent_to_children.keys() and self.root_item.childCount() != len(self.parent_to_children[None])
        else:
            parent_item = self.getItem(parent)
            if parent_item not in self.loaded_parent_items:
                # If the children for this parent have not been loaded yet, we can fetch more
                return parent_item.data(0) in self.parent_to_children.keys()
            # If the children for this parent have already been loaded, we cannot fetch more
            return False

    def fetchMore(self, parent: QtCore.QModelIndex = ...):
        """
        Fetches more child items for the given parent index. This method is called by the view when it determines that there
        are more child items to fetch for a parent index (as determined by canFetchMore). It calls load_children to load
        the child items for the specified parent index.
        :param parent: QModelIndex of the parent item for which to fetch more child items
        """
        self.load_children(parent)

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        """
        Returns the number of rows under the given parent index. This method is used to determine how many child items
        are under a given parent item in the tree model. If the parent index is valid, it checks if the corresponding
        parent ID has already been loaded. If not, it returns 0.
        :param parent: QModelIndex of the parent item for which to count child rows
        :return: Number of child rows under the given parent index
        """
        if not parent.isValid():
            return self.root_item.childCount()
        else:
            parent_item = self.getItem(parent)
            if parent_item not in self.loaded_parent_items:
                return 0
            return parent_item.childCount()

    def hasChildren(self, parent: QtCore.QModelIndex = ...) -> bool:
        """
        Returns whether the given parent index has child items. This method is used to determine if a parent item in the
        tree model can be expanded to show child items. If the parent index is valid, it checks if the corresponding
        parent ID has already been loaded. If not, it returns True to indicate that there are potentially child items to
        load.
        :param parent: QModelIndex of the parent item for which to check for children
        :return: True if the parent index has child items or isn't expanded, False otherwise
        """
        if not parent.isValid():
            return self.root_item.childCount() > 0
        else:
            parent_item = self.getItem(parent)
            if parent_item not in self.loaded_parent_items:
                return parent_item.data(0) in self.parent_to_children.keys()
            return parent_item.childCount() > 0

    def load_children(self, parent: QtCore.QModelIndex):
        """
        Loads the child items for the given parent index. This method is called when a parent item in the tree model is
        expanded in the view. It checks if the corresponding parent ID has already been loaded, and if not, it calls
        add_to_tree to load the child items for that parent.
        :param parent: QModelIndex of the parent item for which to load child items
        """
        if not parent.isValid():
            if self.root_item.childCount() == len(self.parent_to_children[None]):
                # Top-level items are already loaded in the tree, so do not load them again
                return
            else:
                parent_item = self.root_item
        else:
            parent_item = self.getItem(parent)
        if parent_item in self.loading_children:
            # If the children for this parent are already being loaded, do not load them again
            return
        if parent_item in self.loaded_parent_items and parent_item.childCount() == len(self.parent_to_children[None]):
            return
        # Need to determine the scope of the insertion (first and last row) before adding children, so get child IDs first
        parent_id = parent_item.itemData.value(0)
        child_ids = self.parent_to_children.get(parent_id, [])
        if not parent_id and not self.first_load:
            # Load the rest of the children for the root item
            child_ids = child_ids[self.n_first_load:]
        if not child_ids:
            self.loaded_parent_items.add(parent_item)
            return
        first = parent_item.childCount()
        last = first + len(child_ids) - 1

        self.beginInsertRows(parent, first, last)
        self.add_to_tree(parent_item)
        self.endInsertRows()

    def load_all(self):
        """
        Loads all items in the tree model. This method is called to ensure that all items in the tree model are loaded
        in the view.
        """
        def load_all_children(parent: QtCore.QModelIndex):
            for row in range(self.rowCount(parent)):
                child_index = self.index(row, 0, parent)
                self.load_children(child_index)
                load_all_children(child_index)

        load_all_children(QtCore.QModelIndex())

    def load_checked(self):
        """
        Loads all parent items down to checked items. This method is called to ensure that all parent items of checked
        items are loaded and expanded in the tree view.
        """
        self.load_id_list(list(self.checked_ids))
        self.load_id_list(list(self.partially_checked_ids))

    def load_id_list(self, id_list: list[int]):
        """
        Loads all parent items down to the items in the given list of IDs. This method is called to ensure that all parent
        items of the specified item IDs are loaded and expanded in the tree view.
        :param id_list: list of item IDs for which to load parent items
        """
        for item_id in id_list:
            parent_ids = self.get_all_parents_selected(item_id)
            if not parent_ids:
                # child of the root, already loaded
                continue
            for parent_id in parent_ids:
                loaded_parent_items = self.loaded_parent_items.copy()
                # For each loaded parent, check if its children have the parent_id of the next parent to load, and if so, load the children of the new parent
                for loaded_parent_item in loaded_parent_items:
                    child_items = loaded_parent_item.childItems
                    for child_item in child_items:
                        if child_item not in self.loaded_parent_items:
                            if child_item.itemData.value(0) == parent_id:
                                parent_index = self.createIndex(child_item.row(), 0, child_item)
                                self.load_children(parent_index)
                                break

    def get_all_parents_selected(self, selected_id) -> list:
        """
        Given the selected item id, get all parent ids so they can be loaded
        :param selected_id: item ID for which to get parent IDs
        :return: list of parent IDs for the given selected item ID, ordered from highest hierarchy level to lowest.
        """
        parent_ids = []
        current_id = selected_id
        while current_id is not None:
            if current_id != selected_id:
                parent_ids.append(current_id)
            parent = None
            for key, children in self.parent_to_children.items():
                if current_id in children:
                    parent = key
                    break
            current_id = parent
        if len(parent_ids)>1:
            return parent_ids[::-1]
        else:
            return parent_ids

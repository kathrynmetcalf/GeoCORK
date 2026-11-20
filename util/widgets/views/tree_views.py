import time

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QSortFilterProxyModel

import logger_setup
from Functions.Settings_manager import SettingsManager
from Functions.Widget_classes import find_tree_model, map_from_tree_model
from util.widgets.models.tree_models import CheckableTreeModel

settings = SettingsManager().settings


class TrackExpandedTreeView(QtWidgets.QTreeView):
    """
    A QTreeView subclass that tracks the IDs from the source model that are expanded as indexes are expanded or collapsed.
    The set is reset from the settings when the model is set or updated, and a custom method expands all indexes with IDs in the set.
    Saving the expanded state just retrieves the set and stores it as a list in settings.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.header().setSectionsMovable(False)
        self.expanded_ids = set()

    def setModel(self, model):
        super().setModel(model)
        tree_model = find_tree_model(model, [])[0]
        if not tree_model:
            return
        table = tree_model.tableName()
        self.expanded_ids = settings.value(f'expanded_ids_{table}')
        if not self.expanded_ids:
            self.expanded_ids = set()
        self.expand_from_ids()
        # tree_model.modelReset.connect(self.on_model_reset)
        self.expanded.connect(self.on_expanded)
        self.collapsed.connect(self.on_collapsed)

    # def on_model_reset(self):
    #     QtCore.QTimer.singleShot(0, self.expand_from_ids)

    def expand_from_ids(self):
        if not self.expanded_ids:
            return
        tree_model = find_tree_model(self.model(), [])[0]
        if not tree_model:
            return
        logger_setup.get_logger().info(f'Expanding {len(self.expanded_ids)} items')
        start_time = time.time()
        for expanded_id in self.expanded_ids:
            index = self.id_to_index(expanded_id)
            if index and index.isValid() and not self.isExpanded(index):
                self.setExpanded(index, True)
                logger_setup.get_logger().info(f'Expanded ID {expanded_id}')
        logger_setup.get_logger().info(
            f'Expanded {len(self.expanded_ids)} items in {time.time() - start_time:.2f} seconds')

    def id_to_index(self, item_id: int):
        tree_model = find_tree_model(self.model(), [])[0]
        if item_id not in tree_model.id_to_item:
            return QtCore.QModelIndex()
        tree_index = tree_model.get_index_from_item(tree_model.id_to_item[item_id])
        indexes = map_from_tree_model(self.model(), [tree_index])
        try:
            index = indexes[0]
            if index == None or not index.isValid():
                return QtCore.QModelIndex()
            return index
        except:
            logger_setup.get_logger().critical(f'Error expanding/collapsing {tree_model.tableName()}')
            return QtCore.QModelIndex()

    def index_to_id(self, index: QtCore.QModelIndex):
        tree_model, tree_indexes = find_tree_model(self.model(), [index])
        if not tree_model:
            return
        try:
            item_id = tree_model.getItem(tree_indexes[0]).data(0)
            return item_id
        except:
            logger_setup.get_logger().critical(f'Error expanding/collapsing {tree_model.tableName()}')
            return None

    def on_expanded(self, index):
        item_id = self.index_to_id(index)
        if item_id and item_id not in self.expanded_ids:
            self.expanded_ids.add(item_id)

    def on_collapsed(self, index):
        item_id = self.index_to_id(index)
        if item_id and item_id in self.expanded_ids:
            self.expanded_ids.remove(item_id)


class CheckableTreeView(TrackExpandedTreeView):
    """
    A QTreeView subclass that allows for checkable items in a tree structure. This class extends QTreeView to allows users
    to select multiple items. The model can be set to a CheckableTreeModel, which provides the data for the tree.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.expandAll()
        self.hideColumn(1)  # don't show ID column
        self.hideColumn(2)  # don't show parent ID column
        self.hideColumn(3)  # don't show parent row column
        self.setSortingEnabled(False)
        self.setHeaderHidden(False)
        self.setUniformRowHeights(True)

        self.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        # self.clicked.connect(self.toggle_check_state)

    def setModel(self, model: CheckableTreeModel | QSortFilterProxyModel):
        """
        Set the model for the tree view. This method overrides the default setModel method to ensure that the model
        is a CheckableTreeModel or a proxy model wrapping a CheckableTreeModel.
        :param model: CheckableTreeModel to be set as the model for the tree view
        :return:
        """
        if not isinstance(model, CheckableTreeModel | QSortFilterProxyModel):
            super().setModel(model)
            return
        tree_model, indexes = find_tree_model(model, [])
        if not tree_model:
            logger_setup.get_logger().critical('Error displaying tree')
            logger_setup.get_logger().debug(f'No tree model found for model passed to CheckableTreeView')
            return
        from util.widgets.models.proxy_models import TreeSortFilterProxyModel
        if isinstance(model, TreeSortFilterProxyModel):
            model.update_visible_columns()
        # self.expanded.connect(self.on_expanded)
        super().setModel(model)

    def on_expanded(self, index: QtCore.QModelIndex):
        """
        Handle the expanded signal for the tree view. Find the underlying tree model and its corresponding index for the
        expanded index. If the model is a LazyCheckableTreeModel, it loads the children of the expanded item.
        :param index: QModelIndex of the expanded item in the tree view
        """
        super().on_expanded(index)
        tree_model, indexes = find_tree_model(self.model, [index])
        from util.widgets.models.tree_models import LazyCheckableTreeModel
        if not isinstance(tree_model, LazyCheckableTreeModel):
            return
        if indexes:
            tree_index = indexes[0]
            tree_model.load_children(tree_index)

    def resizeColumnsToContents(self):
        """
        Resize all columns in the tree view to fit their contents. This method iterates through all columns in the model
        and resizes each column to fit the contents of the items in that column. This is useful for ensuring that all
        columns are displayed correctly and that the text in each column is fully visible.
        :return:
        """
        for column in range(self.model().columnCount()):
            self.resizeColumnToContents(column)

    def toggle_check_state(self, model_index: QtCore.QModelIndex):
        """
        Toggle the check state of the item at the given index. This method checks if the model is set and if the index
        is valid and user-checkable. If so, it toggles the check state of the item between Checked and Unchecked.
        :param model_index: QModelIndex to be checked or unchecked
        :return:
        """
        if self.model():
            if model_index.isValid() and QtCore.Qt.ItemFlag.ItemIsUserCheckable in self.model().flags(model_index):
                if not isinstance(self.model(), CheckableTreeModel):
                    tree_model, indexes = find_tree_model(self.model(), [model_index])
                    tree_index = indexes[0] if indexes else QtCore.QModelIndex()
                else:
                    tree_model = self.model()
                    tree_index = model_index
                item_id = tree_model.index(tree_index.row(), 1, tree_index.parent()).data(
                    QtCore.Qt.ItemDataRole.DisplayRole)
                if not item_id:
                    return
                if item_id in tree_model.checked_ids:
                    tree_model.checked_ids.remove(item_id)
                elif item_id in tree_model.partially_checked_ids:
                    tree_model.partially_checked_ids.remove(item_id)
                    tree_model.checked_ids.add(item_id)
                else:
                    tree_model.checked_ids.add(item_id)
                tree_model.dataChanged.emit(tree_index, tree_index, [QtCore.Qt.ItemDataRole.CheckStateRole])
                tree_model.checksChanged.emit()

    def expand_all_checked(self):
        """
        Expand all parents of checked items in the tree view. This method traverses the tree model and expands all
        parent items of checked and partially checked items. It ensures that all parents of checked items are visible
        in the tree view, making it easier for users to see the hierarchy of checked items.
        :return:
        """
        tree_model, indexes = find_tree_model(self.model(), [])
        if not tree_model:
            logger_setup.get_logger().info(f'No checkable tree model found in {self.objectName()}')
            return
        if not tree_model.checked_ids and not tree_model.partially_checked_ids:
            return
        tree_checked_indices, tree_partially_checked_indices = tree_model.traverse_checkable_tree(QtCore.QModelIndex())
        if isinstance(self.model(), QSortFilterProxyModel):
            checked_indices = map_from_tree_model(self.model(), tree_checked_indices)
            partially_checked_indices = map_from_tree_model(self.model(), tree_partially_checked_indices)
        else:
            checked_indices = tree_checked_indices
            partially_checked_indices = tree_partially_checked_indices

        def expand_parents(item_index: QtCore.QModelIndex):
            """
            Expand parent index of the given item index in the tree view. Recursively expands each parent.
            :param item_index: QModelIndex of the item whose parent should be expanded
            :return:
            """
            if not item_index.isValid():
                return
            parent = item_index.parent()
            while parent.isValid():
                if not self.isExpanded(parent):
                    self.expand(parent)
                parent = parent.parent()

        for index in checked_indices:
            expand_parents(index)
        for index in partially_checked_indices:
            expand_parents(index)

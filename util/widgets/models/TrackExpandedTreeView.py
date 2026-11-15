import time

from PyQt6 import QtWidgets, QtCore

import logger_setup
from Functions.Settings_manager import SettingsManager
from Functions.Widget_classes import find_tree_model, map_from_tree_model

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
        logger_setup.get_logger().info(f'Expanded {len(self.expanded_ids)} items in {time.time() - start_time:.2f} seconds')

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
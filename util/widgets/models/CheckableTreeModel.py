import typing

from PyQt6 import QtCore, QtSql
from PyQt6.QtSql import QSqlTableModel, QSqlQueryModel

import logger_setup
from Functions.Widget_classes import update_other_table_with_checks, get_name_from_id, update_many_table_with_checks
from util.widgets.models.SQLiteTableModel import SQLiteTableModel
from util.widgets.models.TreeModel import TreeModel, TreeItem


class CheckableTreeModel(TreeModel):
    """
    A tree model that supports checkable items. This model extends the TreeModel to allow items to be checked or
    unchecked in the tree view. It uses TreeItem to represent each item in the tree and stores lists of id check states.
    This model is used to display hierarchical data in a tree structure, where each item can be expanded or collapsed,
    and items can be selected by checking them.
    """
    checksChanged = QtCore.pyqtSignal()
    def __init__(self, source_model: QSqlTableModel | QSqlQueryModel | SQLiteTableModel=QSqlTableModel(), parent=None):
        # database table
        super().__init__(source_model, parent)
        self.root_item = TreeItem(QtSql.QSqlRecord(), None)
        self.parent_item = TreeItem(QtSql.QSqlRecord(), None)
        self.child_item = TreeItem(QtSql.QSqlRecord(), None)
        self.item_ids = None
        self.many_to_many = None
        self.checked_ids = set()
        self.partially_checked_ids = set()
        self.single_click = False
        self.not_null = False
        self._map_to_source_cache = {}
        if self.source_model:
            # Check if a table model was set
            if isinstance(self.source_model, QSqlTableModel):
                if self.source_model.tableName() == '':
                    return
                while self.source_model.canFetchMore():
                    self.source_model.fetchMore()
            elif isinstance(self.source_model, QSqlQueryModel):
                query_object = source_model.query()
                while self.source_model.canFetchMore():
                    self.source_model.fetchMore()
                if query_object.lastQuery() == '':
                    return
            elif isinstance(self.source_model, SQLiteTableModel) and self.view_query:
                if source_model.query_text == '':
                    return
            self.setSourceModel(self.source_model)

    def data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = ...):
        """
        Returns the data for the given index and role. This method is used to retrieve the data for each item in the tree
        model, including the check state for checkable items.
        :param index: QModelIndex for which to get the data
        :param role: role for the data, such as DisplayRole or CheckStateRole
        :return: CheckState of the item if the index is valid and the role is CheckStateRole, otherwise calls the base class
        """
        if not index.isValid():
            item = self.root_item
        else:
            item = self.getItem(index)
        if index.column() == 0 and role == QtCore.Qt.ItemDataRole.CheckStateRole:
            if item.itemData.value(0) in self.checked_ids:
                return QtCore.Qt.CheckState.Checked
            elif item.itemData.value(0) in self.partially_checked_ids:
                return QtCore.Qt.CheckState.PartiallyChecked
            else:
                return QtCore.Qt.CheckState.Unchecked

        return super().data(index, role)

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: QtCore.Qt.ItemDataRole = ...) -> bool:
        """
        Sets the data for the given index and role. This method is used to update the check state of checkable items in
        the tree model. If the index is valid and the column is the first column (the checkable item), it updates the
        check state of the item and emits the dataChanged signal to notify the view of the change. If the index is not
        valid or the column is not the first column, it calls the base class implementation to handle other data roles.
        :param index: QModelIndex for which to set the data
        :param value: value to set for the item, such as CheckState
        :param role: role for the data, such as DisplayRole or CheckStateRole
        :return: True if the data was successfully set, False otherwise
        """
        if not index.isValid():
            return super().setData(index, value, role)
        if index.column() == 0 and role == QtCore.Qt.ItemDataRole.CheckStateRole:
            tree_item = self.getItem(index)
            tree_item_id = tree_item.itemData.value(0)
            if not tree_item_id or not isinstance(tree_item_id, int):
                logger_setup.get_logger().debug(f'No item ID found for {tree_item.itemData.value(0)}, cannot set check state')
                return False
            if value == QtCore.Qt.CheckState.Checked:
                self.checked_ids.add(tree_item_id)
                if tree_item_id in self.partially_checked_ids:
                    self.partially_checked_ids.remove(tree_item_id)
                self.dataChanged.emit(index, index, [role])
                return True
            elif value == QtCore.Qt.CheckState.PartiallyChecked:
                self.partially_checked_ids.add(tree_item_id)
                if tree_item_id in self.checked_ids:
                    self.checked_ids.remove(tree_item_id)
                self.dataChanged.emit(index, index, [role])
                return True
            elif value == QtCore.Qt.CheckState.Unchecked:
                if tree_item_id in self.checked_ids:
                    self.checked_ids.remove(tree_item_id)
                if tree_item_id in self.partially_checked_ids:
                    self.partially_checked_ids.remove(tree_item_id)
                self.dataChanged.emit(index, index, [role])
                return True
        return super().setData(index, value, role)

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """
        Returns the item flags for the given index. This determines whether the item is checkable, editable, selectable,
        draggable, and droppable. Only the first column (the checkable item) is checkable. For other columns, it calls
        the base class implementation to get the default flags.
        :param index: QModelIndex for which to get the item flags
        :return: Item flags for the given index, which include ItemIsEnabled, ItemIsSelectable, ItemIsEditable,
        ItemIsUserCheckable, ItemIsDragEnabled, and ItemIsDropEnabled for the first column, or the default flags for other
        columns.
        """
        # name_col = name_column(self.table)
        if not index.isValid():
            return QtCore.Qt.ItemFlag.NoItemFlags
        if index.column() == 0:
            # If the column is the name item, it is checkable
            return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEditable | QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsDragEnabled | QtCore.Qt.ItemFlag.ItemIsDropEnabled
        return super().flags(index)

    def return_checked_ids(self):
        """Returns a list of checked_ids and a list of partially_checked_ids"""
        return list(self.checked_ids), list(self.partially_checked_ids)

    def selected_items_string(self):
        """
        Returns a list of strings representing the items selected by the user.
        Includes both checked and partially checked items.
        """
        selected_names = set()
        for checked_id in self.checked_ids:
            name = get_name_from_id(self.tableName(), checked_id)
            if name is not None:
                selected_names.add(name)
        for partially_checked_id in self.partially_checked_ids:
            name = get_name_from_id(self.tableName(), partially_checked_id)
            if name is not None:
                selected_names.add(name)
        # Sort the names alphabetically (case-insensitive) and return as a semicolon separated string
        return '; '.join(sorted(selected_names, key=lambda s: s.lower()))

    def clear_checks(self):
        """
        Clears the check state of all items in the tree model.
        This method clears the checked_id and partially_checked_ids sets.
        """
        if self.checked_ids or self.partially_checked_ids:
            self.update_model_checks(set(), set())

    def check_all(self):
        """
        Adds all IDs in the source model to the set of checked_ids and clear the set of
        partially_checked_ids.
        """
        all_ids = set()
        for row in range(self.source_model.rowCount()):
            item_id = self.source_model.index(row, 0).data(QtCore.Qt.ItemDataRole.DisplayRole)
            if item_id:
                all_ids.add(item_id)
        self.update_model_checks(all_ids, set())

    def update_model_checks(self, checked_items: set[int], partially_checked_items: set[int]):
        """
        Checks the checkable items in the model based on the provided sets of checked and partially checked IDs.
        This method updates the checked_id and partially_checked_ids sets.
        :param checked_items: set of item IDs that should be checked
        :param partially_checked_items: set of item IDs that should be partially checked
        :return:
        """
        if self.checked_ids != checked_items or self.partially_checked_ids != partially_checked_items:
            self.checked_ids = checked_items
            self.partially_checked_ids = partially_checked_items
            logger_setup.get_logger().info(f'{self.table} checks updated')
            self.checksChanged.emit()

    def traverse_checkable_tree(self, parent: QtCore.QModelIndex):
        """
        Traverses the checkable tree model and collects the indices of checked and partially checked items. This method
        iterates through all rows under the specified parent index and checks the check state of each item. It collects
        the indices of checked items and partially checked items and recursively traverses child items under the parent
        index to gather their checked and partially checked indices.
        :param parent: QModelIndex of the parent item whose children should be checked, usually first called with
        QModelIndex() for the root item
        :return: tuple containing lists of checked indices and partially checked indices.
        """
        checked_indices = set()
        partially_checked_indices = set()
        for row in range(self.rowCount(parent)):
            name_index = self.index(row, 0, parent)
            id_index = self.index(row, 1, parent)
            item_id = self.data(id_index, QtCore.Qt.ItemDataRole.DisplayRole)
            if item_id in self.checked_ids:
                checked_indices.add(name_index)
            elif item_id in self.partially_checked_ids:
                partially_checked_indices.add(name_index)
            child_checked_indices, child_partially_checked_indices = self.traverse_checkable_tree(name_index)
            if child_checked_indices:
                checked_indices = checked_indices | child_checked_indices
            if child_partially_checked_indices:
                partially_checked_indices = partially_checked_indices | child_partially_checked_indices
        return checked_indices, partially_checked_indices

    def update_other_table(self, other_table: str, other_ids: list[int]) -> str:
        """
        Collect the checked IDs and partially checked IDs from this table and update that field in another table.
        It calls the update_other_table_with_checks function to perform the update operation. This is useful for one-to-many
        relationships. The relationship must be one-to-one or one-to-many, so there should be only one checked ID. If
        there are partially checked IDs, no item has been selected to associate with all IDs in the other table, so do
        not update. If the relationship is many-to-many, use update_many_table instead.
        :param other_table: name of the other table to update with the checked IDs from this table (e.g. Samples)
        :param other_ids: list of IDs in the other table that correspond to the checked items in this tree model
        (e.g. list of SampleIDs)
        :return: 'True' if successful, 'No' if not needed, 'False' needed but failed
        """
        if not other_ids:
            logger_setup.get_logger().error(f'No item IDs given for {other_table}')
            return 'False'
        if self.partially_checked_ids:
            # Any selection for a one-to-many relationship should be complete, so there should be no partially checked IDs
            logger_setup.get_logger().info(f'Partially checked IDs for one-to-many relationship, no changes to update')
            return 'No'
        if len(self.checked_ids) > 1:
            # If there are multiple checked IDs, this is a many-to-many relationship, so we should not use this function
            logger_setup.get_logger().error(
                f'Multiple checked IDs given for {self.tableName()}. Select only one ID to update {other_table}.')
            logger_setup.get_logger().debug(
                f'This should be a one-to-many relationship, so set the checkable combo box to single click.')
            return 'False'
        return update_other_table_with_checks(self.table, list(self.checked_ids), list(self.partially_checked_ids), other_table, other_ids)

    def update_many_table(self, many_table: str, item_ids: list | None) -> str:
        """
        Updates many-to-many relationship with another table. This method is useful when editing joined views, like
        editing the Units associated with Samples.
        :param many_table: name of the many-to-many table to update (e.g. Samples_Units)
        :param item_ids: list of foreign IDs to update in the many-to-many table (e.g. SampleIDs)
        :return: 'True' if successful, 'No' if not needed, 'False' needed but failed
        """
        if not item_ids:
            logger_setup.get_logger().error(f'No item IDs given for {many_table}')
            return 'False'
        return update_many_table_with_checks(self.table, list(self.checked_ids), list(self.partially_checked_ids), many_table, item_ids)

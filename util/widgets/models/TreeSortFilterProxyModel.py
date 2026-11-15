from PyQt6 import QtCore, QtWidgets

from Functions.Widget_classes import find_tree_model
from util.widgets.models.ReadableProxyModel import ReadableProxyModel
from util.widgets.models.TrackExpandedTreeView import TrackExpandedTreeView


class TreeSortFilterProxyModel(ReadableProxyModel):
    """
    A proxy model that filters and sorts items in a tree structure. This model extends QSortFilterProxyModel to
    provide custom filtering logic for tree items. It allows filtering based on a regular expression and supports
    recursive filtering for tree structures. The model can be used with a QTreeView to display hierarchical data
    while applying the specified filter criteria.
    """
    def __init__(self, parent=None, view: QtWidgets.QTreeView =None):
        super().__init__(parent)
        self.setRecursiveFilteringEnabled(True)  # Enables recursive filtering for tree structures
        self.view = view  # The view containing the model (e.g., QTreeView)
        if not view:
            self.view = TrackExpandedTreeView(parent)
        if isinstance(self.view, QtWidgets.QTreeView):
            self.view.setUniformRowHeights(True)
        self.filter_column = 0  # Default column to filter on
        self.filter_ids = set()  # set of IDs to filter by
        self.visible_columns = set()  # set of columns that are visible in the view

    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole = ...):
        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            # If the role is for tooltips, return the data from the source model
            tree_model, source_indexes = find_tree_model(self, [index])
            if tree_model and source_indexes:
                return tree_model.data(source_indexes[0], role)
            else:
                return super().data(index, role)
        else:
            # For other roles, use the default implementation
            return super().data(index, role)

    def filterAcceptsRow(self, source_row: int, source_parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        """
        Determines whether a row in the source model should be accepted or rejected based on the filter criteria.
        This method checks if the row matches the filter pattern and if the row's ID is in the list of filter IDs.
        :param source_row: row number in the source model to check for acceptance
        :param source_parent: parent index in the source model, used for hierarchical filtering
        :return: True if the row matches the filter criteria, False otherwise
        """
        # Override this method to implement custom filtering logic
        model = self.sourceModel()
        # If there is a list of filter IDs, check if the current row's ID matches any of them
        if self.filter_column and self.filter_ids:
            item_id = model.data(model.index(source_row, self.filter_column, source_parent),
                                 QtCore.Qt.ItemDataRole.DisplayRole)
            if item_id not in self.filter_ids:
                return False
            else:
                return True
        # If no filter IDs are set or the current row's ID matches, proceed with the default filtering logic
        # If the filter pattern is empty, accept all rows
        if self.filterRegularExpression().pattern() == '' or not self.filterRegularExpression().pattern():
            return True
        # Iterate through visible columns of the given row to check for a match
        for column in self.visible_columns:
            index = model.index(source_row, column, source_parent)
            # logger_setup.get_logger().debug(f'Checking if {index.data()} matches filter {self.filterRegularExpression().pattern()}')
            # If the current column's data matches the filter, accept this row
            if index.data() is not None and self.filterRegularExpression().match(str(index.data())).hasMatch():
                # logger_setup.get_logger().debug(f'We have a match')
                return True
        # If no column matches, reject this row
        return False

    def update_visible_columns(self):
        """
        Updates the set of visible columns based on the view's current column visibility. This method is called when the
        source model changes or when columns are shown or hidden in the view. It iterates through all columns and checks
        if they are hidden in the view, updating the set of visible columns accordingly.
        """
        if self.view is not None:
            self.visible_columns = set()
            for column in range(self.sourceModel().columnCount()):
                if not self.view.isColumnHidden(column):
                    self.visible_columns.add(column)
        else:
            self.visible_columns = set(range(self.sourceModel().columnCount()))


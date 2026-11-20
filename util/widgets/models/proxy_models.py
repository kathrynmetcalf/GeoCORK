import re
import typing

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QStringListModel
from PyQt6.QtGui import QBrush, QColor, QFont

from util.database.database_helper import get_readable_header, get_name_column, find_tree_model
from util.display_formatting import display_age

from util.widgets.views.tree_views import TrackExpandedTreeView


class ColumnListProxyModel(QtCore.QSortFilterProxyModel):
    """
    A proxy model that filters and sorts columns in a list. This model extends QSortFilterProxyModel to display headers
    in the list as user-readable strings instead of raw database column names.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.setSortCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)

    def data(self, index: QtCore.QModelIndex, role: int = ...):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            header = super().data(index, role)
            readable_header = get_readable_header(header)
            return readable_header
        return super().data(index, role)


class ReadableProxyModel(QtCore.QSortFilterProxyModel):
    """
    Displays readable headers for any table. Uses get_readable_header to convert header text.
    Setting original_headers to True returns unmodified headers.
    Sorting takes into account mixed text and numeric data in strings so that A14 is considered less than A104.
    If doi column is present, returns more readable text and creates a tool tip for each entry.
    """

    def __init__(self, view=False):
        super().__init__()
        self.original_headers = False
        self.doi_column_exists = False
        self.doi_column = None
        self.doi_regex = re.compile(r"^(10\.\d{4,9}\/[-._;()\/:A-Z0-9]+)$", re.IGNORECASE)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.setSortCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)

    def setSourceModel(self, sourceModel):
        super().setSourceModel(sourceModel)
        self.doi_column_exists = False
        self.doi_column = None
        self._check_doi_column()

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: QtCore.Qt.ItemDataRole = ...):
        if self.original_headers:
            super().headerData(section, orientation, role)
        if role == QtCore.Qt.ItemDataRole.DisplayRole and orientation == QtCore.Qt.Orientation.Horizontal:
            header = super().headerData(section, orientation, role)
            header = '' if header is None else header
            if '_' in header:
                return header
            readable_header = get_readable_header(header)
            return readable_header
        super().headerData(section, orientation, role)

    def _check_doi_column(self):
        """Checks if a doi column exists in the table and sets the boolean to True."""
        model = self.sourceModel()
        if not model or isinstance(model, QStringListModel):
            return

        # For QSqlTableModel or QAbstractItemModel
        for col in range(model.columnCount()):
            header = model.headerData(col, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole)
            if str(header).strip().lower() == "doi":
                self.doi_column = col
                self.doi_column_exists = True
                break

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        """
        Method to modify data in the table. Currently modifies a doi column's display roles to show invalid/valid dois
        and adds colors, tooltips, and hyperlinking. Currently implemented roles are ForegroundRole, FontRole,
        and ToolTipRole.
        :param index: QModelIndex of the record
        :param role: ItemDataRole to pass in
        :return: The modified data and role for the record
        """
        if not index.isValid():
            return super().data(index, role)

        if role not in (QtCore.Qt.ItemDataRole.ForegroundRole, QtCore.Qt.ItemDataRole.FontRole,
                        QtCore.Qt.ItemDataRole.ToolTipRole):
            return super().data(index, role)

        # Handle tooltip for DOI column
        if self.doi_column_exists and index.column() == self.doi_column:
            source_index = self.mapToSource(index)
            text = self.sourceModel().data(source_index, QtCore.Qt.ItemDataRole.DisplayRole)
            if isinstance(text, str):
                if text.startswith('doi:'):
                    text = text.replace('doi:', '')
                if re.match(self.doi_regex, text):
                    if role == QtCore.Qt.ItemDataRole.ForegroundRole:
                        return QBrush(QColor("blue"))
                    elif role == QtCore.Qt.ItemDataRole.FontRole:
                        font = QFont()
                        font.setUnderline(True)
                        return font
                    elif role == QtCore.Qt.ItemDataRole.ToolTipRole:
                        return "Valid DOI format, double click to open in browser"
                else:
                    if role == QtCore.Qt.ItemDataRole.ToolTipRole:
                        return "Invalid DOI format, consider using '10.XXXX/XXXXXX'"

        # Default return for all other roles
        return super().data(index, role)

    def setData(self, index: QtCore.QModelIndex, value: typing.Any,
                role: int = QtCore.Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid():
            return super().setData(index, value, role)
        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            source_index = self.mapToSource(index)
            return self.sourceModel().setData(source_index, value, role)
        return super().setData(index, value, role)

    def determine_numeric(self, value):
        if isinstance(value, str):
            if value == '':
                return value
            elif '.' in value:
                try:
                    float(value)  # value is float, not text
                    if float(value) - int(float(value)) != 0:
                        return float(value)
                    else:  # value is an integer
                        return int(float(value))
                except ValueError:
                    return value
            try:
                int(value)  # value is integer, not text
                return int(value)
            except ValueError:
                return value
        elif isinstance(value, float):
            if value - int(value) != 0:
                return value
            else:
                return int(value)
        else:
            return value

    def separate_parts(self, text):
        parts = re.split(r'(\d+)', text)
        if parts:
            # return all sets of numbers and strings
            return [int(part) if part.isdigit() else part.lower() for part in parts]
        else:
            return None

    def compare_parts(self, left_parts, right_parts):
        for left_part, right_part in zip(left_parts, right_parts):
            if left_part != right_part:
                return left_part < right_part
        # If all compared parts are equal, return the shorter one
        return len(left_parts) < len(right_parts)

    def lessThan(self, left, right):
        left_data = self.determine_numeric(left.data(QtCore.Qt.ItemDataRole.DisplayRole))
        right_data = self.determine_numeric(right.data(QtCore.Qt.ItemDataRole.DisplayRole))
        if isinstance(left_data, str) and isinstance(right_data, str):
            left_parts = self.separate_parts(left_data)
            right_parts = self.separate_parts(right_data)
            return self.compare_parts(left_parts, right_parts)
        elif isinstance(left_data, (int, float)) and isinstance(right_data, (int, float)):
            return left_data < right_data
        else:
            return super().lessThan(left, right)


class SampleAgeProxyModel(QtCore.QSortFilterProxyModel):
    """
    Proxy model to display updated SampleAgeConverted and SampleAgeDisplay while generated columns cannot update during a transaction.
    """

    def __init__(self):
        super().__init__()
        self.edited = True

    def data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            name_col = get_name_column('SampleAges')
            if index.column() == name_col:
                from util.database.alter_database import return_sample_age_display
                from util.database.alter_database import return_sample_age_converted
                id = self.sourceModel().index(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole)
                if id is not None:
                    # get the updated sample age display calculated from the database
                    age_display = return_sample_age_display(id)
                    age_converted = return_sample_age_converted(id)
                    if not self.edited and age_display is not None:
                        # return the user-readable age display
                        return display_age(age_display)
                    elif self.edited and age_converted is not None:
                        # return the editable age converted
                        return display_age(age_converted)
        return super().data(index, role)


class TreeSortFilterProxyModel(ReadableProxyModel):
    """
    A proxy model that filters and sorts items in a tree structure. This model extends QSortFilterProxyModel to
    provide custom filtering logic for tree items. It allows filtering based on a regular expression and supports
    recursive filtering for tree structures. The model can be used with a QTreeView to display hierarchical data
    while applying the specified filter criteria.
    """

    def __init__(self, parent=None, view: QtWidgets.QTreeView = None):
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

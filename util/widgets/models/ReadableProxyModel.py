import re
import typing

from PyQt6 import QtCore
from PyQt6.QtCore import QStringListModel
from PyQt6.QtGui import QFont, QBrush, QColor

from Functions.Widget_classes import get_readable_header


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

        if role not in (QtCore.Qt.ItemDataRole.ForegroundRole, QtCore.Qt.ItemDataRole.FontRole, QtCore.Qt.ItemDataRole.ToolTipRole):
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

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = QtCore.Qt.ItemDataRole.EditRole) -> bool:
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


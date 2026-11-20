from PyQt6 import QtCore

from Functions.Widget_classes import get_readable_header


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
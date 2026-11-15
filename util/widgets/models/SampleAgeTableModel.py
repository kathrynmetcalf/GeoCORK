from PyQt6 import QtGui, QtCore

from util.display_formatting import display_age
from util.widgets.models.CheckableSqlQueryModel import CheckableSqlQueryModel


class SampleAgeTableModel(CheckableSqlQueryModel):
    """
    Custom CheckableSqlQueryModel (subclasses DisplayRoundedQueryModel and QSqlQueryModel).
    Intended to track default ages as bolded rows in the model.
    """
    def __init__(self):
        super().__init__()
        self.bolded_rows = []
        self.default_query = 'SELECT * FROM SampleAges'

    def tableName(self):
        return 'SampleAges'

    def data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        if index.row in self.bolded_rows and role == QtCore.Qt.ItemDataRole.FontRole:
            font = QtGui.QFont()
            font.setBold(True)
            return font
        if index.column() == 1 and role == QtCore.Qt.ItemDataRole.DisplayRole:
            string = super().data(index, role)
            return display_age(string)
        return super().data(index, role)

    def make_bold(self, index):
        """Age is the default age for a sample and should be marked as bold"""
        row = index.row()
        if row not in self.bolded_rows:
            self.bolded_rows.append(row)
            self.dataChanged.emit(index, index, [QtCore.Qt.ItemDataRole.FontRole])

    def make_not_bold(self, index):
        """Age is not a default age for any sample and should be marked as bold"""
        row = index.row()
        if row in self.bolded_rows:
            self.bolded_rows.remove(row)
            self.dataChanged.emit(index, index, [QtCore.Qt.ItemDataRole.FontRole])
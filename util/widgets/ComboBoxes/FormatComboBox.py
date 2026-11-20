from PyQt6 import QtCore, QtWidgets, QtSql

from util.widgets.models.table_models import SQLiteTableModel


class FormatComboBox(QtWidgets.QComboBox):
    """
    A QcomboBox class that return the format name as a tool tip if the table ends in 'Formats'
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def data(self, index,
             role=
             QtCore.Qt.ItemDataRole.DisplayRole | QtCore.Qt.ItemDataRole.ToolTipRole):
        if not index.isValid():
            return
        if (self.model() and isinstance(self.model(), QtSql.QSqlTableModel | QtSql.QSqlQueryModel | SQLiteTableModel)
                and self.model().tableName().endswith('Formats') and role == QtCore.Qt.ItemDataRole.ToolTipRole):
            format_name = self.model().data(self.model().index(index.row(), 1), QtCore.Qt.ItemDataRole.DisplayRole)
            return format_name
        super().data(index, role)

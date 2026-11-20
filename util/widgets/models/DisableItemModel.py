from PyQt6 import QtGui, QtCore
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtSql import QSqlQuery


class DisableItemModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.disabled_items = []

    def data(self, index: QtCore.QModelIndex, role: int = ...):
        if not index.isValid():
            return None
        if role == QtCore.Qt.ItemDataRole.DisplayRole or role == QtCore.Qt.ItemDataRole.EditRole:
            item = self.item(index.row(), index.column()).data(QtCore.Qt.ItemDataRole.DisplayRole)
            if item:
                return item
        elif role == QtCore.Qt.ItemDataRole.ToolTipRole:
            item = self.item(index.row(), index.column()).data(QtCore.Qt.ItemDataRole.DisplayRole)
            if not isinstance(item, str):
                item = item.text()
            query = QSqlQuery()
            if query.exec(f'SELECT GeoChemAnalyteName, GeoChemAnalyteDescription FROM GeoChemicalAnalytes WHERE GeoChemAnalyteAbbreviation IS {item}'):
                if query.next():
                    if query.value('GeoChemAnalyteName') or query.value('GeoChemAnalyteDescription'):
                        tool_tip = f'{query.value('GeoChemAnalyteName')}: {query.value('GeoChemAnalyteDescription')}'
                        return tool_tip
        elif role == QtCore.Qt.ItemDataRole.ForegroundRole:
            # Return gray text if the row is disabled
            item = self.item(index.row(), index.column()).data(QtCore.Qt.ItemDataRole.DisplayRole)
            if item in self.disabled_items:
                # logger_setup.get_logger().debug(f'Setting gray text for disabled item}')
                return QBrush(QColor("#A0A0A0"))  # Gray text
        return super().data(index, role)

    def flags(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return None
        item = self.item(index.row(), index.column()).data(QtCore.Qt.ItemDataRole.DisplayRole)
        if item in self.disabled_items:
            # Item is not selectable
            return QtCore.Qt.ItemFlag.NoItemFlags
        return super().flags(index)
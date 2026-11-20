from PyQt6 import QtGui, QtCore
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtSql import QSqlQuery

from Functions import SQLUtils


class ColumnItemModel(QtGui.QStandardItemModel):
    """
    A model that represents a list of columns with checkable items. This model extends QStandardItemModel to provide
    functionality for displaying a list of columns with checkboxes. It allows users to select which columns should be
    displayed in a view. The model can be used with a QTreeView or QListView to show the columns as checkable items.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.permanent_header = ''

    def set_permanent_header(self, header: str):
        """
        Set the permanent header that should always be checked. This header will not be allowed to be unchecked by the user.
        :param header: name of the header that should always be checked
        :return:
        """
        # Set the header that should always be checked, the name or display column
        self.permanent_header = header

    def data(self, index, role: int = ...):
        """
        Return the data for the given index and role. This method overrides the default data method to provide
        custom behavior for the check state role. If the role is CheckStateRole, it checks if the item is the permanent
        header and returns Checked if it is, otherwise it calls the superclass method to get the default behavior.
        :param index:
        :param role:
        :return:
        """
        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            if self.data(index, QtCore.Qt.ItemDataRole.DisplayRole) == self.permanent_header:
                return QtCore.Qt.CheckState.Checked
            else:
                return super().data(index, role)
        return super().data(index, role)

    def setData(self, index, value, role: int = ...):
        """
        Set the data for the given index and role. This method overrides the default setData method to provide
        custom behavior for the check state role. If the role is CheckStateRole and the item is the permanent header,
        it prevents the user from unchecking it by returning False. Otherwise, it calls the superclass method to set the data.
        :param index:
        :param value:
        :param role:
        :return:
        """
        if not index.isValid():
            return super().setData(index, value, role)
        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            if self.data(index, QtCore.Qt.ItemDataRole.DisplayRole) == self.permanent_header and value == QtCore.Qt.CheckState.Unchecked:
                return False
        return super().setData(index, value, role)


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
        elif role == QtCore.Qt.ItemDatdaRole.ToolTipRole:
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

class TableToolTipModel(QtGui.QStandardItemModel):
    """
    Subclass of QStandardItemModel to link table items in the model with descriptions to return as tool tips. Can be
    applied to any combo box or list that accepts QStandardItemModel
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            table = self.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
            if table in SQLUtils.table_attributes_description_dict.keys():
                description = SQLUtils.table_attributes_description_dict[table]['description']
                return description
        return super().data(index, role)
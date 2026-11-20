from PyQt6 import QtGui, QtCore

from Functions import SQLUtils


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
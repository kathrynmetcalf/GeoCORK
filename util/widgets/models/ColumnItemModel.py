from PyQt6 import QtGui, QtCore


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
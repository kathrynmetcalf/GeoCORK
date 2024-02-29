import typing
from PyQt6 import QtCore as QtC
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6.uic import loadUi
import Functions.Text_manipulations as TxM

'''
Editable tree model example:
https://doc.qt.io/qt-6/qtwidgets-itemviews-editabletreemodel-example.html

qsqltablemodel source code:
https://github.com/openwebos/qt/blob/master/src/sql/models/qsqltablemodel.cpp

qsortfilterproxymodel source code:
https://github.com/openwebos/qt/blob/92fde5feca3d792dfd775348ca59127204ab4ac0/src/gui/itemviews/qsortfilterproxymodel.cpp#L143
'''

class TreeItem:
    def __init__(self, itemData: QtS.QSqlRecord, parentItem):
        self.itemData = itemData
        self.parentItem = parentItem
        self.childItems = []

    def __del__(self):
        for child in self.childItems:
            del child
        del self.childItems
        
    def appendChild(self, child_item):
        # add each child item
        self.childItems.append(child_item)

    def removeChild(self, row: int):
        # remove a child item at a position
        if row < 0 or row >= len(self.childItems):
            return False
        else:
            self.childItems.remove(row)
            return True

    def child(self, row: int):
        # child in given row
        if row < 0 or row >= len(self.childItems):
            return None
        else:
            return self.childItems[row]

    def childCount(self):
        # number of children
        return len(self.childItems)

    def row(self):
        # row of item in its parent's list of children
        if self.parentItem:
            # return self.parentItem.childItems.indexOf(TreeItem(self))
            return self.parentItem.childItems.index(self)
        return 0

    def columnCount(self):
        # number of columns in input data
        if self.itemData:
            return self.itemData.count()
        else:
            return 0

    def data(self, column: int):
        # get data at given column
        if self.itemData is None:
            return QtC.QVariant()
        if column < 0 or column >= self.itemData.count():
            return QtC.QVariant()
        else:
            field = self.itemData.field(column)
            return field.value()

    def setData(self, column: int, value: typing.Any):
        if column < 0 or column >= self.itemData.count():
            return False
        else:
            field = self.itemData.field(column)
            self.itemData.setValue(field.name(), value)
            return True

    def parent(self):
        # parent for given item
        if self.itemData is None or type(self.itemData.value(self.itemData.field(1).value())) is not int:
            return None
        else:
            return self.parentItem


class TreeModel(QtC.QAbstractProxyModel):
    def __init__(self, sourceModel: QtS.QSqlTableModel, parent=None):
        # database table
        super().__init__(parent)

        self.sourceModel = sourceModel
        self.headers = []
        self.column_headers()
        self.rootItem = TreeItem(None, None)
        self.parentItem = TreeItem(None, None)
        self.childItem = TreeItem(None, None)
        self.setup_model_data()

        # self.sourceModel.dataChanged().connect


    def __del__(self):
        del self.rootItem

    def setup_model_data(self):
        # Add all nodes to the tree model
        # start with root item, look for children
        root_id = 0
        child_ids = self.find_children(root_id)
        # add each child to model with parent (root)
        self.add_to_tree(child_ids, self.rootItem)
            # look for children of those
            # add each child to the model with parent
            # etc. until there are no more children

    def find_children(self, parent_id: int):
        # Query the table and find children of given ID
        parent_id_header = TxM.remove_spaces(self.headers[1])
        if parent_id == 0:
            self.sourceModel.setFilter(f'{parent_id_header} IS Null')
        else:
            self.sourceModel.setFilter(f'{parent_id_header} = {parent_id}')
        child_ids = []
        for row in range(self.sourceModel.rowCount()):
            # store each child ID in a list
            record = self.sourceModel.record(row)
            child_ids.append(record.value(0))
        return child_ids

    def add_to_tree(self, child_ids: list, parent: TreeItem):
        for item_id in child_ids:
            # find entry with this item ID
            item_id_header = TxM.remove_spaces(self.headers[0])
            self.sourceModel.setFilter(f'{item_id_header} = {item_id}')
            data = self.sourceModel.record(0)
            item = TreeItem(data, parent)
            parent.appendChild(item)
            new_parent = item
            new_parent_id = item_id
            new_child_ids = self.find_children(new_parent_id)
            self.add_to_tree(new_child_ids, new_parent)

    def add_top_item(self, data):
        TreeItem(data, 0)

    def column_headers(self):
        for col in range(self.sourceModel.columnCount()):
            self.headers.append(self.sourceModel.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))

    def getItem(self, index: QtC.QModelIndex):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.rootItem

    def index(self, row: int, column: int, parent: QtC.QModelIndex = ...):
    # Given row, column, and parent, create an index for a child item at row and column
    # First check if parent is valid and parent item exists
    # Then get the child at the specified row and create an index for it
    # index for views and delegates
        if not parent.isValid() and parent.column() != 0:
            parentItem = self.rootItem
        else:
            parentItem = self.getItem(parent)
        if not parentItem:
            return QtC.QModelIndex()
        treeItem = parentItem.child(row)
        if treeItem:
            return self.createIndex(row, column, treeItem)
        else:
            return QtC.QModelIndex()

    def parent(self, index: QtC.QModelIndex):
    # Given index, find parent and create index for parent item
        if not index.isValid():
            return QtC.QModelIndex()
        childItem = self.getItem(index)
        if not childItem:
            return QtC.QModelIndex()
        parentItem = childItem.parent()
        if parentItem == self.rootItem or not parentItem:
            return QtC.QModelIndex()
        return self.createIndex(self.parentItem.row(), 0, parentItem)

    def rowCount(self, parent: QtC.QModelIndex = ...) -> int:
        if not parent.isValid():
            self.parentItem = self.rootItem
        else:
            self.parentItem = self.getItem(parent)
        return self.parentItem.childCount()

    def columnCount(self, parent: QtC.QModelIndex = ...) -> int:
        # return 1
        return len(self.headers)

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            return None
        item = self.getItem(index)
        if role == QtC.Qt.ItemDataRole.DisplayRole:
            return item.data(index.column())
        return None

    def mapToSource(self, proxy_index: QtC.QModelIndex) -> QtC.QModelIndex:
        if not proxy_index.isValid() or not self.sourceModel:
            return QtC.QModelIndex()
        if not isinstance(self.sourceModel, QtS.QSqlTableModel):
            QtC.qWarning("QSortFilterProxyModel: index from wrong model passed to mapToSource")
            return QtC.QModelIndex()
        proxyCol = proxy_index.column()
        parent = proxy_index.parent()
        if not parent.isValid():
            return QtC.QModelIndex()
        elif parent == self.rootItem:
            return QtC.QModelIndex()
        item = self.getItem(proxy_index)
        itemID = item.data(0)
        for row in range(self.sourceModel.rowCount()):
            record = self.sourceModel.record(row)
            if record.value(0) == itemID:
                sourceRow = row
                break
        if not sourceRow:
            return QtC.QModelIndex()
        sourceCol = proxyCol
        return self.createIndex(sourceRow, sourceCol)

    def mapFromSource(self, sourceIndex: QtC.QModelIndex) -> QtC.QModelIndex:
        if not sourceIndex.isValid():
            return QtC.QModelIndex()
        sourceRow = sourceIndex.row()
        sourceCol = sourceIndex.column()
        record = self.sourceModel.record(sourceRow)
        itemID = record.value(0)
        treeItem = self.findIDinTree(itemID, self.rootItem)
        parentItem = treeItem.parent()
        proxyRow = treeItem.row() # row number of item in its parent's child list
        proxyCol = sourceCol # same column as table model
        parentIndex = self.parent()
        if not parentIndex.isValid():
            return QtC.QModelIndex()
        elif parentItem == self.rootItem:
            return QtC.QModelIndex()
        return self.index(proxyRow, proxyCol, parentIndex)

    def findIDinTree(self, itemID: int, parent: TreeItem) -> TreeItem:
        for childItem in parent.childItems:
            if childItem.data(0) == itemID:
                result = childItem
                return result
            else:
                self.findIDinTree(itemID, childItem)

    def flags(self, index: QtC.QModelIndex) -> QtC.Qt.ItemFlag:
        if not index.isValid():
            return QtC.Qt.ItemFlag.NoItemFlags
        return QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable | QtC.Qt.ItemFlag.ItemIsEnabled

    def headerData(self, section: int, orientation: QtC.Qt.Orientation, role: int = ...):
        if role != QtC.Qt.ItemDataRole.DisplayRole:
            return QtC.QVariant()
        if orientation == QtC.Qt.Orientation.Horizontal:
            return TxM.add_spaces_camel(self.headers[section])
        return QtC.QVariant()

    def setData(self, index: QtC.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if not index.isValid():
            return False
        if role == QtC.Qt.ItemDataRole.EditRole:  # If item is edited
            self.sourceModel.setData(self.sourceModel.index(index.row(), index.column()), value, role)
            return True





import typing
from PyQt6 import QtCore as QtC
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6.uic import loadUi
import Functions.Text_manipulations as TxM


class TreeItem:
    def __init__(self, itemData, parentItem):
        self.itemData = itemData
        self.parentItem = parentItem
        self.childItems = []

    # def __del__(self):
    #     del self.childItems
        
    def appendChild(self, child_item):
        # add each child item
        self.childItems.append(child_item)

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
            return len(self.itemData)
        else:
            return 0

    def data(self, column: int):
        # get data at given column
        if self.itemData is None:
            return QtC.QVariant()
        if column < 0 or column >= len(self.itemData):
            return QtC.QVariant()
        else:
            return self.itemData[column]

    def setData(self, column: int, value: typing.Any):
        self.itemData[column] = value

    def parent(self):
        # parent for given item
        if self.itemData is None or type(self.itemData[1]) is not int:
            return None
        else:
            return self.parentItem


class TreeModel(QtC.QAbstractItemModel):
    def __init__(self, table, parent):
        # database table
        super().__init__(parent)

        self.table = table
        self.headers = []
        self.column_headers()
        self.rootItem = TreeItem(tuple(self.headers), None)
        # self.rootItem = TreeItem(("ID", "Parent ID", "Name", "Description", "Created", "Modified"), None)
        self.parents = {0: self.rootItem}
        self.parentItem = TreeItem(None, None)
        self.childItem = TreeItem(None, None)
        self.setup_model_data()

    # def __del__(self):
    #     del self.rootItem

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
        query = QtS.QSqlQuery()
        if parent_id == 0:
            query.prepare(f'SELECT * FROM {self.table} WHERE {self.headers[1]} IS NULL')
        else:
            query.prepare(f'SELECT * FROM {self.table} WHERE {self.headers[1]} = {parent_id}')
        if query.exec():
            child_ids = []
            while query.next():
                # store each child ID in a list
                child_ids.append(query.value(0))
        return child_ids

    def add_to_tree(self, child_ids: list, parent: TreeItem):
        query = QtS.QSqlQuery()
        for item_id in child_ids:
            # find entry with this item ID
            query.prepare(f'SELECT * FROM {self.table} WHERE {self.headers[0]} = {item_id}')
            if query.exec():
                while query.next():
                    # data = query.value(2)
                    data = []
                    for col in self.headers:
                        data.append(query.value(col))
                    data.insert(0, data.pop(2))
                    item = TreeItem(data, parent)
                    parent.appendChild(item)
            new_parent = item
            new_parent_id = item_id
            new_child_ids = self.find_children(new_parent_id)
            self.add_to_tree(new_child_ids, new_parent)

    def add_top_item(self, data):
        TreeItem(data, 0)

    def column_headers(self):
        query = QtS.QSqlQuery()
        query.prepare(f'PRAGMA table_info({self.table})')
        if query.exec():
            while query.next():
                self.headers.append(query.value(1))

    def index(self, row: int, column: int, parent: QtC.QModelIndex = ...):
        # parent is QModelIndex
        # index for views and delegates
        if not self.hasIndex(row, column, parent):
            return QtC.QModelIndex()
        if not parent.isValid():
            self.parentItem = self.rootItem
        else:
            self.parentItem = parent.internalPointer()
        self.childItem = self.parentItem.child(row)
        if self.childItem:
            return self.createIndex(row, column, self.childItem)
        else:
            return QtC.QModelIndex()

    def parent(self, index: QtC.QModelIndex):
        if not index.isValid():
            return QtC.QModelIndex()
        self.childItem = index.internalPointer()
        if not self.childItem:
            return QtC.QModelIndex()
        self.parentItem = self.childItem.parent()
        if self.parentItem == self.rootItem:
            return QtC.QModelIndex()
        return self.createIndex(self.parentItem.row(), 0, self.parentItem)

    def rowCount(self, parent: QtC.QModelIndex = ...) -> int:
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            self.parentItem = self.rootItem
        else:
            self.parentItem = parent.internalPointer()
        return self.parentItem.childCount()

    def columnCount(self, parent: QtC.QModelIndex) -> int:
        # return 1
        return len(self.headers)

    def data(self, index: QtC.QModelIndex, role):
        if not index.isValid():
            return None
        item = index.internalPointer()
        if role == QtC.Qt.ItemDataRole.DisplayRole:
            return item.data(index.column())
        return None

    def flags(self, index: QtC.QModelIndex) -> QtC.Qt.ItemFlag:
        if not index.isValid():
            return QtC.Qt.ItemFlag.NoItemFlags
        return QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable

    def headerData(self, section: int, orientation: QtC.Qt.Orientation, role: int = ...):
        if role != QtC.Qt.ItemDataRole.DisplayRole:
            return QtC.QVariant()
        if orientation == QtC.Qt.Orientation.Horizontal:
            return TxM.add_spaces_camel(self.rootItem.data(section))
        return QtC.QVariant()

    def setData(self, index: QtC.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if not index.isValid():
            return False
        if role == QtC.Qt.ItemDataRole.EditRole:  # If item is edited
            item = index.internalPointer()
            column = index.column()
            if item.setData(column, value):
                self.dataChanged.emit(index, index)
                return True





import typing
from PyQt6 import QtCore as QtC
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6.uic import loadUi
import sys

# Working off of examples from Qt and PyQt:
# https://doc-snapshots.qt.io/qtforpython-dev/overviews/qtwidgets-itemviews-simpletreemodel-example.html


class TreeItem:
    def __init__(self):
        self.table = None
        self.itemData = None
        self.parentItem = []
        self.childItems = []

    def __del__(self):
        del self.childItems

    def setData(self, table, data):
        self.table = table
        self.itemData = data
        self.appendChild()
        self.parent()
        
    def appendChild(self):
        # add all child items
        if self.itemData is None or type(self.itemData[0]) is not int:
            pass
        else:
            item_id = self.itemData[0]
            query = QtS.QSqlQuery()
            if self.table == 'Ages':
                id_col = 'ParentAgeID'
            query.prepare(f'SELECT * FROM {self.table} WHERE {id_col} = {item_id}')
            query.exec()
            while query.next():
                child_data = []
                column_indexes = self.columnCount() - 1
                for c in range(column_indexes):
                    child_data.append(query.value(c))
                self.childItems.append(child_data)

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
            item_id = self.itemData[0]
            parent_id = self.itemData[1]
            query = QtS.QSqlQuery()
            if self.table == 'Ages':
                pid_col = 'ParentAgeID'
            # Select all with the same parent ID as the item
            query.prepare(f'SELECT * FROM {self.table} WHERE {pid_col} = {parent_id}')
            query.exec()
            r = 0
            while query.next():
                if query.value(0) == item_id:
                    return r
                else:
                    r += 1
        else:
            return 0

    def columnCount(self):
        # number of columns in input data
        return len(self.itemData)

    def data(self, column: int):
        # get data at given column
        if column < 0 or column >= len(self.itemData):
            return QtC.QVariant()
        else:
            return self.itemData.at(column)

    def parent(self):
        # parent for given item
        if self.itemData is None or type(self.itemData[1]) is not int:
            return None
        else:
            parent_id = self.itemData[1]
            query = QtS.QSqlQuery()
            if self.table == 'Ages':
                id_col = 'AgeID'
            query.prepare(f'SELECT * FROM {self.table} WHERE {id_col} = {parent_id}')
            query.exec()
            while query.next():
                parent_data = []
                i = 0
                for item in self.itemData:
                    parent_data.append(query.value(i))
                    i += 1
                self.parentItem.append(parent_data)


class TreeModel(QtC.QAbstractItemModel):
    def __init__(self, table, parent):
        # database table
        super().__init__(parent)

        self.table = table
        self.rootItem = TreeItem()
        self.headers = []
        self.column_headers()
        self.parentItem = TreeItem()
        self.childItem = TreeItem()
        self.setup_model_data()

    def __del__(self):
        del self.rootItem

    def setup_model_data(self):
        query = QtS.QSqlQuery()
        query.prepare(f'SELECT * FROM {self.table} WHERE ifnull(ParentAgeID, "") = ""')
        if query.exec():
            while query.next():
                data = []
                for col in self.headers:
                    data.append(query.value(col))
                self.parentItem.setData(self.table, data)

                n_child = self.parentItem.childCount()
        else:
            print('Problem executing the query')

    def column_headers(self):
        query = QtS.QSqlQuery()
        query.prepare(f'PRAGMA table_info({self.table})')
        if query.exec():
            while query.next():
                self.headers.append(query.value(1))
            self.rootItem.setData(self.table, self.headers)

    def index(self, row: int, column: int, parent: QtC.QModelIndex = ...):
        # parent is QModelIndex
        # index for views and delegates
        if not self.hasIndex(row, column, parent):
            return QtC.QModelIndex()
        if not self.parent.isValid():
            self.parentItem = self.rootItem
        else:
            self.parentItem = TreeItem(parent.internalPointer())
            self.childItem = self.parentItem.child(row)
            if self.childItem:
                return self.createIndex(row, column, self.childItem)
            else:
                return QtC.QModelIndex()

    def parent(self, index: QtC.QModelIndex):
        if not index.isValid():
            return QtC.QModelIndex()
        self.childItem = TreeItem(index.internalPointer())
        self.parentItem = self.childItem.parentItem()
        if self.parentItem == self.rootItem:
            return QtC.QModelIndex()
        return self.createIndex(self.parentItem.row(), 0, self.parentItem)

    def rowCount(self, parent: QtC.QModelIndex = ...) -> int:
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            self.parentItem = self.rootItem
        else:
            self.parentItem = TreeItem(parent.internalPointer())
            return self.parentItem.childCount()

    def columnCount(self, parent: QtC.QModelIndex = ...) -> int:
        if parent.isValid():
            return TreeItem(parent.internalPointer()).columnCount()
        return self.rootItem.columnCount()

    def data(self, index: QtC.QModelIndex, role: int):
        if not index.isValid():
            return QtC.QVariant
        if role != QtC.Qt.ItemDataRole.DisplayRole:
            return QtC.QVariant
        item = TreeItem(index.internalPointer())
        return item.data(index.column())

    def flags(self, index: QtC.QModelIndex) -> QtC.Qt.ItemFlag:
        if not index.isValid():
            return QtC.Qt.ItemFlag.NoItemFlags
        return QtC.QAbstractItemModel.flags(index)

    def headerData(self, section: int, orientation: QtC.Qt.Orientation, role: int = ...) -> typing.Any:
        if orientation == QtC.Qt.Orientation.Horizontal and role == QtC.Qt.ItemDataRole.DisplayRole:
            return self.rootItem.data(section)
        return QtC.QVariant




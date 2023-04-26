import sys
from pathlib import Path
import sqlite3

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS


# Working off of examples from Qt and PyQt:
# https://doc-snapshots.qt.io/qtforpython-dev/overviews/qtwidgets-itemviews-simpletreemodel-example.html

class TreeItem:
    def __init__(self, data, parent):
        self.itemData = data
        self.parentItem = parent

        self.childItems = []

    def __del__(self):
        del self.childItems

    def append_child(self):
        # add all child items
        for item in self.itemData:
            self.childItems.append(item)

    def child(self, row: int):
        # child in given row
        if row < 0 or row >= len(self.childItems):
            return None
        else:
            pass  # return child item at given row

    def childCount(self):
        # number of children
        return self.childItems.count()

    def row(self):
        # row of item in its parent's list of children
        if self.parentItem:
            # return self.parentItem.childItems.indexOf(TreeItem(self))
            pass
        else:
            return 0

    def columnCount(self):
        # number of columns in input data
        return self.itemData.count()

    def data(self, column: int):
        # get data at given column
        if column < 0 or column >= len(self.itemData):
            return QtC.QVariant()
        else:
            return self.itemData.at(column)

    def parent(self):
        # parent for given item
        pass


class TreeModel(QtC.QAbstractItemModel):
    def __init__(self, data, parent):
        super().__init__(parent)

        self.rootItem = TreeItem({})  # pass column headings to TreeItem
        self.parentItem = TreeItem()
        self.childItem = TreeItem()
        self.setupModelData(data.split('\n'), self.rootItem)

    def __del__(self):
        del self.rootItem

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
        self.parentItem = TreeItem()
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


def build_age_tree(self):
    age_tree_model = TreeModel()
    query = QtS.QSqlQuery()
    query.prepare("SELECT * FROM Ages")
    query.exec()
    while query.next():
        age_item = AgeItem(query.value(2))
        root_node.appendRow(age_item)

    return age_tree_model


class UnitTreeModel(QtG.QStandardItemModel):
    def __init__(self, db):
        super().__init__()

        self.db = db

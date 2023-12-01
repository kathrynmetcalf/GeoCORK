import typing
from PyQt6 import QtCore as QtC
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6.uic import loadUi
import Functions.Text_manipulations as TxM


class TreeItem:
    def __init__(self, itemData: QtS.QSqlRecord, parentItem):
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
        field = self.itemData.field(column)
        self.itemData.setValue(field.name(), value)

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
        self.headers = self.column_headers()
        self.rootItem = TreeItem(None, None)
        # self.rootItem = TreeItem(("ID", "Parent ID", "Name", "Description", "Created", "Modified"), None)
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
        if parent_id == 0:
            self.sourceModel.setFilter(f'{self.headers[1]} IS Null')
        else:
            self.sourceModel.setFilter(f'{self.headers[1]} = {parent_id}')
        child_ids = []
        for row in range(self.sourceModel.rowCount()):
            # store each child ID in a list
            record = self.sourceModel.record(row)
            child_ids.append(record.value(0))
        return child_ids

    def add_to_tree(self, child_ids: list, parent: TreeItem):
        for item_id in child_ids:
            # find entry with this item ID
            self.sourceModel.setFilter(f'{self.headers[0]} = {item_id}')
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
        headers = []
        query = QtS.QSqlQuery()
        query.prepare(f'PRAGMA table_info({self.table})')
        if query.exec():
            while query.next():
                headers.append(query.value(1))
        return headers

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

    def columnCount(self, parent: QtC.QModelIndex = ...) -> int:
        # return 1
        return len(self.headers)

    def data(self, index: QtC.QModelIndex = ..., role: int = ...):
        if not index.isValid():
            return None
        item = index.internalPointer()
        if role == QtC.Qt.ItemDataRole.DisplayRole:
            return item.data(index.column())
        return None

    def mapToSource(self, index: QtC.QModelIndex):
        if not index.isValid():
            return QtC.QModelIndex()
        return self.index(index.column(), index.row())

    def mapFromSource(self, sourceIndex: QtC.QModelIndex):
        if not sourceIndex.isValid():
            return QtC.QModelIndex()
        return self.index(sourceIndex.column(), sourceIndex.row())

    def flags(self, index: QtC.QModelIndex) -> QtC.Qt.ItemFlag:
        if not index.isValid():
            return QtC.Qt.ItemFlag.NoItemFlags
        return QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable

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
            return self.sourceModel.setData(self.sourceModel.index(index.row(), index.column()), value, role)





import typing
from PyQt6 import QtCore as QtC
from PyQt6 import QtSql as QtS
from PyQt6 import QtTest as QtT
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
        """
        Create a tree item with given data and parent item
        Parameters
        ----------
        itemData: SQL record from QSqlTableModel
        parentItem: parent tree item
        """
        self.itemData = itemData
        self.parentItem = parentItem
        self.childItems = []

    def __del__(self):
        """
        Deletes all children of deleted item
        """
        for child in self.childItems:
            del child
        del self.childItems
        
    def appendChild(self, child_item):
        """
        Add each child item
        Parameters
        ----------
        child_item
        """
        # add each child item
        self.childItems.append(child_item)

    def removeChild(self, row: int):
        """
        Remove a child item at a position
        Parameters
        ----------
        row: number of child in list of its parent's children
        """
        # remove a child item at a position
        if row < 0 or row >= len(self.childItems):
            return False
        else:
            self.childItems.remove(row)
            return True

    def child(self, row: int):
        """
        Return the # row child of the item, or none if the row is invalid or there are no children
        Parameters
        ----------
        row
        Returns
        -------
        None or child item
        """
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
            value = self.itemData.value(column)
            return value

    def setData(self, column: int, value: typing.Any):
        if column < 0 or column >= self.itemData.count():
            return False
        else:
            field = self.itemData.field(column)
            self.itemData.setValue(field.name(), value)
            return True

    def parent(self):
        # parent for given item
        if self.itemData is None:
            return None
        else:
            return self.parentItem


class TreeModel(QtC.QAbstractProxyModel):
    def __init__(self, sourceModel: QtS.QSqlTableModel, parent=None):
        # database table
        super().__init__(parent)

        self.sourceModel = sourceModel
        self.sourceHeaders = []
        self.proxyHeaders = []
        self.column_headers()
        self.rootItem = TreeItem(QtS.QSqlRecord(), None)
        self.parentItem = TreeItem(QtS.QSqlRecord(), None)
        self.childItem = TreeItem(QtS.QSqlRecord(), None)
        self.setup_model_data()
        self.sourceModel.setFilter("")
        self.testModelIndexing(self.rootItem)

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
        parent_id_header = TxM.remove_spaces(self.sourceHeaders[1])
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
            item_id_header = TxM.remove_spaces(self.sourceHeaders[0])
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
            self.sourceHeaders.append(self.sourceModel.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            if col == 0:
                # Label the first column with the item name
                self.proxyHeaders.append(self.sourceModel.headerData(2, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            elif col == 1:
                # Label the second column with the item ID
                self.proxyHeaders.append(self.sourceModel.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            elif col == 2:
                # Label the third column with the parent ID
                self.proxyHeaders.append(self.sourceModel.headerData(1, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            else:
                self.proxyHeaders.append(self.sourceModel.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            # print(f'{col} header is {self.headers[col]}')

    def getItem(self, index: QtC.QModelIndex) -> TreeItem: # returns tree item
        if not index.isValid():
            # print("getItem root")
            return self.rootItem
        else:
            item = index.internalPointer()
            # print(f'Get item {item.data(2)}')
            return item

    def index(self, row: int, column: int, parent: QtC.QModelIndex = ...) -> QtC.QModelIndex:
        # Given row, column, and parent, create an index for a child item at row and column
        # First check if parent is valid and parent item exists
        # Then get the child at the specified row and create an index for it
        # index for views and delegates
        if not self.hasIndex(row, column, parent):
            # print("index invalid")
            return QtC.QModelIndex()
        if parent.isValid():
            parentItem = self.getItem(parent)
            # print(f'index parent is {parentItem.data(2)}')
        else:
            # print("index parent is the root")
            parentItem = self.rootItem
        if not parentItem:
            return QtC.QModelIndex()
        if row < 0 or row > self.rowCount(parent):
            return QtC.QModelIndex()
        if column < 0 or column > self.columnCount(parent):
            return QtC.QModelIndex()
        item = parentItem.child(row)
        if item:
            # print(f"indexing valid item {item.data(2)}")
            return self.createIndex(row, column, item)
        else:
            # print("no item")
            return QtC.QModelIndex()

    def parent(self, index: QtC.QModelIndex):
        # Given index, find parent and create index for parent item
        if not index.isValid():
            # print("This is the root, so it doesn't have a parent")
            return QtC.QModelIndex()
        item = self.getItem(index)
        parentItem = item.parent()
        if parentItem == self.rootItem or not parentItem:
            return QtC.QModelIndex()
        # print(f'Parent item is {parentItem.data(2)}')
        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent: QtC.QModelIndex = ...) -> int:
        if not parent.isValid():
            # print("Root rows are the same as source model")
            return self.sourceModel.rowCount()
        else:
            parentItem = self.getItem(parent)
        if parent.column() > 0:
            return 0
        else:
            # print(f'Parent {parentItem.data(2)} has {parentItem.childCount()} children')
            return parentItem.childCount()

    def columnCount(self, parent: QtC.QModelIndex = ...) -> int:
        # print(f'Parent index for columns is at {parent.row()},{parent.column()}')
        if not parent.isValid():
            # print(f'Columns in root same as source model: {self.sourceModel.columnCount()}')
            return self.sourceModel.columnCount()
        elif parent.column() > 0:
            # print("Columns >0 have no subcolumns")
            return 0
        else:
            parentItem = self.getItem(parent)
            parentName = parentItem.data(2)
            ncols = parentItem.columnCount()
            # print(f'{ncols} columns in {parentName}')
            return ncols

    def hasChildren(self, parent: QtC.QModelIndex = ...):
        if not parent.isValid():
            # print("Root has children")
            return True
        parentItem = self.getItem(parent)
        if parentItem.childCount() > 0:
            # print(f'{parentItem.data(2)} has children')
            return True
        # print(f'{parentItem.data(2)} has no children')
        return False

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            # print("No data for root item")
            item = self.rootItem
        else:
            item = self.getItem(index)
        if role == QtC.Qt.ItemDataRole.DisplayRole or role == QtC.Qt.ItemDataRole.EditRole:
            if index.column() == 0:
                # Show name in first column
                return item.data(2)
            elif index.column() == 1:
                # Show item ID in second column
                return item.data(0)
            elif index.column() == 2:
                # Show parent ID in third column
                return item.data(1)
            else:
                return item.data(index.column())
        return None

    def setData(self, index: QtC.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if not index.isValid():
            # print("Root has no data to set")
            return False
        if role == QtC.Qt.ItemDataRole.EditRole:
            sourceIndex = self.mapToSource(index)
            if sourceIndex.isValid():
                self.sourceModel.setData(sourceIndex, value, role)
                return True

    def mapToSource(self, proxy_index: QtC.QModelIndex) -> QtC.QModelIndex:
        # print(f'mapping proxy index {proxy_index.row()},{proxy_index.column()}')
        if not proxy_index.isValid() or not self.sourceModel:
            # print("proxy root maps to source root")
            return QtC.QModelIndex()
        if not isinstance(self.sourceModel, QtS.QSqlTableModel):
            QtC.qWarning("QSortFilterProxyModel: index from wrong model passed to mapToSource")
            return QtC.QModelIndex()
        proxyCol = proxy_index.column()
        item = self.getItem(proxy_index)
        # print(f"Mapping valid item {item.data(2)}")
        itemID = item.data(0)
        for row in range(self.sourceModel.rowCount()):
            record = self.sourceModel.record(row)
            if record.value(0) == itemID:
                sourceRow = row
                break
        try:
            sourceRow # Check if the variable has been assigned
        except NameError: # If not
            return QtC.QModelIndex()
        if proxyCol == 0:  # first column is item name which maps to third column in source model
            sourceCol = 2
        elif proxyCol == 1:  # second column is item ID which maps to first column in source model
            sourceCol = 0
        elif proxyCol == 2:  # third column is parent ID which maps to second column in source model
            sourceCol = 1
        else:
            sourceCol = proxyCol
        # print(f'Proxy index {proxy_index.row()},{proxy_index.column()} maps to source index {sourceRow},{sourceCol}')
        return self.sourceModel.index(sourceRow, sourceCol, QtC.QModelIndex())

    def mapFromSource(self, sourceIndex: QtC.QModelIndex) -> QtC.QModelIndex:
        if not sourceIndex.isValid():
            # print("source root maps to proxy root")
            return QtC.QModelIndex()
        sourceRow = sourceIndex.row()
        sourceCol = sourceIndex.column()
        if sourceCol == 0:  # first column is item ID which maps to second column in proxy model
            proxyCol = 1
        elif sourceCol == 1:  # second column is parent ID which maps to third column in proxy model
            proxyCol = 2
        elif sourceCol == 2:  # third column is item name which maps to first column in proxy model
            proxyCol = 0
        else:
            proxyCol = sourceCol  # same column as table model
        record = self.sourceModel.record(sourceRow)
        itemID = record.value(0)
        item = self.findIDinTree(itemID)
        proxyRow = item.row()  # row number of item in its parent's child list
        parentItem = item.parent()
        if parentItem == self.rootItem:
            parentIndex = QtC.QModelIndex()
        else:
            parentIndex = self.createIndex(parentItem.row(), proxyCol, parentItem)
        return self.index(proxyRow, proxyCol, parentIndex)

    def findIDinTree(self, itemID: int) -> TreeItem: # returns tree item with itemID
        def search(itemIndex: QtC.QModelIndex):
            item = self.getItem(itemIndex)
            # print(f'Searching {item.data(2)}')
            if not itemIndex.isValid():
                if item != self.rootItem:
                    print(f'Invalid index for {item.data(2)}')
            if item.data(0) == itemID:
                # print(f'Found {itemID} in {item.data(2)}')
                return item
            for row in range(item.childCount()):
                childIndex = self.index(row, 0, itemIndex)
                result = search(childIndex)
                if result:
                    return result
            return None
        return search(QtC.QModelIndex())

    def flags(self, index: QtC.QModelIndex) -> QtC.Qt.ItemFlag:
        if not index.isValid():
            # print("root doesn't have flags")
            return QtC.Qt.ItemFlag.NoItemFlags
        if index.column() == 1 or index.column() == 2 or index.column() == self.sourceModel.columnCount() -1 or index.column() == self.sourceModel.columnCount() -2:
            # If the column is the ID, parent ID, created timestamp, or modified timestamp, it is not editable
            return QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable
        else:
            return QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable

    def headerData(self, section: int, orientation: QtC.Qt.Orientation, role: int = ...):
        if role != QtC.Qt.ItemDataRole.DisplayRole:
            return QtC.QVariant()
        if orientation == QtC.Qt.Orientation.Horizontal:
            return TxM.add_spaces_camel(self.proxyHeaders[section])
        return QtC.QVariant()

    def setData(self, index: QtC.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if not index.isValid():
            # print("root has no data to set")
            return False
        if role == QtC.Qt.ItemDataRole.EditRole:  # If item is edited
            sourceIndex = self.mapToSource(index)
            self.sourceModel.setData(self.sourceModel.createIndex(sourceIndex.row(), sourceIndex.column()), value, role)
            return True

    def testModelIndexing(self, parentItem: TreeItem):
        if parentItem == self.rootItem:
            parentName = "root"
            parentIndex = QtC.QModelIndex()
        else:
            parentIndex = self.createIndex(parentItem.row(), 0, parentItem)
            parentName = parentItem.data(2)
        # print(f'Parent {parentName} has {parentItem.childCount()} children')
        cols = self.sourceModel.columnCount()
        for row in range(parentItem.childCount()):
            item = parentItem.child(row)
            itemName = item.data(2)
            for col in range(cols):
                # index_a = self.index(row, col, parentIndex)
                # index_b = self.index(row, col, parentIndex)
                # if index_a.isValid() and index_b.isValid():
                    # print(f"Item {itemName} index {row},{col} in {parentName} is valid")
                # else:
                    # print(f"Error: Item {itemName} index {row},{col} in {parentName} is invalid")
                    # return
                itemIndex = self.index(row, col, parentIndex)
                if itemIndex.isValid():
                    data = self.data(itemIndex, QtC.Qt.ItemDataRole.DisplayRole)
                    # print(f"{itemName} at row {row}, column {col}: {data} should match SQL table data: {self.sourceModel.data(sourceIndex, QtC.Qt.ItemDataRole.DisplayRole)}")
                    sourceIndex = self.mapToSource(itemIndex)
                # else:
                    # print(f"Error: Invalid index in {parentName} at row {row}, column {col}")
            self.testModelIndexing(item)


if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    db_file = '../TestSchema.db'
    db = QtS.QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName(db_file)
    model = QtS.QSqlTableModel()
    model.setTable('Units')
    model.select()
    tree_model = TreeModel(model, None)

    tester = QtT.QAbstractItemModelTester(tree_model, QtT.QAbstractItemModelTester.FailureReportingMode.Warning)




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
        self.rootItem = TreeItem(QtS.QSqlRecord(), None)
        self.parentItem = TreeItem(QtS.QSqlRecord(), None)
        self.childItem = TreeItem(QtS.QSqlRecord(), None)
        self.setup_model_data()
        self.sourceModel.setFilter("")
        # self.testModelIndexing(self.rootItem)
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
            # print(f'{col} header is {self.headers[col]}')

    def getItem(self, index: QtC.QModelIndex) -> TreeItem: # returns tree item
        if not index.isValid():
            print("getItem root")
            return self.rootItem
        else:
            item = index.internalPointer()
            print(f'Get item {item.data(2)}')
            return item

    def index(self, row: int, column: int, parent: QtC.QModelIndex = ...):
    # Given row, column, and parent, create an index for a child item at row and column
    # First check if parent is valid and parent item exists
    # Then get the child at the specified row and create an index for it
    # index for views and delegates
        if parent.isValid():
            parentItem = parent.internalPointer()
        else:
            print("index parent is the root")
            parentItem = self.rootItem
        if not parentItem:
            return QtC.QModelIndex()
        if row < 0 or row > self.rowCount(parent):
            return QtC.QModelIndex()
        if column < 0 or column > self.columnCount(parent):
            return QtC.QModelIndex()
        item = parentItem.child(row)
        if item:
            print(f"indexing valid item {item.data(2)}")
            return self.createIndex(row, column, item)
        else:
            print("no item")
            return QtC.QModelIndex()

    def parent(self, index: QtC.QModelIndex):
    # Given index, find parent and create index for parent item
        if not index.isValid():
            print("This is the root, so it doesn't have a parent")
            return QtC.QModelIndex()
        item = index.internalPointer()
        parentItem = item.parent()
        if not parentItem:
            return QtC.QModelIndex()
        print(f'Parent item is {parentItem.data(2)}')
        return self.createIndex(parentItem.row(), 0, parentItem)


    def rowCount(self, parent: QtC.QModelIndex = ...) -> int:
        if not parent.isValid():
            print("rowCount of root")
            parentItem = self.rootItem
        else:
            parentItem = self.getItem(parent)
        print(f'Parent {parentItem.data(2)} has {parentItem.childCount()} children')
        return parentItem.childCount()

    def columnCount(self, parent: QtC.QModelIndex = ...) -> int:
        print(f'Parent index for columns is at {parent.row()},{parent.column()}')
        if not parent.isValid():
            parentItem = self.rootItem
            parentName = 'root'
        else:
            parentItem = parent.internalPointer()
            parentName = parentItem.data(2)
        ncols = self.sourceModel.columnCount()
        print(f'{ncols} columns in {parentName}')
        return ncols

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            print("No data for root item")
            item = self.rootItem
        else:
            item = self.getItem(index)
        if role == QtC.Qt.ItemDataRole.DisplayRole:
            return item.data(index.column())
        return None

    def mapToSource(self, proxy_index: QtC.QModelIndex) -> QtC.QModelIndex:
        print(f'mapping proxy index {proxy_index.row()},{proxy_index.column()}')
        if not proxy_index.isValid() or not self.sourceModel:
            print("proxy root maps to source root")
            return QtC.QModelIndex()
        if not isinstance(self.sourceModel, QtS.QSqlTableModel):
            QtC.qWarning("QSortFilterProxyModel: index from wrong model passed to mapToSource")
            return QtC.QModelIndex()
        proxyCol = proxy_index.column()
        item = self.getItem(proxy_index)
        print(f"Mapping valid item {item.data(2)}")
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
        sourceCol = proxyCol
        return self.index(sourceRow, sourceCol, QtC.QModelIndex())

    def mapFromSource(self, sourceIndex: QtC.QModelIndex) -> QtC.QModelIndex:
        if not sourceIndex.isValid():
            print("source root maps to proxy root")
            return QtC.QModelIndex()
        sourceRow = sourceIndex.row()
        sourceCol = sourceIndex.column()
        proxyCol = sourceCol  # same column as table model
        record = self.sourceModel.record(sourceRow)
        itemID = record.value(0)
        item = self.findIDinTree(itemID, self.rootItem, QtC.QModelIndex())
        proxyRow = item.row()  # row number of item in its parent's child list
        parentItem = item.parent()
        parentIndex = self.createIndex(parentItem.row(), proxyCol, parentItem)
        return self.index(proxyRow, proxyCol, parentIndex)

    def findIDinTree(self, itemID: int, parentItem: TreeItem, parentIndex: QtC.QModelIndex) -> TreeItem: # returns tree item with itemID
        for childItem in parentItem.childItems:
            if childItem.data(0) == itemID:
                item = childItem
                return item
            else:
                row = childItem.row()
                childIndex = self.index(row, 0, parentIndex)
                self.findIDinTree(itemID, childItem, childIndex)

    def flags(self, index: QtC.QModelIndex) -> QtC.Qt.ItemFlag:
        if not index.isValid():
            print("root doesn't have flags")
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
            print("root has no data to set")
            return False
        if role == QtC.Qt.ItemDataRole.EditRole:  # If item is edited
            sourceIndex = self.mapToSource(index)
            self.sourceModel.setData(self.sourceModel.createIndex(sourceIndex.row(), sourceIndex.column()), value, role)
            return True

    def testModelIndexing(self, parentItem: TreeItem):
        parentIndex = self.createIndex(parentItem.row(), 0, parentItem)
        parentName = parentItem.data(2)
        cols = self.sourceModel.columnCount()
        for row in range(parentItem.childCount()):
            item = parentItem.child(row)
            for col in range(cols):
                itemIndex = self.index(row, col, parentIndex)
                if itemIndex.isValid():
                    data = self.data(itemIndex, QtC.Qt.ItemDataRole.DisplayRole)
                    print(f"Data in {parentName} at row {row}, column {col}: {data}")
                    sourceIndex = self.mapToSource(itemIndex)
                    print(f"Should match SQL table data: {self.sourceModel.data(sourceIndex, QtC.Qt.ItemDataRole.DisplayRole)}")
                else:
                    print(f"Error: Invalid index in {parentName} at row {row}, column {col}")
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




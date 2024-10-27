import typing
# from formatter import NullWriter
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtSql import QSqlTableModel, QSqlDatabase
from PyQt6 import QtTest as QtT
from numpy import integer

import Functions.Errors as Er
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

    def setRecord(self, record: QtS.QSqlRecord):
        self.itemData = record

    def parent(self):
        # parent for given item
        if self.itemData is None:
            return None
        else:
            return self.parentItem


class TreeModel(QtC.QAbstractProxyModel):
    dataEdited = QtC.pyqtSignal()
    def __init__(self, source_model=QSqlTableModel(), parent=None):
        # database table
        super().__init__(parent)

        self.source_model = source_model
        self.base_filter = ""
        self.base_filter_sql = ""
        self.db = QSqlDatabase()
        self.table = ''
        self.sourceHeaders = []
        self.proxyHeaders = []
        self.rootItem = TreeItem(QtS.QSqlRecord(), None)
        self.parentItem = TreeItem(QtS.QSqlRecord(), None)
        self.childItem = TreeItem(QtS.QSqlRecord(), None)

        if self.source_model.tableName():
            # If a table model with a valid table was passed, set the source model and create the tree
            self.setSourceModel(self.source_model)

    def sourceModel(self):
        return self.source_model

    def setSourceModel(self, source_model: QSqlTableModel):
        self.source_model = source_model
        self.db = self.source_model.database()
        self.table = self.source_model.tableName()
        self.base_filter = f"{self.source_model.filter()}"
        if len(self.base_filter) > 0:
            self.base_filter_sql = f"{self.base_filter} AND "
        else:
            self.base_filter_sql = self.base_filter
        self.sourceHeaders = []
        self.proxyHeaders = []
        self.column_headers()
        self.header_variables()
        self.rootItem = TreeItem(QtS.QSqlRecord(), None)
        self.parentItem = TreeItem(QtS.QSqlRecord(), None)
        self.childItem = TreeItem(QtS.QSqlRecord(), None)
        self.setup_model_data()
        self.source_model.setFilter(self.base_filter)

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
        # Find children of a given ID using the source_model's filtered data
        self.source_model.setFilter(f"{self.base_filter_sql}  "
                                    f"{self.parent_id_header} is {parent_id if parent_id != 0 else 'NULL'}")
        # print(self.source_model.filter())
        child_ids = []
        for row in range(self.source_model.rowCount()):
            child_ids.append(self.source_model.record(row).value(0))

        # print("childIds:" + str(child_ids))

        return child_ids

    def add_to_tree(self, child_ids: list, parent: TreeItem):
        for child_id in child_ids:
            self.source_model.setFilter(f"{self.base_filter_sql} {self.id_header} is {child_id}")
            if self.source_model.rowCount() > 0:
                record = self.source_model.record(0)

                item = TreeItem(record, parent)
                parent.appendChild(item)
                new_child_ids = self.find_children(child_id)
                self.add_to_tree(new_child_ids, item)

    def add_top_item(self, data):
        TreeItem(data, 0)

    def column_headers(self):
        for col in range(self.source_model.columnCount()):
            self.sourceHeaders.append(self.source_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            if col == 0:
                # Label the first column with the item name
                self.proxyHeaders.append(self.source_model.headerData(3, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            elif col == 1:
                # Label the second column with the item ID
                self.proxyHeaders.append(self.source_model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            elif col == 2:
                # Label the third column with the parent ID
                self.proxyHeaders.append(self.source_model.headerData(1, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            elif col == 3:
                # Label the fourth column with the parent row
                self.proxyHeaders.append(self.source_model.headerData(2, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            else:
                self.proxyHeaders.append(self.source_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            # print(f'{col} header is {self.headers[col]}')

    def header_variables(self):
        self.id_header = self.sourceHeaders[0]
        self.parent_id_header = self.sourceHeaders[1]
        self.parent_row_header = self.sourceHeaders[2]
        self.item_name_header = self.sourceHeaders[3]
        self.item_description_header = self.sourceHeaders[4]

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

    def rowCount(self, parent: QtC.QModelIndex = QtC.QModelIndex) -> int:
        if not parent.isValid():
            # print("Root rows are the same as source model")
            parentItem = self.rootItem
        else:
            parentItem = self.getItem(parent)
        # if parent.column() > 0:
        #     return 0
        # else:
        #     # print(f'Parent {parentItem.data(3)} has {parentItem.childCount()} children')
        #     return parentItem.childCount()
        return parentItem.childCount()

    def columnCount(self, parent: QtC.QModelIndex = ...) -> int:
        return self.source_model.columnCount()

    def hasChildren(self, parent: QtC.QModelIndex = ...):
        if not parent.isValid():
            # print("Root has children")
            return True
        parentItem = self.getItem(parent)
        if parentItem.childCount() > 0:
            # print(f'{parentItem.data(3)} has children')
            return True
        # print(f'{parentItem.data(3)} has no children')
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
                return item.data(3)
            elif index.column() == 1:
                # Show item ID in second column
                return item.data(0)
            elif index.column() == 2:
                # Show parent ID in third column
                return item.data(1)
            elif index.column() == 3:
                # Show parent ID in third column
                return item.data(2)
            else:
                return item.data(index.column())
        return None

    def setData(self, index: QtC.QModelIndex, value: typing.Any, role: QtC.Qt.ItemDataRole = ...) -> bool:
        if not index.isValid():
            # print("Root has no data to set")
            return False
        if role == QtC.Qt.ItemDataRole.EditRole:
            sourceIndex = self.mapToSource(index)
            if sourceIndex.isValid():
                # update the source model
                treeItem = self.getItem(index)
                if index.column() == 0:
                    # Show name in first column
                    dataCol = 3
                elif index.column() == 1:
                    # Show item ID in second column
                    dataCol = 0
                elif index.column() == 2:
                    # Show parent ID in third column
                    dataCol = 1
                elif index.column() == 3:
                    # Show parent row in third column
                    dataCol = 2
                else:
                    dataCol = index.column()
                # Get the updated modified timestamp
                mcol = self.source_model.columnCount() - 1
                sourcemIndex = self.source_model.index(sourceIndex.row(), mcol, QtC.QModelIndex())
                proxymIndex = self.mapFromSource(sourcemIndex)
                if proxymIndex.isValid() and sourcemIndex.isValid():
                    # If the changed data index and the modified timestamp index are valid for both models, change the data
                    try:
                        self.source_model.setData(sourceIndex, value, role)
                    except:
                        # print(f'Error setting data in source model at {sourceIndex.row()},{sourceIndex.column()}')
                        return False
                    modified = self.source_model.data(sourcemIndex, QtC.Qt.ItemDataRole.DisplayRole)
                    treeItem.setData(dataCol, value)
                    self.dataChanged.emit(index, index)
                    treeItem.setData(mcol, modified)
                    self.dataChanged.emit(index, index)
                    return True
                else:
                    # print(f'Error setting data in proxy model at {index.row()},{index.column()}')
                    return False
        return False

    def moveItem(self, itemID: int, row: int, pID: str):
        """
        Move an item to a new parent and parent row
        @param itemID: unique ID of the item to move
        @param row: new parent row number for the item
        @param pID: new parent ID for the item, represented by a string to use in the setFilter method, either 'IS NULL' or 'is parentID'
        @return: True if the item was successfully moved, None if there was an error
        """
        # Try making change to database, then reset the tree model
        if pID == 'IS NULL':
            parentID = 'NULL'
        else:
            parentID = int(pID[2:])
        self.source_model.setFilter(f"{self.base_filter_sql}  {self.id_header} is {itemID} AND {self.parent_id_header} {pID} AND {self.parent_row_header} is {row}")
        if self.source_model.rowCount() > 0:
            # If the item is already in the correct place, do nothing
            # print(f'No change in parent or row for item {itemID}')
            return None
        self.source_model.setFilter(f"{self.base_filter_sql}  {self.id_header} is {itemID}")  # Only one record for each item ID
        oldParentID = self.source_model.record(0).value(1)  # Get the current parent
        # ID
        if isinstance(oldParentID, int):
            opID = f'= {oldParentID}'
        else:
            opID = 'IS NULL'
            oldParentID = 'NULL'
        oldParentRow = self.source_model.record(0).value(2)  # Get the current parent row
        # Look for children of the new parent at and below the point of insertion, order them by parent row from largest to smallest
        filtered_model = QtS.QSqlQueryModel()
        filtered_model.setQuery(f"SELECT * FROM {self.table} WHERE {self.parent_id_header} {pID} AND {self.parent_row_header} >= {row} ORDER BY {self.parent_row_header} DESC")
        childCount = filtered_model.rowCount()
        if childCount > 0:
            # If the parent already has children and the new one is replacing an existing row, update their parent rows
            for child in range(childCount):  # Starting with the last child
                # increase the parent row by 1 for each child after the target row
                childID = filtered_model.record(child).value(0)
                currentParentRow = filtered_model.record(child).value(2)
                newParentRow = currentParentRow + 1
                self.source_model.setFilter(self.base_filter)  # Reset the filter
                if not self.update_parent_info(childID, parentID, newParentRow):
                    return None
                if currentParentRow == row:
                    # Now update the moved item into the new space
                    self.source_model.setFilter(self.base_filter)  # Reset the filter
                    if not self.update_parent_info(itemID, parentID, row):
                        return None
        else: # no children to update
            self.source_model.setFilter(self.base_filter)  # Reset the filter
            if not self.update_parent_info(itemID, parentID, row):
                return None
        # Look for remaining children of the old parent whose parent rows need to be updated, order them by parent row from smallest to largest
        self.source_model.setFilter(
            f"{self.base_filter_sql}  {self.parent_id_header} {opID} AND {self.parent_row_header} > {oldParentRow} ORDER BY {self.parent_row_header} ASC")
        childCount = self.source_model.rowCount()
        if childCount > 0:
            currentRows = []
            childIDs = []
            for child in range(childCount):  # Starting with the first child to update, save important values before the model filter is reset
                # decrease the parent row by 1 for each child after the old parent row
                currentRows.append(self.source_model.record(child).value(2))
                childIDs.append(self.source_model.record(child).value(0))
            for child in range(childCount):
                newParentRow = currentRows[child] - 1
                self.source_model.setFilter(self.base_filter)  # Reset the filter
                if not self.update_parent_info(childIDs[child], oldParentID, newParentRow):
                    return None
        self.source_model.setFilter(self.base_filter)  # Reset the filter
        return True

    def update_parent_info(self, itemID: int, parentID, parentRow: int):
        # Update the parent ID and parent row for a given item ID
        query = QtS.QSqlQuery(self.db)
        query.prepare(f'UPDATE {self.table} SET {self.parent_id_header} = :parentID, {self.parent_row_header} = :parentRow WHERE {self.id_header} = :itemID')
        if parentID == 'NULL':
            query.bindValue(':parentID', QtC.QVariant())
        else:
            query.bindValue(':parentID', parentID)
        query.bindValue(':parentRow', parentRow)
        query.bindValue(':itemID', itemID)
        if not query.exec():
            # print(f'Error updating parent for {itemID}')
            return None
        else:
            # print(f'Successfully updated parent for {itemID}')
            return True

    def insertItem(self, itemName: str, itemDescription: str, parentID = None, parentRow = None):
        # Add a new item to the database, first as a top-level item, then move it to the correct parent and row
        query = QtS.QSqlQuery(self.db)
        pID = 'IS NULL'
        self.source_model.setFilter(f"{self.base_filter_sql} {self.sourceHeaders[1]} {pID}")
        childCount = self.source_model.rowCount()
        query.prepare(f'INSERT INTO {self.table}({self.parent_row_header}, {self.item_name_header}, {self.item_description_header}) VALUES(:parentRow, :itemName, :itemDescription)')
        query.bindValue(':parentRow', childCount)
        query.bindValue(':itemName', itemName)
        query.bindValue(':itemDescription', itemDescription)
        self.createSavepoint()
        if not query.exec():
            # print(f'Error inserting new item {itemName}')
            self.rollback()
            return None
        else:
            # print(f'Successfully inserted new item {itemName}')
            if parentID:
                pID = f'= {parentID}'
            else:
                pID = 'IS NULL'
            if parentRow is None:
                # If no parent row is given, the item is added to the end of the list
                self.source_model.setFilter(f"{self.base_filter_sql} {self.parent_id_header} {pID}")
                childCount = self.source_model.rowCount()
                parentRow = childCount
            self.source_model.setFilter(f"{self.base_filter_sql} {self.item_name_header} is '{itemName}'")
            itemID = self.source_model.record(0).value(0)
            if not self.moveItem(itemID, parentRow, pID):
                self.rollback()
                return None
            self.releaseSavepoint()
            self.dataEdited.emit()
            return True

    def removeItem(self, itemID: int, parentRow: int, parentID = None):
        # Remove an item and all children from the database
        del_ids = [itemID]
        def find_child_ids(parentID: int, del_ids: list):
            # Find all children of a given parent ID
            filtered_model = QtS.QSqlQueryModel()
            filtered_model.setQuery(f"SELECT * FROM {self.table} WHERE {self.parent_id_header} = {parentID}")
            # self.source_model.setFilter(f"{self.parent_id_header} = {parentID}")
            for row in range(filtered_model.rowCount()):
                record = filtered_model.record(row)
                del_ids.append(record.value(0))
                find_child_ids(record.value(0), del_ids)
            return del_ids

        del_ids = find_child_ids(itemID, del_ids)
        del_join = ', '.join([str(i) for i in del_ids])
        del_string = f'({del_join})'
        self.source_model.setFilter(self.base_filter)  # Reset the filter
        query = QtS.QSqlQuery(self.db)
        query.prepare(f'DELETE FROM {self.table} WHERE {self.id_header} IN {del_string}')
        self.createSavepoint()
        if not query.exec(): # if item and children not deleted, rollback
            # print(f'Error deleting {del_ids}')
            self.rollback()
            return None
        # else:
            # print(f'Successfully deleted {del_ids}')
        if parentID:
            pID = f'= {parentID}'
        else:
            pID = 'IS NULL'
            parentID = 'NULL'
        filtered_model = QtS.QSqlQueryModel()
        filtered_model.setQuery(f"SELECT * FROM {self.table} WHERE {self.parent_id_header} {pID} AND {self.parent_row_header} >= {parentRow} ORDER BY {self.parent_row_header} ASC")
        childCount = filtered_model.rowCount()
        if childCount > 0:
            # If the parent already has children at rows beyond the deleted one, update their parent rows to close the gap
            for child in range(childCount):  # Starting with the next child after the deleted one
                # decrease the parent row by 1 for each child after the deleted one
                childID = filtered_model.record(child).value(0)
                currentParentRow = filtered_model.record(child).value(2)
                newParentRow = currentParentRow - 1
                self.source_model.setFilter(self.base_filter)  # Reset the filter
                if not self.update_parent_info(childID, parentID, newParentRow):
                    # print(f'Error updating parent row for child {childID}')
                    self.rollback()
                    return None
        self.releaseSavepoint()
        self.dataEdited.emit()
        return True

    def mapToSource(self, proxy_index: QtC.QModelIndex) -> QtC.QModelIndex:
        # print(f'mapping proxy index {proxy_index.row()},{proxy_index.column()}')
        if not proxy_index.isValid() or not self.source_model:
            # print("proxy root maps to source root")
            return QtC.QModelIndex()
        if not isinstance(self.source_model, QtS.QSqlTableModel):
            QtC.qWarning("QSortFilterProxyModel: index from wrong model passed to mapToSource")
            return QtC.QModelIndex()
        proxyCol = proxy_index.column()
        item = self.getItem(proxy_index)
        # print(f"Mapping valid item {item.data(3)}")
        itemID = item.data(0)
        for row in range(self.source_model.rowCount()):
            record = self.source_model.record(row)
            if record.value(0) == itemID:
                sourceRow = row
                break
        try:
            sourceRow # Check if the variable has been assigned
        except NameError: # If not
            return QtC.QModelIndex()
        if proxyCol == 0:  # first column is item name which maps to fourth column in source model
            sourceCol = 3
        elif proxyCol == 1:  # second column is item ID which maps to first column in source model
            sourceCol = 0
        elif proxyCol == 2:  # third column is parent ID which maps to second column in source model
            sourceCol = 1
        elif proxyCol == 3:  # fourth column is parent row which maps to third column in source model
            sourceCol = 2
        else:
            sourceCol = proxyCol
        # print(f'Proxy index {proxy_index.row()},{proxy_index.column()} maps to source index {sourceRow},{sourceCol}')
        return self.source_model.index(sourceRow, sourceCol, QtC.QModelIndex())

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
        elif sourceCol == 2:  # third column is parent row which maps to fourth column in proxy model
            proxyCol = 3
        elif sourceCol == 3:  # fourth column is item name which maps to first column in proxy model
            proxyCol = 0
        else:
            proxyCol = sourceCol  # same column as table model
        record = self.source_model.record(sourceRow)
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
            # print(f'Searching {item.data(3)}')
            if not itemIndex.isValid():
                if item != self.rootItem:
                    # print(f'Invalid index for {item.data(3)}')
                    return None
            if item.data(0) == itemID:
                # print(f'Found {itemID} in {item.data(3)}')
                return item
            for row in range(item.childCount()):
                childIndex = self.index(row, 0, itemIndex)
                result = search(childIndex)
                if result:
                    return result
            return None
        return search(QtC.QModelIndex())

    def findIDSourceRow(self, itemID: int):
        for row in range(self.source_model.rowCount()):
            record = self.source_model.record(row)
            if record.value(0) == itemID:
                return row
        return

    def flags(self, index: QtC.QModelIndex) -> QtC.Qt.ItemFlag:
        if not index.isValid():
            # the root can be a drop destination
            return QtC.Qt.ItemFlag.ItemIsDropEnabled
        modifiedCol = self.source_model.columnCount() - 1
        createdCol = self.source_model.columnCount() - 2
        if index.column() == modifiedCol or index.column() == createdCol:
            # If the column is the created timestamp or modified timestamp, it is not editable. IDs should not be visible at all
            return QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsDragEnabled | QtC.Qt.ItemFlag.ItemIsDropEnabled
        else:
            return QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable | QtC.Qt.ItemFlag.ItemIsDragEnabled | QtC.Qt.ItemFlag.ItemIsDropEnabled

    def mimeTypes(self):
        return ['application/x-qabstractitemmodeldatalist']

    def mimeData(self, indexes):
        mimeData = QtC.QMimeData()
        encodedData = QtC.QByteArray()
        stream = QtC.QDataStream(encodedData, QtC.QIODevice.OpenModeFlag.WriteOnly)
        for index in indexes:
            if index.isValid() and index.column() == 0:
                item = self.getItem(index)
                stream.writeInt32(item.data(0))  # item ID
        mimeData.setData('application/x-qabstractitemmodeldatalist', encodedData)
        return mimeData

    def canDropMimeData(self, data, action, row, column, parent):
        if action == QtC.Qt.DropAction.IgnoreAction:
            # print("Ignoring drop action")
            return False
        if not data.hasFormat('application/x-qabstractitemmodeldatalist'):
            # print("Data format not recognized")
            return False
        return True

    def dropMimeData(self, data: QtC.QMimeData, action: QtC.Qt.DropAction, row: int, column: int, parent: QtC.QModelIndex):
        if not self.canDropMimeData(data, action, row, column, parent):
            return False
        encodedData = data.data('application/x-qabstractitemmodeldatalist')
        stream = QtC.QDataStream(encodedData, QtC.QIODevice.OpenModeFlag.ReadOnly)
        itemIDs = []
        rows = []
        parentID = self.getItem(parent).data(0)
        if isinstance(parentID, int):
            pID = f'= {parentID}'
        else:   # If the parent ID is not an integer
            pID = 'IS NULL'
        self.createSavepoint()
        while not stream.atEnd():
            itemIDs.append(stream.readInt32())
            if row == -1:
                # If the row is -1, the item is being moved to the end of the list
                self.source_model.setFilter(f"{self.base_filter_sql} {self.sourceHeaders[1]} {pID}")
                childCount = self.source_model.rowCount()
                row = childCount
            rows.append(row)
            row += 1
        for move in range(len(itemIDs)):
            if not self.moveItem(itemIDs[move], rows[move], pID):
                # Move was unsuccessful
                self.rollback()
                return False
        # All moves were successful
        self.source_model.setFilter(self.base_filter)  # Reset the filter
        self.releaseSavepoint()
        # Emit signal so that the view can rebuild the tree model
        self.dataEdited.emit()
        return True

    def supportedDropActions(self):
        return QtC.Qt.DropAction.CopyAction | QtC.Qt.DropAction.MoveAction

    def supportedDragActions(self):
        return QtC.Qt.DropAction.CopyAction | QtC.Qt.DropAction.MoveAction

    def headerData(self, section: int, orientation: QtC.Qt.Orientation, role: int = ...):
        if role != QtC.Qt.ItemDataRole.DisplayRole:
            return QtC.QVariant()
        if orientation == QtC.Qt.Orientation.Horizontal:
            return TxM.add_spaces_camel(self.proxyHeaders[section])
        return QtC.QVariant()

    def createSavepoint(self):
        query = QtS.QSqlQuery(self.db)
        if query.exec('SAVEPOINT before_move') is False:
            errtxt = Er.savepoint_fail(self.table)
            # print(errtxt)

    def rollback(self):
        query = QtS.QSqlQuery(self.db)
        if query.exec('ROLLBACK TO SAVEPOINT before_move') is False:
            errtxt = Er.rollback_fail(self.table)
            # print(errtxt)

    def releaseSavepoint(self):
        query = QtS.QSqlQuery(self.db)
        if query.exec('RELEASE SAVEPOINT before_move') is False:
            errtxt = Er.savepoint_release_fail(self.table)
            # print(errtxt)

    def testModelIndexing(self, parentItem: TreeItem):
        if parentItem == self.rootItem:
            parentName = "root"
            parentIndex = QtC.QModelIndex()
        else:
            parentIndex = self.createIndex(parentItem.row(), 0, parentItem)
            parentName = parentItem.data(3)
        # print(f'Parent {parentName} has {parentItem.childCount()} children')
        cols = self.source_model.columnCount()
        for row in range(parentItem.childCount()):
            item = parentItem.child(row)
            itemName = item.data(3)
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
                    # print(f"{itemName} at row {row}, column {col}: {data} should match SQL table data: {self.source_model.data(sourceIndex, QtC.Qt.ItemDataRole.DisplayRole)}")
                    sourceIndex = self.mapToSource(itemIndex)
                # else:
                    # print(f"Error: Invalid index in {parentName} at row {row}, column {col}")
            self.testModelIndexing(item)


    def top_node(self, item_ids: list) -> tuple:
        def walk_tree(parent_id, item_ids: list):
            if isinstance(parent_id, int):
                pID = f'= {parent_id}'
            else:
                pID = 'IS NULL'
            filtered_model = QtS.QSqlQueryModel()
            filtered_model.setQuery(
                f"SELECT * FROM {self.table} WHERE {self.parent_id_header} {pID} ORDER BY {self.parent_row_header} ASC")
            childCount = filtered_model.rowCount()
            for child in range(childCount):
                child_id = filtered_model.record(child).value(0)
                parent_row = child
                if child_id in item_ids:
                    return parent_id, parent_row
                else:
                    walk_tree(child_id, item_ids)

        parent_id = 'Null'
        (top_parent_id, top_parent_row) = walk_tree(parent_id, item_ids)
        return top_parent_id, top_parent_row

def save_expanded_state(table: str, filter_model: QtC.QSortFilterProxyModel, treeView: QtW.QTreeView, settings: QtC.QSettings):
    expanded_ids = []

    def save_state(index):
        if index.isValid() and treeView.isExpanded(index):
            item_id = filter_model.data(index.siblingAtColumn(1))
            expanded_ids.append(item_id)
        for i in range(filter_model.rowCount(index)):
            save_state(filter_model.index(i, 0, index))

    root_index = QtC.QModelIndex()
    for i in range(filter_model.rowCount(root_index)):
        save_state(filter_model.index(i, 0, root_index))
    settings.setValue(f'expanded_ids_{table}', expanded_ids)

def restore_expanded_state(table: str, filter_model: QtC.QSortFilterProxyModel, treeView: QtW.QTreeView, settings: QtC.QSettings):
    expanded_ids = settings.value(f'expanded_ids_{table}', [])

    def restore_state(index):
        item_id = filter_model.data(index.siblingAtColumn(1))
        if item_id in expanded_ids:
            treeView.setExpanded(index, True)
        for i in range(filter_model.rowCount(index)):
            restore_state(filter_model.index(i, 0, index))

    restore_state(QtC.QModelIndex())

class CheckableTreeView(QtW.QTreeView):
    close = QtC.pyqtSignal()
    def __init__(self):
        super().__init__()
        self.expandAll()
        self.hideColumn(1)  # don't show ID column
        self.hideColumn(2)  # don't show parent ID column
        self.hideColumn(3)  # don't show parent row column
        self.setSortingEnabled(False)
        self.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
        self.clicked.connect(self.toggle_check_state)

    def toggle_check_state(self, index: QtC.QModelIndex):
        if index.isValid():
            current_state = self.model().data(index, QtC.Qt.ItemDataRole.CheckStateRole)
            new_state = QtC.Qt.CheckState.Unchecked if current_state == QtC.Qt.CheckState.Checked else QtC.Qt.CheckState.Checked
            self.model().setData(index, new_state, QtC.Qt.ItemDataRole.CheckStateRole)

class TreeCombobox(QtW.QComboBox):
    closing = QtC.pyqtSignal()
    def __init__(self):
        super().__init__()
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.closedOnLineEditClick = False
        self.treeView = CheckableTreeView()
        self.setView(self.treeView)

        self.checkable_tree_model = CheckableTreeModel()
        self.setModel(self.checkable_tree_model)

        self.lineEdit().installEventFilter(self)
        self.treeView.viewport().installEventFilter(self)
        self.checkable_tree_model.dataChanged.connect(self.update_line_edit)

    def set_line_edit_text(self, text):
        self.lineEdit().setText(text)

    def update_line_edit(self):
        current_line_edit_text = self.lineEdit().text()
        text_items = current_line_edit_text.split(',')
        index = self.treeView.currentIndex()
        if index.isValid():
            item_text = self.model().data(index, QtC.Qt.ItemDataRole.DisplayRole)
            current_state = self.model().data(index, QtC.Qt.ItemDataRole.CheckStateRole)
            if current_state == QtC.Qt.CheckState.Checked:
                if item_text not in text_items:
                    text_items.append(item_text)
            else:
                if item_text in text_items:
                    text_items.remove(item_text)
            new_line_edit_text = ','.join(text_items)
            self.lineEdit().setText(new_line_edit_text)

    def showPopup(self):
        self.treeView.expandAll()
        self.treeView.hideColumn(1)  # don't show ID column
        self.treeView.hideColumn(2)  # don't show parent ID column
        self.treeView.hideColumn(3)  # don't show parent row column
        self.treeView.setSortingEnabled(False)
        self.treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
        super().showPopup()

    def hidePopup(self):
        super().hidePopup()
        self.closing.emit()
        # self.startTimer(100)

    def eventFilter(self, obj, event):
        print(f'Event type: {event.type()}')
        if obj == self.lineEdit():
            if event.type() == QtC.QEvent.Type.MouseButtonRelease:
                if self.closedOnLineEditClick:
                    self.hidePopup()
                else:
                    self.showPopup()
                return True
            return super().eventFilter(obj, event)

        if obj == self.treeView.viewport():
            if event.type() == QtC.QEvent.Type.MouseButtonRelease:
                self.treeView.toggle_check_state(self.treeView.currentIndex())
                self.showPopup()
                # self._prevent_hide = True
                return True
            return super().eventFilter(obj, event)

        if event.type() == QtC.QEvent.Type.WindowDeactivate:
            print(f'Window deactivated for object: {obj}')
            return super().eventFilter(obj, event)

    # def focusOutEvent(self, event):
    #     self.hidePopup()
    #     super().focusOutEvent(event)

class CheckableTreeItem(TreeItem):
    def __init__(self, record: QtS.QSqlRecord, parent: TreeItem = None):
        super().__init__(record, parent)
        self.checkState = QtC.Qt.CheckState.Unchecked

    def setCheckState(self, state: QtC.Qt.CheckState):
        self.checkState = state

    def getCheckState(self):
        return self.checkState

class CheckableTreeModel(TreeModel):
    def __init__(self, source_model=QSqlTableModel(), parent=None):
        # database table
        super().__init__(source_model, parent)
        self.rootItem = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.parentItem = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.childItem = CheckableTreeItem(QtS.QSqlRecord(), None)

        if self.source_model.tableName():
            # If a table model with a valid table was passed, set the source model and create the tree
            self.setSourceModel(self.source_model)

    def setSourceModel(self, source_model: QSqlTableModel):
        self.source_model = source_model
        self.db = self.source_model.database()
        self.table = self.source_model.tableName()
        self.base_filter = f"{self.source_model.filter()}"
        if len(self.base_filter) > 0:
            self.base_filter_sql = f"{self.base_filter} AND "
        else:
            self.base_filter_sql = self.base_filter
        self.sourceHeaders = []
        self.proxyHeaders = []
        self.column_headers()
        self.header_variables()
        self.rootItem = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.parentItem = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.childItem = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.setup_model_data()
        self.source_model.setFilter(self.base_filter)

    def add_to_tree(self, child_ids: list, parent: CheckableTreeItem):
        for child_id in child_ids:
            self.source_model.setFilter(f"{self.base_filter_sql} {self.id_header} is {child_id}")
            if self.source_model.rowCount() > 0:
                record = self.source_model.record(0)

                item = CheckableTreeItem(record, parent)
                parent.appendChild(item)
                new_child_ids = self.find_children(child_id)
                self.add_to_tree(new_child_ids, item)

    def set_sample(self, sample_ID: int):
        self.sample_ID = sample_ID
        item_IDs = []
        query = QtS.QSqlQuery(self.db)
        query.prepare(f"SELECT * FROM SAMPLES_{self.table} WHERE SampleID = {self.sample_ID}")
        if query.exec():
            while query.next():
                item_IDs.append(query.value(1))
            for item_ID in item_IDs:
                item = self.findIDinTree(item_ID)
                if item:
                    item.setCheckState(QtC.Qt.CheckState.Checked)

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            # print("No data for root item")
            item = self.rootItem
        else:
            item = self.getItem(index)
        if role == QtC.Qt.ItemDataRole.CheckStateRole:
            return item.getCheckState()
        return super().data(index, role)

    def setData(self, index: QtC.QModelIndex, value: typing.Any, role: QtC.Qt.ItemDataRole = ...) -> bool:
        if not index.isValid():
            # print("Root has no data to set")
            return False
        if role == QtC.Qt.ItemDataRole.CheckStateRole:
            tree_item = self.getItem(index)
            tree_item.setCheckState(value)
            self.dataChanged.emit(index, index, [role])
            return True
        return super().setData(index, value, role)

    def flags(self, index: QtC.QModelIndex) -> QtC.Qt.ItemFlag:
        if index.column() == 0:
            # If the column is the name item, it is checkable
            return QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable | QtC.Qt.ItemFlag.ItemIsUserCheckable | QtC.Qt.ItemFlag.ItemIsDragEnabled | QtC.Qt.ItemFlag.ItemIsDropEnabled
        return super().flags(index)

    def update_db(self, checked_list: list):
        current_IDs = []
        query = QtS.QSqlQuery(self.db)
        query.prepare(f"SELECT * FROM SAMPLES_{self.table} WHERE SampleID = {self.sample_ID}")
        if query.exec():
            while query.next():
                current_IDs.append(query.value(1))
            checked_IDs = []
            query.prepare(f"SELECT * FROM {self.table} WHERE {self.item_name_header} in {checked_list}")
            if query.exec():
                while query.next():
                    checked_IDs.append(query.value(0))
            self.createSavepoint()
            to_remove = []
            to_add = []
            for ID in current_IDs:
                if ID not in checked_IDs:
                    to_remove.append(ID)
            for ID in checked_IDs:
                if ID not in current_IDs:
                    to_add.append(ID)
            for ID in to_remove:
                query.prepare(f"DELETE FROM SAMPLES_{self.table} WHERE SampleID = {self.sample_ID} AND {self.id_header} = {ID}")
                if not query.exec():
                    print(f"Error removing {ID} from SAMPLES_{self.table}")
                    self.rollback()
                    return
            for ID in to_add:
                query.prepare(f"INSERT INTO SAMPLES_{self.table}(SampleID, {self.id_header}) VALUES({self.sample_ID}, {ID})")
                if not query.exec():
                    print(f"Error adding {ID} to SAMPLES_{self.table}")
                    self.rollback()
                    return
            self.releaseSavepoint()
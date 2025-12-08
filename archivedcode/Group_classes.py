# import random
# import typing
#
# from PyQt6 import QtCore as QtC
# from PyQt6 import QtSql as QtS
#
#
# # Based on code from https://stackoverflow.com/questions/7858653/qt-pyside-qsqlmodel-qabstractitemmodel-and-qtreeview-interaction
# # Originally written for PyQt4
#
# class TreeItem:
#     def __init__(self, itemData, parentItem):
#         self.itemData = itemData
#         self.parentItem = parentItem
#         self.childItems = []
#
#     # def __del__(self):
#     #     del self.childItems
#
#     def appendChild(self, child_item):
#         # add each child item
#         self.childItems.append(child_item)
#
#     def child(self, row: int):
#         # child in given row
#         if row < 0 or row >= len(self.childItems):
#             return None
#         else:
#             return self.childItems[row]
#
#     def childCount(self):
#         # number of children
#         return len(self.childItems)
#
#     def row(self):
#         # row of item in its parent's list of children
#         if self.parentItem:
#             # return self.parent_item.childItems.indexOf(TreeItem(self))
#             return self.parentItem.childItems.index(self)
#         return 0
#
#     def columnCount(self):
#         # number of columns in input data
#         if self.itemData:
#             return len(self.itemData)
#         else:
#             return 0
#
#     def data(self, column: int):
#         # get data at given column
#         if self.itemData is None:
#             return QtC.QVariant()
#         if column < 0 or column >= len(self.itemData):
#             return QtC.QVariant()
#         else:
#             return self.itemData[column]
#
#     def setData(self, column: int, value: typing.Any):
#         self.itemData[column] = value
#
#     def parent(self):
#         # parent for given item
#         if self.itemData is None or type(self.itemData[1]) is not int:
#             return None
#         else:
#             return self.parentItem
#
#
# class GrouperProxyModel(QtC.QAbstractProxyModel):
#     def __init__(self, parent=None):
#         super(GrouperProxyModel, self).__init__(parent)
#
#         self._rootItem = QtC.QModelIndex()
#         self._groups = []       # list of groupItems
#         self._groupMap = {}     # map of group names to group indexes
#         self._groupIndexes = [] # list of groupIndexes for locating group row
#         self._sourceRows = []   # map of source rows to group index
#         self._groupColumn = 0   # grouping column.
#
#     def setSourceModel(self, table, groupColumn=0):
#         self.sourceModel = QtS.QSqlTableModel()
#         self.sourceModel.setTable(table)
#         self.sourceModel.select()
#         super(GrouperProxyModel, self).setSourceModel(self.sourceModel)
#
#         # connect signals
#         '''Don't expect columns to change'''
#         # self.sourceModel().columnsAboutToBeInserted.connect(self.columnsAboutToBeInserted.emit)
#         # self.sourceModel().columnsInserted.connect(self.columnsInserted.emit)
#         # self.sourceModel().columnsAboutToBeRemoved.connect(self.columnsAboutToBeRemoved.emit)
#         # self.sourceModel().columnsRemoved.connect(self.columnsRemoved.emit)
#         '''This part needs to be updated for PyQt6'''
#         # self.sourceModel.rowsInserted.connect(self._rowsInserted)
#         # self.sourceModel().rowsRemoved.connect(self._rowsRemoved)
#         # self.sourceModel().dataChanged.connect(self._dataChanged)
#
#         # set grouping
#         self.groupBy(groupColumn)
#
#     def rowCount(self, parent = ...):
#         if parent == self._rootItem:
#             # root level
#             return len(self._groups)
#         elif parent.internalPointer() == self._rootItem:
#             # children level
#             return len(self._groups[parent.row()].children)
#         else:
#             return 0
#
#     def columnCount(self, parent = ...):
#         if self.sourceModel:
#             return self.sourceModel.columnCount(QtC.QModelIndex())
#         else:
#             return 0
#
#     def index(self, row, column, parent = ...):
#         if parent == self._rootItem:
#             # this is a group
#             return self.createIndex(row,column,self._rootItem)
#         elif parent.internalPointer() == self._rootItem:
#             return self.createIndex(row,column,self._groups[parent.row()].index)
#         else:
#             return QtC.QModelIndex()
#
#     def parent(self, index):
#         parent =  index.internalPointer()
#         if parent == self._rootItem:
#             return self._rootItem
#         else:
#             parentRow = self._getGroupRow(parent)
#             return self.createIndex(parentRow,0,self._rootItem)
#
#     def data(self, index: QtC.QModelIndex, role: int = ...):
#         if role == QtC.Qt.ItemDataRole.DisplayRole:
#             parent = index.internalPointer()
#             if parent == self._rootItem:
#                 return self._groups[index.row()].name
#             else:
#                 parentRow = self._getGroupRow(parent)
#                 sourceRow = self._sourceRows.index(self._groups[parentRow].children[index.row()])
#                 sourceIndex = self.createIndex(sourceRow, index.column(), 0)
#                 return self.sourceModel.data(sourceIndex, role)
#         return None
#
#     def flags(self, index):
#         return QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable
#
#     def headerData(self, section: int, orientation: QtC.Qt.Orientation, role: int = ...):
#         return self.sourceModel.headerData(section, orientation, role)
#
#     def mapToSource(self, index):
#         if not index.isValid():
#             return QtC.QModelIndex()
#
#         parent = index.internalPointer()
#         if not parent.isValid():
#             return QtC.QModelIndex()
#         elif parent == self._rootItem:
#             return QtC.QModelIndex()
#         else:
#             rowItem_ = self._groups[parent.row()].children[index.row()]
#             sourceRow = self._sourceRows.index(rowItem_)
#             return self.createIndex(sourceRow, index.column(), QtC.QModelIndex())
#
#     def mapFromSource(self, index):
#         rowItem_ = self._sourceRows[index.row()]
#         groupRow = self._getGroupRow(rowItem_.groupIndex)
#         itemRow = self._groups[groupRow].children.index(rowItem_)
#         return self.createIndex(itemRow,index.column(),self._groupIndexes[groupRow])
#
#     def _clearGroups(self):
#         self._groups = []  # list of groupItems
#         self._groupMap = {}  # map of group names to group indexes
#         self._groupIndexes = []  # list of groupIndexes for locating group row
#         self._sourceRows = []  # map of source rows to group index
#
#     def groupBy(self,column=0):
#         self.beginResetModel()
#         self._clearGroups()
#         self._groupColumn = column
#         for row in range(self.sourceModel.rowCount(QtC.QModelIndex())):
#             groupName = self.sourceModel.data(self.createIndex(row,column,0),
#                                          QtC.Qt.ItemDataRole.DisplayRole)
#
#             groupIndex = self._getGroupIndex(groupName)
#             rowItem_ = rowItem(groupIndex,random.random())
#             self._groups[groupIndex.row()].children.append(rowItem_)
#             self._sourceRows.append(rowItem_)
#
#         self.endResetModel()
#
#     def _getGroupIndex(self, groupName):
#         """ return the index for a group denoted with name.
#         if there is no group with given name, create and then return"""
#         if groupName in self._groupMap:
#             return self._groupMap[groupName]
#         else:
#             groupRow = len(self._groupMap)
#             groupIndex = self.createIndex(groupRow,0,self._rootItem)
#             self._groupMap[groupName] = groupIndex
#             self._groups.append(groupItem(groupName,[],groupIndex))
#             self._groupIndexes.append(groupIndex)
#             self.layoutChanged.emit()
#             return groupIndex
#
#     def _getGroupRow(self, groupIndex):
#         for i,x in enumerate(self._groupIndexes):
#             if id(groupIndex)==id(x):
#                 return i
#         return 0
#
#     def _rowsInserted(self, parent, start, end):
#         for row in range(start, end+1):
#             groupName = self.sourceModel.data(self.createIndex(row,self._groupColumn,0),
#                                                 QtC.Qt.ItemDataRole.DisplayRole)
#             groupIndex = self._getGroupIndex(groupName)
#             self._getGroupRow(groupIndex)
#             groupItem_ = self._groups[self._getGroupRow(groupIndex)]
#             rowItem_ = rowItem(groupIndex,random.random())
#             groupItem_.children.append(rowItem_)
#             self._sourceRows.insert(row, rowItem_)
#         self.layoutChanged.emit()
#
#     def _rowsRemoved(self, parent, start, end):
#         for row in range(start, end+1):
#             rowItem_ = self._sourceRows[start]
#             groupIndex = rowItem_.groupIndex
#             groupItem_ = self._groups[self._getGroupRow(groupIndex)]
#             childrenRow = groupItem_.children.index(rowItem_)
#             groupItem_.children.pop(childrenRow)
#             self._sourceRows.pop(start)
#             if not len(groupItem_.children):
#                 # remove the group
#                 groupRow = self._getGroupRow(groupIndex)
#                 groupName = self._groups[groupRow].name
#                 self._groups.pop(groupRow)
#                 self._groupIndexes.pop(groupRow)
#                 del self._groupMap[groupName]
#         self.layoutChanged.emit()
#
#     def _dataChanged(self, topLeft, bottomRight):
#         topRow = topLeft.row()
#         bottomRow = bottomRight.row()
#         # loop through all the changed data
#         for row in range(topRow,bottomRow+1):
#             oldGroupIndex = self._sourceRows[row].groupIndex
#             oldGroupItem = self._groups[self._getGroupRow(oldGroupIndex)]
#             newGroupName = self.sourceModel.data(self.createIndex(row,self._groupColumn,0),QtC.Qt.ItemDataRole.DisplayRole)
#             if newGroupName != oldGroupItem.name:
#                 # move to new group...
#                 newGroupIndex = self._getGroupIndex(newGroupName)
#                 newGroupItem = self._groups[self._getGroupRow(newGroupIndex)]
#
#                 rowItem_ = self._sourceRows[row]
#                 newGroupItem.children.append(rowItem_)
#
#                 # delete from old group
#                 oldGroupItem.children.remove(rowItem_)
#                 if not len(oldGroupItem.children):
#                     # remove the group
#                     groupRow = self._getGroupRow(oldGroupItem.index)
#                     groupName = oldGroupItem.name
#                     self._groups.pop(groupRow)
#                     self._groupIndexes.pop(groupRow)
#                     del self._groupMap[groupName]
#
#         self.layoutChanged.emit()
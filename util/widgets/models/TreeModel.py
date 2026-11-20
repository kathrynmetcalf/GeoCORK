import time
import typing
from datetime import datetime, timezone

from PyQt6 import QtCore, QtSql
from PyQt6.QtCore import QModelIndex
from PyQt6.QtSql import QSqlQueryModel, QSqlTableModel, QSqlDatabase

import logger_setup
from Functions.Check_triggers import update_modified_timestamp
from util.database.Savepoint_manager import rollback_savepoint, release_savepoint, create_savepoint
from Functions.Widget_classes import bulk_update_parent_row, delete_data
from util.widgets.models.DisplayRoundedQueryModel import DisplayRoundedQueryModel
from util.widgets.models.SQLiteTableModel import SQLiteTableModel

from util.loading_dialog_manager import show_loading_dialog, close_loading_dialog


class TreeItem:
    def __init__(self, itemData: QtSql.QSqlRecord | SQLiteTableModel.MockRecord, parent_item):
        """
        Create a tree item with given data and parent item
        Parameters
        ----------
        itemData: SQL record from a QSql model or a mock record from SQLiteTableModel
        parent_item: parent tree item
        """
        self.itemData = itemData
        self.parent_item = parent_item
        self.childItems = []

    # def __del__(self):
    #     """
    #     Deletes all children of deleted item
    #     """
    #     # logger_setup.get_logger().info(f'Deleting tree items')
    #     for child_tree_item in self.childItems:
    #         del child_tree_item
    #     del self.childItems

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
            # remove the child by index (not by value)
            try:
                del self.childItems[row]
            except Exception:
                return False
            return True

    def clear(self):
        """
        Recursively remove all children
        """
        # remove all children
        while len(self.childItems) > 0:
            self.childItems[-1].clear()
            self.childItems.pop(-1)
        self.childItems = []
        self.itemData = None
        self.parent_item = None

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
        if self.parent_item:
            # return self.parent_item.childItems.indexOf(TreeItem(self))
            return self.parent_item.childItems.index(self)
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
            return QtCore.QVariant()
        if column < 0 or column >= self.itemData.count():
            return QtCore.QVariant()
        else:
            value = self.itemData.value(column)
            return value

    def setData(self, column: int, value: typing.Any):
        if column < 0 or column >= self.itemData.count():
            return False
        elif isinstance(self.itemData, QtSql.QSqlRecord):
            field = self.itemData.field(column)
            self.itemData.setValue(field.name(), value)
            return True
        elif isinstance(self.itemData, SQLiteTableModel.MockRecord):
            # The itemData is a mock record
            self.itemData.setValue(column, value)
            return True
        return False

    def setRecord(self, record: QtSql.QSqlRecord):
        self.itemData = record

    def parent(self):
        # parent for given item
        if self.itemData is None:
            return None
        else:
            return self.parent_item


class TreeModel(QtCore.QAbstractProxyModel):
    """
    A tree model that can be used to display hierarchical data in a tree view. A proxy model is used to allow for
    easier translation to and from the source model, which can be a QSqlTableModel, QSqlQueryModel, or SQLiteTableModel.
    Because the order of children is preserved in the database, sorting should not be used on the tree model.
    Assumes that the first four data columns are ordered as follows:
    0: ID
    1: Parent ID
    2: Parent Row
    3: Name
    """
    dataEdited = QtCore.pyqtSignal()
    save_state = QtCore.pyqtSignal()

    def __init__(self, source_model=None, parent=None, db=QSqlDatabase()):
        # database table
        super().__init__(parent)

        self.source_model = source_model
        self.base_filter = ""
        self.base_filter_sql = ""
        self.base_query = ""
        self.base_query_sql = ""
        self.view_query = None
        self.base_where = ""
        self.base_where_sql = ""
        self.show_columns = ""
        self.limit = ""
        self.where = ""
        self.where_ids = ""
        self.group_col = ""
        self.order_col = ""
        self.table = ""
        self.sourceHeaders = []
        self.proxyHeaders = []
        self.root_item = TreeItem(QtSql.QSqlRecord(), None)
        self.parent_item = TreeItem(QtSql.QSqlRecord(), None)
        self.child_item = TreeItem(QtSql.QSqlRecord(), None)
        self.parent_to_children = {}
        self.id_to_item = {}
        self.item_data = {}
        self.lastError = QtSql.QSqlError()
        self.db = db
        self._map_to_source_cache = {}
        self.reset_timer = QtCore.QTimer(self)
        self.reset_timer.setSingleShot(True)
        self.reset_timer.timeout.connect(self.reset_source_model)

        self.id_header = None
        self.parent_id_header = None
        self.parent_row_header = None
        self.item_name_header = None
        self.item_description_header = None

        if self.source_model:
            # Check if a table model was set
            if isinstance(self.source_model, QSqlTableModel):
                if self.source_model.tableName() == '':
                    return
                while self.source_model.canFetchMore():
                    self.source_model.fetchMore()
            elif isinstance(self.source_model, QSqlQueryModel):
                query_object = source_model.query()
                if query_object.lastQuery() == '':
                    return
                while self.source_model.canFetchMore():
                    self.source_model.fetchMore()
            elif isinstance(self.source_model,SQLiteTableModel):
                if source_model.query_text == '':
                    return
            self.setSourceModel(self.source_model)

    def sourceModel(self):
        """
        Returns the source model of the tree model.
        :return: data model
        """
        return self.source_model

    def setSourceModel(self, source_model: QSqlTableModel | QSqlQueryModel | SQLiteTableModel | None = None):
        """
        Set the source model for the tree model. This method initializes the tree model with the given source model,
        retrieves the table name, and sets up the base query and filter for the model. It also clears any previous tree
        model data and sets up the root item, parent item, and child item as TreeItems for the tree structure.
        If the base query is an Aliquot view or from Ages, it will set the source model to a SQLiteTableModel to speed
        up building the tree. Otherwise, it will set the source model to a DisplayRoundedQueryModel.
        :param source_model: Populated QSqlTableModel, QSqlQueryModel, or SQLiteTableModel
        :return: Nothing if there is an error
        """
        logger_setup.get_logger().info(f'Setting source model for tree model...')
        if not source_model and self.source_model:
            source_model = self.source_model
        try:
            if source_model.tableName() != '':
                self.table = source_model.tableName()
            else:
                logger_setup.get_logger().critical('Error setting up tree model')
                logger_setup.get_logger().debug('No table name set')
                return
        except AttributeError:
            logger_setup.get_logger().critical(f'Error displaying the selected table')
            if isinstance(source_model, QSqlQueryModel):
                logger_setup.get_logger().debug(f'Cannot retrieve table name from QSqlQueryModel')
        if isinstance(source_model, QSqlTableModel):
            self.base_filter = f"{source_model.filter()}".split("ORDER")[0]
            if len(self.base_filter) > 0:
                self.base_filter_sql = f"{self.base_filter} AND "
                self.base_query = f"SELECT * FROM {self.table} WHERE {self.base_filter}"
            else:
                self.base_filter_sql = self.base_filter
                self.base_query = f"SELECT * FROM {self.table}"
        elif isinstance(source_model, QSqlQueryModel):
            query_object = source_model.query()
            self.base_query = f"{query_object.lastQuery()}".split("ORDER")[0]
        elif isinstance(source_model, SQLiteTableModel):
            if source_model.view_query:
                self.view_query = source_model.view_query
                self.base_where = self.view_query.where
                if len(self.base_where) > 0:
                    if 'WHERE ' in self.base_where:
                        self.base_where_sql = f"{self.base_where} AND "
                    else:
                        self.base_where_sql = "WHERE "
            else:
                self.base_query = source_model.query_text
                if len(self.base_query) > 0:
                    if 'WHERE ' in self.base_query:
                        self.base_query_sql = f"{self.base_query} AND "
                    else:
                        self.base_query_sql = f"{self.base_query} WHERE "
        if len(self.base_query) > 0:
            if ' WHERE ' in self.base_query:
                self.base_query_sql = f"{self.base_query} AND "
            else:
                self.base_query_sql = f"{self.base_query} WHERE "
        if (('FROM LimitedAliquots' in self.base_query or 'FROM Ages' in self.base_query) or
                isinstance(source_model, SQLiteTableModel)):
            if isinstance(source_model, SQLiteTableModel):
                # If the source model is already a SQLiteTableModel, use it
                self.source_model = source_model
            else:
                try:
                    self.source_model = SQLiteTableModel(query=self.view_query.table_query, view_query=self.view_query)
                except NameError:
                    self.source_model = SQLiteTableModel(query=self.base_query)
                if self.source_model.last_error:
                    logger_setup.get_logger().critical(f'Error displaying the selected table')
                    return
        else:
            self.source_model = DisplayRoundedQueryModel(db=self.db)
            self.source_model.setQuery(f'{self.base_query}')
            while self.source_model.canFetchMore():
                self.source_model.fetchMore()
        self.sourceHeaders = []
        self.proxyHeaders = []
        self.column_headers()
        self.header_variables()
        self.setup_model_data()
        self.dataEdited.connect(self.reset_source_model_timer)

    def reset_source_model_timer(self):
        """
        Start a timer to allow other events to process before this potentially expensive method is called.
        """
        self.reset_timer.start(10)

    def reset_source_model(self):
        """
        Call setSourceModel again unless the source model is a SQLiteTableModel
        """
        show_loading_dialog('Updating', f'Updating {self.table} tree...')
        if not isinstance(self.source_model, SQLiteTableModel):
            self.source_model.setQuery(f'{self.base_query}')
            while self.source_model.canFetchMore():
                self.source_model.fetchMore()
        self.setup_model_data()
        close_loading_dialog('Updating', f'Updating {self.table} tree...')

    def setup_model_data(self):
        """
        Set up the model data for the tree model. This will build the tree from the source model.
        """
        self.beginResetModel()
        if self.root_item.childCount() > 0:
            logger_setup.get_logger().info('Clearing previous tree model...')
            self.root_item.clear()
        self.parent_item = TreeItem(QtSql.QSqlRecord(), None)
        self.child_item = TreeItem(QtSql.QSqlRecord(), None)
        self.parent_to_children = {}
        self.item_data = {}
        self.id_to_item = {}
        self._map_to_source_cache = {}
        try:
            while self.source_model.canFetchMore():
                self.source_model.fetchMore()
        except Exception as e:
            pass
        for row in range(self.source_model.rowCount()):
            record = self.source_model.record(row)
            item_id = record.value(0)  # Assuming the first column is the ID
            parent_id = record.value(1)  # Assuming the second column is the Parent ID
            if not parent_id or parent_id == 'NULL':
                parent_id = None

            self.item_data[item_id] = record
            if parent_id not in self.parent_to_children:
                self.parent_to_children[parent_id] = []

            self.parent_to_children[parent_id].append(item_id)

        for parent_id, child_ids in self.parent_to_children.items():
            child_ids.sort(key=lambda x: self.item_data[x].value(2))  # Sort by parent row

        # Add all nodes to the tree model
        # start with root item, look for children
        logger_setup.get_logger().info(f'Building the {self.table} tree from the model...')
        # show_loading_dialog('Loading', f'Building the {self.table} tree with {self.source_model.rowCount()} items...')
        start_build_time = time.time()
        # add each child to model with parent (root)
        self.add_to_tree(self.root_item)
        # look for children of those
        # add each child to the model with parent
        # etc. until there are no more children
        self.endResetModel()
        # close_loading_dialog('Loading', f'Building the {self.table} tree with {self.source_model.rowCount()} items...')
        logger_setup.get_logger().info(f'Finished building the {self.table} tree with {self.source_model.rowCount()} items in {time.time() - start_build_time:.2f} seconds')

    def add_to_tree(self, parent: TreeItem):
        """
        Add child items with unique child IDs to the tree model under the specified parent item. This method iterates
        through the list of child IDs, finds the corresponding records in the source model, and creates
        TreeItem instances for each child. It appends these items to the parent item in the tree structure. If a child
        ID has children, it recursively calls itself to add those children as well.
        :param parent: TreeItem parent to add children to
        :return: None if there are no child IDs
        """
        if parent == self.root_item:
            parent_id = None
        else:
            parent_id = parent.itemData.value(0)
        child_ids = self.parent_to_children.get(parent_id, [])
        if not child_ids:
            return
        # logger_setup.get_logger().info(f'Adding {len(child_ids)} children to the tree...')
        # logger_setup.get_logger().debug(f'Child IDs: {child_ids}')

        for child_id in child_ids:
            add_time = time.time()
            record = self.item_data[child_id]
            item = TreeItem(record, parent)
            self.id_to_item[child_id] = item
            parent.appendChild(item)
            # logger_setup.get_logger().debug(f'Added {child_id} to the tree')
            # logger_setup.get_logger().info(f'Added {record.value(3)} in {time.time() - add_time} seconds')
            self.add_to_tree(item)

    def column_headers(self):
        """
        Set up the column headers for the tree model based on the source model.
        """
        for col in range(self.source_model.columnCount()):
            self.sourceHeaders.append(
                self.source_model.headerData(col, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole))
            if col == 0:
                # Label the first column with the item name
                self.proxyHeaders.append(
                    self.source_model.headerData(3, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole))
            elif col == 1:
                # Label the second column with the item ID
                self.proxyHeaders.append(
                    self.source_model.headerData(0, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole))
            elif col == 2:
                # Label the third column with the parent ID
                self.proxyHeaders.append(
                    self.source_model.headerData(1, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole))
            elif col == 3:
                # Label the fourth column with the parent row
                self.proxyHeaders.append(
                    self.source_model.headerData(2, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole))
            else:
                self.proxyHeaders.append(
                    self.source_model.headerData(col, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole))

    def header_variables(self):
        """
        Set up variables for commonly-used headers in the tree model based on the source model headers.
        :return: None if there are no source headers
        """
        if len(self.sourceHeaders) == 0:
            return
        self.id_header = self.sourceHeaders[0]
        self.parent_id_header = self.sourceHeaders[1]
        self.parent_row_header = self.sourceHeaders[2]
        self.item_name_header = self.sourceHeaders[3]
        self.item_description_header = None
        for col in range(4,self.columnCount()):
            header = self.source_model.headerData(col, QtCore.Qt.Orientation.Horizontal)
            if 'Description' in header:
                self.item_description_header = self.sourceHeaders[col]

    def tableName(self) -> str:
        """
        Returns the name of the table this model is based on.
        :return: Name of model table
        """
        return self.table

    def getItem(self, index: QtCore.QModelIndex) -> TreeItem:  # returns tree item
        """
        Returns the tree item for a given index.
        :param index: QModelIndex in the model
        :return: TreeItem for the given index, or root item if index is invalid
        """
        if not index.isValid():
            return self.root_item
        else:
            # index = self.index(index.row(), index.column(), index.parent())
            item = index.internalPointer()
            if not item:
                logger_setup.get_logger().error(f"Error finding item for tree index")
                logger_setup.get_logger().debug(f"No item for index {index.row()},{index.column()},{index.parent()}")
            return item

    def index(self, row: int, column: int, parent: QModelIndex=QModelIndex()) -> QtCore.QModelIndex:
        """
        Create an index for a child item at the given row and column under the specified parent.
        :param row: row number of the child item
        :param column: column number of the child item
        :param parent: parent QModelIndex for the child item
        :return: QModelIndex for the child item, or an invalid QModelIndex if the parent is not valid or the row/column
        is out of bounds
        """
        # Given row, column, and parent, create an index for a child item at row and column
        # First check if parent is valid and parent item exists
        # Then get the child at the specified row and create an index for it
        # index for views and delegates
        if not isinstance(parent, QtCore.QModelIndex):
            pass
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
        if parent.isValid():
            parent_item = self.getItem(parent)
        else:
            parent_item = self.root_item
        if not parent_item:
            return QtCore.QModelIndex()
        if row < 0 or row > self.rowCount(parent):
            return QtCore.QModelIndex()
        if column < 0 or column > self.columnCount(parent):
            return QtCore.QModelIndex()
        item = parent_item.child(row)
        if item:
            return self.createIndex(row, column, item)
        else:
            return QtCore.QModelIndex()

    def parent(self, index: QtCore.QModelIndex):
        """
        Returns the parent index of the given index.
        :param index: QModelIndex for which to find the parent
        :return: parent QModelIndex, or an invalid QModelIndex if the index is invalid or has no parent
        """
        # Given index, find parent and create index for parent item
        if not index.isValid():
            return QtCore.QModelIndex()
        item = self.getItem(index)
        parent_item = item.parent()
        if parent_item == self.root_item or not parent_item:
            return QtCore.QModelIndex()
        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex) -> int:
        """
        Returns the number of rows (children) for the given parent index.
        :param parent: parent QModelIndex for which to count children
        :return: Number of child items under the parent index, or 0 if the parent is invalid
        """
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = self.getItem(parent)
        return parent_item.childCount()

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        """
        Returns the number of columns in the model. Regardless of the parent index, the number of columns is always
        the same as the number of columns in the source model.
        :param parent: Any parent QModelIndex (not used in this implementation)
        :return: Number of columns in the source model
        """
        return self.source_model.columnCount()

    def hasChildren(self, parent: QtCore.QModelIndex = ...) -> bool:
        """
        Check if the given parent index has children.
        :param parent: parent QModelIndex to check for children
        :return: True if the parent has children or is the root, False otherwise
        """
        if not parent.isValid():
            return True
        parent_item = self.getItem(parent)
        if parent_item.childCount() > 0:
            return True
        return False

    def data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = ...):
        """
        Returns the data for the given index and role. The expand/collapse icon is only available on the first column,
        and the first column cannot be hidden without hiding the expand/collapse icon, so the columns are shuffled to
        return the order as follows:
        0: Name
        1: Item ID
        2: Parent ID
        3: Parent Row
        If available, the data in the description column will be shown as a tooltip for the first column. For Ages table,
        the tooltip will show the geologic timescale age range in millions of years (Ma).
        :param index: QModelIndex for which to retrieve data
        :param role: Expected role for the data, such as DisplayRole, EditRole, or ToolTipRole
        :return: Data for the given index and role
        """
        if not index.isValid():
            item = self.root_item
        else:
            item = self.getItem(index)
        if role == QtCore.Qt.ItemDataRole.DisplayRole or role == QtCore.Qt.ItemDataRole.EditRole:
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
                # Show parent row in fourth column
                return item.data(2)
            else:
                return item.data(index.column())
        elif index.column() == 0 and role == QtCore.Qt.ItemDataRole.ToolTipRole:
            if self.table == 'Ages':
                # For the Ages table, the tooltip is the age range
                oldest_age = self.data(index.siblingAtColumn(4), QtCore.Qt.ItemDataRole.DisplayRole)
                youngest_age = self.data(index.siblingAtColumn(5), QtCore.Qt.ItemDataRole.DisplayRole)
                return f'{oldest_age}-{youngest_age} Ma'
            description_col = None
            for header_col in range(self.columnCount()):
                header = self.headerData(header_col, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole)
                if 'Description' in header:
                    description_col = header_col
                    break
            if description_col is not None:
                tool_tip = item.data(description_col)
                return tool_tip
        # super().data(index, role)  # Slows down the model considerably
        return None

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: QtCore.Qt.ItemDataRole = ...) -> bool:
        """
        Set the data for the given index and role. This will update the source model and the tree item data. If the
        source model is not a SQLiteTableModel, it is connected to current database values and will also update the
        database with the new data.
        SQLiteTableModel data are based on uncommitted changes, so any changes to the database would not be reflected
        in the tree model until the changes are committed. Here, we manually update the data for display in the tree
        model.
        :param index: QModelIndex for which to set data
        :param value: value to set for the given index
        :param role: role for the data, such as EditRole
        :return: True if the data was successfully set, False if the index is invalid, or the default return value if the
        role is not EditRole.
        """
        if not index.isValid():
            return super().setData(index, value, role)
        if role == QtCore.Qt.ItemDataRole.EditRole:
            logger_setup.get_logger().info(
                f'Setting data in {self.table} tree at {index.row()},{index.column()}')
            start_set_time = time.time()
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
            if not isinstance(self.source_model, SQLiteTableModel):
                # The model is connected to the database
                # Get the updated modified timestamp
                sourceIndex = self.mapToSource(index)
                if sourceIndex.isValid():
                    logger_setup.get_logger().info(
                        f'Setting data in {self.table} tree at {sourceIndex.row()},{sourceIndex.column()}')
                    modified_col = self.source_model.columnCount() - 1
                    source_modified_index = self.source_model.index(sourceIndex.row(), modified_col, QtCore.QModelIndex())
                    proxy_modified_index = self.mapFromSource(source_modified_index)
                    if proxy_modified_index.isValid() and source_modified_index.isValid():
                        # If the changed data index and the modified timestamp index are valid for both models, change the data
                        name_header = self.source_model.headerData(sourceIndex.column(), QtCore.Qt.Orientation.Horizontal)
                        table_id = self.source_model.data(sourceIndex.siblingAtColumn(0), QtCore.Qt.ItemDataRole.DisplayRole)
                        query = QtSql.QSqlQuery()
                        query.prepare(f"UPDATE {self.table} SET {name_header}=:value WHERE {self.id_header}={table_id}")
                        query.bindValue(":value", value)
                        if not query.exec():
                            logger_setup.get_logger().critical(f'Error editing data in {self.table}')
                            logger_setup.get_logger().debug(
                                f'Error setting data in {self.table} tree at {sourceIndex.row()},{sourceIndex.column()}')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                            logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                            return False
                        # modified = self.source_model.data(source_modified_index, QtCore.Qt.ItemDataRole.DisplayRole)
                        update_modified_timestamp(self.table, [table_id])
                        treeItem.setData(modified_col, datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))
            treeItem.setData(dataCol, value)
            self.dataChanged.emit(index, index)
            logger_setup.get_logger().info(
                f'Successfully set data in {self.table} tree at {index.row()},{index.column()} to {value} in {time.time() - start_set_time:.2f} seconds')
            return True
        return super().setData(index, value, role)

    def moveItem(self, item_id: int, row: int, p_id: str, modifier: int = 0) -> bool:
        """
        Move an item to a new parent and parent row. Updates the changes in the source model and the database.
        :param item_id: unique ID of the item to move
        :param row: new parent row number for the item
        :param p_id: new parent ID for the item, either 'IS NULL' or 'is parent_id'
        :param modifier: number of items added or removed from the table since the source model was set
        :return: True if the item was successfully moved, False if there was an error
        """
        # Try making change to database, then reset the tree model
        start_time = time.time()
        show_loading_dialog('Moving', f'Moving {self.table} data')
        if p_id == 'IS NULL':
            parent_id = 'NULL'
        else:
            parent_id = int(p_id[2:])
        query = QtSql.QSqlQuery()
        if not query.exec(f'SELECT {self.parent_id_header}, {self.parent_row_header} FROM {self.table} WHERE {self.id_header} = {item_id}'):
            logger_setup.get_logger().critical(f'Error finding item in {self.table}')
            logger_setup.get_logger().debug(f'Error fetching parent info for {self.table} ID {item_id}')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            return False
        if not query.next():
            logger_setup.get_logger().critical(f'Error finding item in {self.table}')
            logger_setup.get_logger().debug(f'Error fetching parent info for {self.table} ID {item_id}')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            return False
        else:
            old_parent_id = query.value(0)
            if not isinstance(old_parent_id, int):
                old_parent_id = 'NULL'
            old_parent_row = query.value(1)
        if old_parent_id == parent_id:
            if old_parent_row is not None and row > old_parent_row:
                # Moving an item down, so its final position will be row-1
                row = row - 1
            # If moving up, final position will just be row
            # Create space at the new row
            if not bulk_update_parent_row(self.table, parent_id, 1, row, old_parent_row)[0]:
                close_loading_dialog('Moving', f'Moving {self.table} data')
                return False
            # Move item to the new row
            if not self.update_parent_info(item_id, parent_id, row):
                close_loading_dialog('Moving', f'Moving {self.table} data')
                return False

        else:
            # Create space in new parent
            if not bulk_update_parent_row(self.table, parent_id, 1, row, None)[0]:
                close_loading_dialog('Moving', f'Moving {self.table} data')
                return False
            # Move item to the new row in the new parent
            if not self.update_parent_info(item_id, parent_id, row):
                close_loading_dialog('Moving', f'Moving {self.table} data')
                return False
            # Close space in old parent
            if not bulk_update_parent_row(self.table, old_parent_id, 1, None, old_parent_row)[0]:
                close_loading_dialog('Moving', f'Moving {self.table} data')
                return False
        logger_setup.get_logger().info(f'Moved {self.table} data in {time.time() - start_time} seconds')
        close_loading_dialog('Moving', f'Moving {self.table} data')
        return True

    def update_parent_info(self, item_id: int, parent_id, parent_row: int):
        """
        Update the parent ID and parent row for a given item ID in the database.
        :param item_id: unique ID of the item to update
        :param parent_id: unique ID of the new parent, or None if the item has no parent
        :param parent_row: row number of the new parent in the parent's list of children
        :return: True if the update was successful, False if there was an error
        """
        # Update the parent ID and parent row for a given item ID
        query = QtSql.QSqlQuery()
        query.prepare(
            f'UPDATE {self.table} SET {self.parent_id_header} = :parent_id, {self.parent_row_header} = :parent_row WHERE {self.id_header} = :item_id')
        if parent_id == 'NULL':
            query.bindValue(':parent_id', QtCore.QVariant())
        else:
            query.bindValue(':parent_id', parent_id)
        query.bindValue(':parent_row', parent_row)
        query.bindValue(':item_id', item_id)
        if not query.exec():
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            logger_setup.get_logger().debug(f"Bound values: {query.boundValues()}")
            return False
        update_modified_timestamp(self.table, [item_id])
        tree_item = self.find_id_in_tree(item_id)
        if tree_item:
            filtered_model = QtSql.QSqlQueryModel()
            if isinstance(self.source_model, SQLiteTableModel) and self.view_query:
                view_where = f"{self.base_where_sql} {self.id_header} = {item_id}"
                updated_table_query = self.update_view_query(**{'where': view_where})
                filtered_model.setQuery(updated_table_query)
                for row in range(self.source_model.rowCount()):
                    row_id = self.source_model.record(row).value(0)
                    if row_id == item_id:
                        for column in range(self.source_model.columnCount()):
                            source_index = self.source_model.index(row, column)
                            self.source_model.setData(source_index, filtered_model.record(0).value(column), QtCore.Qt.ItemDataRole.EditRole)
                        break
        logger_setup.get_logger().info(f'Successfully updated parent for {item_id} in table {self.table}')
        return True

    def insertItem(self, item_name: str, item_description: str, parent_id=None, parent_row=None, data_parent_id=None) -> bool:
        """
        Insert a new item into the database and the tree model. The item is first added as a top-level item, then moved
        to the correct parent and row. If no parent ID is given, the item is added to the root item. If no parent row is
        given, the item is added to the end of the child list.
        :param item_name: new item name to add to the tree model
        :param item_description: new item description to add to the tree model
        :param parent_id: unique ID of the parent item, or None if the item has no parent
        :param parent_row: row number of the parent item. If None, the item is added to the end of the list.
        :param data_parent_id: unique ID of the item up the data chain. E.g. SampleID for inserting an Aliquot. Required if table is Aliquots.
        :return: True if the item was successfully inserted, False if there was an error adding or moving item
        """
        # Add a new item to the database, first as a top-level item, then move it to the correct parent and row
        if self.table == 'Aliquots' and not data_parent_id:
            logger_setup.get_logger().error(f'Error inserting new item {item_name} into {self.table}: SampleID is required for Aliquots')
            return False
        start_time = time.time()
        logger_setup.get_logger().info(f'Inserting {item_name} in tree model')
        show_loading_dialog('Inserting', f'Inserting new {self.table} item...')
        query = QtSql.QSqlQuery()
        filtered_model = QtSql.QSqlQueryModel()
        p_id = 'IS NULL'
        if isinstance(self.source_model, SQLiteTableModel) and self.view_query:
            view_where = f"{self.base_where_sql} {self.sourceHeaders[1]} {p_id}"
            updated_table_query = self.update_view_query(**{'where': view_where})
            filtered_model.setQuery(updated_table_query)
        else:
            filtered_model.setQuery(f"{self.base_query_sql} {self.sourceHeaders[1]} {p_id}")
        while filtered_model.canFetchMore():
            filtered_model.fetchMore()
        child_count = filtered_model.rowCount()
        if self.item_description_header:
            insert_columns_list = [self.parent_row_header, self.item_name_header, self.item_description_header]
            insert_placeholder_list = [':parent_row', ':item_name', ':item_description']
            insert_values_list = [child_count, item_name, item_description]
        else:
            insert_columns_list = [self.parent_row_header, self.item_name_header]
            insert_placeholder_list = [':parent_row', ':item_name']
            insert_values_list = [child_count, item_name]
        if self.table == 'Aliquots':
            insert_columns_list.append('SampleID')
            insert_placeholder_list.append(':data_parent_id')
            insert_values_list.append(data_parent_id)
        query.prepare(f'INSERT INTO {self.table}({", ".join(insert_columns_list)}) VALUES({", ".join(insert_placeholder_list)})')
        for placeholder, value in zip(insert_placeholder_list, insert_values_list):
            query.bindValue(placeholder, value)
        create_savepoint('before_insert')
        if not query.exec():
            logger_setup.get_logger().critical(f'Error inserting new item {item_name}')
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            logger_setup.get_logger().debug(f"Bound values: {query.boundValues()}")
            rollback_savepoint('before_insert')
            close_loading_dialog('Inserting', f'Inserting new {self.table} item...')
            return False
        else:
            logger_setup.get_logger().info(f'Successfully inserted new item {item_name}')
            if parent_id and parent_id != 'Null' and parent_id != 'NULL':
                p_id = f'= {parent_id}'
            else:
                p_id = 'IS NULL'
            if parent_row is None and parent_id is None:
                # If no parent row or parent ID is given, the item was already added at the end of the root item children
                release_savepoint('before_insert')
                self.dataEdited.emit()
                close_loading_dialog('Inserting', f'Inserting new {self.table} item...')
                return True
            if parent_row is None:
                # If no parent row is given, the item is added to the end of the list
                if isinstance(self.source_model, SQLiteTableModel) and self.view_query:
                    view_where = f"{self.base_where_sql} {self.parent_id_header} {p_id}"
                    updated_table_query = self.update_view_query(**{'where': view_where})
                    filtered_model.setQuery(updated_table_query)
                else:
                    filtered_model.setQuery(f"{self.base_query_sql} {self.parent_id_header} {p_id}")
                while filtered_model.canFetchMore():
                    filtered_model.fetchMore()
                child_count = filtered_model.rowCount()
                parent_row = child_count
            item_id = query.lastInsertId()
            if not self.moveItem(item_id, parent_row, p_id, 1):
                rollback_savepoint('before_insert')
                close_loading_dialog('Inserting', f'Inserting new {self.table} item...')
                return False
        release_savepoint('before_insert')
        self.dataEdited.emit()
        close_loading_dialog('Inserting', f'Inserting new {self.table} item...')
        logger_setup.get_logger().info(f'Successfully inserted new item {item_name} in {time.time() - start_time} seconds')
        return True

    def removeItems(self, del_ids: list[int]) -> bool:
        """
        Removes each item and all its children from the database and the tree model. The item is first deleted from the
        database, then the tree model is updated to reflect the changes. If the item has children, their parent rows are
        updated to close the gap left by the deleted item.
        :param del_ids: list of unique IDs of the items to remove
        :return: True if the item was successfully removed or already removed, False if there was an error deleting the
        item or updating the tree model.
        """
        # Remove an item and all children from the database
        if len(del_ids) == 0:
            logger_setup.get_logger().info(f'No items to delete')
            return True
        start_time = time.time()
        show_loading_dialog('Removing', f'Removing item from {self.table}')
        logger_setup.get_logger().info(f'Removing item from {self.table}')
        # Check if the ids have already been deleted
        query = QtSql.QSqlQuery()
        if not query.exec(f"SELECT {self.id_header}, {self.parent_id_header}, {self.parent_row_header} FROM {self.table} WHERE {self.id_header} IN ({', '.join(map(str, del_ids))})"):
            logger_setup.get_logger().critical(f'Error checking for existing items in {self.table} before deletion')
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            close_loading_dialog('Removing', f'Removing item from {self.table}')
            return False
        existing_data = {}
        while query.next():
            existing_data[query.value(0)] = {'parent_id': query.value(1), 'parent_row': query.value(2)}
        if not existing_data:
            logger_setup.get_logger().info(f'No items to delete')
            return True
        if not delete_data(self.table, del_ids):
            close_loading_dialog('Removing', f'Removing item from {self.table}')
            return False
        logger_setup.get_logger().info(f'Successfully deleted items from {self.table}')
        for del_id, parent_data in existing_data.items():
            parent_id = parent_data['parent_id']
            parent_row = parent_data['parent_row']
            if not parent_id:
                parent_id = 'NULL'
            # If the parent already has children at rows beyond the deleted one, update their parent rows to close the gap
            if not bulk_update_parent_row(self.table, parent_id, 1, None, parent_row)[0]:
                logger_setup.get_logger().critical(f'Error removing {self.table}')
                logger_setup.get_logger().debug(f'Error closing the gap after deleting')
                rollback_savepoint('before_delete')
                close_loading_dialog('Removing', f'Removing item from {self.table}')
                return False
        release_savepoint('before_delete')
        close_loading_dialog('Removing', f'Removing item from {self.table}')
        logger_setup.get_logger().info(
            f'Successfully deleted {len(del_ids)} {self.table} in {time.time() - start_time} seconds...')
        self.dataEdited.emit()
        return True

    def mapToSource(self, proxy_index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        """
        Maps a proxy index (TreeModel index) to the source model index (QSqlQueryModel or SQLiteTableModel index).
        The expand/collapse icon is only available on the first column, and the first column cannot be hidden without
        hiding the expand/collapse icon, so the columns are shuffled as follows:
        TreeModel (proxy model) columns:
        0: Name,
        1: Item ID,
        2: Parent ID,
        3: Parent Row;
        Source Model (QSqlQueryModel or SQLiteTableModel) columns:
        0: Item ID,
        1: Parent ID,
        2: Parent Row,
        3: Item Name;
        :param proxy_index: index of tree model (proxy model) to map to source model
        :return: the source model index corresponding to the given proxy index, or an invalid QModelIndex if the proxy
        index is not valid
        """
        if not proxy_index.isValid() or not self.source_model:
            return QtCore.QModelIndex()
        if not isinstance(self.source_model, QtSql.QSqlQueryModel | SQLiteTableModel):
            logger_setup.get_logger().critical(f'Data type error')
            logger_setup.get_logger().debug(f'Source model is not a QSqlQueryModel or SQLiteTableModel')
            return QtCore.QModelIndex()
        if proxy_index in self._map_to_source_cache:
            return self._map_to_source_cache[proxy_index]
        proxy_col = proxy_index.column()
        item = self.getItem(proxy_index)
        item_id = item.data(0)
        source_row = None
        while self.source_model.canFetchMore():
            self.source_model.fetchMore()
        for row in range(self.source_model.rowCount()):
            record = self.source_model.record(row)
            if record.value(0) == item_id:
                source_row = row
                break
        if source_row is None:
            return QtCore.QModelIndex()
        if proxy_col == 0:  # first column is item name which maps to fourth column in source model
            source_col = 3
        elif proxy_col == 1:  # second column is item ID which maps to first column in source model
            source_col = 0
        elif proxy_col == 2:  # third column is parent ID which maps to second column in source model
            source_col = 1
        elif proxy_col == 3:  # fourth column is parent row which maps to third column in source model
            source_col = 2
        else:
            source_col = proxy_col
        source_index = self.source_model.index(source_row, source_col, QtCore.QModelIndex())
        self._map_to_source_cache[proxy_index] = source_index
        return source_index

    def mapFromSource(self, source_index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        """
        Maps a source index (QSqlQueryModel or SQLiteTableModel index) to the proxy model index (TreeModel index).
        The expand/collapse icon is only available on the first column, and the first column cannot be hidden without
        hiding the expand/collapse icon, so the columns are shuffled as follows:
        Source Model (QSqlQueryModel or SQLiteTableModel) columns:
        0: Item ID,
        1: Parent ID,
        2: Parent Row,
        3: Item Name;
        TreeModel (proxy model) columns:
        0: Name,
        1: Item ID,
        2: Parent ID,
        3: Parent Row;
        :param source_index: the source model index to map to the proxy model
        :return: index of the proxy model (TreeModel) corresponding to the given source index, or an invalid QModelIndex
        if the source index is not valid
        """
        if not source_index.isValid():
            return QtCore.QModelIndex()
        source_row = source_index.row()
        source_col = source_index.column()
        if source_col == 0:  # first column is item ID which maps to second column in proxy model
            proxy_col = 1
        elif source_col == 1:  # second column is parent ID which maps to third column in proxy model
            proxy_col = 2
        elif source_col == 2:  # third column is parent row which maps to fourth column in proxy model
            proxy_col = 3
        elif source_col == 3:  # fourth column is item name which maps to first column in proxy model
            proxy_col = 0
        else:
            proxy_col = source_col  # same column as table model
        record = self.source_model.record(source_row)
        item_id = record.value(0)
        item = self.find_id_in_tree(item_id)
        proxy_row = item.row()  # row number of item in its parent's child list
        parent_item = item.parent()
        if parent_item == self.root_item:
            parent_index = QtCore.QModelIndex()
        else:
            parent_index = self.createIndex(parent_item.row(), proxy_col, parent_item)
        return self.index(proxy_row, proxy_col, parent_index)

    def find_id_in_tree(self, item_id: int) -> TreeItem | None:
        """
        Find an item in the tree model by its unique ID. This method recursively searches through the tree items to find
        the item with the given ID.
        :param item_id: unique ID of the item to find
        :return: tree item with the given ID, or None if the item is not found
        """
        if item_id in self.id_to_item:
            return self.id_to_item[item_id]
        else:
            logger_setup.get_logger().debug(f'Item {item_id} not found in {self.table} tree')
            return None

    def get_index_from_item(self, item: TreeItem) -> QtCore.QModelIndex:
        """
        Given a tree item, use the TreeItem.parent() and TreeItem.row() to find the index of the item in the tree.
        :param item: tree item to find the index
        """
        if item == self.root_item:
            return QtCore.QModelIndex()
        parent_item = item.parent()
        if parent_item == self.root_item:
            parent_index = QtCore.QModelIndex()
        else:
            parent_index = self.createIndex(parent_item.row(), 0, parent_item)
        return self.index(item.row(), 0, parent_index)

    def find_id_source_row(self, item_id: int):
        """
        Find the row number in the source model for a given item ID. This is used to map the item ID to its row in the
        source model, which is necessary for operations like moving or deleting items.
        :param item_id: unique ID of the item to find in the source model
        :return: row number in the source model where the item with the given ID is located, or None if the item is not
        found
        """
        for row in range(self.source_model.rowCount()):
            record = self.source_model.record(row)
            if record.value(0) == item_id:
                return row
        return

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """
        Returns the item flags for the given index. This determines whether the item is editable, selectable, draggable,
        and droppable. All items are selectable, draggable, and droppable, and all but the created and modified
        timestamp columns are editable. ID columns should not be visible at all.
        :param index: index for which to get the item flags
        :return: item flags for the given index
        """
        if not index.isValid():
            # the root can be a drop destination
            return QtCore.Qt.ItemFlag.ItemIsDropEnabled
        modified_col = self.source_model.columnCount() - 1
        created_col = self.source_model.columnCount() - 2
        if index.column() == modified_col or index.column() == created_col:
            # If the column is the created timestamp or modified timestamp, it is not editable. IDs should not be visible at all
            return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsDragEnabled | QtCore.Qt.ItemFlag.ItemIsDropEnabled
        else:
            return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEditable | QtCore.Qt.ItemFlag.ItemIsDragEnabled | QtCore.Qt.ItemFlag.ItemIsDropEnabled

    def mimeTypes(self):
        """
        Returns the MIME types supported by this model for drag and drop operations.
        :return: List of MIME types supported by this model
        """
        return ['application/x-qabstractitemmodeldatalist']

    def mimeData(self, indexes: list[QtCore.QModelIndex]) -> QtCore.QMimeData:
        """
        Creates a QMimeData object containing the data for the given indexes. This is used for drag and drop operations.
        Only the first column (item ID) is included in the MIME data, as it is the unique identifier for the item.
        :param indexes: list of QModelIndex objects to create MIME data for
        :return: MIME data object containing the item IDs for the given indexes
        """
        mimeData = QtCore.QMimeData()
        encodedData = QtCore.QByteArray()
        stream = QtCore.QDataStream(encodedData, QtCore.QIODevice.OpenModeFlag.WriteOnly)
        for index in indexes:
            if index.isValid() and index.column() == 0:
                item = self.getItem(index)
                stream.writeInt32(item.data(0))  # item ID
        mimeData.setData('application/x-qabstractitemmodeldatalist', encodedData)
        return mimeData

    def canDropMimeData(self, data: QtCore.QMimeData, action: QtCore.Qt.DropAction, row, column, parent) -> bool:
        """
        Checks if the model can accept the dropped MIME data. This is used to determine if the drop operation is valid.
        :param data: MIME data to check for drop validity
        :param action: Drop action performed (e.g., MoveAction)
        :param row: row where the item is dropped, not used in this implementation
        :param column: column where the item is dropped, not used in this implementation
        :param parent: parent index where the item is dropped, not used in this implementation
        :return: False if the action is IgnoreAction or if the data format is not recognized, True otherwise
        """
        if action == QtCore.Qt.DropAction.IgnoreAction:
            return False
        if not data.hasFormat('application/x-qabstractitemmodeldatalist'):
            logger_setup.get_logger().critical(f'Error dropping item')
            logger_setup.get_logger().debug(f'Drop data format not recognized')
            return False
        return True

    def dropMimeData(self, data: QtCore.QMimeData, action: QtCore.Qt.DropAction, drop_row: int, column: int,
                     parent: QtCore.QModelIndex):
        """
        Handles the drop of MIME data into the model. This method processes the dropped data, updates the source model,
        and moves the items to the new parent and row. If the drop is successful, it emits the dataEdited signal to
        notify the view to rebuild the tree model.
        :param data: MIME data dropped into the model
        :param action: Drop actio performed (e.g., MoveAction)
        :param drop_row: row where the item is dropped
        :param column: column where the item is dropped, not used in this implementation
        :param parent: parent index where the item is dropped
        :return:
        """
        if not self.canDropMimeData(data, action, drop_row, column, parent):
            return False
        encoded_data = data.data('application/x-qabstractitemmodeldatalist')
        stream = QtCore.QDataStream(encoded_data, QtCore.QIODevice.OpenModeFlag.ReadOnly)
        item_ids = []
        rows = []
        if drop_row == -1:
            drop_row = self.getItem(parent).childCount()
        drop_parent_id = self.getItem(parent).data(0)
        if isinstance(drop_parent_id, int):
            p_id = f'= {drop_parent_id}'
        else:  # If the parent ID is not an integer
            p_id = 'IS NULL'
        create_savepoint('drop_mime_data')
        while not stream.atEnd():
            item_ids.append(stream.readInt32())
        if not item_ids:
            logger_setup.get_logger().debug(f'No items to move')
            rollback_savepoint('drop_mime_data')
            return False
        query = QtSql.QSqlQuery()
        item_ids_text = ', '.join(str(item_id) for item_id in item_ids)
        query.exec(f'SELECT {self.id_header}, {self.parent_id_header}, {self.parent_row_header} FROM {self.table} WHERE {self.id_header} IN ({item_ids_text})')
        item_ids = []
        parent_ids = []
        parent_rows = []
        drop_item_ids = []
        drop_parent_rows = []
        while query.next():
            if query.value(self.parent_id_header) == drop_parent_id:
                drop_item_ids.append(query.value(self.id_header))
                drop_parent_rows.append(query.value(self.parent_row_header))
            else:
                item_ids.append(query.value(self.id_header))
                parent_ids.append(query.value(self.parent_id_header))
                parent_rows.append(query.value(self.parent_row_header))
        drop_parent_move_data = zip(drop_item_ids, drop_parent_rows)
        drop_parent_move_data = sorted(drop_parent_move_data, key=lambda x: x[1])  # Sort by row number to move in ascending order
        move_data = zip(item_ids, parent_ids, parent_rows)
        move_data = sorted(move_data, key=lambda x: x[2])  # Sort by row number to move in ascending order
        move_data = sorted(move_data, key=lambda x: x[1])  # Then sort by parent ID
        # Start with items dropped within the same parent
        item_ids = []
        for item_id, parent_row in drop_parent_move_data:
            item_ids.append(item_id)
            if parent_row > drop_row:
                count = sum(1 for x in drop_parent_rows if parent_row >= x > drop_row)
                rows.append(drop_row + count - 1)
            else:
                rows.append(drop_row)
        for item_id, parent_id, parent_row in move_data:
            item_ids.append(item_id)
            if len(rows) > 0:
                rows.append(rows[-1] + 1)
            else:
                rows.append(drop_row)
        for move in range(len(item_ids)):
            if not self.moveItem(item_ids[move], rows[move], p_id):
                logger_setup.get_logger().critical(f'Error moving item')
                logger_setup.get_logger().debug(f'Item: {item_ids[move]}, rows: {rows[move]}, parent_ID: {p_id}')
                rollback_savepoint('drop_mime_data')
                return False
        release_savepoint('drop_mime_data')
        # Emit signal so that the view can rebuild the tree model
        self.dataEdited.emit()
        return True

    def supportedDropActions(self):
        """
        Returns the drop actions supported by this model. This is used to determine what actions are allowed when
        dropping items into the model.
        :return: Drop actions supported by this model, which are CopyAction and MoveAction
        """
        return QtCore.Qt.DropAction.CopyAction | QtCore.Qt.DropAction.MoveAction

    def supportedDragActions(self):
        """
        Returns the drag actions supported by this model. This is used to determine what actions are allowed when
        dragging items from the model. There is no corresponding QtCore.Qt.DragAction, so we return the drop actions.
        :return: Drag actions supported by this model, which are CopyAction and MoveAction
        """
        return QtCore.Qt.DropAction.CopyAction | QtCore.Qt.DropAction.MoveAction

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...):
        """
        Returns the header data for the given section and orientation. This is used to display the column headers in the
        view. The headers are defined in the source model, and this method retrieves the appropriate header based on the
        section and orientation. If the role is not DisplayRole, it returns an empty QVariant.
        :param section: column index for which to get the header data
        :param orientation: header orientation (horizontal or vertical)
        :param role: role for the header data, such as DisplayRole
        :return: header data for the given section and orientation, or an empty QVariant if the role is not DisplayRole
        """
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return QtCore.QVariant()
        if orientation == QtCore.Qt.Orientation.Horizontal:
            return self.proxyHeaders[section]
        return QtCore.QVariant()

    def top_node(self, item_ids: list) -> tuple:
        """
        Find the top parent ID and row for a list of item IDs. This method traverses the tree model to find the topmost
        parent that contains any of the given item IDs. It returns the top parent ID and the row number of that parent in
        the tree model.
        :param item_ids: list of unique item IDs
        :return: tuple containing the top parent ID and the row number of the top child in that parent
        """
        filtered_model = QtSql.QSqlQueryModel()
        def get_depth(depth_id):
            depth = 0
            while depth_id is not None:
                if isinstance(self.source_model, SQLiteTableModel) and self.view_query:
                    view_where = f"{self.base_where_sql} {self.id_header} is {depth_id}"
                    updated_table_query = self.update_view_query(**{'where': view_where})
                    filtered_model.setQuery(updated_table_query)
                else:
                    filtered_model.setQuery(f"{self.base_query_sql} {self.id_header} is {depth_id}")
                while filtered_model.canFetchMore():
                    filtered_model.fetchMore()
                depth_parent_id = filtered_model.record(0).value(1)
                if depth_parent_id == '':
                    break
                depth_id = depth_parent_id
                depth += 1
            return depth

        if len(item_ids) == 0:
            logger_setup.get_logger().debug(f'No item IDs provided, returning None')
            return None, None
        if '' in item_ids:
            logger_setup.get_logger().debug(f'Empty item ID found, referencing root. Returning None')
            return None, None
        depths = {}
        for item_id in item_ids:
            depths[item_id] = get_depth(item_id)
        # If there is a tie for minimum depth, break it by the minimum parent row
        min_depth = min(depths.values())
        candidates = [item_id for item_id, depth in depths.items() if depth == min_depth]
        if len(candidates) > 1:
            top_parent_row = None
            top_parent_id = None
            for item_id in candidates:
                if isinstance(self.source_model, SQLiteTableModel) and self.view_query:
                    view_where = f"{self.base_where_sql} {self.id_header} is {item_id}"
                    updated_table_query = self.update_view_query(**{'where': view_where})
                    filtered_model.setQuery(updated_table_query)
                else:
                    filtered_model.setQuery(f"{self.base_query_sql} {self.id_header} is {item_id}")
                while filtered_model.canFetchMore():
                    filtered_model.fetchMore()
                parent_id = filtered_model.record(0).value(1)
                parent_row = filtered_model.record(0).value(2)
                if top_parent_row is None or parent_row < top_parent_row:
                    top_parent_row = parent_row
                    top_parent_id = parent_id
        else:
            top_item_id = candidates[0]
            if isinstance(self.source_model, SQLiteTableModel) and self.view_query:
                view_where = f"{self.base_where_sql} {self.id_header} is {top_item_id}"
                updated_table_query = self.update_view_query(**{'where': view_where})
                filtered_model.setQuery(updated_table_query)
            else:
                filtered_model.setQuery(f"{self.base_query_sql} {self.id_header} is {top_item_id}")
            while filtered_model.canFetchMore():
                filtered_model.fetchMore()
            top_parent_id = filtered_model.record(0).value(1)
            top_parent_row = filtered_model.record(0).value(2)
        if top_parent_id == '':
            top_parent_id = 'NULL'
        return top_parent_id, top_parent_row

    def update_view_query(self, **kwargs) -> str:
        self.show_columns = self.view_query.show_columns
        self.limit = self.view_query.limit
        self.where = self.view_query.where
        self.where_ids = self.view_query.where_ids
        self.group_col = self.view_query.group_col
        self.order_col = self.view_query.order_col

        for key, value in kwargs.items():
            setattr(self, key, value)

        query_args = {'show_columns': self.show_columns, 'limit': self.limit, 'where': self.where, 'where_ids': self.where_ids,
                      'group_col': self.group_col, 'order_col': self.order_col}
        updated_view_query = ViewQuery(self.view_query.table, self.view_query.edit_view, **query_args)
        return updated_view_query.table_query
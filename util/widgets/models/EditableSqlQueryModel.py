from PyQt6 import QtCore
from qtpy import QtSql

import logger_setup
from Functions.Check_triggers import update_modified_timestamp
from Functions.Widget_classes import get_name_column, delete_data
from util.widgets.models.DisplayRoundedQueryModel import DisplayRoundedQueryModel


class EditableSqlQueryModel(DisplayRoundedQueryModel):
    """Custom DisplayRoundedQueryModel (subclass of QSqlQueryModel) with editable name column and description column.
    Updates the database likee QSqlTablModel does."""
    def __init__(self):
        super().__init__()
        self.query_text = ''

    def flags(self, index):
        """Sets only the name column and description column as editable"""
        flags = super().flags(index)
        col = get_name_column(self.table)
        if index.column() == col or 'Description' in self.headerData(index.column(), QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole):
            flags |= QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEditable
        return flags

    def setData(self, index: QtCore.QModelIndex, value, role: QtCore.Qt.ItemDataRole = ...):
        if not index.isValid():
            return super().setData(index, value, role)
        if role == QtCore.Qt.ItemDataRole.EditRole:
            edited_id = self.data(self.index(index.row(), 0), QtCore.Qt.ItemDataRole.DisplayRole)
            id_header = self.headerData(0, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole)
            edited_header = self.headerData(index.column(), QtCore.Qt.Orientation.Horizontal)
            query = QtSql.QSqlQuery()
            if not query.exec(f'SELECT {edited_header} FROM {self.table} WHERE {id_header}={edited_id}'):
                logger_setup.get_logger().critical(f'Failed to get {edited_header} from {self.table}')
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                return False
            if query.next():
                if query.value(0) == value:
                    logger_setup.get_logger().info(f'{edited_header} is already set to {value}')
                    return True
            query.prepare(f'UPDATE {self.table} SET {edited_header}=:value WHERE {id_header}=:id')
            query.bindValue(':value', value)
            query.bindValue(':id', edited_id)
            if not query.exec():
                logger_setup.get_logger().critical(f'Failed to update {edited_header} in {self.table}')
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                logger_setup.get_logger().debug(f"Bound values: {query.boundValues()}")
                return False
            logger_setup.get_logger().info(f'Successfully updated {edited_header} in {self.table}')
            update_modified_timestamp(self.tableName(), [edited_id])
            self.setQuery(self.query_text)
            self.dataChanged.emit(index, index)
            return True
        return super().setData(index, value, role)

    def deleteRowFromTable(self, row):
        id = self.data(self.index(row, 0), QtCore.Qt.ItemDataRole.DisplayRole)
        if not id:
            logger_setup.get_logger().warning(f'No ID found for row {row} in {self.table}')
            return False
        if not delete_data(self.table, [id]):
            return False
        logger_setup.get_logger().info(f'Successfully deleted {id} from {self.table}')
        return True
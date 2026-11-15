import typing

from PyQt6 import QtCore

import logger_setup
from Functions.Widget_classes import get_total_records
from util.widgets.models.CheckableSqlTableModel import CheckableSqlTableModel


class LazyCheckableSqlTableModel(CheckableSqlTableModel):
    """
    Custom CheckableSqlTableModel that only loads items when they are first visible.
    Uses the canFetchMore and fetchMore methods to load items in batches when needed, which improves performance for large tables.
    """

    def __init__(self):
        super().__init__()
        self.batch_size = 1000  # Number of rows to load in each batch
        self.loaded_row_count = 0  # Number of rows currently loaded
        self.total_rows = 0  # Number of rows that can be loaded

    def setTable(self, tableName: typing.Optional[str]):
        super().setTable(tableName)
        self.total_rows = get_total_records(self.tableName())

    def rowCount(self, parent=None):
        # Return the number of loaded rows
        return self.loaded_row_count

    def canFetchMore(self, parent=None):
        # Check if there are more rows to load
        return self.loaded_row_count < self.total_rows

    def fetchMore(self, parent=None):
        # Load the next batch of rows
        remaining_rows = self.total_rows - self.loaded_row_count
        rows_to_load = min(self.batch_size, remaining_rows)

        if rows_to_load > 0:
            # Fetch the next batch of rows from the database
            self.beginInsertRows(QtCore.QModelIndex(), self.loaded_row_count, self.loaded_row_count + rows_to_load - 1)
            self.loaded_row_count += rows_to_load
            self.endInsertRows()
            logger_setup.get_logger().debug(f'Loaded {rows_to_load} more rows for {self.tableName()}, total loaded: {self.loaded_row_count}/{self.total_rows}')

    def data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = ...):
        # Override data method to ensure that only loaded rows are accessed
        if index.row() >= self.loaded_row_count:
            return None  # Return None for rows that are not yet loaded
        return super().data(index, role)
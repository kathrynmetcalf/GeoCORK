from PyQt6 import QtCore, QtSql
from PyQt6.QtSql import QSqlQueryModel, QSqlDatabase

import logger_setup
from Functions.Check_triggers import update_modified_timestamp
from Functions.Settings_manager import SettingsManager
from Functions.Widget_classes import update_other_table_with_checks, get_name_column, get_view_from_table, \
    get_name_from_id, update_many_table_with_checks, get_total_records, delete_data
from util.display_formatting import return_rounded, display_value_with_error, display_gps, display_age

settings = SettingsManager().settings


class DisplayRoundedQueryModel(QSqlQueryModel):
    """
    Custom QSqlQueryModel to display the data of a SQLite database table with rounded values.
    This model was created to display the data in a more user-friendly way, such as rounding.
    """

    def __init__(self, db=QSqlDatabase()):
        super().__init__()
        self.table = ''
        self.table_name_col = ''
        self.db = db
        self.query_text = ''
        self.rounded = True

    def setQuery(self, query_text: str):
        """
        Set the query for the model. Also sets the table name, view name, name column in the table, and name column in
        the view based on the query.
        :param query_text: SQLite query as text string
        :return:
        """
        if not query_text:
            logger_setup.get_logger().info(f"No query text provided, skipping setQuery for {self.objectName()}.")
            return
        super().setQuery(query_text, self.db)
        if self.lastError().text():
            logger_setup.get_logger().critical(f"Error displaying table")
            logger_setup.get_logger().debug(f"Failed to set query: {self.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query_text}")
        else:
            self.query_text = query_text
            if 'table_info' in query_text:
                self.set_table('table_info')
            elif 'WITH ' in query_text:
                # The query is too complex to determine the table name directly
                self.set_table(None)
            else:
                self.set_table(query_text.split('FROM ')[1].split(' ')[0].strip())

    def set_table(self, new_table: str | None):
        """
        Updates the model with a new table.
        :param new_table: New table name to apply.
        """
        self.table = new_table
        if self.table:
            if 'JOIN' in self.query_text or 'ReferenceDisplay' in self.query_text:
                # Most likely a view query
                self.table_name_col = get_name_column(get_view_from_table(self.table))
            else:
                self.table_name_col = get_name_column(self.table)
        else:
            self.table_name_col = None

    def tableName(self) -> str:
        """
        Return the table name for the model.
        :return: string with table name or ''
        """
        return self.table

    def data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole):
        """
        Return the data for the given index and role.
        :param index: table index
        :param role: expects DisplayRole
        :return: value if valid index given, False if not
        """
        if not index.isValid():
            return False
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            # check the header of the selected index
            header = self.headerData(index.column(), QtCore.Qt.Orientation.Horizontal,
                                     QtCore.Qt.ItemDataRole.DisplayRole)
            value = super().data(index, role)
            if isinstance(value, str):
                if 'Age' in header:
                    for age_string in [f'({settings.value("age_unit_abbreviation")})', 'AgeCalculated', 'AgeDisplay']:
                        if age_string in header:
                            return display_age(value)
                elif 'GPS' in header:
                    return display_gps(value)
                elif 'Elevation' in header or 'Height' in header or 'Depth' in header:
                    return display_value_with_error(value)
            # if the value is a number but not an integer, and rounded is True
            elif value is not None and isinstance(value, (int, float)) and self.rounded:
                return return_rounded(value)
            else:
                return value
        return super().data(index, role)

    def unrounded_data(self, index: QtCore.QModelIndex = ...,
                       role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole):
        return super().data(index, role)


class CheckableSqlQueryModel(DisplayRoundedQueryModel):
    """
    Custom DisplayRoundedQueryModel (subclass of QSqlQueryModel) with check boxes enabled for each row.
    Name column has a tool tip with the description if available
    Supports partial checks through code, but any user input only toggles checked or unchecked.
    Stores lists of checked_ids and partially_checked_ids.
    """
    checksChanged = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.checked_ids = set()
        self.partially_checked_ids = set()
        self.primary_key_column = 0
        self.single_click = False
        self.not_null = False

    def flags(self, index):
        """Set check boxes on the name column only"""
        flags = super().flags(index)
        col = get_name_column(get_view_from_table(self.tableName()))
        if index.column() == col:
            flags |= QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEditable | QtCore.Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        col = get_name_column(get_view_from_table(self.tableName()))
        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            if self.index(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole) in self.checked_ids:
                return QtCore.Qt.CheckState.Checked
            elif self.index(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole) in self.partially_checked_ids:
                return QtCore.Qt.CheckState.PartiallyChecked
            else:
                return QtCore.Qt.CheckState.Unchecked
        elif index.column() == col and role == QtCore.Qt.ItemDataRole.ToolTipRole:
            description_col = None
            for header_col in range(self.columnCount()):
                header = self.headerData(header_col, QtCore.Qt.Orientation.Horizontal,
                                         QtCore.Qt.ItemDataRole.DisplayRole)
                if 'Description' in header:
                    description_col = header_col
                    break
            if description_col is not None:
                return super().data(self.index(index.row(), description_col), QtCore.Qt.ItemDataRole.DisplayRole)
        return super().data(index, role)

    def setData(self, index: QtCore.QModelIndex, value, role: QtCore.Qt.ItemDataRole = ...) -> bool:
        if not index.isValid():
            return super().setData(index, value, role)
        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            item_id = self.index(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole)
            if not item_id:
                logger_setup.get_logger().debug(f'No ID found for row {index.row()} in {self.tableName()}')
                return False
            if value == QtCore.Qt.CheckState.Checked:
                if item_id not in self.checked_ids:
                    self.checked_ids.add(item_id)
            elif value == QtCore.Qt.CheckState.PartiallyChecked:
                if item_id not in self.partially_checked_ids:
                    self.partially_checked_ids.add(item_id)
            else:
                if item_id in self.checked_ids:
                    self.checked_ids.remove(item_id)
                if item_id in self.partially_checked_ids:
                    self.partially_checked_ids.remove(item_id)
            self.dataChanged.emit(index, index, [role])
            return True
        return super().setData(index, value, role)

    def clear_checks(self):
        """
        Clears the check state of all items in the model.
        This method clears the checked_id and partially_checked_ids sets.
        """
        if self.checked_ids or self.partially_checked_ids:
            self.update_model_checks(set(), set())

    def check_all(self):
        """
        Adds all IDs in the source model to the set of checked_ids and clear the set of
        partially_checked_ids.
        """
        all_ids = set()
        for row in range(self.rowCount()):
            item_id = self.index(row, 0).data(QtCore.Qt.ItemDataRole.DisplayRole)
            if item_id:
                all_ids.add(item_id)
        self.update_model_checks(all_ids, set())

    def update_model_checks(self, checked_items: set[int], partially_checked_items: set[int]):
        """
        Checks the checkable items in the model based on the provided sets of checked and partially checked IDs.
        This method updates the checked_id and partially_checked_ids sets.
        :param checked_items: set of item IDs that should be checked
        :param partially_checked_items: set of item IDs that should be partially checked
        :return:
        """
        if self.checked_ids != checked_items or self.partially_checked_ids != partially_checked_items:
            self.checked_ids = checked_items
            self.partially_checked_ids = partially_checked_items
            self.checksChanged.emit()

    def return_checked_ids(self):
        """Returns a list of checked_ids and a list of partially_checked_ids"""
        return list(self.checked_ids), list(self.partially_checked_ids)

    def selected_items_string(self):
        """
        Returns a list of strings representing the items selected by the user.
        Includes both checked and partially checked items.
        """
        selected_names = set()
        for checked_id in self.checked_ids:
            name = get_name_from_id(self.tableName(), checked_id)
            if name is not None:
                selected_names.add(name)
        for partially_checked_id in self.partially_checked_ids:
            name = get_name_from_id(self.tableName(), partially_checked_id)
            if name is not None:
                selected_names.add(name)
        # Sort the names alphabetically (case-insensitive) and return as a semicolon separated string
        return '; '.join(sorted(selected_names, key=lambda s: s.lower()))

    def update_other_table(self, other_table: str, other_ids: list) -> str:
        """
        Collect the checked IDs and partially checked IDs from this table and update that field in another table.
        It calls the update_other_table_with_checks function to perform the update operation. This is useful for one-to-many
        relationships, such as updating the ColumnID in the Samples table with the checked ID in the Columns table.
        The relationship must be one-to-one or one-to-many, so there should be only one checked ID. If there are partially
        checked IDs, no item has been selected to associate with all IDs in the other table, so do not update. If the
        relationship is many-to-many, use update_many_table instead.
        :param other_table: name of the other table to update with the checked IDs from this table (e.g. Samples)
        :param other_ids: list of IDs in the other table that correspond to the checked items in this tree model
        (e.g. list of SampleIDs)
        :return: 'True' if successful, 'No' if not needed, 'False' needed but failed
        """
        if not other_ids:
            logger_setup.get_logger().error(f'No item IDs given for {other_table}')
            return 'False'
        if self.partially_checked_ids:
            # Any selection for a one-to-many relationship should be complete, so there should be no partially checked IDs
            logger_setup.get_logger().info(f'Partially checked IDs for one-to-many relationship, no changes to update')
            return 'No'
        if len(self.checked_ids) > 1:
            # If there are multiple checked IDs, this is a many-to-many relationship, so we should not use this function
            logger_setup.get_logger().error(
                f'Multiple checked IDs given for {self.tableName()}. Select only one ID to update {other_table}.')
            logger_setup.get_logger().debug(
                f'This should be a one-to-many relationship, so set the checkable combo box to single click.')
            return 'False'
        return update_other_table_with_checks(self.table, list(self.checked_ids), list(self.partially_checked_ids),
                                              other_table, other_ids)

    def update_many_table(self, many_table: str, item_ids: list) -> str:
        """
        Updates many-to-many relationship with another table. This method is useful when editing joined views, like
        editing the Units associated with Samples.
        :param many_table: name of the many-to-many table to update (e.g. Samples_Units)
        :param item_ids: list of foreign IDs to update in the many-to-many table (e.g. SampleIDs)
        :return: 'True' if successful, 'No' if not needed, 'False' needed but failed
        """
        if not item_ids:
            logger_setup.get_logger().error(f'No item IDs given for {many_table}')
            return 'False'
        return update_many_table_with_checks(self.table, list(self.checked_ids), list(self.partially_checked_ids),
                                             many_table, item_ids)


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
        if index.column() == col or 'Description' in self.headerData(index.column(), QtCore.Qt.Orientation.Horizontal,
                                                                     QtCore.Qt.ItemDataRole.DisplayRole):
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


class LazyCheckableSqlQueryModel(CheckableSqlQueryModel):
    """
    Custom CheckableSqlTableModel that only loads items when they are first visible.
    Uses the canFetchMore and fetchMore methods to load items in batches when needed, which improves performance for large tables.
    """

    def __init__(self):
        super().__init__()
        self.batch_size = 1000  # Number of rows to load in each batch
        self.loaded_row_count = 0  # Number of rows currently loaded

    def rowCount(self, parent=None):
        # Return the number of loaded rows
        return self.loaded_row_count

    def canFetchMore(self, parent=None):
        # Check if there are more rows to load
        total_rows = get_total_records(self.tableName())
        return self.loaded_row_count < total_rows

    def fetchMore(self, parent=None):
        # Load the next batch of rows
        total_rows = super().rowCount()
        remaining_rows = total_rows - self.loaded_row_count
        rows_to_load = min(self.batch_size, remaining_rows)

        if rows_to_load > 0:
            # Fetch the next batch of rows from the database
            self.beginInsertRows(QtCore.QModelIndex(), self.loaded_row_count, self.loaded_row_count + rows_to_load - 1)
            self.loaded_row_count += rows_to_load
            self.endInsertRows()

    def data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = ...):
        # Override data method to ensure that only loaded rows are accessed
        if index.row() >= self.loaded_row_count:
            return None  # Return None for rows that are not yet loaded
        return super().data(index, role)

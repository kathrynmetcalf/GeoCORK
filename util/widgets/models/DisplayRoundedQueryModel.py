from PyQt6 import QtCore
from PyQt6.QtSql import QSqlQueryModel, QSqlDatabase

import logger_setup
from Functions.Settings_manager import SettingsManager
from Functions.Widget_classes import get_name_column, get_view_from_table
from util.display_formatting import display_age, display_gps, display_value_with_error, return_rounded

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
            header = self.headerData(index.column(), QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole)
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

    def unrounded_data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole):
        return super().data(index, role)
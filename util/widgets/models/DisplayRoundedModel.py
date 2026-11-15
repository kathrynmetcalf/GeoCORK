from PyQt6 import QtCore, QtSql
from PyQt6.QtSql import QSqlDatabase

from Functions.Settings_manager import SettingsManager
from util.display_formatting import display_age, display_gps, display_value_with_error, return_rounded

settings = SettingsManager().settings

class DisplayRoundedModel(QtSql.QSqlTableModel):
    """
    Custom QSqlTableModel to display the data of a SQLite database table with rounded values.
    This model was created to display the data in a more user-friendly way, such as rounding.
    """
    def __init__(self, db=QSqlDatabase()):
        super().__init__(db=db)

    def data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = ...):
        """
        Return the data for the given index and role.
        :param index: table index
        :param role: expecting DisplayRole
        :return: False if index is invalid, otherwise return the user-readable data stored in the model at the given index
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
                elif 'GPS' in header and 'Format' not in header:
                    return display_gps(value)
                elif 'Elevation' in header or 'Height' in header or 'Depth' in header and 'Unit' not in header:
                    return display_value_with_error(value)
            # if the value is a number but not an integer
            elif value is not None and isinstance(value, (int, float)):
                return return_rounded(value)
            else:
                return value
        if (self.tableName().endswith('Formats') or self.tableName().endswith('Units')) and role == QtCore.Qt.ItemDataRole.ToolTipRole:
            format_name = self.index(index.row(), 1).data(QtCore.Qt.ItemDataRole.DisplayRole)
            return format_name

        return super().data(index, role)

    def unrounded_data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = ...):
        """
        Return the raw data for the given index and role.
        :param index: table index
        :param role: any
        :return: same as super().data(index, role)
        """
        return super().data(index, role)
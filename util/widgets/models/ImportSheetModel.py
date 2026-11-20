import numpy as np
import pandas as pd
import qtawesome
from PyQt6 import QtCore
from PyQt6.QtCore import QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtWidgets import QApplication, QProgressDialog

import logger_setup
from util.loading_dialog_manager import LoadingDialogManager
from Functions.Widget_classes import strip_strings
from util.loading_dialog_manager import show_loading_dialog, close_loading_dialog


class ImportSheetModel(QAbstractTableModel):
    """
    Class to load an openpyxl worksheet into a pandas DataFrame and display it in a QTableView.
    Adds a DataFrame for row status (accepted, rejected, disabled).
    :param sheet:
    :param check_style:
    :param parent:
    """
    userDataChanged = QtCore.pyqtSignal(QModelIndex, QModelIndex, list)
    def __init__(self, sheet, check_style=False, parent=None):
        super().__init__(parent=parent)
        # drop empty rows and columns from the dataframe
        self.sheet = sheet
        non_empty_rows = []
        sheet_rows = []
        for row in sheet.iter_rows(values_only=True):
            sheet_rows.append(row)
        self._dataframe = pd.DataFrame(sheet_rows)
        # strip strings for all items in the dataframe
        self._dataframe = self._dataframe.map(strip_strings)
        # Replace any cells with only whitespace or "" with nan
        self._dataframe.replace(to_replace=r'^\s*$', value=np.nan, regex=True, inplace=True)
        # Replace any cells with only "NULL" (case insensitive) with nan
        self._dataframe.replace(to_replace='NULL', value=np.nan, regex=True, inplace=True)
        # Fill None with nan
        self._dataframe.fillna(value=np.nan, inplace=True)
        # Fill all nan with 'NULL'
        self._dataframe.replace(to_replace=np.nan, value='NULL', regex=True, inplace=True)
        self.header_background_brushes = {}
        self.cell_background_brushes = {}
        # Rename headers as integer of their column index
        column_headers = list(self._dataframe.columns)
        for column_header in column_headers:
            column_index = column_headers.index(column_header)
            if column_header != column_index:
                self._dataframe.columns.values[column_index] = column_index
        # Create another dataframe to store row status, accepted, rejected, disabled. Default accepted.
        # Also store the text color and strikethrough font. Default np.nan
        self._status_dataframe = pd.DataFrame({'_row_status': ['accepted'] * len(self._dataframe),
            '_color': [np.nan] * len(self._dataframe), '_strikethrough': [np.nan] * len(self._dataframe)})
        self.rejected_icon = qtawesome.icon('fa5s.minus-circle', color='red', scale_factor=1.0)
        self.accepted_icon = qtawesome.icon('fa5s.check', color='green', scale_factor=1.0)

        # todo these need to be switched over to color settings
        self.gray_brush = QBrush(QColor("#A0A0A0"))
        self.red_brush = QBrush(QColor("red"))
        self.transparent_brush = QBrush(QtCore.Qt.GlobalColor.transparent)

        if check_style:
            self.style_model()

        self.reset_row_headers()
        self._data_array = self._dataframe.to_numpy()
        self._status_array = self._status_dataframe.to_numpy()

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        if parent == QtCore.QModelIndex():
            return len(self._dataframe)
        return 0

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        if parent == QtCore.QModelIndex():
            return len(self._dataframe.columns)
        return 0

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        if not index.isValid():
            return QtCore.Qt.ItemFlag.NoItemFlags
        return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEditable

    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == QtCore.Qt.ItemDataRole.DisplayRole or role == QtCore.Qt.ItemDataRole.EditRole:
            value = str(self._data_array[index.row(), index.column()])
            return 'NULL' if value == 'nan' else str(value)
        elif role == QtCore.Qt.ItemDataRole.BackgroundRole:
            # Return the cell background color if set
            return self.cell_background_brushes.get(index, self.transparent_brush)
        elif role == QtCore.Qt.ItemDataRole.ForegroundRole:
            # Return gray text if the row is disabled
            status = self._status_array[index.row(), 0]
            if status == 'disabled':
                # logger_setup.get_logger().debug(f'Setting gray text for disabled row {index.row()}')
                return self.gray_brush  # Gray text
            elif isinstance(self._status_array[index.row(), 1], QBrush):
                return self._status_array[index.row(), 1]
        elif role == QtCore.Qt.ItemDataRole.FontRole:
            if isinstance(self._status_array[index.row(), 2], QFont):
                return self._status_array[index.row(), 2]

        # return super().data(index, role)
        return None

    def setData(self, index: QtCore.QModelIndex, value, role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid():
            return super().setData(index, value, role)
        if role in [QtCore.Qt.ItemDataRole.EditRole, QtCore.Qt.ItemDataRole.DisplayRole]:
            if self._dataframe.iat[index.row(), index.column()] != value:
                self._dataframe.iat[index.row(), index.column()] = value
                self.dataChanged.emit(index, index, [role])
                if role == QtCore.Qt.ItemDataRole.EditRole:
                    self.userDataChanged.emit(index, index, [role])
                self._data_array[index.row(), index.column()] = value
            return True
        elif role == QtCore.Qt.ItemDataRole.BackgroundRole:
            # Update the cell background color
            self.cell_background_brushes[index] = value
            self.dataChanged.emit(index, index, [role])
            return True
        return None

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(self._dataframe.columns[section])
            elif orientation == QtCore.Qt.Orientation.Vertical:
                return str(self._dataframe.index[section])
        elif role == QtCore.Qt.ItemDataRole.BackgroundRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                # Return the column header background color if set
                return self.header_background_brushes.get(section, self.transparent_brush)
        if role == QtCore.Qt.ItemDataRole.DecorationRole and orientation == QtCore.Qt.Orientation.Vertical:
            status = self._status_array[section, 0]
            if status == 'accepted':
                return self.accepted_icon
            elif status == 'rejected':
                return self.rejected_icon
            elif status == 'disabled':
                return None  # No icon for disabled
        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return "Double click to define/map column data"
            elif orientation == QtCore.Qt.Orientation.Vertical:
                return 'Double Click to accept/reject analysis data\nright click for more options'

        return super().headerData(section, orientation, role)

    def setHeaderData(self, section, orientation, value, role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.EditRole):
        if orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.EditRole:
            if value != self._dataframe.columns[section]:
                self._dataframe.rename({self._dataframe.columns[section]: value}, axis=1, inplace=True)
                self.headerDataChanged.emit(orientation, section, section)
            return True
        elif orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.BackgroundRole:
            # Update the column header background color
            if section not in self.header_background_brushes or self.header_background_brushes[section] != value:
                self.header_background_brushes[section] = value
                self.headerDataChanged.emit(orientation, section, section)
            return True
        elif orientation == QtCore.Qt.Orientation.Vertical:
            if role == QtCore.Qt.ItemDataRole.DecorationRole:
                # Update the row status based on the value
                if value in ['accepted', 'rejected', 'disabled'] and self._status_array[section, 0] != value:
                    self._status_dataframe.iat[section, 0] = value
                    self.headerDataChanged.emit(orientation, section, section)
                    # Also update the foreground color of all cells in the row
                    for column in range(self.columnCount()):
                        index = self.index(section, column)
                        self.dataChanged.emit(index, index, [QtCore.Qt.ItemDataRole.ForegroundRole])
                    self._status_array = self._status_dataframe.to_numpy()
                    return True
        return super().setHeaderData(section, orientation, value, role)

    def removeSelectedRows(self, rows: list) -> bool:
        """
        Removes rows from the table based on provided row indices.
        :param rows: list of row indices to remove from the table
        :return: True for success, False otherwise
        """
        self.beginRemoveRows(QtCore.QModelIndex(), 0, len(self._dataframe) - 1)
        rows.sort(reverse=True)
        for row in rows:
            if row == self.rowCount() - 1:
                # dropping the last row
                self._dataframe.drop(self._dataframe.tail(1).index, axis=0, inplace=True)
                self._status_dataframe.drop(self._status_dataframe.tail(1).index, axis=0, inplace=True)
            else:
                self._dataframe.drop(self._dataframe.index[row], axis=0, inplace=True)
                self._status_dataframe.drop(self._status_dataframe.index[row], axis=0, inplace=True)
        self._dataframe.reset_index(drop=True, inplace=True)
        self._status_dataframe.reset_index(drop=True, inplace=True)
        self._data_array = self._dataframe.to_numpy()
        self._status_array = self._status_dataframe.to_numpy()
        self.endRemoveRows()
        return True

    def removeRow(self, row: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        """
        Removes a row from the table based on provided row index.
        :param row: row index to remove from the table
        :param parent:
        :return: True for success, False otherwise
        """
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        if row == self.rowCount() - 1:
            # dropping the last row
            self._dataframe.drop(self._dataframe.tail(1).index, axis=0, inplace=True)
            self._status_dataframe.drop(self._status_dataframe.tail(1).index, axis=0, inplace=True)
        else:
            self._dataframe.drop(self._dataframe.index[row], axis=0, inplace=True)
            self._status_dataframe.drop(self._status_dataframe.index[row], axis=0, inplace=True)
        self._dataframe.reset_index(drop=True, inplace=True)
        self._dataframe.index = np.arange(1, len(self._dataframe) + 1)
        self._status_dataframe.reset_index(drop=True, inplace=True)
        self._status_dataframe.index = np.arange(1, len(self._status_dataframe) + 1)
        self._data_array = self._dataframe.to_numpy()
        self._status_array = self._status_dataframe.to_numpy()
        self.endRemoveRows()
        return True

    def removeSelectedColumns(self, columns: list) -> bool:
        """
        Removes columns from the table based on provided column indices.
        :param columns: list of column indices to remove from the table
        :return: True for success, False otherwise
        """
        self.beginResetModel()
        columns.sort(reverse=True)
        for col in columns:
            self._dataframe.drop(self._dataframe.columns[col], axis=1, inplace=True)
        self._data_array = self._dataframe.to_numpy()
        self.endResetModel()
        return True

    def removeColumn(self, column: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        """
        Removes a column from the table based on the provided column index.
        :param column: column index to remove from the table
        :param parent:
        :return: True for success, False otherwise
        """
        self.beginRemoveColumns(QtCore.QModelIndex(), column, column)
        self._dataframe.drop(self._dataframe.columns[column], axis=1, inplace=True)
        self._data_array = self._dataframe.to_numpy()
        self.endRemoveColumns()
        return True

    def insertColumns(self, column: int, count: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        """
        Inserts columns into the table at the given position.
         New columns will be named "{column+count}", and any headers to the left that are the same as their index will be
         renamed to match their new index.
        :param column:
        :param count:
        :param parent:
        :return:
        """
        self.beginInsertColumns(parent, column, column + count - 1)
        for i in range(count):
            new_col_name = f'{column + 1}'
            self._dataframe.insert(column, new_col_name, 'NULL')
        self.endInsertColumns()

        # Rename any integer headers to the right to match their new index
        for col in range(column, len(self._dataframe.columns)):
            try:
                header = int(self._dataframe.columns[col])
                if header != col:
                    self._dataframe.columns.values[col] = col
            except ValueError:
                # This header is not an integer, so skip it
                continue
        self._data_array = self._dataframe.to_numpy()
        return True

    def insertColumn(self, column: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        """
        Inserts a column into the table at the given position.
        :param column:
        :param parent:
        :return:
        """
        self.beginInsertColumns(QtCore.QModelIndex(), column, column)
        new_column = ['NULL'] * len(self._dataframe.index)
        new_df = pd.DataFrame(new_column, index=self._dataframe.index)
        upper_df = self._dataframe.iloc[:, :column]
        lower_df = self._dataframe.iloc[:, column:]
        self._dataframe = pd.concat([upper_df, new_df, lower_df], axis=1)
        # self._dataframe.fillna('NULL', inplace=True)
        self.endInsertColumns()
        # Rename any integer headers to the right to match their new index
        for col in range(column, len(self._dataframe.columns)):
            try:
                header = int(self._dataframe.columns[col])
                if header != col:
                    self._dataframe.columns.values[col] = col
            except ValueError:
                # This header is not an integer, so skip it
                continue
        self._data_array = self._dataframe.to_numpy()
        return True

    def reset_row_headers(self):
        """
        Resets the row headers to be sequential integers starting from 1.
        """
        self.beginResetModel()
        self._dataframe.index = [str(i+1) for i in self._dataframe.index]
        self._status_dataframe.index = [str(i+1) for i in self._status_dataframe.index]
        self.endResetModel()

    def rows_for_status(self, status: str):
        """
        Returns the row index (not header) for all rows with the given status.
        :param status: 'accepted', 'rejected', or 'disabled'
        :return:
        """
        if status in ['accepted', 'rejected', 'disabled']:
            df = self._status_dataframe.copy()
            df.reset_index(drop=True, inplace=True)
            return df.index[df['_row_status'] == status].tolist()
        else:
            return []

    def return_row_status(self, row) -> str:
        """
        Returns the row status of the index's row.
        """
        return str(self._status_array[row, 0])

    def update_row_status(self, row, status: str):
        """
        Updates the row status and icon of the index's row.
        """
        if status in ['accepted', 'rejected', 'disabled']:
            self._status_dataframe.iat[row, 0] = status
            self._status_array[row, 0] = status

    def style_model(self):
        """
        Styles the model by getting the font and color for each cell in the sheet based on its content.
        """
        if self.sheet.max_row != self.rowCount():
            logger_setup.get_logger().error('Rows have been removed and can no longer be mapped to the original import file.\n\nSave the current mapping, reload the import file, and select the checkbox before removing rows.')
            return False
        if self.rowCount() != self._status_dataframe.shape[0]:
            logger_setup.get_logger().critical('Data are unsynced.\n\nSave the current mapping and reload the import file.')
            return False

        logger_setup.get_logger().info('Identifying rejected rows by style')
        show_loading_dialog('Loading', 'Identifying rejected rows...')

        style_progress_dialog = QProgressDialog(
            "Identifying rejected rows...", "Cancel", 0, self.sheet.max_row+1, LoadingDialogManager.get_instance().dialog
        )

        for row in range(1, self.sheet.max_row+1):
            style_progress_dialog.setValue(row)
            QApplication.processEvents()
            if style_progress_dialog.wasCanceled():
                close_loading_dialog('Loading', 'Identifying rejected rows...')
                return False
            for col in range(1, self.sheet.max_column):
                if col > self.columnCount():
                    continue
                if self._status_array[row-1, 0] == 'rejected':
                    continue
                cell = self.sheet.cell(row=row, column=col)
                if cell.font:
                    font = cell.font
                    if font.color and hasattr(font.color, "rgb") and isinstance(font.color.rgb, str):
                        hex_col = "#" + font.color.rgb[-6:]
                        # if the color is red or close to red set the row to rejected automatically
                        if hex_col.lower() in ["#EB1800", "#FF00000"]:  # Red
                            self._status_dataframe.iat[row-1, 0] = 'rejected'
                            self._status_dataframe.iat[row-1, 1] = self.red_brush
                            break
                    # if the row is struck through auto set rejected
                    if font.strike:
                        self._status_dataframe.iat[row-1, 0] = 'rejected'
                        font = QFont()
                        font.setStrikeOut(True)
                        self._status_dataframe.iat[row-1, 2] = font
                        break
        style_progress_dialog.setValue(row+1)
        QApplication.processEvents()
        if style_progress_dialog.wasCanceled():
            close_loading_dialog('Loading', 'Identifying rejected rows...')
            return False

        logger_setup.get_logger().info('Identified rejected rows by style')
        close_loading_dialog('Loading', 'Identifying rejected rows...')
        self._status_array = self._status_dataframe.to_numpy()
        return True

    def unstyle_model(self):
        # Default font color
        for row in range(self.rowCount()):
            self._status_dataframe.iat[row+1, 0] = 'rejected'
            self._status_dataframe.iat[row+1, 1] = np.nan
            self._status_dataframe.iat[row+1, 2] = np.nan
        self._status_array = self._status_dataframe.to_numpy()

    def clear_all_background_colors(self):
        """
        Sets all backgrounds to default which is usually transparent
        """
        self.cell_background_brushes = {}
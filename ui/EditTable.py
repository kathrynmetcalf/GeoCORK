import os
import sys

from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import QRegularExpression
from PyQt6.uic import loadUi

import Functions.Text_manipulations as TxM
import logger_setup
from Functions.Database_manager import update_database
from Functions.LoadingDialog_manager import LoadingDialogManager
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Settings_manager import settings
from Functions.Widget_classes import (get_headers,
                                      ReadableProxyModel, get_name_column, get_total_records, EditableSqlQueryModel)
from ui.AddTags import AddTags


class EditTable(QtW.QDialog):
    """
    Opens an EditTable dialog used to edit a table in the database.
    """

    def __init__(self, parent_window, table_name, **kwargs):
        super().__init__(parent=parent_window)
        self.loading_manager = LoadingDialogManager.get_instance()
        logger_setup.get_logger().info(f'Opening {table_name} edit dialog')
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "EditTable.ui")
        loadUi(sources_ui_file, self)
        self.setModal(True)
        self.setWindowTitle(f'Edit {TxM.add_spaces_camel(table_name)}')
        self.add_pushButton.setText(f'Add {TxM.add_spaces_camel(table_name)}')
        self.updated = False

        self.table = TxM.remove_spaces(table_name)
        self.msg = QtW.QMessageBox(self)


        # Pagination variables
        self.show_per_page_comboBox: QtW.QComboBox
        self.show_per_page_comboBox.addItems(['10', '25', '50', '100', '250', '500', '1000'])
        self.current_page = 0
        self.rows_per_page = settings.value('show_per_page')
        self.show_per_page_comboBox.setCurrentText(str(self.rows_per_page))
        self.total_records = 0

        self.model = EditableSqlQueryModel()
        self.table_proxy_model = ReadableProxyModel()
        self.name_column = None
        self.name_header = None
        self.table_headers = None
        self.create_model()

        create_savepoint('before_edit')

        self.close_by_dialog = False
        self.search_lineEdit.editingFinished.connect(self.search)
        self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        self.cancel_pushButton.clicked.connect(self.rollback)

        self.edit_tableView.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.edit_tableView.customContextMenuRequested.connect(self.show_context_menu)

        self.loading_manager.close_loading_dialog('Loading', f'Opening edit window for {table_name}...')

    def search(self):
        """
        Searches the table for the text in the search line edit using case-insensitive regex.
        """
        self.search_lineEdit: QtW.QLineEdit
        self.table_proxy_model.setRecursiveFilteringEnabled(True)
        search_expression = QtC.QRegularExpression(self.search_lineEdit.text(),
                                                   options=QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.table_proxy_model.setFilterRegularExpression(search_expression)

    def create_model(self):
        """
        Creates the model from the given table and paginates the table.
        :return:
        """
        self.model.setQuery(
            f'SELECT * FROM {self.table} LIMIT {self.rows_per_page} OFFSET {self.current_page * self.rows_per_page}')
        self.table_headers = get_headers(self.table)
        self.table_proxy_model.setSourceModel(self.model)
        self.table_proxy_model.setFilterKeyColumn(-1)  # search all columns

        self.name_column = get_name_column(self.table)
        self.name_header = self.table_headers[self.name_column]

        self.display_table()

    def change_rows_per_page(self):
        """
        Slot to change the number of rows displayed per page
        """
        self.rows_per_page = int(self.show_per_page_comboBox.currentText())
        self.current_page = 0
        self.create_model()

    def next_page(self):
        """
        Slot to move to the next page for the displayed table
        """
        if (self.current_page + 1) * self.rows_per_page < self.total_records:
            self.current_page += 1
            self.create_model()

    def previous_page(self, db_stackedWidget, dbTable_tableView, dbTable_comboBox, edit_pushButton):
        """
        Slot to move to the previous page for the displayed table
        """
        if self.current_page > 0:
            self.current_page -= 1
            self.create_model()

    def show_context_menu(self, pos: QtC.QPoint):
        """
        Shows a context menu for the table view. The context menu has options to clear a cell or delete a row.
        :param QPoint pos:
        """
        indexes = self.edit_tableView.selectedIndexes()
        if not indexes:
            return
        menu = QtW.QMenu()
        if len(indexes) == 1:
            if not indexes[0].isValid():
                return
            clear_action = menu.addAction('Clear value')
        else:
            clear_action = None
        delete_action = menu.addAction('Delete row')
        action = menu.exec(self.edit_tableView.viewport().mapToGlobal(pos))
        if action == clear_action:
            self.model.setData(indexes[0], '', QtC.Qt.ItemDataRole.EditRole)
        elif action == delete_action:
            delete_msg = QtW.QMessageBox()
            delete_msg.setWindowTitle(f'Delete row')
            # get all the rows in the selected indexes
            rows = []
            for index in indexes:
                model_index = self.table_proxy_model.mapToSource(index)
                if model_index.row() not in rows:
                    rows.append(model_index.row())
            if len(rows) == 1:
                delete_msg.setText(f'Are you sure you want to delete the selected row?')
            else:
                delete_msg.setText(f'Are you sure you want to delete the {len(rows)} selected rows?')
            delete_msg.setIcon(QtW.QMessageBox.Icon.Warning)
            delete_msg.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
            delete_msg.setDefaultButton(QtW.QMessageBox.StandardButton.No)
            response = delete_msg.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                for row in rows:
                    if not self.model.deleteRowFromTable(row):
                        logger_setup.get_logger().critical(
                            f'Failed to delete row {row} from {self.table}: {self.model.lastError().text()}')
                self.create_model()
                self.display_table()

    def display_table(self):
        """
        Dislays the table in the table view. Sets the model for the table view to the proxy model.
        """
        logger_setup.get_logger().info(f'Displaying {self.table} table')
        self.loading_manager.show_loading_dialog('Loading', f'Displaying {self.table}...')
        self.edit_tableView.setModel(self.table_proxy_model)
        # self.edit_tableView.setModel(self.filter_proxy_model)
        for column in range(self.table_proxy_model.columnCount()):
            header = self.model.headerData(column, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            if 'ID' in header:
                self.edit_tableView.hideColumn(column)
        self.edit_tableView.resizeColumnsToContents()
        self.edit_tableView.setSortingEnabled(True)
        # Sort the table by the name column
        self.table_proxy_model.sort(self.name_column, QtC.Qt.SortOrder.AscendingOrder)
        self.total_records = get_total_records(self.table)
        if (self.current_page + 1) * self.rows_per_page > self.total_records:
            self.page_info_label.setText(
                f'{self.current_page * self.rows_per_page + 1}-{self.total_records} of {self.total_records}')
        else:
            self.page_info_label.setText(
                f'{self.current_page * self.rows_per_page + 1}-{(self.current_page + 1) * self.rows_per_page} of '
                f'{self.total_records}')
        self.loading_manager.close_loading_dialog('Loading', f'Displaying {self.table}...')

    def add_popup(self):
        """
        Opens an AddTags dialog to add tags to the table.
        """
        self.loading_manager.show_loading_dialog('Loading', f'Opening add window for {self.table}...')
        if not self.model.submit():
            errtxt = f'Failed to save changes to {self.table}: {self.model.lastError().text()}'
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
            return
        else:
            dlg = AddTags(self, self.table)
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
        self.create_model()

    def rollback(self):
        """
        Rolls back the changes to the database. Rejects the dialog and closes the window.
        """
        rollback_savepoint('before_edit')
        self.reject()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        """
        Commits the changes to the database. If there is an active savepoint, it is released.
        """
        current_model_index = self.table_proxy_model.mapToSource(self.edit_tableView.currentIndex())
        if (self.edit_tableView.currentIndex().isValid() and
            not self.model.setData(current_model_index, QtC.Qt.ItemDataRole.EditRole)):
            # There is a valid index selected and submitting data failed
            logger_setup.get_logger().critical('Failed to save changes')
            return
        else:
            release_savepoint('before_edit')
            # Check if there is another existing savepoint. If not, go ahead and update the database
            if not SavepointManager.get_instance().active_savepoints():
                update_database()
            self.accept()
            self.msg.information(self, 'Success', 'Changes saved', QtW.QMessageBox.StandardButton.Ok)
            self.close_by_dialog = True
            self.close()
            self.close_by_dialog = False
            self.accept()

    def discard_question(self):
        """
        Asks the user if they want to discard changes. If they do, the changes are rolled back.
        """
        self.msg.question(self, 'Discard changes', 'Are you sure you want to discard all changes?',
                          QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        self.msg.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = self.msg.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            self.rollback()

    def closeEvent(self, event: QtG.QCloseEvent):
        """
        Overridden close event to handle the case where the user tries to close the dialog
        :param QCloseEvent event:
        """
        if not self.close_by_dialog:
            if self.updated:
                self.discard_question()
                event.ignore()
            else:
                logger_setup.get_logger().info(f'Closing {self.table} edit dialog')
                release_savepoint('before_edit')
                event.accept()
        else:
            logger_setup.get_logger().info(f'Closing {self.table} edit dialog')
            release_savepoint('before_edit')
            event.accept()

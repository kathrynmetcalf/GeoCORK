import os
import sys
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import QModelIndex
from PyQt6.uic import loadUi

import logger_setup
# from pandas.plotting import table

from Functions.Database_manager import update_database
from Functions.Settings_manager import settings
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
import Functions.Text_manipulations as TxM
from Functions.Widget_classes import (SQLiteTableModel, VerifiableSqlTableModel, VerifiableSqlViewModel, set_table, get_headers,
                                      ReadableProxyModel, get_name_column)
import Functions.Alter_database as Alter_db
from ui.AddTags import AddTags
from ui.GPSDialog import GPSDialog
import Functions.SQLUtils as SQLUtils
from ui.New_reference import NewReference


class EditTable(QtW.QDialog):
    def __init__(self, table_name, **kwargs):
        super().__init__()

        logger_setup.get_logger().info(f'Opening {table_name} edit dialog')
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "EditTable.ui")
        loadUi(sources_ui_file, self)
        self.setModal(True)
        self.setWindowTitle(f'Edit {TxM.add_spaces_camel(table_name)}')
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

        # self.model = QtS.QSqlQueryModel()
        self.model = QtS.QSqlTableModel()
        self.proxy_model = ReadableProxyModel()
        self.name_column = None
        self.name_header = None

        create_savepoint('before_edit')

        self.close_by_dialog = False
        self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        self.cancel_pushButton.clicked.connect(self.rollback)
        self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnFieldChange)
        self.edit_tableView.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.edit_tableView.customContextMenuRequested.connect(self.show_context_menu)

    def create_model(self):
        # self.model.setQuery(f'SELECT * FROM {self.table}')

        self.table_headers = get_headers(self.table)
        self.proxy_model.setSourceModel(self.model)

        self.name_column = get_name_column(self.table)
        model_index = self.model.index(0, self.name_column)
        proxy_index = self.proxy_model.mapFromSource(model_index)
        proxy_name_column = proxy_index.column()
        self.name_header = self.proxy_model.headerData(proxy_name_column, QtC.Qt.Orientation.Horizontal,
                                                       QtC.Qt.ItemDataRole.DisplayRole)

        # Sort the table by the name column
        self.proxy_model.sort(proxy_name_column, QtC.Qt.SortOrder.AscendingOrder)
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

    def show_context_menu(self, pos):
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
            self.msg.warning(self, 'Delete row', 'Are you sure you want to delete the selected rows?',
                             QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
            self.msg.setDefaultButton(QtW.QMessageBox.StandardButton.No)
            response = self.msg.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                # get all the rows in the selected indexes
                rows = []
                for index in indexes:
                    if index.row() not in rows:
                        rows.append(index.row())
                for row in rows:
                    if not self.model.deleteRowFromTable(row):
                        logger_setup.get_logger().critical(f'Failed to delete row {row} from {self.table}: {self.model.lastError().text()}')

    def display_table(self):
        logger_setup.get_logger().info(f'Displaying {self.table} table')
        self.edit_tableView.setModel(self.proxy_model)
        # self.edit_tableView.setModel(self.filter_proxy_model)
        for column in range(self.proxy_model.columnCount()):
            header = self.model.headerData(column, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            if 'ID' in header:
                self.edit_tableView.hideColumn(column)
        self.edit_tableView.resizeColumnsToContents()
        self.edit_tableView.setSortingEnabled(True)

    def add_popup(self):
        # if not self.add_pushButton.hasFocus():
        #     return
        if not self.model.submit():
            errtxt = f'Failed to save changes to {self.table}: {self.model.lastError().text()}'
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
            return
        else:
            dlg = AddTags(self.table)
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
        self.create_model()

    def rollback(self):
        rollback_savepoint('before_edit')
        self.reject()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        if self.edit_tableView.currentIndex().isValid() and not self.model.submitAll():
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
        self.msg.question(self, 'Discard changes', 'Are you sure you want to discard all changes?',QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        self.msg.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = self.msg.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            self.rollback()
        else:
            pass

    def closeEvent(self, event: QtG.QCloseEvent):
        if not self.close_by_dialog:
            if self.updated:
                self.discard_question()
                event.ignore()
            else:
                logger_setup.get_logger().info(f'Closing {self.table} edit dialog')
                event.accept()
        else:
            logger_setup.get_logger().info(f'Closing {self.table} edit dialog')
            event.accept()

import os
import sys
from pathlib import Path
import sqlite3
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6.uic import loadUi

import logger_setup
from Functions.Database_manager import update_database
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
import Functions.Text_manipulations as TxM
from Functions.Widget_classes import set_table, get_headers, get_name_column, description_column
import Functions.Check_triggers as Ct

class AddTags(QtW.QDialog):
    def __init__(self, parent_window, table):
        super().__init__(parent=parent_window)
        logger_setup.get_logger().info(f'Starting AddTags dialog for {table}...')
        # Define any widgets here
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "AddTags.ui")
        loadUi(sources_ui_file, self)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | QtC.Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle(f'Add tags to {TxM.add_spaces_camel(table)}')
        self.updated = False

        self.table = table
        self.model = QtS.QSqlTableModel()
        set_table(self.model, self.table)
        self.table_name = TxM.add_spaces_camel(self.table)
        self.selectTags_label.setText(self.table_name)
        self.errmsg = QtW.QMessageBox(self)
        self.clear_warning()

        self.filter_proxy_model = QtC.QSortFilterProxyModel()
        self.filter_proxy_model.setSourceModel(self.model)
        self.filter_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.filter_proxy_model.setFilterKeyColumn(1)
        self.newName_lineEdit.textChanged.connect(self.filter_proxy_model.setFilterRegularExpression)

        self.columns = get_headers(self.table)
        self.name_column = self.columns[get_name_column(self.table)]
        self.description_column = self.columns[description_column(self.table)]
        self.existing_names = []

        self.close_by_dialog = False
        self.display_tags()
        create_savepoint('before_add')
        self.ok_pushButton.clicked.connect(self.add_tag)
        self.cancel_pushButton.clicked.connect(self.discard_question)
        self.finish_pushButton.clicked.connect(self.commit)

    def display_tags(self):
        self.tags_tableView.setModel(self.filter_proxy_model)
        self.tags_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tags_tableView.hideColumn(0)
        self.tags_tableView.resizeColumnsToContents()
        self.tags_tableView.horizontalHeader().setDefaultAlignment(QtC.Qt.AlignmentFlag.AlignLeft)
        query = QtS.QSqlQuery()

        # Get a list of the existing tag names
        query.prepare(f'SELECT {self.name_column} FROM {self.table}')
        if not query.exec():
            logger_setup.get_logger().critical(f'Error selecting display column from {self.table}: {query.lastError().text()}')
            return False
        while query.next():
            self.existing_names.append(query.value(0))
        completer = QtW.QCompleter(self.existing_names)
        self.newName_lineEdit.setCompleter(completer)

    def clear_warning(self):
        self.warning_label.hide()

    def add_tag(self):
        name = self.newName_lineEdit.text()
        description = self.newDescription_lineEdit.text()
        query = QtS.QSqlQuery()
        query.prepare(f'INSERT INTO {self.table}({self.name_column}, {self.description_column}) VALUES(?, ?)')
        query.addBindValue(name)
        query.addBindValue(description)

        logger_setup.get_logger().info(f'Inserting {name}, {description} into {self.table}')

        if not query.exec():
            error = query.lastError().text()
            header = TxM.add_spaces_camel(self.columns[1])
            if 'UNIQUE constraint failed:' in error:
                duplicates = []
                for entry in self.existing_names:
                    if name.casefold() == entry.casefold():
                        duplicates.append(entry)
                logger_setup.get_logger().critical(f'Each entry in {header} must be unique (case insensitive) Duplicates: {duplicates}: {error}')
                self.errmsg.critical(self, 'Error',
                                     f'Each entry in {header} must be unique (case insensitive) Duplicates: {duplicates}: {error}',
                                     QtW.QMessageBox.StandardButton.Ok, QtW.QMessageBox.StandardButton.Ok)
            elif 'CHECK constraint failed:' in error:
                logger_setup.get_logger().critical(f'{header} cannot be blank: {error} ')
                self.errmsg.critical(self, 'Error', f'{header} cannot be blank', QtW.QMessageBox.StandardButton.Ok,
                                     QtW.QMessageBox.StandardButton.Ok)
            else:
                logger_setup.get_logger().critical(f'Error: {error}')
                self.errmsg.critical(self, 'Error', error, QtW.QMessageBox.StandardButton.Ok, QtW.QMessageBox.StandardButton.Ok)
            rollback_savepoint('before_add')

        logger_setup.get_logger().debug(f'SQL command: {query.lastQuery()}')

        self.model.setTable(self.table)
        self.model.select()
        self.newName_lineEdit.clear()
        self.newDescription_lineEdit.clear()
        self.display_tags()

        logger_setup.get_logger().info(f'Successfully inserted {name}, {description} into {self.table}')

    def discard_question(self):
        msg_box = QtW.QMessageBox()
        msg_box.setIcon(QtW.QMessageBox.Icon.Question)
        msg_box.setText('Are you sure you want to discard all changes?')
        msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            self.rollback()
        else:
            pass

    def rollback(self):
        rollback_savepoint('before_add')
        # self.model.revertAll()
        self.reject()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        if self.newName_lineEdit.text():
            if not self.add_tag():
                return False
        release_savepoint('before_add')
        # Check if there is another existing savepoint. If not, go ahead and update the database
        if not SavepointManager.get_instance().active_savepoints():
            update_database()
        self.accept()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def closeEvent(self, event: QtG.QCloseEvent):
        if not self.close_by_dialog:
            self.discard_question()
            event.ignore()
        else:
            event.accept()
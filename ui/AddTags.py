import os
import sys
from pathlib import Path
import sqlite3
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6.uic import loadUi
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
import Functions.Text_manipulations as TxM
import Functions.Errors as Er
import Functions.Check_triggers as Ct

class AddTags(QtW.QDialog):
    def __init__(self, model, table):
        super().__init__()

        # Define any widgets here
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "AddTags.ui")
        loadUi(sources_ui_file, self)

        self.model = model
        self.table = table
        self.table_name = TxM.add_spaces_camel(self.table)
        self.selectTags_label.setText(self.table_name)
        self.errmsg = QtW.QMessageBox(self)
        self.clear_warning()

        self.filter_proxy_model = QtC.QSortFilterProxyModel()
        self.filter_proxy_model.setSourceModel(self.model)
        self.filter_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.filter_proxy_model.setFilterKeyColumn(1)
        self.newName_lineEdit.textChanged.connect(self.filter_proxy_model.setFilterRegularExpression)

        self.columns = []
        self.name_column = ''
        self.description_column = ''
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

        # Get a list of column names for the selected table
        query.prepare(f'PRAGMA table_info({self.table})')
        query.exec()
        while query.next():
            self.columns.append(query.value(1))
            if 'Name' in query.value(1):
                self.name_column = query.value(1)
            elif 'Description' in query.value(1):
                self.description_column = query.value(1)

        # Get a list of the existing tag names
        query.prepare(f'SELECT {self.name_column} FROM {self.table}')
        query.exec()
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
        if query.exec():
            self.model.setTable(self.table)
            self.model.select()
            self.newName_lineEdit.clear()
            self.newDescription_lineEdit.clear()
            self.display_tags()
        else:
            error = query.lastError().text()
            header = TxM.add_spaces_camel(self.columns[1])
            if 'UNIQUE constraint failed:' in error:
                duplicates = []
                for entry in self.existing_names:
                    if name.casefold() == entry.casefold():
                        duplicates.append(entry)
                errtxt = Er.duplicate_entry(header, duplicates)
                self.errmsg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok, QtW.QMessageBox.StandardButton.Ok)
            elif 'CHECK constraint failed:' in error:
                errtxt = Er.blank_entry(header)
                self.errmsg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok,
                                     QtW.QMessageBox.StandardButton.Ok)
            else:
                self.errmsg.critical(self, 'Error', error, QtW.QMessageBox.StandardButton.Ok, QtW.QMessageBox.StandardButton.Ok)
            rollback_savepoint('before_add')

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
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        if self.newName_lineEdit.text():
            if not self.add_tag():
                return False
        release_savepoint('before_add')
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def closeEvent(self, event: QtG.QCloseEvent):
        if not self.close_by_dialog:
            self.discard_question()
            event.ignore()
        else:
            event.accept()
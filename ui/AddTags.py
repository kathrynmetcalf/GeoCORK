import sys
from pathlib import Path
import sqlite3
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6.uic import loadUi
import Functions.Text_manipulations as TxM
import Functions.Errors as Er

class AddTags(QtW.QDialog):
    def __init__(self, database, model, table):
        super().__init__()

        # Define any widgets here
        tags_ui_file = "ui/AddTags.ui"
        loadUi(tags_ui_file, self)
        self.db = database
        self.model = model
        self.table = table
        self.table_name = TxM.add_spaces_camel(self.table)
        self.selectTags_label.setText(self.table_name)
        self.errmsg = QtW.QMessageBox(self)

        self.filter_proxy_model = QtC.QSortFilterProxyModel()
        self.filter_proxy_model.setSourceModel(self.model)
        self.filter_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.filter_proxy_model.setFilterKeyColumn(1)
        self.newName_lineEdit.textChanged.connect(self.filter_proxy_model.setFilterRegularExpression)

        self.columns = []
        self.existing_names = []

        self.display_tags()
        self.ok_pushButton.clicked.connect(self.add_tag)
        self.cancel_pushButton.clicked.connect(self.reject)

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

        # Get a list of the existing tag names
        query.prepare(f'SELECT {self.columns[1]} FROM {self.table}')
        query.exec()
        while query.next():
            self.existing_names.append(query.value(0))
        completer = QtW.QCompleter(self.existing_names)
        self.newName_lineEdit.setCompleter(completer)

    # def clear_warning(self):
    #     self.warning_label.hide()

    def add_tag(self):
        name = self.newName_lineEdit.text()
        description = self.newDescription_lineEdit.text()
        query = QtS.QSqlQuery()
        query.prepare(f'INSERT INTO {self.table}({self.columns[1]}, {self.columns[2]}) VALUES(?, ?)')
        query.addBindValue(name)
        query.addBindValue(description)
        if query.exec():
            self.model.setTable(self.table)
            self.model.select()
            self.newName_lineEdit.clear()
            self.newDescription_lineEdit.clear()
            self.display_tags()
            self.accept()
        else:
            err = query.lastError().text()
            header = TxM.add_spaces_camel(self.columns[1])
            if 'UNIQUE constraint failed:' in err:
                duplicates = []
                for entry in self.existing_names:
                    if name.casefold() == entry.casefold():
                        duplicates.append(entry)
                errtxt = Er.duplicate_entry(header, duplicates)
                self.errmsg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok, QtW.QMessageBox.StandardButton.Ok)
            elif 'CHECK constraint failed:' in err:
                errtxt = Er.blank_entry(header)
                self.errmsg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok,
                                     QtW.QMessageBox.StandardButton.Ok)
            else:
                self.errmsg.critical(self, 'Error', err, QtW.QMessageBox.StandardButton.Ok, QtW.QMessageBox.StandardButton.Ok)

if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QDialog(sys.argv)  # pass command line arguments
    w = AddTags()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

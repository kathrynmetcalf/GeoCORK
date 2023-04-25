import sys
from pathlib import Path
import sqlite3
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6.uic import loadUi


class AddTags(QtW.QDialog):
    def __init__(self, database, model, table_name):
        super().__init__()

        # Define any widgets here
        tags_ui_file = "AddTags.ui"
        loadUi(tags_ui_file, self)
        self.db = database
        self.model = model
        self.table = table_name.replace(" ", "")
        self.selectTags_label.setText(table_name)
        self.clear_warning()

        self.filter_proxy_model = QtC.QSortFilterProxyModel()
        self.filter_proxy_model.setSourceModel(self.model)
        self.filter_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.filter_proxy_model.setFilterKeyColumn(1)
        self.newName_lineEdit.textChanged.connect(self.filter_proxy_model.setFilterRegularExpression)

        self.columns = []
        self.existing_names = []
        self.completer()

        self.display_tags()
        self.ok_pushButton.clicked.connect(self.add_tag)

    def display_tags(self):
        self.tags_tableView.setModel(self.filter_proxy_model)
        self.tags_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tags_tableView.hideColumn(0)
        self.tags_tableView.resizeColumnsToContents()
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

    def completer(self):
        # Get a list of the existing tag names
        query = QtS.QSqlQuery()
        # Get a list of column names for the selected table
        query.prepare(f'PRAGMA table_info({self.table})')
        query.exec()
        while query.next():
            self.columns.append(query.value(1))
        query.prepare(f'SELECT {self.columns[1]} FROM {self.table}')
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
        # Check to see if name is empty or exists, throw error if so
        if name == '':
            self.warning_label.show()
            self.warning_label.setText('<font color="red">Name cannot be blank</font>')
            self.warning_label.setAlignment(QtC.Qt.AlignmentFlag.AlignRight | QtC.Qt.AlignmentFlag.AlignVCenter)
        elif name in self.existing_names:
            self.warning_label.show()
            self.warning_label.setText('<font color="red">Name must be unique</font>')
            self.warning_label.setAlignment(QtC.Qt.AlignmentFlag.AlignRight | QtC.Qt.AlignmentFlag.AlignVCenter)
        else:
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


if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QDialog(sys.argv)  # pass command line arguments
    w = AddTags()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

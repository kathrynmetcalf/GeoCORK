import sys
from pathlib import Path
import sqlite3
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6.uic import loadUi


class EditTags(QtW.QDialog):
    def __init__(self, database, model, table_name, row):
        super().__init__()

        # Define any widgets here
        tags_ui_file = "EditTags.ui"
        loadUi(tags_ui_file, self)
        self.db = database
        self.model = model
        self.table = table_name.replace(" ", "")
        self.row = row
        self.selectTags_label.setText(table_name)
        self.clear_warning()

        self.columns = []
        self.existing_names = []
        self.completer()

        # Populate line edits with existing values
        self.name_lineEdit.setText(self.model.record(self.row).value(self.columns[1]))
        self.description_lineEdit.setText(self.model.record(self.row).value(self.columns[2]))

        self.ok_pushButton.clicked.connect(self.edit_tag)
        # self.name_lineEdit.textChanged.connect(self.clear_warning)

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
        self.name_lineEdit.setCompleter(completer)

    def clear_warning(self):
        self.warning_label.hide()

    def edit_tag(self):
        name = self.name_lineEdit.text()
        description = self.description_lineEdit.text()
        # Check to see if name is empty
        if name == '':
            self.warning_label.show()
            self.warning_label.setText('<font color="red">Name cannot be blank</font>')
            self.warning_label.setAlignment(QtC.Qt.AlignmentFlag.AlignRight | QtC.Qt.AlignmentFlag.AlignVCenter)
            self.name_lineEdit.setText(self.model.record(self.row).value(self.columns[1]))
        # Check to see if name is same as any row except the current one
        elif name in self.existing_names and name != self.model.record(self.row).value(self.columns[1]):
            self.warning_label.show()
            self.warning_label.setText('<font color="red">Name must be unique</font>')
            self.warning_label.setAlignment(QtC.Qt.AlignmentFlag.AlignRight | QtC.Qt.AlignmentFlag.AlignVCenter)
            self.name_lineEdit.setText(self.model.record(self.row).value(self.columns[1]))
        else:
            item_id = self.model.record(self.row).value(self.columns[0])
            query = QtS.QSqlQuery()
            query.prepare(f'''
                UPDATE {self.table} SET {self.columns[1]} = '{name}', {self.columns[2]} = '{description}'
                WHERE {self.columns[0]} = {item_id}
                ''')
            if query.exec():
                self.model.setTable(self.table)
                self.model.select()
                self.accept()


if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QDialog(sys.argv)  # pass command line arguments
    w = EditTags()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

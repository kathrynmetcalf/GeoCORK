import sys
from pathlib import Path
import sqlite3
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
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

        self.columns = []
        self.existing_names = []
        self.completer()

        self.ok_buttonBox.accepted.connect(self.edit_tag)

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

    def edit_tag(self):
        name = self.name_lineEdit.text()
        description = self.description_lineEdit.text()
        name_exists = False
        # Check to see if name exists, throw error if so
        if name in self.existing_names:
            name_exists = True
            error_dialog = QtW.QErrorMessage()
            error_dialog.showMessage('Name must be unique')

        if not name_exists:
            item_id = self.model.record(self.row).value(self.columns[0])
            print(item_id)
            query = QtS.QSqlQuery()
            query.prepare(f'''
                UPDATE {self.table} SET {self.columns[1]} = '{name}', {self.columns[2]} = '{description}'
                WHERE {self.columns[0]} = {item_id}
                ''')
            if query.exec():
                self.model.setTable(self.table)
                self.model.select()
                self.name_lineEdit.clear()
                self.description_lineEdit.clear()


if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QDialog(sys.argv)  # pass command line arguments
    w = EditTags()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

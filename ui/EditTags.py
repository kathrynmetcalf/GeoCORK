import sys
from pathlib import Path
import sqlite3
from PyQt6 import QtWidgets as QtW
from PyQt6.uic import loadUi


class EditTags(QtW.QDialog):
    def __init__(self, database, model, table_name):
        super().__init__()

        # Define any widgets here
        tags_ui_file = "EditTags.ui"
        loadUi(tags_ui_file, self)
        self.db = database
        self.model = model
        self.selectTags_label.setText(table_name)
        self.display_tags()
        self.addNewTag_pushButton.clicked.connect(self.add_tag)

    def display_tags(self):
        self.tags_tableView.setModel(self.model)
        self.tags_tableView.hideColumn(0)
        self.tags_tableView.resizeColumnsToContents()

    def add_tag(self):
        name = self.newName_lineEdit.text()
        description = self.newDescription_lineEdit.text()
        table = self.table_name.replace(" ", "")
        sql = f'PRAGMA table_info({table})'

        sql = '''INSERT INTO Ages(ParentAgeID, AgeName, MaxMa, MinMa)
                        VALUES(?,?,?,?)'''
        values = (name, description)


if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QDialog(sys.argv)  # pass command line arguments
    w = EditTags()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

import os
import sys
import sqlite3
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6.uic import loadUi
from PyQt6.QtSql import QSqlQuery


class NewReference(QtW.QDialog):
    def __init__(self, parent_window):
        super().__init__(parent=parent_window)

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        base_path = os.path.normpath(base_path)
        sources_ui_file = fr'{os.path.join(base_path, "New_reference.ui")}'
        sources_ui_file = os.path.normpath(sources_ui_file)
        loadUi(sources_ui_file, self)
        self.setWindowTitle('Add Reference')
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | QtC.Qt.WindowType.WindowStaysOnTopHint)

        self.ok_buttonBox.accepted.connect(self.add_reference)
        self.ok_buttonBox.rejected.connect(self.rejected)

    def add_reference(self):
        authors = self.authors_lineEdit.text()
        year = self.year_lineEdit.text()
        title = self.title_lineEdit.text()
        source = self.source_lineEdit.text()
        doi = self.doi_lineEdit.text()
        description = self.description_lineEdit.text()

        query = QSqlQuery()
        query.prepare('INSERT INTO "References" (Authors, Year, Title, Source, DOI, ReferenceDescription) VALUES (?, ?, ?, ?, ?, ?)')
        query.addBindValue(authors)
        query.addBindValue(year)
        query.addBindValue(title)
        query.addBindValue(source)
        query.addBindValue(doi)
        query.addBindValue(description)
        if not query.exec():
            print('Error inserting reference:', query.lastError().text())
            return
        self.accept()


# if __name__ == '__main__':
#     # only run these commands if this script is run
#     # Can't be run when used as a library for another script
#     app = QtW.QDialog(sys.argv)  # pass command line arguments
#     w = NewSource()
#     sys.exit(app.exec())  # runs event loop, pass exit status to the system

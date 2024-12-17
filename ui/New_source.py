import os
import sys
import sqlite3
from PyQt6 import QtWidgets as QtW
from PyQt6.uic import loadUi


class NewSource(QtW.QDialog):
    def __init__(self, existing):
        super().__init__()

        # Define any widgets here
        self.db_file = '../geochron_samples.db'
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "New_source.ui")
        loadUi(sources_ui_file, self)

        self.existing = existing
        completer = QtW.QCompleter(self.existing)
        self.short_lineEdit.setCompleter(completer)

        self.ok_buttonBox.clicked()
        self.ok_buttonBox.rejected(self.rejected)


# if __name__ == '__main__':
#     # only run these commands if this script is run
#     # Can't be run when used as a library for another script
#     app = QtW.QDialog(sys.argv)  # pass command line arguments
#     w = NewSource()
#     sys.exit(app.exec())  # runs event loop, pass exit status to the system

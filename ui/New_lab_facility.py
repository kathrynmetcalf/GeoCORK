import os
import sys

from PyQt6 import QtWidgets as QtW
from PyQt6.uic import loadUi


class NewLabFacility(QtW.QDialog):
    def __init__(self, db_file, *arg, **kwargs):
        super().__init__(*arg, **kwargs)

        # Define any widgets here
        self.db_file = db_file
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "New_lab_facility.ui")
        loadUi(sources_ui_file, self)

        self.ok_buttonBox.accepted(self.accepted())
        self.ok_buttonBox.rejected(self.rejected())


if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QDialog(sys.argv)  # pass command line arguments
    w = NewLabFacility()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

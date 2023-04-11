import sys
from PyQt6 import QtWidgets as QtW
from PyQt6.uic import loadUi


class EditTags(QtW.QDialog):
    def __init__(self, existing):
        super().__init__()

        # Define any widgets here
        self.db_file = '../geochron_samples.db'
        sources_ui_file = "EditTags.ui"
        loadUi(sources_ui_file, self)



        self.ok_buttonBox.clicked()
        self.ok_buttonBox.rejected(self.rejected)


if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QDialog(sys.argv)  # pass command line arguments
    w = EditTags()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

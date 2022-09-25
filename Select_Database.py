import sys
from PyQt5 import QtWidgets as QtW  # all windows
from PyQt5 import QtSql as QtS  # sql stuff
from PyQt5 import QtCore as QtC  # more low-level stuff
from PyQt5 import QtGui as QtG  # font and color classes, etc.
from PyQt5.uic import loadUi
# import any other class you need

class MainWindow(QtW.QWidget):  # know what you chose for your window, that has to be your super class

    def __init__(self, *arg, **kwargs):   # dunder (__) methods
        super().__init__(*arg, **kwargs)  # need to call super, pass all args into the super class (QWidget

        # Define any widgets here

        # self.ui = Ui_SampleDataForm()  # create instance
        # self.ui.setupUi(self)  # build it

        # End widgets here
        self.show()  # show the window when done, used for making a top-level window

    # Define any methods here

    # End methods here

def createConnection() -> bool:
    con = QtS.QSqlDatabase.addDatabase('QSQLITE')
    con.setDatabaseName(db_file)
    if not con.open():
        QtW.QMessageBox.critical(
            None,
            'QTableView Example - Error!',
            'Database Error: %s' % con.lastError().databaseText(),
        )
        return False
    return True

if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QApplication(sys.argv)  # pass command line arguments
    if not createConnection():
        sys.exit(1)
    w = MainWindow()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system
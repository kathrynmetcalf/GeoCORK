import sys
import sqlite3
from PyQt5 import QtWidgets as QtW  # all windows
from PyQt5 import QtCore as QtC  # more low-level stuff
from PyQt5 import QtGui as QtG  # font and color classes, etc.
from PyQt5 import QtSql as QtS  # sql stuff
from PyQt5.uic import loadUi
import database as db


class MainWindow(QtW.QMainWindow):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)

        # Define any widgets here

        db_file = 'geochron_samples.db'
        sources_ui_file = "GeochronMain.ui"
        loadUi(sources_ui_file, self)

        self.conn = QtS.QSqlDatabase.addDatabase('QSQLITE')
        self.conn.setDatabaseName(db_file)
        self.conn.open()
        self.model = QtS.QSqlTableModel()

        # Try to open the connection and handle possible errors
        if not self.conn.open():
            QtW.QMessageBox.critical(
                None,
                "Database Error!",
                "Database Error: %s" % self.conn.lastError().databaseText(),
            )
            sys.exit(1)

        # Create the tables if they don't already exist
        query = QtS.QSqlQuery()
        db.create_tables(query)

        # Add data for testing
        # self.create_source()

        # Display the list of tables
        dbtable_list = self.conn.tables()
        self.dbTable_comboBox.addItems(dbtable_list)

        # Display the selected table
        self.dbTable_comboBox.activated.connect(self.display_table)


        # Close connection
        # self.conn.close()

        # End widgets here
        self.show()  # show the window when done, used for making a top-level window

    # Define any methods here

    def display_table(self):
        table = self.dbTable_comboBox.currentText()
        if self.model.isDirty() is not None:
            self.commit_popup
        self.model.setTable(table)
        self.model.setEditStrategy(QtS.QSqlTableModel.OnManualSubmit)

        query = QtS.QSqlQuery()
        (table_data, table_headers) = db.retrieve_table(query, table)
        self.model.setHeaderData(table_headers)

    def commit_popup(self):
        msg = QtW.QMessageBox()
        msg.setIcon(QtW.QMessageBox.Information)
        msg.setWindowTitle('Commit changes')
        msg.setText('Save changes to the database? This cannot be undone.')
        msg.setStandardButtons(QtW.QMessageBox.No | QtW.QMessageBox.Yes)

    def commit_popup_clicked(self, click):
        if click.text == 'Yes':
            self.model.submitAll()
        if click.text == 'No':
            self.model.revertAll()

    def create_source(self):
        source = ('Hu et al.', '2016', 'The timing of India-Asia collision onset – Facts, theories, controversies',
                  'Earth-Science Reviews', '10.1016/j.earscirev.2016.07.014', 'Hu et al., 2016, ESR')
        db.create_source(self.conn, source)



    # End methods here



if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QApplication(sys.argv)  # pass command line arguments
    w = MainWindow()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

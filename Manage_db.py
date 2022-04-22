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

        self.conn = db.create_connection(db_file)
        self.model = QtS.QSqlTableModel()

        if self.conn is not None:
            db.create_tables(self.conn)

            with self.conn:

                # Create the tables if they don't already exist
                db.create_tables(self.conn)

                # Add data for testing
                self.create_source()


                # Display the list of tables
                dbtable_list = db.list_tables(self.conn)
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
        for model in reversed(self.model_list):
            if model[0] is table:  # look for most recent view for this table
                self.dbTable_tableView.setModel(model[1])

        (table_data, table_headers) = db.retrieve_table(self.conn, table)
        self.model.setHorizontalHeaderLabels(table_headers)
        for row in table_data:
            self.model.appendRow(row)
        self.dbTable_tableView.setModel(self.model)


    def create_source(self):
        source = ('Hu et al.', '2016', 'The timing of India-Asia collision onset – Facts, theories, controversies',
                  'Earth-Science Reviews', '10.1016/j.earscirev.2016.07.014', 'Hu et al., 2016, ESR')
        db.create_source(self.conn, source)


    def save(self):
        # pop-up asking if the user is sure, changes cannot be undone
        db.commit_changes(self.conn, self.model_list)
        self.model_list = []  # reset the list of table views

    # End methods here



if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QApplication(sys.argv)  # pass command line arguments
    w = MainWindow()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

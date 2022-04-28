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
        self.sample_model = QtS.QSqlRelationalTableModel()

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

        # Display the list of tables
        dbtable_list = self.conn.tables()
        self.dbTable_comboBox.addItems(dbtable_list)

        # Display the selected table
        self.dbTable_comboBox.activated.connect(self.display_table)

        # Signal for saving
        self.save_pushButton.clicked.connect(self.commit_popup)


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
        self.model.select()
        self.dbTable_tableView.setModel(self.model)
        self.dbTable_tableView.hideColumn(0)  # don't show ID column
        self.dbTable_tableView.resizeColumnsToContents()

    def commit_popup(self):
        print('save clicked')
        msg = QtW.QMessageBox()
        msg.setIcon(QtW.QMessageBox.Information)
        msg.setWindowTitle('Commit changes')
        msg.setText('Save changes to the database? This cannot be undone.')
        msg.setStandardButtons(QtW.QMessageBox.Save | QtW.QMessageBox.Discard | QtW.QMessageBox.Cancel)
        msg.buttonClicked.connect(self.commit_popup_clicked)
        msg.exec()

    def commit_popup_clicked(self, i):
        print(f'user clicked {i.text()}')
        if i.text() == 'Save':
            self.model.submitAll()
        if i.text() == 'Discard' or i.text() == 'Don\'t Save':
            self.model.revertAll()

    def contextMenuEvent(self, event: QtG.QContextMenuEvent) -> None:
        table = self.dbTable_comboBox.currentText()
        menu = QtW.QMenu(self)
        addAct = menu.addAction('Add item')
        deleteAct = menu.addAction('Remove selected')
        bulkAct = menu.addAction('Bulk edit selected')
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == addAct:
            if table == 'Sources':
                self.create_source()
        if action == deleteAct:
            index_list = []
            for model_index in self.dbTable_tableView.selectionModel().selectedRows():
                index = QtC.QPersistentModelIndex(model_index)
                index_list.append(index)
            for index in index_list:
                self.model.removeRow(index.row())

    def create_source(self):
        self.model.setTable('Sources')
        newSource = self.model.record()
        source = ('', '', '', '', '', '')
        newSource.setValue('Authors', source[0])
        newSource.setValue('Year', source[1])
        newSource.setValue('Title', source[2])
        newSource.setValue('Source', source[3])
        newSource.setValue('doi', source[4])
        newSource.setValue('Short Citation', source[5])
        if self.model.insertRecord(-1, newSource) is True:
            self.model.submitAll()
            self.dbTable_tableView.hideColumn(0)  # don't show ID column
            self.dbTable_tableView.resizeColumnsToContents()
        # if self.model.insertRows(self.model.rowCount(), 1) is True:
        #     self.model.submitAll()



    # End methods here



if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QApplication(sys.argv)  # pass command line arguments
    w = MainWindow()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

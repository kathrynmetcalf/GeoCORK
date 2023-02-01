import sys
from pathlib import Path

import pandas as pd
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtWidgets import QFileDialog

from PyQt6.uic import loadUi
import Functions.Create_database as create_db
import database as db
import ui.import_wizard


# import Select_Database as sd  # Eventually get database file from initial dialog


class GeoChron(QtW.QMainWindow):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)

        # Define any widgets here

        sources_ui_file = "GeochronMain.ui"
        loadUi(sources_ui_file, self)
        self.db_file = '../geochron_samples.db'
        self.db = QtS.QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(self.db_file)

        self.model = QtS.QSqlRelationalTableModel()
        self.sample_model = QtS.QSqlRelationalTableModel()
        self.status_bar = QtW.QStatusBar()
        # self.status_bar.show()

        create_db.create_tables(self.db_file)
        self.display_table_list()

        # self.dbTable_comboBox.setPlaceholderText('Select table')  # Bug in Qt5.15, broke this in 5.15.2
        # self.dbTable_comboBox.setCurrentIndex(-1)

        # Display the selected table
        self.dbTable_comboBox.activated.connect(self.display_table)

        # Signal for saving before switching tables, only saves the model, doesn't update the db file
        self.save_pushButton.clicked.connect(self.save_popup)

        # Signal for committing changes to the database file
        self.commit_pushButton.clicked.connect(self.commit_popup)
        self.actionImport.triggered.connect(self.show_import_wizard_dialog)

        # End widgets here
        self.show()  # show the window when done, used for making a top-level window

    # Define any methods here

    def show_import_wizard_dialog(self):
        home_dir = str(Path.home()) + '\Downloads'
        fname = QFileDialog.getOpenFileName(self, 'Open file', home_dir)
        print(fname[0])
        import_wizard = ui.import_wizard.ImportWizardDialog(fname[0])
        import_wizard.exec()

    def display_table_list(self):
        dbtable_list = db.list_tables(self.db_file)
        self.dbTable_comboBox.addItems(dbtable_list)
        self.dbTable_comboBox.setCurrentText('Samples')
        self.display_table()

    def display_table(self):
        if self.model.isDirty() is True:
            self.save_popup()
            '''Click cancel should stop this method'''
        table = self.dbTable_comboBox.currentText()
        # self.model.setTable(table)
        # self.model.setEditStrategy(QtS.QSqlTableModel.OnManualSubmit)
        # self.model.select()
        self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnFieldChange)
        if table == 'Samples':
            self.model.setTable('Samples')
            # self.model.setRelation(3, QtS.QSqlRelation('Age signature ID', 'Age signature ID', 'Age signature name'))
            self.model.setRelation(2, QtS.QSqlRelation("Sources", "Source ID", "Short Citation"))  # Currently breaking the table display
            self.model.select()
            self.dbTable_tableView.setModel(self.model)
            self.dbTable_tableView.setItemDelegate(QtS.QSqlRelationalDelegate(self.dbTable_tableView))
            self.dbTable_tableView.hideColumn(0)  # don't show ID column
            self.dbTable_tableView.resizeColumnsToContents()
        else:
            self.model.setTable(table)
            self.model.select()
            self.dbTable_tableView.setModel(self.model)
            self.dbTable_tableView.setItemDelegate(QtS.QSqlRelationalDelegate(self.dbTable_tableView))
            self.dbTable_tableView.hideColumn(0)  # don't show ID column
            self.dbTable_tableView.resizeColumnsToContents()

    def save_popup(self):
        print('save clicked')
        msg = QtW.QMessageBox()
        msg.setIcon(QtW.QMessageBox.Icon.Information)
        msg.setWindowTitle('Commit changes')
        msg.setText('Save changes to the database? This cannot be undone.')
        msg.setStandardButtons(QtW.QMessageBox.StandardButton.Save
                               | QtW.QMessageBox.StandardButton.Discard
                               | QtW.QMessageBox.StandardButton.Cancel)
        msg.setText('Save changes to the database view? This does not commit changes to the database file.')
        msg.setStandardButtons(QtW.QMessageBox.Save | QtW.QMessageBox.Discard | QtW.QMessageBox.Cancel)
        msg.buttonClicked.connect(self.save_popup_clicked)
        msg.exec()

    def save_popup_clicked(self, i):
        if i.text() == 'Save':
            '''Find a way to save the display when switching tables but not commit to database'''
        if i.text() == 'Discard' or i.text() == 'Don\'t Save':
            self.model.revertAll()
            self.display_table()
            self.status_bar.showMessage('Changes discarded', 1000)

    def commit_popup(self):
        msg = QtW.QMessageBox()
        msg.setIcon(QtW.QMessageBox.Information)
        msg.setWindowTitle('Commit changes')
        msg.setText('Save all changes to the database? This cannot be undone.')
        msg.setStandardButtons(QtW.QMessageBox.SaveAll | QtW.QMessageBox.Discard | QtW.QMessageBox.Cancel)
        msg.buttonClicked.connect(self.commit_popup_clicked)
        msg.exec()

    def commit_popup_clicked(self, i):
        if i.text() == 'SaveAll':
            self.model.submitAll()
            self.display_table()
        if i.text() == 'Discard' or i.text() == 'Don\'t Commit':
            self.model.revertAll()
            self.display_table()

    def contextMenuEvent(self, event: QtG.QContextMenuEvent) -> None:
        table = self.dbTable_comboBox.currentText()
        menu = QtW.QMenu(self)
        add_act = menu.addAction('Add item')
        delete_act = menu.addAction('Remove selected')
        # bulkAct = menu.addAction('Bulk edit selected')
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == add_act:
            if table == 'Sources':
                self.create_source()
            if table == 'Regions':
                self.create_region()
            if table == 'Settings':
                self.create_setting()
            if table == 'Rock Types':
                self.create_rocktype()
            if table == 'Units':
                self.create_unit()
            if table == 'Age Signatures':
                self.create_agesignature()
        if action == delete_act:
            index_list = []
            for model_index in self.dbTable_tableView.selectionModel().selectedRows():
                index = QtC.QPersistentModelIndex(model_index)
                index_list.append(index)
            for index in index_list:
                self.model.removeRow(index.row())

    # End methods here


if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QApplication(sys.argv)  # pass command line arguments
    w = GeoChron()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

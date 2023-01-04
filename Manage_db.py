import sys
from pathlib import Path

import pandas as pd
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtWidgets import QFileDialog

from PyQt6.uic import loadUi
import database as db
import ui.import_wizard


# import Select_Database as sd  # Eventually get database file from initial dialog


class GeoChron(QtW.QMainWindow):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)

        # Define any widgets here

        sources_ui_file = "GeochronMain.ui"
        loadUi(sources_ui_file, self)
        self.db_file = 'geochron_samples.db'
        self.db = QtS.QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(self.db_file)

        self.model = QtS.QSqlRelationalTableModel()
        self.sample_model = QtS.QSqlRelationalTableModel()
        self.status_bar = QtW.QStatusBar()
        # self.status_bar.show()

        db.create_tables(self.db_file)
        self.display_table_list()

        # self.dbTable_comboBox.setPlaceholderText('Select table')  # Bug in Qt5.15, broke this in 5.15.2
        # self.dbTable_comboBox.setCurrentIndex(-1)

        # Display the selected table
        self.dbTable_comboBox.activated.connect(self.display_table)

        # Signal for saving before switching tables, only saves the model, doesn't update the db file
        self.save_pushButton.clicked.connect(self.save_popup)

        # Signal for committing changes to the database file
        self.commit_pushButton.clicked.connect(self.commit_popup)

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
        self.model.setEditStrategy(QtS.QSqlTableModel.OnManualSubmit)
        if table == 'Samples':
            self.model.setTable(table)
            # self.model.setRelation(3, QtS.QSqlRelation('Age signature ID', 'Age signature ID', 'Age signature name'))
            self.model.setRelation(2, QtS.QSqlRelation("Sources", "Source ID", "Short Citation"))  # Currently breaking the table display
            self.model.select()
            self.dbTable_tableView.setModel(self.model)
            self.dbTable_tableView.hideColumn(0)  # don't show ID column
            self.dbTable_tableView.resizeColumnsToContents()
        else:
            self.model.setTable(table)
            self.model.select()
            self.dbTable_tableView.setModel(self.model)
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
        msg.setText('Commit changes to the database? This cannot be undone.')
        msg.setStandardButtons(QtW.QMessageBox.Commit | QtW.QMessageBox.Discard | QtW.QMessageBox.Cancel)
        msg.buttonClicked.connect(self.commit_popup_clicked)
        msg.exec()

    def commit_popup_clicked(self, i):
        if i.text() == 'Commit':
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
            '''This will commit all previous changes too, 
            but we only want to change the model before committing to the database'''

    def create_region(self):
        self.model.setTable('Regions')
        newRegion = self.model.record()
        source = ('', '')
        newRegion.setValue('Name', source[0])
        newRegion.setValue('Description', source[1])
        if self.model.insertRecord(-1, newRegion) is True:
            self.model.submitAll()
            self.display_table()

    def create_setting(self):
        self.model.setTable('Settings')
        newSetting = self.model.record()
        source = ('', '')
        newSetting.setValue('Name', source[0])
        newSetting.setValue('Description', source[1])
        if self.model.insertRecord(-1, newSetting) is True:
            self.model.submitAll()
            self.display_table()

    def create_rocktype(self):
        self.model.setTable('Rock Types')
        newRockType = self.model.record()
        source = ('', '')
        newRockType.setValue('Name', source[0])
        newRockType.setValue('Description', source[1])
        if self.model.insertRecord(-1, newRockType) is True:
            self.model.submitAll()
            self.display_table()

    def create_unit(self):
        self.model.setTable('Units')
        newUnit = self.model.record()
        source = ('', '')
        newUnit.setValue('Name', source[0])
        newUnit.setValue('Description', source[1])
        if self.model.insertRecord(-1, newUnit) is True:
            self.model.submitAll()
            self.display_table()

    def create_agesignature(self):
        self.model.setTable('Age Signatures')
        newAgeSignature = self.model.record()
        source = ('', '')
        newAgeSignature.setValue('Name', source[0])
        newAgeSignature.setValue('Description', source[1])
        if self.model.insertRecord(-1, newAgeSignature) is True:
            self.model.submitAll()
            self.display_table()

    # def create_sample(self):
    #     self.model.setTable('Samples')
    #     newSample = self.model.record()
    #     source = ('', '', '', '', '', '')
    #     newSample.setValue('Authors', source[0])
    #     newSample.setValue('Year', source[1])
    #     newSample.setValue('Title', source[2])
    #     newSample.setValue('Source', source[3])
    #     newSample.setValue('doi', source[4])
    #     newSample.setValue('Short Citation', source[5])
    #     if self.model.insertRecord(-1, newSample) is True:
    #         self.model.submitAll()
    #         self.display_table()

    # End methods here


if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QApplication(sys.argv)  # pass command line arguments
    w = GeoChron()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

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
        sources_ui_file = "GeochronMain.ui"
        loadUi(sources_ui_file, self)

        self.setWindowTitle("GeoChron")
        self.db_file = 'geochron_samples.db'
        self.db = QtS.QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(self.db_file)

        db.create_tables(self.db_file)

        self.model = QtS.QSqlRelationalTableModel(self)
        self.display_table_list()

        # self.dbTable_comboBox.setPlaceholderText('Select table')  # Bug in Qt5.15, broke this in 5.15.2
        # self.dbTable_comboBox.setCurrentIndex(-1)

        # Display the selected table
        self.dbTable_comboBox.activated.connect(self.display_table)

        # Signal for saving
        self.save_pushButton.clicked.connect(self.commit_popup)
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
        table = self.dbTable_comboBox.currentText()
        # if self.model.isDirty() is True:
        #     self.commit_popup

        self.model.setTable(table)
        self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnManualSubmit)

        if table == 'Samples':
            self.model.setRelation(2, QtS.QSqlRelation('Sources', '"Source ID"', '"Short Citation"'))

        self.model.select()
        self.dbTable_tableView.setModel(self.model)
        self.dbTable_tableView.hideColumn(0)  # don't show ID column
        self.dbTable_tableView.resizeColumnsToContents()

    def commit_popup(self):
        print('save clicked')
        msg = QtW.QMessageBox()
        msg.setIcon(QtW.QMessageBox.Icon.Information)
        msg.setWindowTitle('Commit changes')
        msg.setText('Save changes to the database? This cannot be undone.')
        msg.setStandardButtons(QtW.QMessageBox.StandardButton.Save
                               | QtW.QMessageBox.StandardButton.Discard
                               | QtW.QMessageBox.StandardButton.Cancel)
        msg.buttonClicked.connect(self.commit_popup_clicked)
        msg.exec()

    def commit_popup_clicked(self, i):
        print(f'user clicked {i.text()}')
        if i.text() == 'Save':
            self.model.submitAll()
            self.display_table()
        if i.text() == 'Discard' or i.text() == 'Don\'t Save':
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

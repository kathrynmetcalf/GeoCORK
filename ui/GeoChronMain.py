import sys
from pathlib import Path
import sqlite3
# import pandas as pd
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtWidgets import QFileDialog

from PyQt6.uic import loadUi
import Functions.Create_database as Create_db
import Functions.Table_classes as TC
import ui.import_wizard
import ui.New_source
from ui.EditTags import EditTags
from ui.AddTags import AddTags


# import Select_Database as sd  # Eventually get database file from initial dialog


class GeoChron(QtW.QMainWindow):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)

        # Define any widgets here

        sources_ui_file = "GeochronMain.ui"
        loadUi(sources_ui_file, self)
        self.db_file = '../TestSchema.db'
        # self.db_file = self.open_db()
        self.db = QtS.QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(self.db_file)

        self.sample_model = QtS.QSqlQueryModel()
        self.aliquot_model = QtS.QSqlQueryModel()
        self.spot_model = QtS.QSqlQueryModel()
        self.model = QtS.QSqlTableModel()
        self.filter_proxy_model = QtC.QSortFilterProxyModel()
        self.delegate = QtS.QSqlRelationalDelegate()
        self.status_bar = QtW.QStatusBar()
        # self.status_bar.show()

        Create_db.create_tables(self.db_file)
        self.display_table_list()

        # self.dbTable_comboBox.setPlaceholderText('Select table')  # Bug in Qt5.15, broke this in 5.15.2
        # self.dbTable_comboBox.setCurrentIndex(-1)

        # Display the selected table
        self.dbTable_comboBox.activated.connect(self.display_table)

        # Signal for search bar
        self.search_lineEdit.textChanged.connect(self.filter_proxy_model.setFilterRegularExpression)
        # Signal for double-clicked cell in dbTable_TableView
        self.dbTable_tableView.doubleClicked.connect(self.edit_popup)
        # Signal for clicked add button in main window
        self.add_pushButton.clicked.connect(self.add_popup)

        # End widgets here
        self.show()  # show the window when done, used for making a top-level window

    # Define any methods here

    def open_db(self):
        """
        Opens a file dialog to select an existing database file, must be in the format .db
        :return: database file name with path
        """
        home_dir = str(Path.home())
        db_file = QFileDialog.getOpenFileName(self, 'Open file', home_dir, 'db(*.db)')
        return db_file[0]

    def show_import_wizard_dialog(self):
        home_dir = str(Path.home()) + '\Downloads'
        fname = QFileDialog.getOpenFileName(self, 'Open file', home_dir)
        print(fname[0])
        import_wizard = ui.import_wizard.ImportWizardDialog(fname[0])
        import_wizard.exec()

    def display_table_list(self):
        dbtable_list = ['Age Signatures', 'Aliquots', 'Aliquot Context', 'Columns', 'Lab Facilities', 'Regions',
                        'Rock Types', 'Sample Context', 'Samples', 'Sampling Methods', 'Settings', 'Sources',
                        'Spot Compositions', 'Spot Context', 'UPb Data', 'UPb Analysis Methods', 'Units']
        self.dbTable_comboBox.addItems(dbtable_list)
        self.dbTable_comboBox.setCurrentText('Samples')
        self.display_table()

    def display_table(self):
        # if self.model.isDirty() is True:
        #     self.save_popup()
        #     '''Click cancel should stop this method'''
        table_name = self.dbTable_comboBox.currentText()
        # Remove spaces from display names
        table = table_name.replace(" ", "")
        if table == 'Samples':
            query = TC.SampleTableModel.setupQuery(self)
            self.sample_model.setQuery(QtS.QSqlQuery(query))
            self.dbTable_tableView.setModel(self.sample_model)
            self.dbTable_tableView.hideColumn(0)  # don't show ID column
            self.dbTable_tableView.resizeColumnsToContents()
        else:
            self.model.setTable(table)
            self.model.select()
            self.filter_proxy_model.setSourceModel(self.model)
            self.filter_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
            self.filter_proxy_model.setFilterKeyColumn(-1)  # search all columns
            self.dbTable_tableView.setModel(self.filter_proxy_model)
            self.dbTable_tableView.hideColumn(0)  # don't show ID column
            self.dbTable_tableView.resizeColumnsToContents()
            self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.add_pushButton.setText(f"Add {table_name}")

    def get_existing(self, field, table):
        conn = sqlite3.connect(self.db_file)
        with conn:
            c = conn.cursor()
            sql = f'''SELECT {field} FROM {table}'''
            if c.execute(sql):
                existing = c.fetchall()
                print(existing)
                return existing

    def open_new_source(self):
        source_list = self.get_existing('"Short Citation"', '"Sources"')
        new_source = ui.New_source.NewSource(source_list[0])
        new_source.exec()

    def edit_popup(self):
        index = self.dbTable_tableView.indexAt(QtC.QPoint())
        table_name = self.dbTable_comboBox.currentText()
        col = index.column()
        id_index = index.siblingAtColumn(0)
        if table_name == 'Samples':
            sample_id = self.sample_model.data(id_index)
            column_name = self.sample_model.record(index.row()).fieldName(col)
        elif table_name == 'Sources' or table_name == 'Aliquots' or table_name == 'UPb Data':
            pass
        else:
            tag_id = self.model.data(id_index)
            dlg = EditTags(self.db, self.model, table_name, tag_id)
            dlg.exec()
            self.display_table()

    def add_popup(self):
        table_name = self.dbTable_comboBox.currentText()
        if table_name == 'Samples' or table_name == 'Sources' or table_name == 'Aliquots' or table_name == 'UPb Data':
            pass
        else:
            dlg = AddTags(self.db, self.model, table_name)
            dlg.exec()
            self.display_table()

    # End methods here


if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QApplication(sys.argv)  # pass command line arguments
    w = GeoChron()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

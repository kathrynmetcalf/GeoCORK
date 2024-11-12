from PyQt6 import uic
from PyQt6.QtCore import QSettings
from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtWidgets import QWidget, QApplication


class ExportWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        for widget in QApplication.topLevelWidgets():
            if widget.inherits("QMainWindow"):
                self.db_file = widget.db_file

        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(self.db_file)
        self.settings = QSettings("CSUF", "GeoChron")

        self.db.open()

        # self.loadWindowState()

        uic.loadUi('ui/ExporterUI.ui', self)

        # list of all user-viewable tables in the database
        self.user_view_tables = ['Ages',
                                 'Age Signatures', 'Aliquots', 'Aliquot Contexts', 'Columns', 'Lab Facilities',
                                 'Instruments',
                                 'Regions', 'Rock Types', 'Sample Contexts', 'Samples', 'Sampling Methods', 'Settings',
                                 'Sources', 'Spots',
                                 'Spot Compositions', 'Spot Contexts', 'UPb Data', 'Analysis Methods', 'Units',
                                 'UPb Analysis Methods']

        # list of tables to display as a tree structure
        self.dbtree_list = ['Ages', 'AgeSignatures', 'AliquotContexts', 'Regions', 'RockTypes', 'SampleContexts',
                            'SamplingMethods', 'Settings', 'SpotCompositions', 'SpotContexts', 'Units']
       # list of tables to display as a table structure
        self.dbtable_list = ['Aliquots', 'Columns', 'LabFacilities', 'Instruments', 'Sources', 'UPbData', 'Spots',
                             'UPbAnalysisMethods']

        self.show()

    def closeEvent(self, a0):
        self.saveWindowState()
        super().closeEvent(a0)

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from Functions.Settings_manager import settings
from Functions.Database_views import AliquotViewQuery, SpotViewQuery, UPbViewQuery
import Functions.Table_classes as TbC
from ui.EditTable import EditTable
from ui.EditTree import EditTree


class ViewDataTab(QtW.QWidget):
    def __init__(self, parent_id: int, parent_type: str, child_type: str):
        super().__init__()
        self.parent_id = parent_id
        self.parent_type = parent_type
        self.child_type = child_type

        self.v_layout = QtW.QVBoxLayout()
        self.setLayout(self.v_layout)
        self.edit_pushButton = QtW.QPushButton('Edit')
        self.edit_pushButton.clicked.connect(self.edit_popup)
        self.h_layout = QtW.QHBoxLayout()
        self.h_layout.addWidget(self.edit_pushButton)
        self.h_layout.addStretch(6)
        self.v_layout.addLayout(self.h_layout)
        self.show_cols = []
        self.display_table()

    def display_table(self):
        if self.child_type == 'Aliquot':
            self.view = QtW.QTreeView()
        else:
            self.view = QtW.QTableView()
        self.v_layout.addWidget(self.view)
        if self.child_type == 'Aliquot' and self.parent_type == 'Sample':
            # Columns to select from the view
            self.show_cols = settings.value('aliquot_columns')
            table_query = f'SELECT {", ".join(self.show_cols)} FROM AliquotView WHERE SampleID = {self.parent_id}'
        elif self.child_type == 'Spot':
            self.show_cols = settings.value('spot_columns')
            if self.parent_type == 'Aliquot':
                table_query = f'SELECT {", ".join(self.show_cols)} FROM SpotView WHERE AliquotID = {self.parent_id}'
            elif self.parent_type == 'Sample':
                table_query = f'SELECT {", ".join(self.show_cols)} FROM SpotView WHERE SampleID = {self.parent_id}'
            else:
                print(f'Error: Invalid parent type {self.parent_type} for Spot table')
                table_query = None
        elif self.child_type == 'UPbAnalysis':
            self.show_cols = settings.value('upb_analysis_columns')
            if self.parent_type == 'Sample':
                table_query = f'SELECT {", ".join(self.show_cols)} FROM UPbView WHERE SampleID = {self.parent_id}'
            elif self.parent_type == 'Aliquot':
                table_query = f'SELECT {", ".join(self.show_cols)} FROM UPbView WHERE AliquotID = {self.parent_id}'
            elif self.parent_type == 'Spot':
                table_query = f'SELECT {", ".join(self.show_cols)} FROM UPbView WHERE SpotID = {self.parent_id}'
            else:
                print(f'Error: Invalid parent type {self.parent_type} for UPbAnalysis table')
                table_query = None
        else:
            print(f'Error: Invalid child type {self.child_type}')
            table_query = None
        self.model = QtS.QSqlQueryModel()
        if table_query is not None:
            # print(table_query)
            self.model.setQuery(table_query)
            self.proxy_model = TbC.ReadableProxyModel()
            self.proxy_model.setSourceModel(self.model)
            self.view.setModel(self.proxy_model)

    def edit_popup(self):
        if self.child_type == 'Aliquot':
            table = 'Aliquots'
            dlg = EditTree(table, self.parent_id, self.parent_type)
        elif self.child_type == 'Spot':
            table = 'Spots'
            dlg = EditTable(table, self.parent_id, self.parent_type)
        elif self.child_type == 'UPbAnalysis':
            table = 'UPbAnalysis'
            dlg = EditTable(table, self.parent_id, self.parent_type)
        else:
            return
        dlg.exec()
        self.display_table()
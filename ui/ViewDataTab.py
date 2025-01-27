from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from Functions.Settings_manager import settings
from Functions.Database_views import AliquotViewQuery, SpotViewQuery, UPbViewQuery
import Functions.Table_classes as TbC


class ViewDataTab(QtW.QWidget):
    def __init__(self, parent_id: int, parent_type: str, child_type: str):
        super().__init__()
        self.parent_id = parent_id
        self.parent_type = parent_type
        self.child_type = child_type

        self.v_layout = QtW.QVBoxLayout()
        self.setLayout(self.v_layout)
        self.edit_pushButton = QtW.QPushButton('Edit')
        self.edit_pushButton.clicked
        self.h_layout = QtW.QHBoxLayout()
        self.h_layout.addWidget(self.edit_pushButton)
        self.h_layout.addStretch(6)
        self.v_layout.addLayout(self.h_layout)
        if child_type == 'Aliquot':
            self.view = QtW.QTreeView()
        else:
            self.view = QtW.QTableView()
        self.v_layout.addWidget(self.view)
        if child_type == 'Aliquot' and parent_type == 'Sample':
            self.show_cols = settings.value('aliquot_columns')
            table_query = AliquotViewQuery([parent_id])
        elif child_type == 'Spot':
            self.show_cols = settings.value('spot_columns')
            if parent_type == 'Aliquot':
                table_query = SpotViewQuery(parent_id, 'Aliquot')
            elif parent_type == 'Sample':
                table_query = SpotViewQuery(parent_id, 'Sample')
            else:
                print(f'Error: Invalid parent type {parent_type} for Spot table')
                table_query = None
        elif child_type == 'UPbAnalysis':
            self.show_cols = settings.value('upb_analysis_columns')
            if parent_type == 'Sample':
                table_query = UPbViewQuery(parent_id, 'Sample')
            elif parent_type == 'Aliquot':
                table_query = UPbViewQuery(parent_id, 'Aliquot')
            elif parent_type == 'Spot':
                table_query = UPbViewQuery(parent_id, 'Spot')
            else:
                print(f'Error: Invalid parent type {parent_type} for UPbAnalysis table')
                table_query = None
        else:
            print(f'Error: Invalid child type {child_type}')
            table_query = None
        self.model = QtS.QSqlQueryModel()
        if table_query is not None:
            # print(table_query)
            self.model.setQuery(table_query)
            self.proxy_model = TbC.ReadableProxyModel()
            self.proxy_model.setSourceModel(self.model)
            self.view.setModel(self.proxy_model)
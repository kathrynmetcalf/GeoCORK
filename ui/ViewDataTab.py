import time

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QAbstractItemView, QHeaderView

import logger_setup
import time
from Functions.Settings_manager import settings
from Functions.Database_manager import update_database
from Functions.Widget_classes import SQLiteTableModel, WordWrapDelegate, ReadableProxyModel
from ui.EditTable import EditTable
from ui.EditTree import EditTree


class ViewDataTab(QtW.QWidget):
    def __init__(self, parent_id: int, parent_type: str, child_type: str):
        super().__init__()
        logger_setup.get_logger().info(f'Creating a new ViewDataTab for {child_type} with parent {parent_type} ID {parent_id}')
        start_view_data_tab_time = time.time()
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
        end_view_data_tab_time = time.time()
        logger_setup.get_logger().info(f'Time to create ViewDataTab: {end_view_data_tab_time - start_view_data_tab_time}')

    def optimizeVerticalResize(self, logical_index, old_size, new_size):
        """Trigger a delayed row height update when the user resizes the window vertically."""
        self.resize_timer.start(250)  # Add a slight delay to avoid excessive updates

    def resizeRowsOptimized(self):
        """Resize rows only when resizing stops."""
        self.view.resizeRowsToContents()


    def display_table(self):
        logger_setup.get_logger().info(f'Displaying table for {self.child_type} with parent {self.parent_type} ID {self.parent_id}')
        start_display_table_time = time.time()
        if self.child_type == 'Aliquot':
            self.view = QtW.QTreeView()
        else:
            self.view = QtW.QTableView()

            self.view.setWordWrap(True)
            self.view.setTextElideMode(Qt.TextElideMode.ElideNone)  # Prevent text truncation
            self.view.setItemDelegate(WordWrapDelegate(self.view))

            self.view.resizeRowsToContents()
            self.view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

            # Optimize window resizing
            self.resize_timer = QTimer()
            self.resize_timer.setSingleShot(True)
            self.resize_timer.timeout.connect(self.resizeRowsOptimized)

            # Connect resizing events
            self.view.horizontalHeader().sectionResized.connect(self.optimizeVerticalResize)
            self.view.verticalHeader().sectionResized.connect(self.optimizeVerticalResize)

        self.v_layout.addWidget(self.view)
        if self.child_type == 'Aliquot' and self.parent_type == 'Sample':
            # Columns to select from the view
            self.show_cols = settings.value('aliquot_columns')
            self.show_cols = ', '.join(self.show_cols)
            table_query = f'SELECT {self.show_cols} FROM AliquotView WHERE SampleID = {self.parent_id}'
        elif self.child_type == 'Spot':
            self.show_cols = settings.value('spot_columns')
            self.show_cols = ', '.join(self.show_cols)
            if self.parent_type == 'Aliquot':
                table_query = f'SELECT {self.show_cols} FROM SpotView WHERE AliquotID = {self.parent_id}'
            elif self.parent_type == 'Sample':
                table_query = f'SELECT {self.show_cols} FROM SpotView WHERE SampleID = {self.parent_id}'
            else:
                logger_setup.get_logger().critical(f'Error: Invalid parent type {self.parent_type} for Spot table')
                table_query = None
        elif self.child_type == 'UPbAnalysis':
            self.show_cols = settings.value('upb_analysis_view_columns')
            self.show_cols = ', '.join(self.show_cols)
            if self.parent_type == 'Sample':
                table_query = f'SELECT {self.show_cols} FROM UPbView WHERE SampleID = {self.parent_id}'
            elif self.parent_type == 'Aliquot':
                table_query = f'SELECT {self.show_cols} FROM UPbView WHERE AliquotID = {self.parent_id}'
            elif self.parent_type == 'Spot':
                table_query = f'SELECT {self.show_cols} FROM UPbView WHERE SpotID = {self.parent_id}'
            else:
                logger_setup.get_logger().critical(f'Error: Invalid parent type {self.parent_type} for UPbAnalysis table')
                table_query = None
        else:
            logger_setup.get_logger().critical(f'Error: Invalid child type {self.child_type}')
            table_query = None
        if table_query is not None:
            self.model = SQLiteTableModel(table_query)
            self.proxy_model = ReadableProxyModel()
            self.proxy_model.setSourceModel(self.model)
            self.view.setModel(self.proxy_model)
            self.view.setSortingEnabled(True)
            # Hide the ID columns
            self.view.hideColumn(0)
            self.view.hideColumn(1)
            if self.child_type == 'Spot':
                self.view.hideColumn(2)
            if self.child_type == 'UPbAnalysis':
                self.view.hideColumn(2)
                self.view.hideColumn(3)
        end_display_table_time = time.time()
        logger_setup.get_logger().info(f'Time to display table: {end_display_table_time - start_display_table_time}')

    def edit_popup(self):
        logger_setup.get_logger().info(f'Opening edit dialog for {self.child_type} with parent {self.parent_type} ID {self.parent_id}')
        if self.child_type == 'Aliquot':
            table = 'Aliquots'
            dlg = EditTree(table, self.parent_id, self.parent_type)
        elif self.child_type == 'Spot':
            table = 'Spots'
            dlg = EditTable(table, self.parent_id, self.parent_type)
        elif self.child_type == 'UPbAnalysis':
            table = 'UPbAnalyses'
            dlg = EditTable(table, self.parent_id, self.parent_type)
        else:
            return
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            update_database()
            self.display_table()
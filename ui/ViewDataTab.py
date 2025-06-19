import time

import qtawesome
from PyQt6 import QtCore as QtC
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtGui as QtG
from PyQt6.QtCore import Qt, QTimer, QRegularExpression
from PyQt6.QtWidgets import QHeaderView, QLabel, QPushButton

import logger_setup
from Functions.Database_manager import update_database
from Functions.Database_views import ViewQuery
from Functions.LoadingDialog_manager import LoadingDialogManager
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.Widget_classes import (SQLiteTableModel, WordWrapDelegate, ReadableProxyModel, TreeModel,
                                      TreeContextMenu, expand_collapse, get_name_column, get_headers,
                                      get_view_from_table, TreeSortFilterProxyModel, get_readable_header)
from ui.EditTreeView import EditTreeView
from ui.EditView import EditView


class ViewDataTab(QtW.QWidget):
    def __init__(self, parent_id: int, parent_type: str, child_type: str, label: str):
        super().__init__()
        logger_setup.get_logger().info(
            f'Creating a new ViewDataTab for {child_type} with parent {parent_type} ID {parent_id}')
        start_view_data_tab_time = time.time()

        self.loading_manager = LoadingDialogManager.get_instance()

        self.parent_id = parent_id
        self.parent_type = parent_type
        self.child_type = child_type
        self.view = None
        self.model = None
        self.tree_model = None
        self.proxy_model = None
        self.show_cols = []

        # Retrieve the main window
        for widget in QtW.QApplication.topLevelWidgets():
            if widget.inherits("QMainWindow"):
                self.main_window = widget
                break

        self.v_layout = QtW.QVBoxLayout()
        self.setLayout(self.v_layout)
        self.h_layout = QtW.QHBoxLayout()
        self.edit_pushButton = QtW.QPushButton(f'Edit {label}')
        self.edit_pushButton.clicked.connect(self.edit_popup)
        self.top_spacer = QtW.QSpacerItem(20, 20, QtW.QSizePolicy.Policy.Expanding, QtW.QSizePolicy.Policy.Minimum)
        self.refresh_button = QPushButton()
        self.refresh_button.setFixedSize(QtC.QSize(25, 25))
        self.refresh_button.setIcon(qtawesome.icon('fa6s.rotate-right', color='green', scale_factor=1.0))
        self.refresh_button.clicked.connect(self.display_table)
        self.h_layout.addWidget(self.edit_pushButton)
        self.h_layout.addWidget(self.refresh_button)
        self.h_layout.addItem(self.top_spacer)
        self.search_label = QLabel('Search: ')
        self.search_lineEdit = QtW.QLineEdit()
        self.search_lineEdit.setPlaceholderText('search this page')
        self.search_lineEdit.setMinimumWidth(100)
        self.search_lineEdit.returnPressed.connect(self.search)
        self.h_layout.addWidget(self.search_label)
        self.h_layout.addWidget(self.search_lineEdit)
        self.v_layout.addLayout(self.h_layout)
        self.resize_timer = QTimer()
        self.display_table()

        self.loading_manager.close_loading_dialog('Loading', f'Loading {label}...')
        end_view_data_tab_time = time.time()
        logger_setup.get_logger().info(
            f'Time to create ViewDataTab: {end_view_data_tab_time - start_view_data_tab_time}')

    def optimizeVerticalResize(self, logical_index, old_size, new_size):
        """Trigger a delayed row height update when the user resizes the window vertically."""
        self.resize_timer.start(250)  # Add a slight delay to avoid excessive updates

    def resizeRowsOptimized(self):
        """Resize rows only when resizing stops."""
        self.view.resizeRowsToContents()

    def display_table(self):
        logger_setup.get_logger().info(
            f'Displaying table for {self.child_type} with parent {self.parent_type} ID {self.parent_id}')
        loading_manager = LoadingDialogManager.get_instance()
        loading_manager.show_loading_dialog('Loading', 'Displaying table...')
        start_display_table_time = time.time()
        if not self.view:
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
                self.resize_timer.setSingleShot(True)
                self.resize_timer.timeout.connect(self.resizeRowsOptimized)

                # Connect resizing events
                self.view.horizontalHeader().sectionResized.connect(self.optimizeVerticalResize)
                self.view.verticalHeader().sectionResized.connect(self.optimizeVerticalResize)

            self.view.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
            self.view.customContextMenuRequested.connect(self.show_context_menu)
            self.v_layout.addWidget(self.view)
        if self.child_type == 'Aliquot' and self.parent_type == 'Sample':
            table = 'Aliquots'
            self.show_cols = settings.value('aliquot_view_columns')
            query_args = {'show_columns': self.show_cols, 'where': f'WHERE SampleID = {self.parent_id}'}
        elif self.child_type == 'Spot':
            table = 'Spots'
            self.show_cols = settings.value('spot_view_columns')
            if self.parent_type == 'Aliquot':
                query_args = {'show_columns': self.show_cols, 'where': f'WHERE AliquotID = {self.parent_id}'}
            elif self.parent_type == 'Sample':
                query_args = {'show_columns': self.show_cols, 'where': f'WHERE SampleID = {self.parent_id}'}
            else:
                logger_setup.get_logger().critical(f'Error: Invalid parent type {self.parent_type} for Spot table')
                table = None
        elif self.child_type == 'UPbAnalysis':
            table = 'UPbAnalyses'
            self.show_cols = settings.value('upb_analysis_view_columns')
            if self.parent_type == 'Sample':
                query_args = {'show_columns': self.show_cols, 'where': f'WHERE SampleID = {self.parent_id}'}
            elif self.parent_type == 'Aliquot':
                query_args = {'show_columns': self.show_cols, 'where': f'WHERE AliquotID = {self.parent_id}'}
            elif self.parent_type == 'Spot':
                query_args = {'show_columns': self.show_cols, 'where': f'WHERE SpotID = {self.parent_id}'}
            else:
                logger_setup.get_logger().critical(
                    f'Error: Invalid parent type {self.parent_type} for UPbAnalysis table')
                table = None
        else:
            logger_setup.get_logger().critical(f'Error: Invalid child type {self.child_type}')
            table = None
        if table is not None:
            view_query = ViewQuery(table, False, **query_args)
            table_query = view_query.table_query
            self.model = SQLiteTableModel(table_query)
            if self.model.last_error:
                logger_setup.get_logger().critical(f'Error displaying table')
                return
            self.model.set_table(table)
            if isinstance(self.view, QtW.QTreeView):
                self.proxy_model = TreeSortFilterProxyModel()
                self.tree_model = TreeModel(self.model)
                self.proxy_model.setSourceModel(self.tree_model)
            else:
                self.proxy_model = ReadableProxyModel()
                self.proxy_model.setSourceModel(self.model)
            self.proxy_model.setFilterKeyColumn(-1) # search all columns
            self.view.setModel(self.proxy_model)
            if isinstance(self.view, QtW.QTreeView):
                self.view.setSortingEnabled(False)
                self.view.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
                for column in range(self.model.columnCount()):
                    self.view.resizeColumnToContents(column)
            else:
                self.view.resizeColumnsToContents()
                self.view.setSortingEnabled(True)
                proxy_name_column = None
                name_column = self.model.table_name_col
                if name_column is not None:
                    name_header = get_readable_header(get_headers(get_view_from_table(self.model.table))[name_column])
                    for column in range(self.proxy_model.columnCount()):
                        header = self.proxy_model.headerData(column, QtC.Qt.Orientation.Horizontal,
                                                             QtC.Qt.ItemDataRole.DisplayRole)
                        if header == name_header:
                            proxy_name_column = column
                            break
                if proxy_name_column:
                    self.proxy_model.sort(proxy_name_column, QtC.Qt.SortOrder.AscendingOrder)
                for column in range(self.proxy_model.columnCount()):
                    if self.view.columnWidth(column) > 400:
                        self.view.setColumnWidth(column, 400)

            match self.child_type:
                case 'Sample':
                    self.view.hideColumn(0)  # don't show SampleID column
                case 'Aliquot':
                    self.view.hideColumn(1)  # don't show AliquotID
                    self.view.hideColumn(2)  # don't show ParentAliquotID
                    self.view.hideColumn(3)  # don't show AliquotParentRow
                    self.view.hideColumn(4)  # don't show SampleID
                case 'Spot':
                    self.view.hideColumn(0)  # don't show SpotID
                    self.view.hideColumn(1)  # don't show SampleID
                    self.view.hideColumn(2)  # don't show AliquotID
                case 'UPbAnalysis':
                    self.view.hideColumn(0)  # don't show UPbAnalysisID
                    self.view.hideColumn(1)  # don't show SampleID
                    self.view.hideColumn(2)  # don't show AliquotID
                    self.view.hideColumn(3)  # don't show SpotID
        end_display_table_time = time.time()
        loading_manager.close_loading_dialog('Loading', 'Displaying table...')
        logger_setup.get_logger().info(f'Time to display table: {end_display_table_time - start_display_table_time}')

    def show_context_menu(self, pos):
        tree_menu = TreeContextMenu()
        table_menu = QtW.QMenu()
        if isinstance(self.view, QtW.QTreeView):
            tree_menu.set_view(self.view, False, False)
            action = tree_menu.exec(self.view.viewport().mapToGlobal(pos))
            if action:
                if action.text() == 'Edit':
                    self.edit_popup()
                elif 'Expand' in action.text() or 'Collapse' in action.text():
                    expand_collapse(self.view, action)
                elif 'View' in action.text():
                    self.display_data(action)
        else:
            edit_action = table_menu.addAction('Edit')
            if self.model.table == 'Spots':
                view_upb_analyses_action = table_menu.addAction('View U-Pb Analyses')
            else:
                view_upb_analyses_action = None
            action = table_menu.exec(self.view.viewport().mapToGlobal(pos))
            if action:
                if action == edit_action:
                    self.edit_popup()
                elif action == view_upb_analyses_action:
                    self.display_data(action)

    def display_data(self, action):
        # get the row that was right-clicked
        logger_setup.get_logger().info(f'Displaying data for {action.text()}')
        parent_ids = []
        if self.view.selectedIndexes():
            selected_indexes = self.view.selectedIndexes()
        else:
            logger_setup.get_logger().error("Select cell or row")
            return
        for index in selected_indexes:
            if self.tree_model:
                parent_id = self.proxy_model.index(index.row(), 1, index.parent()).data(QtC.Qt.ItemDataRole.DisplayRole)
            else:
                parent_id = self.proxy_model.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole)
            if parent_id not in parent_ids:
                parent_ids.append(parent_id)
        if 'Spot' in action.text():
            self.main_window.open_tab(parent_ids, 'Aliquot', 'Spot')
        elif 'U-Pb' in action.text():
            if isinstance(self.view, QtW.QTreeView):
                self.main_window.open_tab(parent_ids, 'Aliquot', 'UPbAnalysis')
            else:
                self.main_window.open_tab(parent_ids, 'Spot', 'UPbAnalysis')

    def edit_popup(self):
        logger_setup.get_logger().info(
            f'Opening edit dialog for {self.child_type} with parent {self.parent_type} ID {self.parent_id}')
        if self.child_type == 'Aliquot':
            table = 'Aliquots'
            dlg_args = {'parent_id': self.parent_id, 'parent_type': self.parent_type}
            dlg = EditTreeView(self, table, **dlg_args)
        elif self.child_type == 'Spot':
            table = 'Spots'
            dlg_args = {'parent_id': self.parent_id, 'parent_type': self.parent_type}
            dlg = EditView(self, table, **dlg_args)
        elif self.child_type == 'UPbAnalysis':
            table = 'UPbAnalyses'
            dlg_args = {'parent_id': self.parent_id, 'parent_type': self.parent_type}
            dlg = EditView(self, table, **dlg_args)
        else:
            return
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            if not update_database():
                logger_setup.get_logger().error('Error updating and displaying database')
                self.parent().close()
            self.display_table()

    def search(self):
        """
        Search the current table for the text in the search box
        Check if the case-sensitive box is checked or not
        :return:
        """
        self.search_lineEdit: QtW.QLineEdit

        search_expression = QtC.QRegularExpression(self.search_lineEdit.text(),
                                                   options=QRegularExpression.PatternOption.CaseInsensitiveOption)
        if self.child_type == 'Aliquot':
            self.proxy_model.setRecursiveFilteringEnabled(True)
            self.proxy_model.setFilterRegularExpression(search_expression)
            if search_expression != "":
                self.view.expandAll()
        else:
            self.proxy_model.setFilterRegularExpression(search_expression)

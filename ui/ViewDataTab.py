import time

import qtawesome
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import Qt, QTimer, QRegularExpression
from PyQt6.QtWidgets import QAbstractItemView, QHeaderView, QLabel, QPushButton

import logger_setup
import time
from Functions.Settings_manager import settings
from Functions.Database_manager import update_database
from Functions.LoadingDialog_manager import LoadingDialogManager
from Functions.Widget_classes import (SQLiteTableModel, WordWrapDelegate, ReadableProxyModel, TreeModel,
                                      restore_expanded_state, TreeContextMenu, expand_collapse, find_tree_model)
from ui.EditTreeView import EditTreeView
from ui.EditView import EditView


class ViewDataTab(QtW.QWidget):
    def __init__(self, parent_id: int, parent_type: str, child_type: str, label: str):
        super().__init__()
        logger_setup.get_logger().info(f'Creating a new ViewDataTab for {child_type} with parent {parent_type} ID {parent_id}')
        start_view_data_tab_time = time.time()

        self.loading_manager = LoadingDialogManager.get_instance()

        self.parent_id = parent_id
        self.parent_type = parent_type
        self.child_type = child_type
        self.view = None
        self.model = None
        self.tree_model = None
        self.proxy_model = None

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
        self.h_layout.addWidget(self.edit_pushButton)
        self.refresh_button = QPushButton()
        self.refresh_button.setFixedSize(QtC.QSize(25, 25))
        self.refresh_button.setIcon(qtawesome.icon('fa6s.rotate-right', color='green', scale_factor=1.0))
        self.refresh_button.clicked.connect(self.display_table)
        self.h_layout.addWidget(self.refresh_button)
        self.h_layout.addStretch(2)
        self.search_label = QLabel('Search: ')
        self.search_lineEdit = QtW.QLineEdit()
        self.search_lineEdit.setPlaceholderText('search this page')
        self.search_lineEdit.setMinimumWidth(100)
        self.h_layout.addWidget(self.search_label)
        self.h_layout.addWidget(self.search_lineEdit)
        self.v_layout.addLayout(self.h_layout)
        self.show_cols = []
        self.view = None
        self.resize_timer = QTimer()

        self.search_lineEdit.textChanged.connect(self.search)
        self.loading_manager.close_loading_dialog('Loading', 'Loading tab window...')
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
            # Columns to select from the view
            self.show_cols = settings.value('aliquot_view_columns')
            self.show_cols = ', '.join(self.show_cols)
            table_query = f'SELECT {self.show_cols} FROM AliquotView WHERE SampleID = {self.parent_id}'
        elif self.child_type == 'Spot':
            self.show_cols = settings.value('spot_view_columns')
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
            """
            The commented out code searches for all children of each aliquot with the selected sample ID. Since all
            aliquots have SampleID and aliquots can only be viewed per sample, this is unnecessary. Just search for all
            with the sample ID.
            """
            # if self.child_type == 'Aliquot':
            #     query = (f'SELECT * FROM AliquotView WHERE AliquotID IN ( '
            #                     f'WITH RECURSIVE ParentTree AS '
            #                     f'(SELECT * FROM AliquotView '
            #                     f'WHERE SampleID = {self.parent_id} '
            #                     f'UNION ALL '
            #                     f'SELECT AliquotView.* FROM AliquotView '
            #                     f'INNER JOIN ParentTree ON AliquotView.AliquotID = ParentTree.ParentAliquotID) '
            #                     f'SELECT AliquotID FROM ParentTree) ')
            #     logger_setup.get_logger().debug(f'SQL command: {query}')
            #     self.model = SQLiteTableModel(query, None)
            #
            #     self.model = TreeModel(self.model, None)
            # else:
            #     self.model = SQLiteTableModel(table_query)
            self.model = SQLiteTableModel(table_query)
            self.proxy_model = ReadableProxyModel()
            if isinstance(self.view, QtW.QTreeView):
                # todo: Now that it is actually creating a tree, it is taking 7 seconds to add 2 aliquots
                self.tree_model = TreeModel(self.model)
                self.proxy_model.setSourceModel(self.tree_model)
            else:
                self.proxy_model.setSourceModel(self.model)
            self.view.setModel(self.proxy_model)
            self.view.setSortingEnabled(True)
            self.proxy_model.setFilterKeyColumn(-1)

            if self.child_type == 'Aliquot':
                self.view.setSortingEnabled(False)
                self.view.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
                for column in range(self.model.columnCount()):
                    self.view.resizeColumnToContents(column)
            else:
                self.view.resizeColumnsToContents()
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
        logger_setup.get_logger().info(f'Time to display table: {end_display_table_time - start_display_table_time}')

    def show_context_menu(self, pos):
        tree_menu = TreeContextMenu()
        table_menu = QtW.QMenu()
        edit_action = table_menu.addAction('Edit')
        add_action = table_menu.addAction('Add')
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
            action = table_menu.exec(self.dbTable_tableView.viewport().mapToGlobal(pos))
            if action:
                if action == edit_action:
                    self.edit_popup()
                elif action == view_upb_analyses_action:
                    self.display_data(action)

    def display_data(self, action):
        # get the row that was right-clicked
        parent_ids = []
        if self.view.selectedIndexes():
            selected_indexes = self.view.selectedIndexes()
        else:
            logger_setup.get_logger().error("Select cell or row")
            return
        for index in selected_indexes:
            if isinstance(self.view, QtW.QTreeView):
                tree_model = find_tree_model(self.view)
                parent_id = tree_model.index(index.row(), 2, index.parent()).data(QtC.Qt.ItemDataRole.DisplayRole)
            else:
                parent_id = self.proxy_model.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole)
            if parent_id not in parent_ids:
                parent_ids.append(str(parent_id))
        if 'Spot' in action.text():
            self.main_window.open_tab(parent_ids, 'Aliquot', 'Spot')
        elif 'U-Pb' in action.text():
            if isinstance(self.view, QtW.QTreeView):
                self.main_window.open_tab(parent_ids, 'Aliquot', 'UPbAnalysis')
            else:
                self.main_window.open_tab(parent_ids, 'Spot', 'UPbAnalysis')

    def edit_popup(self):
        logger_setup.get_logger().info(f'Opening edit dialog for {self.child_type} with parent {self.parent_type} ID {self.parent_id}')
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
            update_database()
            self.display_table()

    def search(self):
        """
        Search the current table for the text in the search box
        Check if the case-sensitive box is checked or not
        :return:
        """
        self.search_lineEdit: QtW.QLineEdit

        search_expression = QtC.QRegularExpression(self.search_lineEdit.text(), options=QRegularExpression.PatternOption.CaseInsensitiveOption)
        if self.child_type == 'Aliquot':
            # self.proxy_model.setRecursiveFilteringEnabled(True)
            self.proxy_model.setFilterRegularExpression(search_expression)
            if search_expression != "":
                self.view.expandAll()
        else:
            self.proxy_model.setFilterRegularExpression(search_expression)
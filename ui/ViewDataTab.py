import time

import qtawesome
from PyQt6 import QtCore as QtC
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import QTimer, QRegularExpression
from PyQt6.QtWidgets import QHeaderView, QLabel, QPushButton

import logger_setup
from Functions.Database_manager import update_database
from Functions.Database_views import ViewQuery
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.Widget_classes import (SQLiteTableModel, ReadableProxyModel, TreeModel,
                                      TreeContextMenu, expand_collapse, get_name_column, get_headers,
                                      get_view_from_table, TreeSortFilterProxyModel, get_readable_header,
                                      show_loading_dialog, close_loading_dialog, get_record_row,
                                      get_id_from_name, columns_as_list, save_expanded_state,
                                      TrackExpandedTreeView, FrozenTableView, scroll_to_record)
from ui.EditTreeView import EditTreeView
from ui.EditView import EditView

class ViewDataTab(QtW.QWidget):
    def __init__(self, parent_id: int, parent_type: str, child_type: str, label: str):
        super().__init__()
        logger_setup.get_logger().info(
            f'Creating a new ViewDataTab for {child_type} with parent {parent_type} ID {parent_id}')
        start_view_data_tab_time = time.time()

        self.setAttribute(QtC.Qt.WidgetAttribute.WA_DeleteOnClose)

        self.parent_id = parent_id
        self.parent_type = parent_type
        self.child_type = child_type
        self.view = None
        self.model = None
        self.tree_model = None
        self.proxy_model = None
        self.show_cols = []
        self.limit = None
        self.where = f' WHERE {get_headers(parent_type)[0]} = {self.parent_id}'
        self.table_item_ids = []
        if self.child_type not in ['Aliquots', 'Grains', 'Spots', 'UPbAnalyses']:
            logger_setup.get_logger().critical(f'Error: Invalid child type {self.child_type}')
            self.close()
        self.table = self.child_type
        self.name_header = get_headers(get_view_from_table(self.table))[get_name_column(get_view_from_table(self.table))]
        self.name_completer = QtW.QCompleter()

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
        self.h_layout_bottom = QtW.QHBoxLayout()
        if self.table != 'Aliquots':
            self.goto_line_edit = QtW.QLineEdit()
            self.goto_line_edit.setPlaceholderText(f'Go to {get_headers(self.table)[get_name_column(self.table)]}')
            self.prev_button = QPushButton('Back')
            self.next_button = QPushButton('Next')
            self.show_label = QLabel('Show per page:')
            self.show_per_page_comboBox = QtW.QComboBox()
            self.page_info_label = QLabel('')
            self.h_layout_bottom.addWidget(self.prev_button)
            self.h_layout_bottom.addWidget(self.next_button)
            self.h_layout_bottom.addWidget(self.show_label)
            self.h_layout_bottom.addWidget(self.show_per_page_comboBox)
            self.h_layout_bottom.addWidget(self.page_info_label)
            self.h_layout_bottom.addItem(QtW.QSpacerItem(20, 20, QtW.QSizePolicy.Policy.Expanding, QtW.QSizePolicy.Policy.Minimum))
            self.h_layout_bottom.addWidget(self.goto_line_edit)
        else:
            self.goto_line_edit = None
            self.prev_button = None
            self.next_button = None
            self.show_label = None
            self.show_per_page_comboBox = None
            self.page_info_label = QLabel('')
            self.h_layout_bottom.addWidget(self.page_info_label)

        self.v_layout.addLayout(self.h_layout)

        if self.table != 'Aliquots':
            # Pagination variables
            self.show_per_page_comboBox.addItems(['10', '25', '50', '100', '250', '500', '1000'])
            self.current_page = 0
            self.rows_per_page = settings.value('show_per_page')
            self.show_per_page_comboBox.setCurrentText(str(self.rows_per_page))
            self.goto_line_edit.returnPressed.connect(self.go_to_record)
            self.prev_button.clicked.connect(self.previous_page)
            self.next_button.clicked.connect(self.next_page)
            self.show_per_page_comboBox.currentIndexChanged.connect(self.change_rows_per_page)
            self.set_go_to_completer()
        self.total_records = 0

        self.search_lineEdit.returnPressed.connect(self.search)

        self.resize_timer = QTimer()
        self.display_table()
        if self.model.rowCount() == 0:
            close_loading_dialog('Loading', f'Loading {label}...')
            return
        self.v_layout.addLayout(self.h_layout_bottom)

        close_loading_dialog('Loading', f'Loading {label}...')
        end_view_data_tab_time = time.time()
        logger_setup.get_logger().info(
            f'Time to create ViewDataTab: {end_view_data_tab_time - start_view_data_tab_time}')

    def optimizeVerticalResize(self, logical_index, old_size, new_size):
        """Trigger a delayed row height update when the user resizes the window vertically."""
        self.resize_timer.start(100)  # Add a slight delay to avoid excessive updates

    def resizeRowsOptimized(self):
        """Resize rows only when resizing stops."""
        self.view.resizeRowsToContents()

    def change_rows_per_page(self):
        """
        Slot to change the number of rows displayed per page
        """
        self.rows_per_page = int(self.show_per_page_comboBox.currentText())
        self.current_page = 0
        self.limit = f'LIMIT {self.rows_per_page} OFFSET {self.current_page * self.rows_per_page}'
        self.display_table()

    def next_page(self):
        """
        Slot to move to the next page for the displayed table
        """
        if (self.current_page + 1) * self.rows_per_page < self.total_records:
            self.current_page += 1
            self.limit = f'LIMIT {self.rows_per_page} OFFSET {self.current_page * self.rows_per_page}'
            self.display_table()

    def previous_page(self):
        """
        Slot to move to the previous page for the displayed table
        """
        if self.current_page > 0:
            self.current_page -= 1
            self.limit = f'LIMIT {self.rows_per_page} OFFSET {self.current_page * self.rows_per_page}'
            self.display_table()

    def set_go_to_completer(self):
        # Populate the value input with a completer based on the selected attribute

        query = QtS.QSqlQuery()
        query_args = {'show_columns': [self.name_header], 'where': self.where}
        view_query = ViewQuery(self.table, True, **query_args)
        table_query = view_query.table_query
        logger_setup.get_logger().debug(f'SQL command: {table_query}')
        query.setForwardOnly(True)
        if not query.exec(table_query):
            logger_setup.get_logger().critical(f'Error creating the completer for input')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL command: {table_query}')
        all_names = set()
        while query.next():
            all_names.add(query.value(0))
        list_model = QtC.QStringListModel(sorted(all_names, key=str.casefold))
        list_proxy_model = ReadableProxyModel()
        list_proxy_model.setSourceModel(list_model)
        self.name_completer.setModel(list_proxy_model)
        self.name_completer.setFilterMode(QtC.Qt.MatchFlag.MatchContains)
        self.name_completer.setCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.name_completer.setModelSorting(QtW.QCompleter.ModelSorting.CaseInsensitivelySortedModel)
        self.name_completer.setCompletionMode(QtW.QCompleter.CompletionMode.PopupCompletion)

        self.goto_line_edit.setCompleter(self.name_completer)

    def go_to_record(self):
        """
        Slot to go to a specific record display name for the displayed table.
        """
        try:
            record_name = self.goto_line_edit.text()
            self.goto_line_edit.setText('')
            if record_name == "":
                return
            record_id = get_id_from_name(self.table, record_name)
            if not record_id:
                logger_setup.get_logger().error(f'Could not find record ID for record name: {record_name}')
                return
            row = get_record_row(self.table, record_id, self.table_item_ids)

            if row != -1:
                new_page = row // self.rows_per_page
                if self.current_page != new_page:
                    self.current_page = new_page
                    self.limit = f'LIMIT {self.rows_per_page} OFFSET {self.current_page * self.rows_per_page}'
                    self.display_table()
                scroll_to_record(record_id, self.view)
            else:
                logger_setup.get_logger().critical(f"Record {self.name_header} not found: {self.goto_line_edit.text()}")
        except Exception as e:
            logger_setup.get_logger().critical(f"Invalid Record {self.name_header}: {self.goto_line_edit.text()}")
            logger_setup.get_logger().debug(f'Error: {e}')
        # self.goto_line_edit.clear()
        # self.goto_line_edit.setText('')

    def display_table(self):
        logger_setup.get_logger().info(
            f'Displaying table for {self.child_type} with parent {self.parent_type} ID {self.parent_id}')
        if settings.value('show_items_missing_data'):
            msg = f'Displaying table...\n\nSettings to speed up loading:\n- Hide items with missing data\n- Reduce the columns shown'
        else:
            msg = f'Displaying table...\n\nSettings to speed up loading:\n- Reduce the columns shown'
        show_loading_dialog('Loading', msg)
        start_display_table_time = time.time()
        if not self.view:
            if self.child_type == 'Aliquots':
                self.view = TrackExpandedTreeView()
                self.view.setUniformRowHeights(True)
                self.view.setSortingEnabled(False)
            else:
                self.view = FrozenTableView()
                self.view.setSelectionBehavior(QtW.QAbstractItemView.SelectionBehavior.SelectRows)
                self.view.frozen_table_view.setSelectionBehavior(QtW.QAbstractItemView.SelectionBehavior.SelectRows)

                # Optimize window resizing
                self.resize_timer.setSingleShot(True)
                self.resize_timer.timeout.connect(self.resizeRowsOptimized)

                # Connect resizing events
                self.view.horizontalHeader().sectionResized.connect(self.optimizeVerticalResize)
                self.view.verticalHeader().sectionResized.connect(self.optimizeVerticalResize)
                self.view.frozen_table_view.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
                self.view.frozen_table_view.customContextMenuRequested.connect(self.show_context_menu)

            self.view.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
            self.view.customContextMenuRequested.connect(self.show_context_menu)
            self.v_layout.addWidget(self.view)
        self.view.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
        if self.child_type == 'Aliquots' and self.parent_type == 'Samples':
            self.show_cols = settings.value('aliquot_view_columns')
        elif self.child_type == 'Grains':
            self.show_cols = settings.value('grain_view_columns')
        elif self.child_type == 'Spots':
            self.show_cols = settings.value('spot_view_columns')
        elif self.child_type == 'UPbAnalyses':
            self.show_cols = settings.value('upb_analysis_view_columns')
        if self.child_type != 'Aliquots':
            limit = f'LIMIT {self.rows_per_page} OFFSET {self.current_page * self.rows_per_page}'
            query_args = {'show_columns': self.show_cols, 'limit': limit, 'where': self.where}
        else:
            query_args = {'show_columns': self.show_cols, 'where': self.where}
        view_query = ViewQuery(self.table, False, **query_args)
        table_query = view_query.table_query
        if settings.value('show_items_missing_data'):
            related_msg = f'Loading related data for {self.table}...\n\nSettings to speed up loading:\n- Hide items with missing data\n- Reduce the columns shown'
        else:
            related_msg = f'Loading related data for {self.table}...\n\nSettings to speed up loading:\n- Reduce the columns shown'
        show_loading_dialog('Loading', related_msg)
        self.model = SQLiteTableModel(table_query, view_query=view_query)
        close_loading_dialog('Loading', related_msg)
        if self.model.last_error:
            logger_setup.get_logger().critical(f'Error displaying table')
            close_loading_dialog('Loading', msg)
            return
        self.model.set_table(self.table)
        if self.model.rowCount() == 0:
            logger_setup.get_logger().error(f'No {self.child_type} for selected {self.parent_type}')
            close_loading_dialog('Loading', msg)
            self.close()
            return
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

        hidden_columns = []
        frozen_column = None
        match self.table:
            case 'Samples':
                hidden_columns = [0]  # don't show SampleID column
                frozen_column = 1
            case 'Aliquots':
                hidden_columns = [1, 2, 3, 4]  # don't show AliquotID, ParentAliquotID, AliquotParentRow, SampleID
            case 'Grains':
                hidden_columns = [0, 1, 2]  # don't show GrainID, AliquotID, SampleID
                frozen_column = 3
            case 'Spots':
                hidden_columns = [0, 1, 2, 3]  # don't show SpotID, GrainID, AliquotID, SampleID
                frozen_column = 4
            case 'UPbAnalyses':
                hidden_columns = [0, 1, 2, 3, 4]  # don't show UPbAnalysisID, SpotID, GrainID, AliquotID, SampleID
                frozen_column = 5
        for column in range(self.view.model().columnCount()):
            if column in hidden_columns:
                self.view.hideColumn(column)
            else:
                self.view.showColumn(column)
        if isinstance(self.view.model(), TreeSortFilterProxyModel):
            self.view.model().update_visible_columns()
        elif frozen_column is not None:
            self.view.set_frozen_column(frozen_column)

        query_args = {'show_columns': [self.show_cols[0]], 'where': self.where}
        view_query = ViewQuery(self.table, True, **query_args)
        table_query = view_query.table_query
        self.table_item_ids = columns_as_list(table_query, [0], view_query)[0]
        self.total_records = len(self.table_item_ids)
        if self.table != 'Aliquots':
            self.page_info_label.setText(
            f'{self.current_page * self.rows_per_page + 1}-{min((self.current_page + 1) * self.rows_per_page, self.total_records)} of {self.total_records}')
        else:
            self.page_info_label.setText(f'{self.total_records} {self.table}')
        end_display_table_time = time.time()
        close_loading_dialog('Loading', msg)
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
            if self.model.table == 'Grains':
                view_spots_action = table_menu.addAction('View Spots')
            else:
                view_spots_action = None
            if self.model.table in ['Spots', 'Grains']:
                view_upb_analyses_action = table_menu.addAction('View U-Pb Analyses')
            else:
                view_upb_analyses_action = None
            action = table_menu.exec(self.view.viewport().mapToGlobal(pos))
            if action:
                if action == edit_action:
                    self.edit_popup()
                elif action == view_upb_analyses_action or action == view_spots_action:
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
        if 'Grain' in action.text():
            self.main_window.open_tab(parent_ids, 'Aliquots', 'Grains')
        elif 'Spot' in action.text():
            if isinstance(self.view, QtW.QTreeView):
                self.main_window.open_tab(parent_ids, 'Aliquots', 'Spots')
            else:
                self.main_window.open_tab(parent_ids, 'Grains', 'Spots')
        elif 'U-Pb' in action.text():
            if isinstance(self.view, QtW.QTreeView):
                self.main_window.open_tab(parent_ids, 'Aliquots', 'UPbAnalyses')
            else:
                self.main_window.open_tab(parent_ids, self.table, 'UPbAnalyses')

    def edit_popup(self):
        logger_setup.get_logger().info(
            f'Opening edit dialog for {self.child_type} with parent {self.parent_type} ID {self.parent_id}')
        dlg_args = {'parent_id': self.parent_id, 'parent_type': self.parent_type}
        if self.child_type == 'Aliquots':
            dlg = EditTreeView(self, self.table, **dlg_args)
        else:
            dlg = EditView(self, self.table, **dlg_args)
        if isinstance(self.view, QtW.QTreeView):
            save_expanded_state(self.table, self.view)
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

    def close(self):
        if isinstance(self.view, QtW.QTreeView) and self.tree_model:
            save_expanded_state(self.table, self.view)
        super().close()

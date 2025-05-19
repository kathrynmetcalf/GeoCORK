import os
import sys
import time
from operator import index, itemgetter

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import QPoint, QSize, QSortFilterProxyModel
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtWidgets import QCompleter, QMessageBox
from PyQt6.uic import loadUi
import Functions.Text_manipulations as TxM
import logger_setup
import difflib

from Functions.SQLUtils import spot_aliquot_join, aliquot_sample_join
from Functions.Widget_classes import (
    TreeModel, CheckableTreeCombobox, CheckableTreeModel, CheckableTreeView, ReadableProxyModel, DisplayRoundedModel,
    SQLiteTableModel, CheckableComboBox, CheckableSqlTableModel, CheckableSqlQueryModel, get_headers, get_name_column,
    set_table, populate_many_combo_checks, populate_model_checks,
    WordWrapDelegate, get_columns, get_table_from_view, find_sub_items, get_total_records, get_record_index,
    get_id_from_name, add_tree_popup, save_expanded_state, restore_expanded_state, get_readable_header,
    get_name_from_id, DisplayRoundedQueryModel
)
from Functions import SQLUtils
from Functions.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint, SavepointManager
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.Database_views import ViewQuery
from Functions.LoadingDialog_manager import LoadingDialogManager
from ui.AddTags import AddTags
from ui.AddTreeTags import AddTreeTags
from ui.EditTree import EditTree
from ui.EditTable import EditTable
from ui.GPSDialog import GPSDialog
from ui.New_reference import NewReference
from ui.AgeDialog import AgeDialog
import time

class SetSelectedValues(QtW.QDialog):
    def __init__(self, parent_window, widget: QtW.QWidget):
        super().__init__(parent=parent_window)
        self.setWindowTitle('Set selected values')
        self.setModal(True)
        self.close_by_dialog = False
        self.loading_manager = LoadingDialogManager.get_instance()
        # self.setMinimumSize(600, 200)

        self.widget = widget
        self.widget.setVisible(True)
        self.widget.setSizePolicy(QtW.QSizePolicy.Policy.Expanding, QtW.QSizePolicy.Policy.Expanding)
        if isinstance(self.widget, QtW.QComboBox):
            self.widget.setSizeAdjustPolicy(QtW.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.commit_button = QtW.QPushButton('Commit')
        self.cancel_button = QtW.QPushButton('Cancel')
        self.commit_button.autoDefault()
        self.commit_button.clicked.connect(self.commit)
        self.cancel_button.clicked.connect(self.cancel)

        button_layout = QtW.QHBoxLayout()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.commit_button)
        main_layout = QtW.QVBoxLayout()
        main_layout.addWidget(self.widget)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        self.adjustSize()
        self.loading_manager.close_loading_dialog('Loading', f'Loading...')

    def commit(self):
        self.close_by_dialog = True
        self.accept()

    def cancel(self):
        self.close_by_dialog = True
        self.reject()

    def closeEvent(self, event):
        if self.close_by_dialog:
            event.accept()
        else:
            self.cancel()

class EditView(QtW.QDialog):
    def __init__(self, parent_window, table_name, **kwargs):
        super().__init__(parent=parent_window)
        self.loading_manager = LoadingDialogManager.get_instance()
        self.loadWindowState()

        logger_setup.get_logger().info(f'Creating a new EditView for {get_readable_header(table_name)}')
        edit_view_start_time = time.time()
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "EditTable.ui")
        loadUi(sources_ui_file, self)
        self.setModal(True)
        self.setWindowTitle(f'Edit {TxM.add_spaces_camel(table_name)}')
        self.updated = False
        self.name_completer = QCompleter()

        self.parent_id: int = None
        self.parent_type: str = None
        self.table_item_ids: list = None
        for key, value in kwargs.items():
            setattr(self, key, value)
        if isinstance(self.parent_id, str):
            self.parent_id = int(self.parent_id)

        # Pagination variables
        self.show_per_page_comboBox: QtW.QComboBox
        self.show_per_page_comboBox.addItems(['10', '25', '50', '100', '250', '500', '1000'])
        self.current_page = 0
        self.rows_per_page = settings.value('show_per_page')
        self.show_per_page_comboBox.setCurrentText(str(self.rows_per_page))
        self.total_records = 0

        self.table = TxM.remove_spaces(table_name)
        self.msg = QtW.QMessageBox()
        self.model = None
        self.proxy_model = None
        self.name_column = None
        self.name_header = None
        self.show_cols = []
        self.limit = ''
        self.where = ''

        self.create_model()
        self.combo = None
        self.combo_index = QtC.QModelIndex()
        self.combo_model = None
        self.combo_proxy = None
        self.dropdown_table = None
        self.lineEdit = None
        self.msg = QtW.QMessageBox(self)
        self.close_by_dialog = False
        self.tabbed_from_editor = False

        self.table_headers = get_headers(self.table)
        self.gps_headers = []
        self.age_headers = []
        for header in self.show_cols:
            if 'GPS' in header or 'Elevation' in header:
                self.gps_headers.append(header)
            elif 'SampleAge' in header and 'AgeSignature' not in header:
                self.age_headers.append(header)

        create_savepoint('before_edit')

        self.edit_tableView.installEventFilter(self)
        self.edit_tableView.selectionModel().currentChanged.connect(self.on_index_change)
        self.edit_tableView.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.edit_tableView.customContextMenuRequested.connect(self.show_context_menu)
        self.commit_pushButton.clicked.connect(self.commit_question)
        self.cancel_pushButton.clicked.connect(self.discard_question)
        self.edit_tableView.selectionModel().currentRowChanged.connect(self.on_row_change)
        self.edit_tableView.doubleClicked.connect(self.display_widget)
        self.goto_line_edit.returnPressed.connect(self.go_to_record)
        self.prev_button.clicked.connect(self.previous_page)
        self.next_button.clicked.connect(self.next_page)
        self.show_per_page_comboBox.currentIndexChanged.connect(self.change_rows_per_page)
        self.set_go_to_completer()

        self.loading_manager.close_loading_dialog('Loading', f'Opening edit window for {self.table}...')
        logger_setup.get_logger().info(f'EditView created for {self.table} in {time.time() - edit_view_start_time:.2f} seconds')

    def create_model(self):
        name_column = get_name_column(self.table)
        id_header = get_headers(self.table)[0]
        if name_column is not None:
            self.name_header = get_headers(self.table)[name_column]
        if self.table in SQLUtils.trigger_tables:
            if self.table == 'Columns':
                self.show_cols = settings.value('column_edit_columns')
                self.add_pushButton.clicked.connect(self.add_popup)
            elif self.table == 'Samples':
                self.show_cols = settings.value('sample_edit_columns')
                self.add_pushButton.hide()
            elif self.table == 'Spots' or self.table == 'UPbAnalyses':
                self.parent_id_header = 'SampleID' if self.parent_type == 'Sample' \
                    else 'AliquotID' if self.parent_type == 'Aliquot' \
                    else 'SpotID' if self.parent_type == 'Spot' else None
                if self.parent_id_header:
                    self.where = f' WHERE {self.parent_id_header} = {self.parent_id}'
                if self.table == 'Spots':
                    self.show_cols = settings.value('spot_edit_columns')
                elif self.table == 'UPbAnalyses':
                    self.show_cols = settings.value('upb_analysis_edit_columns')
                self.add_pushButton.hide()
        elif self.table == 'References':
            self.show_cols = settings.value('reference_view_columns')
            self.add_pushButton.clicked.connect(self.add_popup)
        if self.table_item_ids is not None:
            if len(self.table_item_ids) == 1:
                sql_where_str = f'= {self.table_item_ids[0]}'
            else:
                sql_where_str = f'IN {tuple(self.table_item_ids)}'
            if self.where == '':
                self.where = f' WHERE {id_header} {sql_where_str}'
            else:
                self.where = f'{self.where} AND {id_header} {sql_where_str}'
        query_args = {'show_columns': self.show_cols, 'limit': self.limit, 'where': self.where}
        view_query = ViewQuery(self.table, True, **query_args)
        table_query = view_query.table_query
        self.model = SQLiteTableModel(table_query)
        if self.model.last_error is not None:
            logger_setup.get_logger().critical(f'Error displaying {self.table}.')
            return
        self.model.table = self.table
        self.display_table()

    def optimizeVerticalResize(self, logical_index, old_size, new_size):
        """Trigger a delayed row height update when the user resizes the window vertically."""
        self.resize_timer.start(250)  # Add a slight delay to avoid excessive updates

    def resizeRowsOptimized(self):
        """Resize rows only when resizing stops."""
        self.edit_tableView.resizeRowsToContents()

    def change_rows_per_page(self):
        """
        Slot to change the number of rows displayed per page
        """
        self.rows_per_page = int(self.show_per_page_comboBox.currentText())
        self.current_page = 0
        self.create_model()
        self.limit = f'LIMIT {self.rows_per_page} OFFSET {self.current_page * self.rows_per_page}'

    def next_page(self):
        """
        Slot to move to the next page for the displayed table
        """
        if (self.current_page + 1) * self.rows_per_page < self.total_records:
            self.current_page += 1
            self.create_model()
        self.limit = f'LIMIT {self.rows_per_page} OFFSET {self.current_page * self.rows_per_page}'

    def previous_page(self):
        """
        Slot to move to the previous page for the displayed table
        """
        if self.current_page > 0:
            self.current_page -= 1
            self.create_model()
        self.limit = f'LIMIT {self.rows_per_page} OFFSET {self.current_page * self.rows_per_page}'

    def set_go_to_completer(self):
        # Populate the value input with a completer based on the selected attribute

        query = QSqlQuery()
        query_args = {'show_columns': [self.name_header], 'where': self.where}
        view_query = ViewQuery(self.table, True, **query_args)
        table_query = view_query.table_query
        logger_setup.get_logger().debug(f'SQL command: {table_query}')
        query.setForwardOnly(True)
        if not query.exec(table_query):
            logger_setup.get_logger().critical(f'Error creating the completer for input')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        values = set()
        while query.next():
            values.add(query.value(0))
        self.name_completer.setModel(QtC.QStringListModel(values))
        self.name_completer.setFilterMode(QtC.Qt.MatchFlag.MatchContains)
        self.name_completer.setCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
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
            index = get_record_index(self.table, record_id)

            if index != -1:
                new_page = index // self.rows_per_page
                if self.current_page == new_page:
                    QMessageBox.information(self, 'Record Found', 'Record already displayed')
                else:
                    self.current_page = new_page
                    self.create_model()
            else:
                logger_setup.get_logger().critical(f"Record {self.name_header} not found: {self.goto_line_edit.text()}")
        except Exception as e:
            logger_setup.get_logger().critical(f"Invalid Record {self.name_header}: {self.goto_line_edit.text()}")
            logger_setup.get_logger().debug(f'Error: {e}')
        self.goto_line_edit.clear()
        self.goto_line_edit.setText('')

    def eventFilter(self, object, event):
        if event.type() in (
            QtC.QEvent.Type.MouseButtonPress, QtC.QEvent.Type.MouseButtonRelease, QtC.QEvent.Type.MouseButtonDblClick,
            QtC.QEvent.Type.InputMethodQuery
        ):
            self.tabbed_from_editor = False
        if self.combo:
            objects_statement = object is self.combo or object is self.lineEdit or object is self.combo.view()
        else:
            objects_statement = object is self.lineEdit
        if objects_statement:
            # the object is one of the widgets we are interested in
            if event.type() == QtC.QEvent.Type.KeyPress and event.key() == QtC.Qt.Key.Key_Tab:
                self.advance_tab()
                self.display_widget()
                return True
            if event.type() == QtC.QEvent.Type.KeyPress and event.key() == QtC.Qt.Key.Key_Backtab:
                self.reverse_tab()
                self.display_widget()
                return True
            return super().eventFilter(object, event)
        if object is self.lineEdit:
            if event.type() == QtC.QEvent.Type.KeyPress and event.key() in (QtC.Qt.Key.Key_Return, QtC.Qt.Key.Key_Enter):
                self.destroy_lineedit()
                return True
        return super().eventFilter(object, event)

    def show_context_menu(self, pos):
        indexes = self.edit_tableView.selectedIndexes()
        if not indexes:
            return
        menu = QtW.QMenu()
        for index in indexes:
            if not index.isValid():
                return
        clear_action = menu.addAction('Clear selected values')
        single_column = False
        for index in indexes:
            if index.column() != indexes[0].column():
                single_column = False
                break
            single_column = True
        if single_column:
            set_selected_action = menu.addAction('Set selected values')
        else:
            set_selected_action = None
        edit_action = menu.addAction('Edit')
        delete_action = menu.addAction('Delete row')
        action = menu.exec(self.edit_tableView.viewport().mapToGlobal(pos))
        if action is None:
            return
        elif action == clear_action:
            self.clear_data()
        elif action == set_selected_action:
            self.determine_widget(indexes[0])
            if self.lineEdit:
                dlg = SetSelectedValues(self, self.lineEdit)
                if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
                    self.lineEdit = dlg.widget
                    self.loading_manager.show_loading_dialog('Loading', f'Loading...')
                    self.save_lineedit_data()
                else:
                    self.destroy_lineedit()
            elif self.combo:
                dlg = SetSelectedValues(self, self.combo)
                if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
                    self.combo = dlg.widget
                    self.loading_manager.show_loading_dialog('Loading', f'Loading...')
                    self.save_dropdown_data()
                else:
                    self.destroy_dropdown()
        elif action == edit_action:
            self.display_widget()
        elif action == delete_action:
            # get all the rows in the selected indexes
            ids_to_delete = []
            for index in indexes:
                model_index = self.proxy_model.mapToSource(index)
                id = self.model.index(model_index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole)
                if id not in ids_to_delete:
                    ids_to_delete.append(id)
            if len(ids_to_delete) == 1:
                sql_where_str = f'= {ids_to_delete[0]}'
            elif len(ids_to_delete) > 1:
                sql_where_str = f'IN {tuple(ids_to_delete)}'
            else:
                logger_setup.get_logger().error('No rows selected to delete')
                return
            if self.delete_question(ids_to_delete):
                logger_setup.get_logger().info(f'Deleting {len(ids_to_delete)} {self.table_headers[get_name_column(self.table)]} from {self.table}')
                query = QtS.QSqlQuery()
                if not query.exec(f'DELETE FROM {self.table} WHERE {self.table_headers[0]} {sql_where_str}'):
                    logger_setup.get_logger().critical(f'Failed to delete selected rows from {self.table}: {query.lastError().text()}')
                    return
                self.model.removeRows(ids_to_delete)
                self.display_table()

    def display_table(self):
        start_time = time.time()
        logger_setup.get_logger().info(f'Displaying {self.table} table')
        self.loading_manager.show_loading_dialog('Loading', f'Displaying {self.table}...')
        self.proxy_model = ReadableProxyModel(view=True)
        self.proxy_model.setSourceModel(self.model)
        if self.table == 'UPbAnalyses':
            # Use spot name column in the view
            self.name_column = 4
        else:
            self.name_column = get_name_column(self.table)
        proxy_name_column = None
        if self.name_column is not None:
            self.name_header = self.show_cols[self.name_column]
            for column in range(self.proxy_model.columnCount()):
                header = self.model.headerData(column, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
                if header == self.name_header:
                    proxy_name_column = column
                    break
        self.edit_tableView.setModel(self.proxy_model)
        for column in range(self.proxy_model.columnCount()):
            header = self.model.headerData(column, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            if 'ID' in header:
                self.edit_tableView.hideColumn(column)
        self.edit_tableView.setSortingEnabled(True)
        self.edit_tableView.setWordWrap(True)
        self.edit_tableView.setTextElideMode(QtC.Qt.TextElideMode.ElideNone)  # Prevent text truncation
        self.edit_tableView.setItemDelegate(WordWrapDelegate(self.edit_tableView))

        self.edit_tableView.resizeRowsToContents()
        self.edit_tableView.verticalHeader().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
        if proxy_name_column:
            self.proxy_model.sort(proxy_name_column, QtC.Qt.SortOrder.AscendingOrder)

        if self.table_item_ids:
            # If the table_item_ids are provided, we need to set the total records based on the filtered data
            self.total_records = len(self.table_item_ids)
        elif self.where != '':
            self.total_records = get_total_records(self.table, self.where)
        else:
            self.total_records = get_total_records(self.table)
        self.page_info_label.setText(
            f'{self.current_page * self.rows_per_page + 1}-{min((self.current_page + 1) * self.rows_per_page, self.total_records)} of {self.total_records}')
        self.goto_line_edit.clear()
        self.goto_line_edit.setPlaceholderText(f'Go to {self.name_header}...')

        # Optimize window resizing
        self.resize_timer = QtC.QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.resizeRowsOptimized)

        # Connect resizing events
        self.edit_tableView.horizontalHeader().sectionResized.connect(self.optimizeVerticalResize)
        self.edit_tableView.verticalHeader().sectionResized.connect(self.optimizeVerticalResize)

        self.edit_tableView.resizeColumnsToContents()
        for column in range(self.proxy_model.columnCount()):
            if self.edit_tableView.columnWidth(column) > 400:
                self.edit_tableView.setColumnWidth(column, 400)

        self.loading_manager.close_loading_dialog('Loading', f'Displaying {self.table}...')
        end_time = time.time()
        logger_setup.get_logger().info(f'Displayed {self.table} in {end_time - start_time} seconds')
        self.loading_manager.close_loading_dialog('Loading', f'Loading...')

    def display_widget(self):
        if len(self.edit_tableView.selectedIndexes()) == 0:
            return
        elif len(self.edit_tableView.selectedIndexes()) > 1:
            logger_setup.get_logger().error('Right-click with selected values in single column to edit multiple selections')
            return
        proxy_index = self.edit_tableView.selectedIndexes()[0]
        model_index = self.proxy_model.mapToSource(proxy_index)
        self.determine_widget(model_index)
        if self.lineEdit is not None and self.edit_index.isValid():
            self.display_lineedit()
        elif self.combo is not None and self.combo_index.isValid():
            self.display_dropdown()

    def determine_widget(self, model_index):
        if not model_index.isValid():
            return
        if self.lineEdit is not None:
            self.destroy_lineedit()
            if self.lineEdit is not None:
                logger_setup.get_logger().info('Error destroying previous line edit')
                return
        elif self.combo is not None:
            self.save_dropdown_data()
            if self.combo is not None:
                logger_setup.get_logger().info('Error destroying previous dropdown')
                return
        if model_index.column() == self.name_column and self.table != 'UPbAnalyses':
            # The column is the name column for the table. This should be edited with a line edit.
            self.create_lineedit()
            return
        self.loading_manager.show_loading_dialog('Loading', f'Loading...')
        header = self.model.headerData(model_index.column(), QtC.Qt.Orientation.Horizontal,
                                       QtC.Qt.ItemDataRole.DisplayRole)
        if 'GPS' in header or 'Elevation' in header:
            if not self.tabbed_from_editor:
                # Do not open the popup if tabbing here, only when double-clicking
                item_ids = []
                row = model_index.row()
                item_ids.append(self.model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole))
                self.loading_manager.close_loading_dialog('Loading', f'Loading...')
                self.loading_manager.show_loading_dialog('Loading', f'Opening GPS editor...')
                dlg = GPSDialog(self.table, item_ids, self)
                dlg.exec()
                if dlg.gps_fields.updated:
                    self.updated = True
                    logger_setup.get_logger().info(f'Repopulating {get_readable_header(header)} for {item_ids[0]}')
                    query = QtS.QSqlQuery()
                    if not query.exec(f'SELECT {', '.join(self.gps_headers)} FROM {self.table} WHERE {self.table_headers[0]} = {item_ids[0]}'):
                        logger_setup.get_logger().critical(f'Failed to get {get_readable_header(header)} for {item_ids[0]}: {query.lastError().text()}')
                        return
                    if query.next():
                        for header in self.gps_headers:
                            col = self.show_cols.index(header)
                            self.model.setData(self.model.index(row, col), query.value(header), QtC.Qt.ItemDataRole.EditRole)
                            logger_setup.get_logger().info(f'New value: {self.model.index(row, col).data(QtC.Qt.ItemDataRole.DisplayRole)}')
            else:
                self.edit_tableView.setFocus()
        elif 'SampleAge' in header and 'AgeSignature' not in header:
            if not self.tabbed_from_editor:
                item_ids = []
                row = model_index.row()
                item_ids.append(self.model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole))
                self.loading_manager.close_loading_dialog('Loading', f'Loading...')
                self.loading_manager.show_loading_dialog('Loading', f'Opening sample age editor...')
                dlg = AgeDialog(self.table, item_ids, self)
                dlg.exec()
                if dlg.age_fields.updated:
                    self.updated = True
                    logger_setup.get_logger().info(f'Repopulating {get_readable_header(header)} for {item_ids[0]}')
                    query = QtS.QSqlQuery()
                    if not query.exec(f'SELECT {header} FROM {self.table} WHERE {self.table_headers[0]} = {item_ids[0]}'):
                        logger_setup.get_logger().critical(f'Failed to get {get_readable_header(header)} for {item_ids[0]}: {query.lastError().text()}')
                        return
                    if query.next():
                        col = self.show_cols.index(header)
                        self.model.setData(self.model.index(row, col), query.value(header), QtC.Qt.ItemDataRole.EditRole)
            else:
                self.edit_tableView.setFocus()
        else:
            self.dropdown_table = ''
            if 'Rejected' in header:
                self.dropdown_table = 'Rejected'
            else:
                columns = None
                if header in SQLUtils.non_editable[self.table]:
                    logger_setup.get_logger().error(f'{get_readable_header(header)} is not editable')
                    return
                elif header in SQLUtils.many_editable[self.table].keys():
                    columns = SQLUtils.many_editable[self.table]
                elif header in SQLUtils.one_editable[self.table].keys():
                    columns = SQLUtils.one_editable[self.table]
                else:
                    for key, values in SQLUtils.many_editable.items():
                        if header in values.keys():
                            columns = values
                            break
                    if columns is None:
                        for key, values in SQLUtils.one_editable.items():
                            if header in values.keys():
                                columns = values
                                break
                    if columns is None:
                        for key, values in SQLUtils.non_editable.items():
                            if header in values:
                                logger_setup.get_logger().info(f'{get_readable_header(header)} is not editable')
                                return
                if columns is not None:
                    for col_key in columns:
                        if header == col_key:
                            self.dropdown_table = columns[header]
                            break
            if self.dropdown_table == '':
                query, virtual, stored, columns = get_columns(self.table)
                if f'"{header}"' in virtual or f'"{header}"' in stored:
                    logger_setup.get_logger().error(f'{get_readable_header(header)} is auto-generated and not editable')
                    return
                self.create_lineedit()
            else:
                query, virtual, stored, columns = get_columns(self.dropdown_table)
                if f'"{header}"' in virtual or f'"{header}"' in stored:
                    logger_setup.get_logger().error(f'{get_readable_header(header)} is auto-generated and not editable')
                    return
                self.create_dropdown()

    def create_lineedit(self):
        logger_setup.get_logger().info('Displaying line edit')
        self.lineEdit = QtW.QLineEdit()
        if len(self.edit_tableView.selectedIndexes()) > 1:
            self.edit_index = QtC.QModelIndex()
            text_items = []
            for index in self.edit_tableView.selectedIndexes():
                model_index = self.proxy_model.mapToSource(index)
                item_text = model_index.data(QtC.Qt.ItemDataRole.DisplayRole)
                if item_text not in text_items:
                    text_items.append(item_text)
            if len(text_items) == 1:
                self.lineEdit.setText(text_items[0])
            elif len(text_items) > 1:
                self.lineEdit.setText('-')
            else:
                self.lineEdit.setText('')
        else:
            self.edit_index = self.edit_tableView.selectedIndexes()[0]
            model_index = self.proxy_model.mapToSource(self.edit_index)
            # self.lineEdit.setValidator(QtG.QRegularExpressionValidator(QtC.QRegularExpression("[0-9]*")))
            if not model_index.data(QtC.Qt.ItemDataRole.DisplayRole):
                self.lineEdit.setText('')
            else:
                self.lineEdit.setText(str(model_index.data(QtC.Qt.ItemDataRole.DisplayRole)))
                self.lineEdit.selectAll()

    def display_lineedit(self):
        self.lineEdit.installEventFilter(self)
        self.loading_manager.close_loading_dialog('Loading', f'Loading...')
        self.lineEdit.returnPressed.connect(self.save_lineedit_data)
        self.lineEdit.editingFinished.connect(self.save_lineedit_data)
        self.edit_tableView.setIndexWidget(self.edit_tableView.selectedIndexes()[0], self.lineEdit)
        self.lineEdit.setFocus()

    def save_lineedit_data(self):
        logger_setup.get_logger().info('Saving data from line edit')
        if self.lineEdit is not None:
            edit_value = self.lineEdit.text()
            if not self.edit_index.isValid():
                model_indexes = []
                for index in self.edit_tableView.selectedIndexes():
                    model_indexes.append(self.proxy_model.mapToSource(index))
            else:
                model_indexes = [self.proxy_model.mapToSource(self.edit_index)]
            for model_index in model_indexes:
                if self.model.setData(model_index, edit_value, QtC.Qt.ItemDataRole.EditRole):
                    if self.edit_tableView.currentIndex() == self.edit_index:
                        self.tabbed_from_editor = False
                else:
                    logger_setup.get_logger().critical(f'Failed to set data in the table')
                    self.destroy_lineedit()
                    return
            logger_setup.get_logger().info('Data saved from line edit')
            self.destroy_lineedit()
            return

    def destroy_lineedit(self):
        try:
            self.lineEdit.removeEventFilter(self)
            self.lineEdit.editingFinished.disconnect(self.save_lineedit_data)
            self.lineEdit.returnPressed.disconnect(self.save_lineedit_data)
        except TypeError:
            pass
        self.edit_tableView.setIndexWidget(self.edit_index, None)
        self.lineEdit = None
        self.edit_index = QtC.QModelIndex()
        self.edit_tableView.setFocus()

    def create_dropdown(self):
        logger_setup.get_logger().info(f'Displaying dropdown for {self.dropdown_table}')
        if len(self.edit_tableView.selectedIndexes()) > 1:
            self.combo_index = QtC.QModelIndex()
            model_indexes = []
            for index in self.edit_tableView.selectedIndexes():
                model_index = self.proxy_model.mapToSource(index)
                if model_index not in model_indexes:
                    model_indexes.append(model_index)
        else:
            self.combo_index = self.edit_tableView.selectedIndexes()[0]
            model_indexes = [self.proxy_model.mapToSource(self.combo_index)]
        self.combo_model = QtS.QSqlTableModel()
        self.combo = QtW.QComboBox()
        header = self.model.headerData(model_indexes[0].column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        if self.dropdown_table == 'Rejected':
            self.combo = QtW.QComboBox()
            self.combo.addItem('Accepted')
            self.combo.addItem('Rejected')
        else:
            if self.dropdown_table == 'References':
                self.combo = CheckableComboBox()
                self.combo_model = CheckableSqlQueryModel()
                self.combo_model.setQuery(f'SELECT * FROM "References"')
                self.combo_proxy = ReadableProxyModel()
                self.combo_proxy.setSourceModel(self.combo_model)
                self.combo.setModel(self.combo_proxy)
            else:
                set_table(self.combo_model, self.dropdown_table)
            if ((self.table == 'UPbAnalyses' and self.dropdown_table in ('Aliquots', 'Spots')) or
                  (self.table == 'Spots' and self.dropdown_table == 'Aliquots')):
                if self.parent_type == 'Sample':
                    if self.dropdown_table == 'Aliquot':
                        self.combo = CheckableTreeCombobox()
                        combo_model = CheckableSqlQueryModel()
                        combo_model.setQuery(f'SELECT * FROM Aliquots WHERE SampleID = {self.parent_id}')
                        self.tree_model = CheckableTreeModel()
                        self.tree_model.setSourceModel(combo_model)
                        self.combo.setModel(self.tree_model)
                    elif self.dropdown_table == 'Spots':
                        self.combo = CheckableComboBox()
                        self.combo_model = CheckableSqlQueryModel()
                        self.combo_model.setQuery(f'''SELECT * FROM Spots 
                            {SQLUtils.spot_aliquot_join}
                            WHERE SampleID = {self.parent_id}''')
                        self.combo_proxy = ReadableProxyModel()
                        self.combo_proxy.setSourceModel(self.combo_model)
                        self.combo.setModel(self.combo_proxy)
                elif self.parent_type == 'Aliquot':
                    if self.dropdown_table == 'Spots':
                        self.combo = CheckableComboBox()
                        self.combo_model = CheckableSqlQueryModel()
                        self.combo_model.setQuery(f'SELECT * FROM Spots WHERE AliquotID = {self.parent_id}')
                        self.combo_proxy = ReadableProxyModel()
                        self.combo_proxy.setSourceModel(self.combo_model)
                        self.combo.setModel(self.combo_proxy)
            elif self.dropdown_table in SQLUtils.user_viewable_trees:
                self.combo = CheckableTreeCombobox()
                self.tree_model = CheckableTreeModel()
                self.tree_model.setSourceModel(self.combo_model)
                self.combo.setModel(self.tree_model)
            elif self.dropdown_table == 'References':
                pass
            elif 'Abbreviation' in header:
                self.combo = QtW.QComboBox()
                self.combo.setModel(self.combo_model)
            else:
                self.combo = CheckableComboBox()
                self.combo_model = CheckableSqlTableModel()
                set_table(self.combo_model, self.dropdown_table)
                self.combo_proxy = ReadableProxyModel()
                self.combo_proxy.setSourceModel(self.combo_model)
                self.combo.setModel(self.combo_proxy)
            self.combo.setModelColumn(get_name_column(self.dropdown_table))
            selected_ids = []
            for model_index in model_indexes:
                selected_id = self.model.index(model_index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole)
                if selected_id not in selected_ids:
                    selected_ids.append(selected_id)
            if not selected_ids:
                logger_setup.get_logger().critical('No selected ids found')
                self.destroy_dropdown()
                return
            edit_table, edit_ids = self.determine_edit_table(selected_ids)
            if not edit_table or not edit_ids:
                logger_setup.get_logger().critical('No edit table or edit ids found')
                self.destroy_dropdown()
                return
            if '_' in edit_table:
                populate_many_combo_checks(edit_table, self.combo, edit_ids)
                self.combo.single_click = False
            else:
                if isinstance(self.combo_model, CheckableSqlTableModel | CheckableSqlQueryModel | CheckableTreeModel):
                    populate_model_checks(self.combo_model, edit_ids, edit_table)
                    self.combo.single_click = True
        if not self.combo_index.isValid():
            selected_text = model_indexes[0].data(QtC.Qt.ItemDataRole.DisplayRole)
        else:
            selected_text = self.combo_index.data(QtC.Qt.ItemDataRole.DisplayRole)
        self.combo.setCurrentText(selected_text)
        if self.combo.currentText() == '':
            # Make sure there is no selected index
            self.combo.setCurrentIndex(-1)
        # print(f"Selected text: {selected_text}")

    def display_dropdown(self):
        self.edit_tableView.setIndexWidget(self.edit_tableView.selectedIndexes()[0], self.combo)
        self.combo.installEventFilter(self)
        self.combo.view().installEventFilter(self)
        self.combo.model_modifiable = True
        self.combo.closedOnLineEditClick = False
        if isinstance(self.combo, CheckableComboBox | CheckableTreeCombobox):
            self.combo.enable_context_menu(True)
            self.combo.add_triggered.connect(self.add_tag_popup)
            self.combo.edit_triggered.connect(self.edit_tag_popup)
        # self.combo.activated.connect(self.save_dropdown_data)
        self.loading_manager.close_loading_dialog('Loading', f'Loading...')
        self.combo.setFocus()
        # print("showing popup")
        self.combo.showPopup()

    def save_dropdown_data(self):
        logger_setup.get_logger().info('Saving data from dropdown')
        self.edit_tableView: QtW.QTableView
        if self.combo is not None:
            combo = self.combo
        else:
            return
        updated = False
        if not self.combo_index.isValid():
            model_indexes = []
            for index in self.edit_tableView.selectedIndexes():
                model_indexes.append(self.proxy_model.mapToSource(index))
        else:
            model_indexes = [self.proxy_model.mapToSource(self.combo_index)]
        selected_ids = []
        view_headers = []
        for model_index in model_indexes:
            item_id = self.model.index(model_index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole)
            if item_id not in selected_ids:
                selected_ids.append(item_id)
            header = self.model.headerData(model_index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            if header not in view_headers:
                view_headers.append(header)
        if not selected_ids or len(selected_ids) < 1:
            logger_setup.get_logger().critical('No selected ids found')
            self.destroy_dropdown()
            return
        # Figure out which table to update and which IDs to update
        if ((self.table == 'UPbAnalyses' and self.dropdown_table in ('Samples', 'Aliquots')) or
                (self.table == 'Spots' and self.dropdown_table == 'Samples')):
            if self.update_analysis_chain(selected_ids, model_indexes):
                # Update handled
                pass
        elif 'GPS' in self.dropdown_table or 'Elevation' in self.dropdown_table:
            # GPS and Elevation are updated in the GPSDialog, updated handled when dialog closed
            pass
        elif 'SampleAge' in self.dropdown_table and 'AgeSignature' not in self.dropdown_table:
            # SampleAge is updated in the AgeDialog, updated handled when dialog closed
            pass
        elif self.dropdown_table == 'Rejected' and self.table == 'UPbAnalyses':
            # Only the UPb views have an editable Rejected column
            if combo.currentText() == 'Accepted':
                value = 0
            else:
                value = 1
            query = QtS.QSqlQuery()
            if len(selected_ids) == 1:
                sql_where_str = f'= {selected_ids[0]}'
            else:
                sql_where_str = f'IN {tuple(selected_ids)}'
            if not query.exec(f'SELECT REJECTED FROM {self.table} WHERE {self.table_headers[0]} {sql_where_str}'):
                logger_setup.get_logger().critical(f'Failed to get existing value')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            existing = set()
            while query.next():
                existing.add(query.value(0))
            if len(existing) == 1 and list(existing)[0] == value:
                logger_setup.get_logger().info(f'No change to Rejected value')
                self.destroy_dropdown()
                return
            create_savepoint('before_edit_rejected')
            if not query.exec(
                    f'UPDATE {self.table} SET Rejected = {value} WHERE {self.table_headers[0]} {sql_where_str}'):
                logger_setup.get_logger().critical(
                    f'Failed to update Rejected for {selected_ids}: {query.lastError().text()}')
                rollback_savepoint('before_edit_rejected')
                self.destroy_dropdown()
                return
            release_savepoint('before_edit_rejected')
            updated = True
        else:
            edit_table, edit_ids = self.determine_edit_table(selected_ids)
            if edit_table and edit_ids:
                # Save points are in these methods
                if '_' in edit_table:
                    # Many-to-many table
                    if not combo.model().update_many_table(edit_table, edit_ids):
                        logger_setup.get_logger().info(f'{edit_table} was not updated')
                        self.destroy_dropdown()
                        return
                    updated = True
                else:
                    if isinstance(combo.model(),
                                  CheckableSqlTableModel | CheckableSqlQueryModel | CheckableTreeModel):
                        if not combo.model().update_other_table(edit_table, edit_ids):
                            logger_setup.get_logger().info(f'{edit_table} was not updated')
                            self.destroy_dropdown()
                            return
                        updated = True
                    else:
                        header = get_headers(self.combo_model.tableName())[0]
                        if header not in get_headers(edit_table):
                            header = view_headers[0]
                        if 'Abbreviation' in header:
                            header = header.replace('Abbreviation', 'ID')
                        query = QtS.QSqlQuery()
                        if len(edit_ids) == 1:
                            sql_where_str = f'= {edit_ids[0]}'
                        else:
                            sql_where_str = f'IN {tuple(edit_ids)}'
                        if combo.currentText() == '':
                            clicked_id = QtC.QVariant()
                        else:
                            clicked_id = get_id_from_name(self.combo_model.tableName(), combo.currentText())
                            if not clicked_id:
                                logger_setup.get_logger().info(f'No ID found for {combo.currentText()}')
                                self.destroy_dropdown()
                                return
                        create_savepoint('before_edit_id')
                        query.prepare(f'UPDATE "{edit_table}" SET {header} = :clicked_id WHERE {get_headers(edit_table)[0]} {sql_where_str}')
                        query.bindValue(':clicked_id', clicked_id)
                        if not query.exec():
                            logger_setup.get_logger().critical(f'Failed to update {get_readable_header(header)} for {len(edit_ids)} {edit_table}')
                            logger_setup.get_logger().debug(f'Query: {query.lastQuery()}')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                            rollback_savepoint('before_edit_id')
                            self.destroy_dropdown()
                            return
                        updated = True
                        release_savepoint('before_edit_id')
        for model_index in model_indexes:
            if not self.model.setData(model_index, combo.currentText(), QtC.Qt.ItemDataRole.EditRole):
                logger_setup.get_logger().critical(f'Error updating view')
                logger_setup.get_logger().debug(f'Error: {self.model.last_error}')
                self.destroy_dropdown()
                return
        if updated:
            self.updated = True
            for model_index in model_indexes:
                if model_index in self.model.edited_indexes:
                    self.model.edited_indexes.remove(model_index)
        if self.edit_tableView.currentIndex() == self.combo_index:
            self.tabbed_from_editor = False
        self.combo = combo
        logger_setup.get_logger().info('Data saved from dropdown')
        self.destroy_dropdown()
        return

    def destroy_dropdown(self):
        # combo.activated.disconnect(self.save_dropdown_data)
        try:
            self.combo.removeEventFilter(self)
            self.combo.view().removeEventFilter(self)
        except TypeError:
            pass
        except AttributeError:
            pass
        try:
            self.combo.add_triggered.disconnect(self.add_tag_popup)
            self.combo.edit_triggered.disconnect(self.edit_tag_popup)
        except TypeError:
            pass
        except AttributeError:
            pass
        self.edit_tableView.setIndexWidget(self.combo_index, None)
        self.combo = None
        self.dropdown_table = None
        self.combo_index = QtC.QModelIndex()

    def determine_edit_table(self, selected_ids):
        if self.combo and self.combo_index.isValid():
            view_header = self.model.headerData(self.combo_index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        elif self.lineEdit and self.edit_index.isValid():
            view_header = self.model.headerData(self.edit_index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        else:
            selected_index = self.edit_tableView.selectedIndexes()[0]
            model_index = self.proxy_model.mapToSource(selected_index)
            view_header = self.model.headerData(model_index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        for dictionary in [SQLUtils.one_editable, SQLUtils.many_editable]:
            if self.dropdown_table in dictionary[self.table].values():
                for key, values in dictionary[self.table].items():
                    if key == view_header:
                        # The dropdown table has an ID column in the current table or is in a many-to-many table with the current table
                        if dictionary is SQLUtils.many_editable:
                            table = f'{self.table}_{self.dropdown_table}'
                        else:
                            table = self.table
                        item_ids = selected_ids
                        return table, item_ids
            # The dropdown table is not directly related to the current table
            for key, values in dictionary.items():
                if self.dropdown_table in values.values():
                    for sub_key, sub_values in dictionary[key].items():
                        if sub_key == view_header:
                            if dictionary == SQLUtils.one_editable:
                                table = key
                            elif dictionary == SQLUtils.many_editable:
                                table = f'{key}_{self.dropdown_table}'
                            # We have our table to edit, but now we need to relate the IDs in the current table to the IDs in the edit table
                            edit_id_header = get_headers(table)[0]
                            if edit_id_header in self.show_cols:
                                # The ID of the edit table is in the current view, e.g. SampleID in Spots
                                item_ids = []
                                query = QtS.QSqlQuery()
                                if len(selected_ids) == 1:
                                    sql_where_str = f'= {selected_ids[0]}'
                                else:
                                    sql_where_str = f'IN {tuple(selected_ids)}'
                                if not query.exec(f'SELECT {edit_id_header} FROM {self.table} WHERE {self.table_headers[0]} {sql_where_str}'):
                                    logger_setup.get_logger().critical(f'Failed to get {edit_id_header} for {table} IDs {selected_ids}: {query.lastError().text()}')
                                    return None, None
                                while query.next():
                                    if query.value(0) not in item_ids:
                                        item_ids.append(query.value(0))
                                if not item_ids:
                                    logger_setup.get_logger().critical('No item IDs found to update')
                                    return None, None
                                return table, item_ids
                            else:
                                # The ID of the edit table is not in the current view, e.g. SpotID not in Samples
                                if self.table == 'Samples':
                                    # None of its sub-item IDs are in the current view, so we need to find the IDs of the sub-items
                                    aliquot_ids, spot_ids, upb_analysis_ids = find_sub_items(selected_ids, self.table)
                                    if table == 'Aliquots' or 'Aliquots_' in table:
                                        item_ids = aliquot_ids
                                    elif table == 'Spots' or 'Spots_' in table:
                                        item_ids = spot_ids
                                    elif table == 'UPbAnalyses' or 'UPbAnalyses_' in table:
                                        item_ids = upb_analysis_ids
                                    else:
                                        logger_setup.get_logger().error(f'No {table} for selected {self.table} IDs')
                                        return None, None
                                else:
                                    logger_setup.get_logger().error(f'Could not find ID column for {table} in {self.table}')
                                    return None, None
                                return table, item_ids

    def update_analysis_chain(self, selected_ids, model_indexes):
        sample_id = None
        aliquot_id = None
        spot_id = None
        updated = False
        for model_index in model_indexes:
            if model_index.data(QtC.Qt.ItemDataRole.DisplayRole) != self.combo.currentText():
                updated = True
        if not updated:
            logger_setup.get_logger().info('No changes to update')
            self.destroy_dropdown()
            return True
        create_savepoint('before_update_chain')
        if self.table == 'UPbAnalyses':
            if self.dropdown_table == 'Samples':
                self.table_item_ids
                sample_name = self.combo.currentText()
                sample_id = get_id_from_name('Samples', sample_name)
                if not sample_id:
                    logger_setup.get_logger().critical(f'No sample ID found for {sample_name}')
                    create_savepoint('before_update_chain')
                    self.destroy_dropdown()
                    return False
                aliquot_id = self.select_child('Samples', sample_id)
                if not aliquot_id:
                    logger_setup.get_logger().info(f'No aliquot ID selected for {sample_name}')
                    create_savepoint('before_update_chain')
                    self.destroy_dropdown()
                    return False
                spot_id = self.select_child('Aliquots', aliquot_id)
                if not spot_id:
                    logger_setup.get_logger().info(f'No spot ID selected for {sample_name}')
                    create_savepoint('before_update_chain')
                    self.destroy_dropdown()
                    return False
            elif self.dropdown_table == 'Aliquots':
                sample_id = None
                aliquot_name = self.combo.currentText()
                aliquot_id = get_id_from_name('Aliquots', aliquot_name)
                if not aliquot_id:
                    logger_setup.get_logger().critical(f'No aliquot ID found for {aliquot_name}')
                    create_savepoint('before_update_chain')
                    self.destroy_dropdown()
                    return False
                spot_id = self.select_child('Aliquots', aliquot_id)
                if not spot_id:
                    logger_setup.get_logger().info(f'No spot ID selected for {aliquot_name}')
                    create_savepoint('before_update_chain')
                    self.destroy_dropdown()
                    return False
            else:
                pass
            query = QtS.QSqlQuery()
            if len(selected_ids) == 1:
                sql_where = f'= {selected_ids[0]}'
            elif len(selected_ids) > 1:
                sql_where = f'IN {tuple(selected_ids)}'
            if not query.exec(f'UPDATE UPbAnalyses SET SpotID = {spot_id} WHERE UPbAnalysisID {sql_where}'):
                logger_setup.get_logger().critical(f'Failed to update Spot Name for {sample_name}')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                rollback_savepoint('before_update_chain')
                self.destroy_dropdown()
                return False
            self.updated = True
        elif self.table == 'Spots':
            if self.dropdown_table == 'Samples':
                sample_name = self.combo.currentText()
                sample_id = get_id_from_name('Samples', sample_name)
                if not sample_id:
                    logger_setup.get_logger().critical(f'No sample ID found for {sample_name}')
                    create_savepoint('before_update_chain')
                    self.destroy_dropdown()
                    return False
                aliquot_id = self.select_child('Samples', sample_id)
                if not aliquot_id:
                    logger_setup.get_logger().info(f'No aliquot ID selected for {sample_name}')
                    create_savepoint('before_update_chain')
                    self.destroy_dropdown()
                    return False
            else:
                pass
            query = QtS.QSqlQuery()
            if len(selected_ids) == 1:
                sql_where = f'= {selected_ids[0]}'
            elif len(selected_ids) > 1:
                sql_where = f'IN {tuple(selected_ids)}'
            if not query.exec(f'UPDATE Spots SET AliquotID = {aliquot_id} WHERE SpotID {sql_where}'):
                logger_setup.get_logger().critical(f'Failed to update Spot Name for {sample_name}')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                create_savepoint('before_update_chain')
                self.destroy_dropdown()
                return False
            self.updated = True
        else:
            pass
        spot_column = None
        aliquot_column = None
        sample_column = None
        for header in self.show_cols:
            if 'SpotName' in header:
                spot_column = self.show_cols.index(header)
            if 'AliquotName' in header:
                aliquot_column = self.show_cols.index(header)
            if 'SampleName' in header:
                sample_column = self.show_cols.index(header)
        for model_index in model_indexes:
            if spot_column is not None and spot_id is not None:
                update_index = self.model.index(model_index.row(), spot_column)
                if not self.model.setData(update_index, get_name_from_id('Spots', spot_id),
                                          QtC.Qt.ItemDataRole.EditRole):
                    logger_setup.get_logger().critical(f'Error updating view')
                    logger_setup.get_logger().debug(f'Error: {self.model.last_error}')
                    create_savepoint('before_update_chain')
                    self.destroy_dropdown()
                    return False
                self.model.edited_indexes.remove(update_index)
            if aliquot_column is not None and aliquot_id is not None:
                update_index = self.model.index(model_index.row(), aliquot_column)
                if not self.model.setData(update_index, get_name_from_id('Aliquots', aliquot_id),
                                          QtC.Qt.ItemDataRole.EditRole):
                    logger_setup.get_logger().critical(f'Error updating view')
                    logger_setup.get_logger().debug(f'Error: {self.model.last_error}')
                    create_savepoint('before_update_chain')
                    self.destroy_dropdown()
                    return False
                self.model.edited_indexes.remove(update_index)
            if sample_column is not None and sample_id is not None:
                update_index = self.model.index(model_index.row(), sample_column)
                if not self.model.setData(update_index, get_name_from_id('Samples', sample_id),
                                          QtC.Qt.ItemDataRole.EditRole):
                    logger_setup.get_logger().critical(f'Error updating view')
                    logger_setup.get_logger().debug(f'Error: {self.model.last_error}')
                    create_savepoint('before_update_chain')
                    self.destroy_dropdown()
                    return False
                self.model.edited_indexes.remove(update_index)
        release_savepoint('before_update_chain')
        return True

    def select_child(self, parent_table, parent_id):
        # Open a dialog to select the child item
        if parent_table == 'Samples':
            child_table = 'Aliquots'
        elif parent_table == 'Aliquots':
            child_table = 'Spots'
        else:
            return False
        parent_id_header = get_headers(parent_table)[0]
        child_id_header = get_headers(child_table)[0]
        table_model = CheckableSqlTableModel()
        set_table(table_model, child_table)
        table_model.setFilter(f'{parent_id_header} = {parent_id}')
        if child_table == 'Aliquots':
            tree_model = CheckableTreeModel()
            tree_model.setSourceModel(table_model)
            child_combo = CheckableTreeCombobox()
            child_combo.set_single_click(True)
            child_combo.setModel(tree_model)
            child_combo.setModelColumn(0)
            child_combo.setCurrentText('')
            dlg = SetSelectedValues(self, child_combo)
            dlg.setWindowTitle(f'Select {child_table} for {parent_table}')
            if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
                child_combo = dlg.widget
            tree_model = child_combo.model()
            checked_ids = tree_model.traverse_checkable_tree(QtC.QModelIndex())[0]
        else:
            proxy_model = ReadableProxyModel()
            proxy_model.setSourceModel(table_model)
            proxy_model.sort(get_name_column(child_table), QtC.Qt.SortOrder.AscendingOrder)
            child_combo = CheckableComboBox()
            child_combo.set_single_click(True)
            child_combo.setModel(proxy_model)
            child_combo.setModelColumn(get_name_column(child_table))
            child_combo.setCurrentText('')
            dlg = SetSelectedValues(self, child_combo)
            dlg.setWindowTitle(f'Select {child_table} for {parent_table}')
            if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
                child_combo = dlg.widget
            table_model = child_combo.model()
            checked_ids = table_model.checked_ids
        if len(checked_ids) > 1:
            logger_setup.get_logger().error('Multiple items selected, please select only one')
            return None
        elif len(checked_ids) == 0:
            logger_setup.get_logger().info('No items selected')
            return None
        else:
            child_id = checked_ids[0]
            return child_id

    def set_selected_value_dialog(self, table, indexes):
        # Open a dialog to set the selected value for the indexes
        selected_value = ''
        current_values = []
        for index in indexes:
            model_index = self.proxy_model.mapToSource(index)
            current_values.append(model_index.data(QtC.Qt.ItemDataRole.DisplayRole))

    def clear_data(self):
        logger_setup.get_logger().info('Clearing selected values')
        if self.lineEdit is not None:
            self.save_lineedit_data()
        if self.combo is not None:
            self.save_dropdown_data()
        indexes = self.edit_tableView.selectedIndexes()
        columns = {}
        rows = []
        for index in indexes:
            header = self.model.headerData(index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            if header in SQLUtils.not_null[self.table]:
                logger_setup.get_logger().error(f'{get_readable_header(header)} cannot be empty')
                return
            query, virtual, stored, db_columns = get_columns(self.table)
            if f'"{header}"' in virtual or f'"{header}"' in stored:
                logger_setup.get_logger().error(f'{get_readable_header(header)} is auto-generated')
                return
            if header not in columns.keys():
                columns[header] = []
            model_index = self.proxy_model.mapToSource(index)
            rows.append(model_index.row())
            id = self.model.index(model_index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole)
            if id not in columns[header]:
                columns[header].append(id)
        if not columns:
            logger_setup.get_logger().error('No selected IDs found')
            return
        create_savepoint('before_clear')
        # If any of the headers are in the list of GPS headers or age headers, check if the user wants to apply one value to all selected items
        if any(header in self.gps_headers for header in columns.keys()):
            response = self.msg.warning(self, 'Clear GPS', 'Do you want to clear the GPS columns for all selected items?', QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No, QtW.QMessageBox.StandardButton.No)
            if response == QtW.QMessageBox.StandardButton.No:
                rollback_savepoint('before_clear')
                return
            elif response == QtW.QMessageBox.StandardButton.Yes:
                # Set the GPSLocationID to null for all selected items
                # Only relevant for Samples and Columns
                edit_ids = []
                for gps_header in self.gps_headers:
                    if gps_header in columns.keys():
                        edit_ids = columns[gps_header]
                        break
                if not edit_ids:
                    logger_setup.get_logger().error('No IDs found to clear')
                    rollback_savepoint('before_clear')
                    return
                gps_id_header = None
                for table_header in self.table_headers:
                    if 'GPSLocationID' in table_header:
                        gps_id_header = table_header
                        break
                if not gps_id_header:
                    logger_setup.get_logger().error('No GPS ID header found')
                    rollback_savepoint('before_clear')
                    return
                create_savepoint('before_clear_gps')
                query = QtS.QSqlQuery()
                if len(edit_ids) == 1:
                    sql_where_str = f'= {edit_ids[0]}'
                elif len(edit_ids) > 1:
                    sql_where_str = f'IN {tuple(edit_ids)}'
                if not query.exec(f'UPDATE {self.table} SET {gps_id_header} = NULL WHERE {self.table_headers[0]} {sql_where_str}'):
                    logger_setup.get_logger().critical(f'Failed to clear GPS for {self.table} {edit_ids}: {query.lastError().text()}')
                    rollback_savepoint('before_clear_gps')
                    rollback_savepoint('before_clear')
                    return
                release_savepoint('before_clear_gps')
                for gps_header in self.gps_headers:
                    # Set the model data to blank for the gps headers of selected items
                    col = self.show_cols.index(gps_header)
                    for row in rows:
                        self.model.setData(self.model.index(row, col), '', QtC.Qt.ItemDataRole.EditRole)
                    if gps_header in columns.keys():
                        del columns[gps_header]
        if any(header in self.age_headers for header in columns.keys()):
            response = self.msg.warning(self, 'Clear Sample Age', 'Do you want to clear all sample age columns for all selected items?', QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No, QtW.QMessageBox.StandardButton.No)
            if response == QtW.QMessageBox.StandardButton.No:
                rollback_savepoint('before_clear')
                return
            elif response == QtW.QMessageBox.StandardButton.Yes:
                # Set the SampleAgeID to null for all selected samples and remove all Samples_SampleAge rows for the selected samples
                # Only relevant for Samples
                edit_ids = []
                for age_header in self.age_headers:
                    if age_header in columns.keys():
                        edit_ids = columns[age_header]
                        break
                if not edit_ids:
                    logger_setup.get_logger().error(f'No {self.table_headers[0]}s found to clear')
                    rollback_savepoint('before_clear')
                    return
                create_savepoint('before_clear_sample_age')
                query = QtS.QSqlQuery()
                if len(edit_ids) == 1:
                    sql_where_str = f'= {edit_ids[0]}'
                elif len(edit_ids) > 1:
                    sql_where_str = f'IN {tuple(edit_ids)}'
                if not query.exec(f'UPDATE {self.table} SET DefaultSampleAgeID = NULL WHERE {self.table_headers[0]} {sql_where_str}'):
                    logger_setup.get_logger().critical(f'Failed to clear SampleAge for {self.table} {edit_ids}: {query.lastError().text()}')
                    rollback_savepoint('before_clear_sample_age')
                    rollback_savepoint('before_clear')
                    return
                if not query.exec(f'DELETE FROM Samples_SampleAge WHERE SampleID {sql_where_str}'):
                    logger_setup.get_logger().critical(f'Failed to clear SampleAge for {self.table} {edit_ids}: {query.lastError().text()}')
                    rollback_savepoint('before_clear_sample_age')
                    rollback_savepoint('before_clear')
                    return
                release_savepoint('before_clear_sample_age')
                for age_header in self.age_headers:
                    # Set the model data to blank for the age headers of selected items
                    col = self.show_cols.index(age_header)
                    for row in rows:
                        self.model.setData(self.model.index(row, col), '', QtC.Qt.ItemDataRole.EditRole)
                    if age_header in columns.keys():
                        del columns[age_header]
        for column, ids in columns.items():
            # Set the selection to a single column
            edit_indexes = []
            for index in indexes:
                model_index = self.proxy_model.mapToSource(index)
                header = self.model.headerData(model_index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
                if header == column:
                    edit_indexes.append(index)
            if not edit_indexes:
                logger_setup.get_logger().error('No indexes found to clear')
                rollback_savepoint('before_clear')
                return
            if edit_indexes != self.edit_tableView.selectedIndexes():
                # The indexes we need to edit are not the same as the currently selected indexes, so we need to update the selection
                # Disconnect the selection model to prevent methods from triggering
                try:
                    self.edit_tableView.selectionModel().currentChanged.disconnect(self.on_index_change)
                except TypeError:
                    pass
                # Clear the selection
                self.edit_tableView.selectionModel.clearSelection()
                selection = QtC.QItemSelection()
                # Select the indexes to edit
                for index in edit_indexes:
                    selection.select(index, index)
                self.edit_tableView.selectionModel.select(selection, QtC.QItemSelectionModel.SelectionFlag.Select)
                # Reconnect the selection model signal
                self.edit_tableView.selectionModel().selectionChanged.connect(self.on_index_change)
            # Determine which widget to create and display
            self.determine_widget(model_index)
            if self.lineEdit is not None:
                # Clear the line edit
                self.lineEdit.setText('')
                self.save_lineedit_data()
            elif self.combo is not None:
                # Clear the combo box checks
                if isinstance(self.combo_model, CheckableSqlTableModel | CheckableSqlQueryModel):
                    self.combo_model.clear_checks()
                elif isinstance(self.combo_model, CheckableTreeModel):
                    self.combo_model.clear_checks(QtC.QModelIndex())
                self.combo.setCurrentIndex(-1)
                self.save_dropdown_data()

    def delete_question(self, delete_ids):
        msg_box = QtW.QMessageBox()
        msg_box.setIcon(QtW.QMessageBox.Icon.Question)
        if self.table == 'Samples':
            # Samples have a special case where they are related to Aliquots, Spots, and UPbAnalyses
            aliquot_ids, spot_ids, upb_analysis_ids = find_sub_items(delete_ids, self.table)
            msg_box.setText(f'Are you sure you want to delete these {len(delete_ids)} {self.table}?\n'
                            f'Associated with {len(aliquot_ids)} aliquots, {len(spot_ids)} spots, and {len(upb_analysis_ids)} U-Pb analyses')
        elif self.table == 'Spots':
            # Spots have a special case where they are related to UPbAnalyses
            upb_analysis_ids = find_sub_items(delete_ids, self.table)
            msg_box.setText(f'Are you sure you want to delete these {len(delete_ids)} {self.table}?\n'
                            f'Associated with {len(upb_analysis_ids)} U-Pb analyses')
        else:
            msg_box.setText(f'Are you sure you want to delete these {len(delete_ids)} {self.table}?')
        msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

    def advance_tab(self):
        currentIndex = self.edit_tableView.currentIndex()
        if currentIndex.isValid():
            if currentIndex.column() == self.proxy_model.columnCount() - 1:
                if currentIndex.row() == self.proxy_model.rowCount() - 1:
                    # advance to the beginning of the table
                    next_index = self.proxy_model.index(0, 0)
                else:
                    # advance to the beginning of the next row
                    next_index = self.proxy_model.index(currentIndex.row() + 1, 0)
            else:
                # advance to the next column
                next_index = self.proxy_model.index(currentIndex.row(), currentIndex.column() + 1)
            if next_index.isValid():
                self.edit_tableView.setCurrentIndex(next_index)
                self.tabbed_from_editor = True

    def reverse_tab(self):
        currentIndex = self.edit_tableView.currentIndex()
        if currentIndex.isValid():
            if currentIndex.column() == 1:
                # ID column is hidden, so can't go back to it
                if currentIndex.row() == 0:
                    # reverse to the end of the table
                    next_index = self.model.index(self.model.rowCount() - 1, self.model.columnCount() - 1)
                else:
                    # reverse to the end of the previous row
                    next_index = self.model.index(currentIndex.row() - 1, self.model.columnCount() - 1)
            else:
                # reverse to the next column
                next_index = self.model.index(currentIndex.row(), currentIndex.column() - 1)
            if next_index.isValid():
                self.edit_tableView.setCurrentIndex(next_index)
                self.tabbed_from_editor = True

    def on_index_change(self, selected, deselected):
        # Close and save the data from any open widgets
        if self.combo is not None:
            self.save_dropdown_data()
        if self.lineEdit is not None:
            self.destroy_lineedit()

    def on_row_change(self, selected, deselected):
        # Close and save the data from any open widgets
        if self.combo is not None:
            self.save_dropdown_data()
        if self.lineEdit is not None:
            self.save_lineedit_data()
        if deselected.row() == -1:
            # No previous row was selected, so no changes to save
            return True
        logger_setup.get_logger().info('Row changed')
        column = None
        def highlight_error():
            if column is not None:
                index = self.model.index(self.model.edited_indexes[0].row(), column)
                if index.isValid():
                    self.edit_tableView.selectionModel().select(index, QtC.QItemSelectionModel.SelectionFlag.Select)
            else:
                selection = QtC.QItemSelection(self.model.index(self.model.edited_indexes[0].row(), 0),
                                                 self.model.index(self.model.edited_indexes[0].row(), self.model.columnCount() - 1))
                self.edit_tableView.selectionModel().select(selection,
                                                            QtC.QItemSelectionModel.SelectionFlag.ClearAndSelect | QtC.QItemSelectionModel.SelectionFlag.Rows)
            self.edit_tableView.scrollTo(self.model.edited_indexes[0])
            self.edit_tableView.setFocus()

        # Check if the row has changed and if the model has been edited
        if selected.row() != deselected.row():
            if not self.model.edited_indexes:
                logger_setup.get_logger().info('No changes to save')
                return True
            if not self.data_submit():
                # There was an error submitting the changes
                QtC.QTimer.singleShot(0, highlight_error)
                return False
            else:
                self.updated = True
                return True

    def data_submit(self):
        logger_setup.get_logger().info('Submitting changes')
        row = self.model.edited_indexes[0].row()
        row_id = self.model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole)
        row_id_header = self.table_headers[0]
        update_cols = {}
        update_col_values = {}
        where_col_ids = {}
        for key in SQLUtils.one_editable.keys():
            update_cols[key] = []
            update_col_values[key] = []
            where_col_ids[key] = []
        query = QtS.QSqlQuery()
        for model_index in self.model.edited_indexes:
            header = self.model.headerData(model_index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            header_found = False
            if 'GPS' in header or 'Elevation' in header and not header_found:
                # Already handled in the GPSDialog
                header_found = True
                continue
            elif 'SampleAgeCalculated' in header and not header_found:
                # Already handled in the AgeDialog
                header_found = True
                continue
            elif 'Rejected' in header and not header_found:
                text = model_index.data(QtC.Qt.ItemDataRole.DisplayRole)
                if text == 'Accepted':
                    update_cols['UPbAnalyses'].append('Rejected')
                    update_col_values['UPbAnalyses'].append(0)
                elif text == 'Rejected':
                    update_cols['UPbAnalyses'].append('Rejected')
                    update_col_values['UPbAnalyses'].append(1)
                else:
                    update_cols['UPbAnalyses'].append('Rejected')
                    update_col_values['UPbAnalyses'].append('Null')
                if not query.exec(f'SELECT UPbAnalysisID FROM UPbAnalyses WHERE {self.show_cols[0]} = {row_id}'):
                    logger_setup.get_logger().critical(f'Error: changes not commited')
                    logger_setup.get_logger().debug(f'Failed to get UPbAnalysisID for {row_id}')
                    logger_setup.get_logger().debug(f'{query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    return False
                while query.next():
                    where_col_ids['UPbAnalyses'].append(query.value(0))
                header_found = True
            elif header in ['SampleName', 'AliquotName', 'SpotName', 'ColumnName'] and not header_found:
                if header.split('Name')[0] in self.table :
                    # This is the name column for this table
                    text = self.model.index(row, model_index.column()).data(QtC.Qt.ItemDataRole.DisplayRole)
                    update_cols[self.table].append(header)
                    update_col_values[self.table].append(text)
                    header_found = True
                else:
                    # We need to look at two tables
                    other_table = f'{header.split("Name")[0]}s'
                    other_name_header = header
                    other_id_header = get_headers(other_table)[0]
                    other_item_name = model_index.data(QtC.Qt.ItemDataRole.DisplayRole)
                    for db_header in self.table_headers:
                        # Look for an ID column for the other table
                        if other_id_header == db_header or other_id_header in db_header:
                            # Edit the current table with the ID of the other table
                            other_id = 'Null'
                            if not query.exec(f'SELECT {other_id_header} FROM {other_table} WHERE {other_name_header} = "{other_item_name}"'):
                                logger_setup.get_logger().critical(f'Failed to get {other_id_header} for {other_item_name}: {query.lastError().text()}')
                                return False
                            if query.next():
                                other_id = query.value(0)
                            update_cols[self.table].append(db_header)
                            update_col_values[self.table].append(other_id)
                            header_found = True
                            break
                    if not header_found:
                        for db_header in get_headers(other_table):
                            # Look for an ID column for this table in the other table
                            if row_id_header == db_header or row_id_header in db_header:
                                # Edit the other table with the ID of this table
                                update_cols[other_table].append(db_header)
                                update_col_values[other_table].append(row_id)
                                header_found = True
                                break
                    if not header_found:
                        logger_setup.get_logger().critical(f'Could not find columns to update {get_readable_header(header)}')
                        return False
            else:
                if not header_found:
                    for key, values in SQLUtils.non_editable.items():
                        if header in values:
                            # This column is non-editable
                            header_found = True
                            continue
                if not header_found:
                    for key, values in SQLUtils.many_editable.items():
                        if header in values.keys():
                            # This is a many-to-many relationship and was committed when the dropdown was destroyed
                            header_found = True
                            continue
                if not header_found:
                    for key, values in SQLUtils.one_editable.items():
                        for col_key in values.keys():
                            if header == col_key:
                                text = model_index.data(QtC.Qt.ItemDataRole.DisplayRole)
                                if text == '' or text is None:
                                    id = 'Null'
                                else:
                                    id = self.retrieve_id(values[header], text)
                                    if not id:
                                        continue
                                update_cols[key].append(header)
                                update_col_values[key].append(id)
                                if key != self.table:
                                    # todo: figure out how to get the correct IDs for the where clause
                                    pass
                                header_found = True
                                continue
                if not header_found:
                    # header is editable but does not need to be converted to an ID
                    text = model_index.data(QtC.Qt.ItemDataRole.DisplayRole)
                    if text == '' or text is None:
                        # empty string, so save it as a null
                        text = QtC.QVariant()
                    elif isinstance(text, str) and text.isdigit():
                        # string of an integer, so save it as an integer
                        text = int(text)
                    elif isinstance(text, str) and text.isdecimal():
                        # string of a decimal, so save it as a decimal
                        text = float(text)
                    for view in SQLUtils.views:
                        table = get_table_from_view(view)
                        table_headers = get_headers(table)
                        if header in table_headers:
                            break
                    if header not in update_cols[table]:
                        update_cols[table].append(header)
                        update_col_values[table].append(text)
        for table in update_cols.keys():
            if update_col_values[table]:
                sql_cols = ', '.join(update_cols[table])
                table_headers = get_headers(table)
                # todo: figure out updating the ids for the table
                if table == self.table:
                    item_ids = [self.model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole)]
                else:
                    id_col = get_headers(table)[0]
                    item_id = self.retrieve_id(table, id_col)
                sql_values = ", ".join(str(s) for s in update_col_values[table])
                query.prepare(f'UPDATE "{table}" SET {sql_cols} = {sql_values} WHERE {table_headers[0]} = {item_id}')
                if not query.exec():
                    logger_setup.get_logger().critical(f'Failed to update {table}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                    return False
                logger_setup.get_logger().info(f'Updated {sql_cols} to {', '.join(str(val) for val in update_col_values[table])} in {table} where {table_headers[0]} = {item_id}')
        logger_setup.get_logger().info('Changes submitted')
        self.model.edited_indexes = []
        return True

    def retrieve_id(self, table, value):
        if value == '':
            return 'Null'
        table_headers = get_headers(table)
        id_header = table_headers[0]
        query = QtS.QSqlQuery()
        if not query.exec(f'SELECT {id_header} FROM {table} WHERE {table_headers[get_name_column(table)]} = "{value}"'):
            logger_setup.get_logger().critical(f'Failed to get ID for {value}: {query.lastError().text()}')
            return None
        if query.next():
            return query.value(0)
        else:
            logger_setup.get_logger().critical(f'{get_name_column(table)} {value} not found in {table}')
            return None

    def add_popup(self):
        if not self.on_row_change(QtC.QModelIndex(), self.edit_tableView.currentIndex()):
            logger_setup.get_logger().critical(f'Failed to submit changes to {self.table}')
            return
        if self.table == '"References"' or self.table == 'References':
            self.loading_manager.show_loading_dialog('Loading', f'Opening add window for {self.table}...')
            dlg = NewReference(self)
        else:
            self.loading_manager.show_loading_dialog('Loading', f'Opening add window for {self.table}...')
            dlg = AddTags(self, self.table)
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
            self.loading_manager.show_loading_dialog('Loading', f'Loading...')
            self.find_added(dlg.ids_added)
        self.display_table()

    def find_added(self, ids_added):
        if not ids_added:
            return
        query = QtS.QSqlQuery()
        for id in ids_added:
            if not query.exec(f'SELECT {", ".join(self.show_cols)} FROM {self.table} WHERE {self.table_headers[0]} = {id}'):
                logger_setup.get_logger().critical(f'Could not find new {self.table}')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                return
            if query.next():
                row = []
                for i in range(query.record().count()):
                    row.append(query.value(i))
                self.model.insertRow(row)
            else:
                logger_setup.get_logger().critical(f'No new {self.table} in the database')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        logger_setup.get_logger().info(f'Updated {self.table}')

    def add_tag_popup(self, combo: QtW.QComboBox, action: QtG.QAction | None = None):
        if isinstance(combo.model(), TreeModel):
            table = combo.model().table
        else:
            table = combo.model().tableName()
        dlg = None
        if table in SQLUtils.user_viewable_trees:
            save_expanded_state(table, combo.model(), combo.view())
            dlg_args = add_tree_popup(combo.view(), action)
            if dlg_args:
                dlg = AddTreeTags(self, table, **dlg_args)
            else:
                dlg = AddTreeTags(self, table)
        else:
            dlg = AddTags(self, table)
        if not dlg:
            return
        logger_setup.get_logger().info(f"Showing {table} add dialog")
        self.loading_manager.show_loading_dialog('Loading', f'Opening add window for {self.table}...')
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
            # Clear and recreate this combo box
            self.loading_manager.show_loading_dialog('Loading', f'Loading...')
            self.destroy_dropdown()
            self.display_widget()
            self.combo.showPopup()
            self.loading_manager.close_loading_dialog('Loading', f'Loading...')

    def edit_tag_popup(self):
        combo = self.sender()
        if isinstance(combo.model(), TreeModel):
            table = combo.model().table
        else:
            table = combo.model().tableName()
        if table in SQLUtils.user_viewable_trees:
            dlg = EditTree(self, table)
        else:
            dlg = EditTable(self, table)
        if dlg is None:
            return
        logger_setup.get_logger().info(f"Showing {table} edit dialog")
        self.loading_manager.show_loading_dialog('Loading', f'Opening edit window for {self.table}...')
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
            # Clear and recreate this combo box
            self.loading_manager.show_loading_dialog('Loading', f'Loading...')
            self.destroy_dropdown()
            self.display_widget()
            self.combo.showPopup()
            self.loading_manager.close_loading_dialog('Loading', f'Loading...')

    def rollback(self):
        rollback_savepoint('before_edit')
        self.reject()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        release_savepoint('before_edit')
        self.accept()
        self.msg.information(self, 'Success', 'Changes saved', QtW.QMessageBox.StandardButton.Ok)
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False
        self.accept()

    def commit_question(self):
        if not self.on_row_change(QtC.QModelIndex(), self.edit_tableView.currentIndex()):
            logger_setup.get_logger().critical('Failed to save changes')
            return
        if len(self.model.edited_indexes) >= 0:
            self.updated = True
        if self.updated:
            msg_box = QtW.QMessageBox()
            msg_box.setIcon(QtW.QMessageBox.Icon.Question)
            msg_box.setText('Are you sure you want to commit all changes to the database?')
            msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
            response = msg_box.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                self.commit()
            else:
                pass
        else:
            self.rollback()

    def discard_question(self):
        if not self.on_row_change(QtC.QModelIndex(), self.edit_tableView.currentIndex()):
            logger_setup.get_logger().critical('Failed to save changes')
            return
        if len(self.model.edited_indexes) > 0:
            self.updated = True
        if self.updated:
            self.msg.question(self, 'Discard changes', 'Are you sure you want to discard all changes?',QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
            self.msg.setDefaultButton(QtW.QMessageBox.StandardButton.No)
            response = self.msg.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                self.rollback()
            else:
                pass
        else:
            self.rollback()

    def close(self):
        self.saveWindowState()
        if not self.close_by_dialog:
            if not self.on_row_change(QtC.QModelIndex(), self.edit_tableView.currentIndex()):
                logger_setup.get_logger().critical('Failed to save changes')
                self.discard_question()
            elif self.updated or len(self.model.edited_indexes) > 0:
                self.discard_question()
        else:
            logger_setup.get_logger().info(f'Closing {self.table} edit dialog')
            super().close()

    def saveWindowState(self):
        settings.setValue("ui/EditView/pos", self.pos())
        settings.setValue("ui/EditView/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/EditView/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/EditView/size", defaultValue=QSize(810, 569)))

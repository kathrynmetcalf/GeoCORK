import os
import sys
import time
from operator import index, itemgetter

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import QPoint, QSize, QSortFilterProxyModel
from PyQt6.uic import loadUi
import Functions.Text_manipulations as TxM
import logger_setup
import difflib
from Functions.Widget_classes import (
    TreeModel, CheckableTreeCombobox, CheckableTreeModel, CheckableTreeView, ReadableProxyModel, DisplayRoundedModel,
    SQLiteTableModel, CheckableComboBox, CheckableSqlTableModel, CheckableSqlQueryModel, get_headers, get_name_column,
    set_table, VerifiableSqlTableModel, VerifiableSqlViewModel, populate_many_combo_checks, populate_model_checks,
    WordWrapDelegate, get_columns, get_table_from_view, find_sub_items, get_total_records, get_record_index,
    get_id_from_name, add_tree_popup, save_expanded_state, restore_expanded_state
)
from Functions import SQLUtils
from Functions.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint, SavepointManager
from Functions.Settings_manager import settings
from Functions.Database_manager import update_database
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

        logger_setup.get_logger().info(f'Creating a new EditView for {table_name}')
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "EditTable.ui")
        loadUi(sources_ui_file, self)
        self.setModal(True)
        self.setWindowTitle(f'Edit {TxM.add_spaces_camel(table_name)}')
        self.updated = False

        self.add_pushButton.setAutoDefault(False)
        self.commit_pushButton.setAutoDefault(False)
        self.cancel_pushButton.setAutoDefault(False)

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
        self.view = None
        self.model = None
        self.proxy_model = None
        self.name_column = None
        self.name_header = None
        self.updated_timestamp = None
        self.show_cols = []
        self.where = ''
        if self.table in SQLUtils.trigger_tables:
            if self.table == 'Columns':
                self.view = 'ColumnEditView'
                self.show_cols = settings.value('column_edit_columns')
                self.add_pushButton.clicked.connect(self.add_popup)
            elif self.table == 'Samples':
                self.view = 'SampleEditView'
                self.show_cols = settings.value('sample_edit_columns')
                self.add_pushButton.hide()
            elif self.table == 'Spots' or self.table == 'UPbAnalyses':
                self.parent_id_header = 'SampleID' if self.parent_type == 'Sample' else 'AliquotID' if self.parent_type == 'Aliquot' else 'SpotID' if self.parent_type == 'Spot' else None
                if self.table == 'Spots':
                    self.view = 'SpotEditView'
                    self.show_cols = settings.value('spot_edit_columns')
                elif self.table == 'UPbAnalyses':
                    self.view = 'UPbEditView'
                    self.show_cols = settings.value('upb_analysis_edit_columns')
                if self.parent_id_header:
                    self.where = f' WHERE {self.parent_id_header} = {self.parent_id}'
                self.add_pushButton.hide()
        elif self.table == 'References':
            self.view = 'ReferenceView'
            self.show_cols = settings.value('reference_view_columns')
            self.add_pushButton.clicked.connect(self.add_popup)
        if self.table_item_ids is not None:
            if len(self.table_item_ids) == 1:
                sql_where_str = f'= {self.table_item_ids[0]}'
            else:
                sql_where_str = f'IN {tuple(self.table_item_ids)}'
            if self.where == '':
                self.where = f' WHERE {self.show_cols[0]} {sql_where_str}'
            else:
                self.where = f'{self.where} AND {self.show_cols[0]} {sql_where_str}'
        self.create_model()
        self.combo = None
        self.combo_index = QtC.QModelIndex()
        self.combo_model = None
        self.dropdown_table = None
        self.lineEdit = None
        self.msg = QtW.QMessageBox(self)
        self.close_by_dialog = False
        self.tabbed_from_editor = False

        self.view_headers = []
        if self.view is not None:
            self.view_headers = get_headers(self.view)
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
        self.commit_pushButton.clicked.connect(self.commit)
        self.cancel_pushButton.clicked.connect(self.rollback)
        self.edit_tableView.selectionModel().currentRowChanged.connect(self.on_row_change)
        self.edit_tableView.doubleClicked.connect(self.display_widget)
        # self.goto_line_edit.textChanged.connect(self.go_to_record)
        self.prev_button.clicked.connect(self.previous_page)
        self.next_button.clicked.connect(self.next_page)
        self.show_per_page_comboBox.currentIndexChanged.connect(self.change_rows_per_page)

        self.loading_manager.close_loading_dialog('Loading', f'Opening edit window for {self.table}...')

    def create_model(self):
        self.model = SQLiteTableModel(f'''
            SELECT {', '.join(self.show_cols)} FROM {self.view} {self.where} LIMIT {self.rows_per_page} 
            OFFSET {self.current_page * self.rows_per_page}
                                      ''')

        self.display_table()
        self.updated_timestamp = time.time()

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

    def next_page(self):
        """
        Slot to move to the next page for the displayed table
        """
        if (self.current_page + 1) * self.rows_per_page < self.total_records:
            self.current_page += 1
            self.create_model()

    def previous_page(self):
        """
        Slot to move to the previous page for the displayed table
        """
        if self.current_page > 0:
            self.current_page -= 1
            self.create_model()

    def eventFilter(self, object, event):
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
        if action == clear_action:
            self.clear_data()
        elif action == set_selected_action:
            self.determine_widget(indexes[0])
            if self.lineEdit:
                dlg = SetSelectedValues(self, self.lineEdit)
                if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
                    self.lineEdit = dlg.widget
                    self.save_lineedit_data()
                else:
                    self.destroy_lineedit()
            elif self.combo:
                dlg = SetSelectedValues(self, self.combo)
                if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
                    self.combo = dlg.widget
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
        logger_setup.get_logger().info(f'Displaying {self.table} table')
        self.loading_manager.show_loading_dialog('Loading', f'Displaying {self.table}...')
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.name_column = get_name_column(self.table)
        proxy_name_column = None
        if self.name_column:
            self.name_header = get_headers(self.table)[self.name_column]
            for column in range(self.proxy_model.columnCount()):
                header = self.model.headerData(column, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
                if header == self.name_header:
                    proxy_name_column = column
                    break
        if proxy_name_column:
            self.proxy_model.sort(proxy_name_column, QtC.Qt.SortOrder.AscendingOrder)
        self.edit_tableView.setModel(self.proxy_model)
        for column in range(self.proxy_model.columnCount()):
            header = self.model.headerData(column, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            if 'ID' in header:
                self.edit_tableView.hideColumn(column)
        self.edit_tableView.resizeColumnsToContents()
        self.edit_tableView.setSortingEnabled(True)
        self.edit_tableView.setWordWrap(True)
        self.edit_tableView.setTextElideMode(QtC.Qt.TextElideMode.ElideNone)  # Prevent text truncation
        self.edit_tableView.setItemDelegate(WordWrapDelegate(self.edit_tableView))

        self.edit_tableView.resizeRowsToContents()
        self.edit_tableView.verticalHeader().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)

        self.total_records = get_total_records(self.table)
        self.page_info_label.setText(
            f'{self.current_page * self.rows_per_page + 1}-{(self.current_page + 1) * self.rows_per_page} of {self.total_records}')
        self.goto_line_edit.clear()
        self.goto_line_edit.setPlaceholderText(f'Go to {self.name_header}...')

        # Optimize window resizing
        self.resize_timer = QtC.QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.resizeRowsOptimized)

        # Connect resizing events
        self.edit_tableView.horizontalHeader().sectionResized.connect(self.optimizeVerticalResize)
        self.edit_tableView.verticalHeader().sectionResized.connect(self.optimizeVerticalResize)

        self.loading_manager.close_loading_dialog('Loading', f'Displaying {self.table}...')
        logger_setup.get_logger().info(f'Display {self.table} table complete')

    def display_widget(self):
        if len(self.edit_tableView.selectedIndexes()) == 0:
            return
        elif len(self.edit_tableView.selectedIndexes()) > 1:
            logger_setup.get_logger().error('Right-click to edit multiple selections')
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
        if model_index.column() == self.name_column:
            # The column is the name column for the table. This should be edited with a line edit.
            self.create_lineedit()
            return
        header = self.model.headerData(model_index.column(), QtC.Qt.Orientation.Horizontal,
                                       QtC.Qt.ItemDataRole.DisplayRole)
        if 'GPS' in header or 'Elevation' in header:
            if not self.tabbed_from_editor:
                # Do not open the popup if tabbing here, only when double-clicking
                item_ids = []
                row = model_index.row()
                item_ids.append(self.model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole))
                dlg = GPSDialog(self.table, item_ids, self)
                dlg.exec()
                logger_setup.get_logger().info(f'Repopulating {header} for {item_ids[0]}')
                query = QtS.QSqlQuery()
                if not query.exec(f'SELECT {', '.join(self.gps_headers)} FROM {self.view} WHERE {self.view_headers[0]} = {item_ids[0]}'):
                    logger_setup.get_logger().critical(f'Failed to get {header} for {item_ids[0]}: {query.lastError().text()}')
                    return
                if query.next():
                    for header in self.gps_headers:
                        col = self.show_cols.index(header)
                        self.model.setData(self.model.index(row, col), query.value(header), QtC.Qt.ItemDataRole.EditRole)
                        self.updated_timestamp = time.time()
                        logger_setup.get_logger().info(f'New value: {self.model.index(row, col).data(QtC.Qt.ItemDataRole.DisplayRole)}')
            else:
                self.edit_tableView.setFocus()
        elif 'SampleAge' in header and 'AgeSignature' not in header:
            if not self.tabbed_from_editor:
                item_ids = []
                row = model_index.row()
                item_ids.append(self.model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole))
                dlg = AgeDialog(self.table, item_ids, self)
                dlg.exec()
                logger_setup.get_logger().info(f'Repopulating {header} for {item_ids[0]}')
                query = QtS.QSqlQuery()
                if not query.exec(f'SELECT {header} FROM {self.view} WHERE {self.view_headers[0]} = {item_ids[0]}'):
                    logger_setup.get_logger().critical(f'Failed to get {header} for {item_ids[0]}: {query.lastError().text()}')
                    return
                if query.next():
                    col = self.show_cols.index(header)
                    self.model.setData(self.model.index(row, col), query.value(header), QtC.Qt.ItemDataRole.EditRole)
                    self.updated_timestamp = time.time()
            else:
                self.edit_tableView.setFocus()
        else:
            self.dropdown_table = ''
            if 'Rejected' in header:
                self.dropdown_table = 'Rejected'
            else:
                columns = None
                if header in SQLUtils.non_editable[self.table]:
                    logger_setup.get_logger().error(f'{header} is not editable')
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
                                logger_setup.get_logger().info(f'{header} is non-editable')
                                return
                if columns is not None:
                    for col_key in columns:
                        if header == col_key:
                            self.dropdown_table = columns[header]
                            break
            if self.dropdown_table == '':
                self.create_lineedit()
            else:
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
                    self.updated_timestamp = time.time()
                    if self.edit_tableView.currentIndex() == self.edit_index:
                        self.tabbed_from_editor = False
                else:
                    logger_setup.get_logger().critical(f'Failed to set data in the table')
                    self.destroy_lineedit()
                    return False
            logger_setup.get_logger().info('Data saved from line edit')
            self.destroy_lineedit()
            return True

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
                self.combo.setModel(self.combo_model)
            else:
                set_table(self.combo_model, self.dropdown_table)
            if self.dropdown_table in SQLUtils.user_viewable_trees:
                self.combo = CheckableTreeCombobox()
                self.tree_model = CheckableTreeModel()
                self.tree_model.setSourceModel(self.combo_model)
                self.combo.setModel(self.tree_model)
            elif self.dropdown_table == 'References':
                pass
            else:
                if 'Abbreviation' in header:
                    self.combo = QtW.QComboBox()
                else:
                    self.combo = CheckableComboBox()
                    self.combo_model = CheckableSqlTableModel()
                    set_table(self.combo_model, self.dropdown_table)
                self.combo.setModel(self.combo_model)
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
        self.combo.setFocus()
        # print("showing popup")
        self.combo.showPopup()

    def save_dropdown_data(self):
        # todo: add message for changing parent sample, aliquot, or spot because moved entries will disappear from the view
        logger_setup.get_logger().info('Saving data from dropdown')
        self.edit_tableView: QtW.QTableView
        if self.combo is not None:
            combo = self.combo
        else:
            return False
        updated = False
        if not self.combo_index.isValid():
            model_indexes = []
            for index in self.edit_tableView.selectedIndexes():
                model_indexes.append(self.proxy_model.mapToSource(index))
        else:
            model_indexes = [self.proxy_model.mapToSource(self.combo_index)]
        selected_ids = []
        for model_index in model_indexes:
            item_id = self.model.index(model_index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole)
            if item_id not in selected_ids:
                selected_ids.append(item_id)
        if not selected_ids or len(selected_ids) < 1:
            logger_setup.get_logger().critical('No selected ids found')
            self.destroy_dropdown()
            return False
        # Figure out which table to update and which IDs to update
        if 'GPS' in self.dropdown_table or 'Elevation' in self.dropdown_table:
            # GPS and Elevation are updated in the GPSDialog
            updated = True
        elif 'SampleAge' in self.dropdown_table and 'AgeSignature' not in self.dropdown_table:
            # SampleAge is updated in the AgeDialog
            updated = True
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
            create_savepoint('before_edit_rejected')
            if not query.exec(
                    f'UPDATE {self.table} SET Rejected = {value} WHERE {self.table_headers[0]} {sql_where_str}'):
                logger_setup.get_logger().critical(
                    f'Failed to update Rejected for {selected_ids}: {query.lastError().text()}')
                rollback_savepoint('before_edit_rejected')
                self.destroy_dropdown()
                return False
            release_savepoint('before_edit_rejected')
            updated = True
        else:
            edit_table, edit_ids = self.determine_edit_table(selected_ids)
            if edit_table and edit_ids:
                # Save points are in these methods
                if '_' in edit_table:
                    # Many-to-many table
                    if not combo.model().update_many_table(edit_table, edit_ids):
                        logger_setup.get_logger().critical(f'Failed to update {edit_table}')
                        self.destroy_dropdown()
                        return False
                    updated = True
                else:
                    if isinstance(self.combo_model,
                                  CheckableSqlTableModel | CheckableSqlQueryModel | CheckableTreeModel):
                        if not combo.model().update_other_table(edit_table, edit_ids):
                            logger_setup.get_logger().critical(f'Failed to update {edit_table}')
                            self.destroy_dropdown()
                            return False
                    else:
                        clicked_id = get_id_from_name(self.combo_model.tableName(), combo.currentText())
                        if not clicked_id:
                            logger_setup.get_logger().info(f'No ID found for {combo.currentText()}')
                            self.destroy_dropdown()
                            return False
                        header = self.model.headerData(model_indexes[0].column(), QtC.Qt.Orientation.Horizontal,
                                                           QtC.Qt.ItemDataRole.DisplayRole)
                        if 'Abbreviation' in header:
                            header = header.replace('Abbreviation', 'ID')
                        query = QtS.QSqlQuery()
                        if len(edit_ids) == 1:
                            sql_where_str = f'= {edit_ids[0]}'
                        else:
                            sql_where_str = f'IN {tuple(edit_ids)}'
                        create_savepoint('before_edit_id')
                        query.prepare(f'UPDATE {edit_table} SET {header} = :clicked_id WHERE {get_headers(edit_table)[0]} {sql_where_str}')
                        query.bindValue(':clicked_id', clicked_id)
                        if not query.exec():
                            logger_setup.get_logger().critical(f'Failed to update {header} for {len(edit_ids)} {edit_table}')
                            logger_setup.get_logger().debug(f'Query: {query.lastQuery()}')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            rollback_savepoint('before_edit_id')
                            self.destroy_dropdown()
                            return False
                        release_savepoint('before_edit_id')
                    updated = True
        for model_index in model_indexes:
            if not self.model.setData(model_index, combo.currentText(), QtC.Qt.ItemDataRole.EditRole):
                logger_setup.get_logger().critical(f'Failed to set data: {self.model.last_error}')
                self.destroy_dropdown()
                return False
        if updated:
            for model_index in model_indexes:
                if model_index in self.model.edited_indexes:
                    self.model.edited_indexes.remove(model_index)
        self.updated_timestamp = time.time()
        if self.edit_tableView.currentIndex() == self.combo_index:
            self.tabbed_from_editor = False
        self.combo = combo
        logger_setup.get_logger().info('Data saved from dropdown')
        self.destroy_dropdown()
        return True

    def destroy_dropdown(self):
        # combo.activated.disconnect(self.save_dropdown_data)
        try:
            self.combo.removeEventFilter(self)
            self.combo.view().removeEventFilter(self)
        except TypeError:
            pass
        try:
            self.combo.add_triggered.disconnect(self.add_tag_popup)
            self.combo.edit_triggered.disconnect(self.edit_tag_popup)
        except TypeError:
            pass
        self.edit_tableView.setIndexWidget(self.combo_index, None)
        self.combo = None
        self.dropdown_table = None
        self.combo_index = QtC.QModelIndex()

    def determine_edit_table(self, selected_ids):
        for dictionary in [SQLUtils.one_editable, SQLUtils.many_editable]:
            if self.dropdown_table in dictionary[self.table].values():
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
                    table = key
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
                        if not query.exec(f'SELECT {edit_id_header} FROM {self.view} WHERE {self.table_headers[0]} {sql_where_str}'):
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
                            if table == 'Aliquots':
                                item_ids = aliquot_ids
                            elif table == 'Spots':
                                item_ids = spot_ids
                            elif table == 'UPbAnalyses':
                                item_ids = upb_analysis_ids
                            else:
                                logger_setup.get_logger().error(f'No {table} for selected {self.table} IDs')
                                return None, None
                        else:
                            logger_setup.get_logger().error(f'Could not find ID column for {table} in {self.table}')
                            return None, None
                        return table, item_ids

    def set_selected_value_dialog(self, table, indexes):
        # Get the selected value from the indexes
        selected_value = ''
        current_values = []
        for index in indexes:
            model_index = self.proxy_model.mapToSource(index)
            current_values.append(model_index.data(QtC.Qt.ItemDataRole.DisplayRole))
        # Open dialog to set the selected values

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
                logger_setup.get_logger().error(f'{header} cannot be empty')
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
                self.save_dropdown_data()

        self.updated_timestamp = time.time()

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
                if not query.exec(f'SELECT UPbAnalysisID FROM UPbEditView WHERE {self.show_cols[0]} = {row_id}'):
                    logger_setup.get_logger().critical(f'Failed to get UPbAnalysisID for {row_id}: {query.lastError().text()}')
                    return False
                while query.next():
                    where_col_ids['UPbAnalyses'].append(query.value(0))
                header_found = True
            elif header in ['SampleName', 'AliquotName', 'SpotName', 'ColumnName'] and not header_found:
                if header.split('Name')[0] in self.table :
                    # This is the name column for this table
                    text = self.model.index(row, self.model.fieldIndex(header)).data(QtC.Qt.ItemDataRole.DisplayRole)
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
                        logger_setup.get_logger().critical(f'Could not find columns to update {header}')
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
                        text = 'Null'
                    elif isinstance(text, str) and text.isdigit():
                        # string of an integer, so save it as an integer
                        text = int(text)
                    elif isinstance(text, str) and text.isdecimal():
                        # string of a decimal, so save it as a decimal
                        text = float(text)
                    update_cols[self.table].append(header)
                    update_col_values[self.table].append(text)
        for table in update_cols.keys():
            if update_col_values[table]:
                sql_cols = ', '.join(update_cols[table])
                table_headers = get_headers(table)
                if table == self.table:
                    item_id = self.model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole)
                else:
                    for header in self.table_headers:
                        if header in table_headers:
                            edit_table_col = header
                            break
                        elif table_headers[0] in self.table_headers:
                            edit_table_col = table_headers[0]
                    # edit_table_col
                    item_id = self.retrieve_id(table, edit_table_col)
                sql_placeholder = ', '.join('?' for i in range(len(update_cols[table])))
                query.prepare(f'UPDATE "{table}" SET {sql_cols} = {sql_placeholder} WHERE {table_headers[0]} = {item_id}')
                for i in range(len(update_cols[table])):
                    query.addBindValue(update_col_values[table][i])
                if not query.exec():
                    logger_setup.get_logger().critical(f'Failed to update {table}')
                    logger_setup.get_logger().debug(f'Failed query: {query.lastQuery()}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
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
            self.find_added(dlg.ids_added)
        self.display_table()

    def find_added(self, ids_added):
        if not ids_added:
            return
        query = QtS.QSqlQuery()
        for id in ids_added:
            if not query.exec(f'SELECT {", ".join(self.show_cols)} FROM {self.view} WHERE {self.table_headers[0]} = {id}'):
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
            dlg_args = add_tree_popup(combo.view(), combo.model(), action)
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
            self.destroy_dropdown()
            self.display_widget()
            self.combo.showPopup()

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
            self.destroy_dropdown()
            self.display_widget()
            self.combo.showPopup()

    def rollback(self):
        rollback_savepoint('before_edit')
        self.reject()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        if not self.on_row_change(QtC.QModelIndex(), self.edit_tableView.currentIndex()):
            logger_setup.get_logger().critical('Failed to save changes')
            return
        else:
            release_savepoint('before_edit')
            # Check if there is another existing savepoint. If not, go ahead and update the database
            if not SavepointManager.get_instance().active_savepoints():
                update_database()
            self.accept()
            self.msg.information(self, 'Success', 'Changes saved', QtW.QMessageBox.StandardButton.Ok)
            self.close_by_dialog = True
            self.close()
            self.close_by_dialog = False
            self.accept()

    def discard_question(self):
        self.msg.question(self, 'Discard changes', 'Are you sure you want to discard all changes?',QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        self.msg.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = self.msg.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            self.rollback()
        else:
            pass

    def close(self):
        self.saveWindowState()
        if not self.close_by_dialog:
            if not self.on_row_change(QtC.QModelIndex(), self.edit_tableView.currentIndex()):
                logger_setup.get_logger().critical('Failed to save changes')
                self.discard_question()
            elif self.updated:
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

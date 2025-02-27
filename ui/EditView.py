import os
import sys
import time
from operator import index, itemgetter

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import QPoint, QSize
from PyQt6.uic import loadUi
import Functions.Text_manipulations as TxM
import logger_setup
import difflib
from Functions.Widget_classes import (
    TreeModel, CheckableTreeCombobox, CheckableTreeModel, CheckableTreeView, ReadableProxyModel, DisplayRoundedModel,
    SQLiteTableModel, CheckableComboBox, CheckableSqlTableModel, CheckableSqlQueryModel, get_headers, get_name_column,
    set_table, VerifiableSqlTableModel, VerifiableSqlViewModel, populate_combo_checks, populate_model_checks,
    WordWrapDelegate, get_columns
)
from Functions import SQLUtils
from Functions.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint, SavepointManager
from Functions.Settings_manager import settings
from Functions.Database_manager import update_database
from ui.AddTags import AddTags
from ui.GPSDialog import GPSDialog
from ui.New_reference import NewReference
from ui.AgeDialog import AgeDialog
import time

class SetSelectedValues(QtW.QDialog):
    def __init__(self, table, header, ids):
        super().__init__()
        self.table = table
        self.header = header
        self.ids = ids
        if self.table == "Samples":
            self.view = "SampleEditView"
        elif self.table == "Spots":
            self.view = "SpotEditView"
        elif self.table == "UPbAnalyses":
            self.view = "UPbEditView"
        self.show_cols = settings.value(SQLUtils.view_setting_dict[self.view])
        self.view_headers = get_headers(self.view)

        self.widget = None

    def display_widget(self):
        if 'GPS' in self.header or 'Elevation' in self.header:
            # Do not open the popup if tabbing here, only when double-clicking
            dlg = GPSDialog(self.table, self.ids)
            dlg.exec()
            logger_setup.get_logger().info(f'Repopulating {self.header} for {self.ids}')
            # query = QtS.QSqlQuery()
            # gps_headers = []
            # for header in self.show_cols:
            #     if 'GPS' in header or 'Elevation' in header:
            #         gps_headers.append(header)
            # if not query.exec(f'SELECT {', '.join(gps_headers)} FROM {self.view} WHERE {self.view_headers[0]} = {self.ids}'):
            #     logger_setup.get_logger().critical(f'Failed to get {header} for {self.ids}: {query.lastError().text()}')
            #     return
            # if query.next():
            #     for header in gps_headers:
            #         col = self.show_cols.index(header)
            #         self.model.setData(self.model.index(row, col), query.value(header), QtC.Qt.ItemDataRole.EditRole)
            #         self.updated_timestamp = time.time()
            #         print(f'New value: {self.model.index(row, col).data(QtC.Qt.ItemDataRole.DisplayRole)}')
        elif 'SampleAge' in self.header and 'AgeSignature' not in self.header:
            dlg = AgeDialog(self.table, self.ids)
            dlg.exec()
            logger_setup.get_logger().info(f'Repopulating {self.header} for {self.ids}')
            # query = QtS.QSqlQuery()
            # if not query.exec(f'SELECT {self.header} FROM {self.table} WHERE {self.table_headers[0]} = {self.ids}'):
            #     logger_setup.get_logger().critical(f'Failed to get {self.header} for {self.ids}: {query.lastError().text()}')
            #     return
            # if query.next():
            #     index = self.model.fieldIndex(self.header)
            #     self.model.setData(self.model.index(row, index), query.value(self.header), QtC.Qt.ItemDataRole.EditRole)
            #     self.updated_timestamp = time.time()
        else:
            dropdown_table = ''
            if 'Rejected' in self.header:
                dropdown_table = 'Rejected'
            else:
                for key, values in SQLUtils.many_editable.items():
                    if key == self.table and self.header in values.keys():
                        for col_key in values.keys():
                            if self.header == col_key:
                                dropdown_table = values[self.header]
                                break
                        if dropdown_table == '':
                            logger_setup.get_logger().info(f'No matches found for {self.header} in {key}')
                            break
                if dropdown_table == '':
                    for key, values in SQLUtils.one_editable.items():
                        if key == self.table and self.header in values.keys():
                            for col_key in values.keys():
                                if self.header == col_key:
                                    dropdown_table = values[self.header]
                                    break
                            if dropdown_table == '':
                                logger_setup.get_logger().info(f'No matches found for {self.header} in {key}')
                                break
            if dropdown_table == '':
                for key, values in SQLUtils.non_editable.items():
                    if key == self.table and self.header in values:
                        for col in values:
                            if self.header == col:
                                logger_setup.get_logger().info(f'{self.header} is non-editable')
                                return
                        break
                self.display_lineedit()
            else:
                self.display_dropdown(dropdown_table)

    def display_lineedit(self):
        logger_setup.get_logger().info('Displaying line edit')
        self.widget = QtW.QLineEdit()
        current_values = []
        query = QtS.QSqlQuery()

        for id in self.ids:
            current_values.append(self.model.index(id, 0).data(QtC.Qt.ItemDataRole.DisplayRole))

class EditView(QtW.QDialog):
    def __init__(self, table_name, **kwargs):
        super().__init__()
        logger_setup.get_logger().info(f'Creating a new EditView for {table_name}')
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "EditTable.ui")
        loadUi(sources_ui_file, self)
        self.setModal(True)
        self.setWindowTitle(f'Edit {TxM.add_spaces_camel(table_name)}')
        self.updated = False

        self.parent_id: int = None
        self.parent_type: str = None
        self.table_item_ids: list = None
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.table = TxM.remove_spaces(table_name)
        self.msg = QtW.QMessageBox()
        self.view = None
        self.model = None
        self.updated_timestamp = None
        self.show_cols = []
        self.where = ''
        if self.table in SQLUtils.trigger_tables:
            if self.table == 'Columns':
                self.view = 'ColumnEditView'
                self.show_cols = settings.value('column_edit_columns')
            elif self.table == 'Samples':
                self.view = 'SampleEditView'
                self.show_cols = settings.value('sample_edit_columns')
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
            elif self.table == 'References':
                self.view = 'ReferenceEditView'
                self.show_cols = settings.value('reference_edit_columns')
        elif self.table == 'Spots':
            self.view = 'SpotEditView'
            self.show_cols = settings.value('spot_edit_columns')
            self.parent_id_header = 'SampleID' if self.parent_type == 'Sample' else 'AliquotID' if self.parent_type == 'Aliquot' else 'SpotID' if self.parent_type == 'Spot' else None
            if self.parent_id_header:
                self.where = f' WHERE {self.parent_id_header} = {self.parent_id}'
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
        self.lineEdit = None
        self.msg = QtW.QMessageBox(self)
        self.close_by_dialog = False
        self.tabbed_from_editor = False

        self.view_headers = []
        if self.view is not None:
            self.view_headers = get_headers(self.view)
        self.table_headers = get_headers(self.table)
        self.proxy_model = ReadableProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.display_table()
        create_savepoint('before_edit')

        self.edit_tableView.installEventFilter(self)
        self.edit_tableView.selectionModel().currentChanged.connect(self.on_index_change)
        self.edit_tableView.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.edit_tableView.customContextMenuRequested.connect(self.show_context_menu)
        # self.combo.closing.connect(self.destroy_dropdown)
        # self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        self.cancel_pushButton.clicked.connect(self.rollback)
        self.edit_tableView.selectionModel().currentRowChanged.connect(self.on_row_change)
        self.edit_tableView.doubleClicked.connect(self.display_widget)

    def create_model(self):
        self.model = SQLiteTableModel(f'SELECT {', '.join(self.show_cols)} FROM {self.view} {self.where}')
        self.updated_timestamp = time.time()

    def optimizeVerticalResize(self, logical_index, old_size, new_size):
        """Trigger a delayed row height update when the user resizes the window vertically."""
        self.resize_timer.start(250)  # Add a slight delay to avoid excessive updates

    def resizeRowsOptimized(self):
        """Resize rows only when resizing stops."""
        self.edit_tableView.resizeRowsToContents()

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
                clear_action = None
                return
            clear_action = menu.addAction('Clear selected values')
        for index in indexes:
            if not index.isValid():
                set_selected_action = None
                return
            if index.column != indexes[0].column():
                set_selected_action = None
                return
            set_selected_action = menu.addAction('Set selected values')
        edit_action = menu.addAction('Edit')
        delete_action = menu.addAction('Delete row')
        action = menu.exec(self.edit_tableView.viewport().mapToGlobal(pos))
        if action == clear_action:
            for index in indexes:
                model_index = self.proxy_model.mapToSource(index)
                self.model.setData(model_index, '', QtC.Qt.ItemDataRole.EditRole)
            self.updated_timestamp = time.time()
        elif action == set_selected_action:
            value = self.set_selected_values_dialog(self.table, indexes)
            for index in indexes:
                model_index = self.proxy_model.mapToSource(index)
                self.model.setData(model_index, indexes[0].data(QtC.Qt.ItemDataRole.DisplayRole), QtC.Qt.ItemDataRole.EditRole)
            self.updated_timestamp = time.time
        elif action == edit_action:
            self.display_widget()
        elif action == delete_action:
            response = self.msg.warning(self, 'Delete row', 'Are you sure you want to delete the selected rows?', QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No, QtW.QMessageBox.StandardButton.No)
            if response == QtW.QMessageBox.StandardButton.Yes:
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
                logger_setup.get_logger().info(f'Deleting {len(ids_to_delete)} {self.table_headers[get_name_column(self.table)]} from {self.table}')
                query = QtS.QSqlQuery()
                if not query.exec(f'DELETE FROM {self.table} WHERE {self.table_headers[0]} {sql_where_str}'):
                    logger_setup.get_logger().critical(f'Failed to delete selected rows from {self.table}: {query.lastError().text()}')
                    return
                self.model.removeRows(ids_to_delete)
                self.updated_timestamp = time.time()

    def display_table(self):
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

        # Optimize window resizing
        self.resize_timer = QtC.QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.resizeRowsOptimized)

        # Connect resizing events
        self.edit_tableView.horizontalHeader().sectionResized.connect(self.optimizeVerticalResize)
        self.edit_tableView.verticalHeader().sectionResized.connect(self.optimizeVerticalResize)

    def find_new_rows(self):
        # Find the new rows that have been added to the database and add them to the model
        pass

    def display_widget(self):
        if len(self.edit_tableView.selectedIndexes()) == 0:
            return
        elif len(self.edit_tableView.selectedIndexes()) > 1:
            logger_setup.get_logger().error('Right-click to edit multiple selections')
            return
        logger_setup.get_logger().info('Displaying widget')
        proxy_index = self.edit_tableView.selectedIndexes()[0]
        model_index = self.proxy_model.mapToSource(proxy_index)
        if not model_index.isValid():
            return
        if self.lineEdit is not None:
            self.destroy_lineedit()
            if self.lineEdit is not None:
                logger_setup.get_logger().info('Error destroying previous line edit')
                return
        elif self.combo is not None:
            self.destroy_dropdown()
            if self.combo is not None:
                logger_setup.get_logger().info('Error destroying previous dropdown')
                return
        header = self.model.headerData(model_index.column(), QtC.Qt.Orientation.Horizontal,
                                                    QtC.Qt.ItemDataRole.DisplayRole)

        if 'GPS' in header or 'Elevation' in header:
            if not self.tabbed_from_editor:
                # Do not open the popup if tabbing here, only when double-clicking
                item_ids = []
                row = model_index.row()
                item_ids.append(self.model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole))
                dlg = GPSDialog(self.table, item_ids)
                dlg.exec()
                logger_setup.get_logger().info(f'Repopulating {header} for {item_ids[0]}')
                query = QtS.QSqlQuery()
                gps_headers = []
                for header in self.show_cols:
                    if 'GPS' in header or 'Elevation' in header:
                        gps_headers.append(header)
                if not query.exec(f'SELECT {', '.join(gps_headers)} FROM {self.view} WHERE {self.view_headers[0]} = {item_ids[0]}'):
                    logger_setup.get_logger().critical(f'Failed to get {header} for {item_ids[0]}: {query.lastError().text()}')
                    return
                if query.next():
                    for header in gps_headers:
                        col = self.show_cols.index(header)
                        self.model.setData(self.model.index(row, col), query.value(header), QtC.Qt.ItemDataRole.EditRole)
                        self.updated_timestamp = time.time()
                        print(f'New value: {self.model.index(row, col).data(QtC.Qt.ItemDataRole.DisplayRole)}')
            else:
                self.edit_tableView.setFocus()
        elif 'SampleAge' in header and 'AgeSignature' not in header:
            if not self.tabbed_from_editor:
                item_ids = []
                row = model_index.row()
                item_ids.append(self.model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole))
                dlg = AgeDialog(self.table, item_ids)
                dlg.exec()
                logger_setup.get_logger().info(f'Repopulating {header} for {item_ids[0]}')
                query = QtS.QSqlQuery()
                if not query.exec(f'SELECT {header} FROM {self.table} WHERE {self.table_headers[0]} = {item_ids[0]}'):
                    logger_setup.get_logger().critical(f'Failed to get {header} for {item_ids[0]}: {query.lastError().text()}')
                    return
                if query.next():
                    index = self.model.fieldIndex(header)
                    self.model.setData(self.model.index(row, index), query.value(header), QtC.Qt.ItemDataRole.EditRole)
                    self.updated_timestamp = time.time()
            else:
                self.edit_tableView.setFocus()
        else:
            dropdown_table = ''
            if 'Rejected' in header:
                dropdown_table = 'Rejected'
            else:
                for key, values in SQLUtils.many_editable.items():
                    if key == self.table and header in values.keys():
                        for col_key in values.keys():
                            if header == col_key:
                                dropdown_table = values[header]
                                break
                        if dropdown_table == '':
                            logger_setup.get_logger().info(f'No matches found for {header} in {key}')
                            break
                if dropdown_table == '':
                    for key, values in SQLUtils.one_editable.items():
                        if key == self.table and header in values.keys():
                            for col_key in values.keys():
                                if header == col_key:
                                    dropdown_table = values[header]
                                    break
                            if dropdown_table == '':
                                logger_setup.get_logger().info(f'No matches found for {header} in {key}')
                                break
            if dropdown_table == '':
                for key, values in SQLUtils.non_editable.items():
                    if key == self.table and header in values:
                        for col in values:
                            if header == col:
                                logger_setup.get_logger().info(f'{header} is non-editable')
                                return
                        break
                self.display_lineedit()
            else:
                self.display_dropdown(dropdown_table)

    def display_lineedit(self):
        logger_setup.get_logger().info('Displaying line edit')
        self.edit_index = self.edit_tableView.selectedIndexes()[0]
        model_index = self.proxy_model.mapToSource(self.edit_index)
        self.lineEdit = QtW.QLineEdit()
        # self.lineEdit.setValidator(QtG.QRegularExpressionValidator(QtC.QRegularExpression("[0-9]*")))
        if not model_index.data(QtC.Qt.ItemDataRole.DisplayRole):
            self.lineEdit.setText('')
        else:
            self.lineEdit.setText(str(model_index.data(QtC.Qt.ItemDataRole.DisplayRole)))
            self.lineEdit.selectAll()
        self.lineEdit.installEventFilter(self)
        self.lineEdit.returnPressed.connect(self.destroy_lineedit)
        self.lineEdit.editingFinished.connect(self.destroy_lineedit)
        self.edit_tableView.setIndexWidget(self.edit_tableView.selectedIndexes()[0], self.lineEdit)
        self.lineEdit.setFocus()

    def destroy_lineedit(self):
        logger_setup.get_logger().info('Saving data from line edit')
        if self.lineEdit is not None:
            value = self.lineEdit.text()
            # todo: actually save the value to the database
            # print(f'Typed: {value}')
            model_index = self.proxy_model.mapToSource(self.edit_index)
            view_header = self.model.headerData(model_index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            edit_table = ''
            for table in ["Samples", "UPbAnalyses", "Columns"]:
                if edit_table == '':
                    if view_header in get_headers(table):
                        edit_table = table
                        table_value_header = view_header
                        table_id_header = get_headers(table)[0]
                else:
                    break
            if edit_table == '':
                # todo: figure out how to identify the table and column to update
                return
            query = QtS.QSqlQuery()
            query.prepare(f'UPDATE {table} SET {table_value_header} = :value WHERE {table_id_header} = :id')
            query.bindValue(':value', value)
            query.bindValue(':id', self.model.index(model_index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole))
            if not query.exec():
                logger_setup.get_logger().critical(f'Failed to set data {value}: {query.lastError().text()}')
                self.lineEdit.setFocus()
                return
            logger_setup.get_logger().info(f'Set {value} for {table_value_header} in {edit_table}')
            if self.model.setData(model_index, value, QtC.Qt.ItemDataRole.EditRole):
                self.updated_timestamp = time.time()
                if self.edit_tableView.currentIndex() == self.edit_index:
                    self.tabbed_from_editor = False
                self.lineEdit.removeEventFilter(self)
                self.lineEdit.editingFinished.disconnect(self.destroy_lineedit)
                self.lineEdit.returnPressed.disconnect(self.destroy_lineedit)
                self.edit_tableView.setIndexWidget(self.edit_index, None)
                self.lineEdit = None
                self.edit_index = QtC.QModelIndex()
                self.edit_tableView.setFocus()
            else:
                logger_setup.get_logger().critical(f'Failed to set data: {self.model.lastError().text()}')
                self.lineEdit.setFocus()
        logger_setup.get_logger().info('Data saved from line edit')

    def display_dropdown(self, dropdown_table: str):
        logger_setup.get_logger().info(f'Displaying dropdown for {dropdown_table}')

        self.combo_index = self.edit_tableView.selectedIndexes()[0]
        model_index = self.proxy_model.mapToSource(self.combo_index)
        self.combo_model = QtS.QSqlTableModel()
        self.combo = QtW.QComboBox()
        if dropdown_table == 'Rejected':
            self.combo = QtW.QComboBox()
            self.combo.addItem('Accepted')
            self.combo.addItem('Rejected')
        else:
            if dropdown_table == 'References':
                self.combo = CheckableComboBox()
                self.combo_model = CheckableSqlQueryModel()
                self.combo_model.setQuery(f'SELECT * FROM "References"')
                self.combo.setModel(self.combo_model)
            else:
                set_table(self.combo_model, dropdown_table)
            if dropdown_table in SQLUtils.user_viewable_trees:
                self.combo = CheckableTreeCombobox()
                self.tree_model = CheckableTreeModel()
                self.tree_model.setSourceModel(self.combo_model)
                self.combo.setModel(self.tree_model)
            elif dropdown_table == 'References':
                pass
            else:
                if 'Abbreviation' in self.model.headerData(model_index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole):
                    self.combo = QtW.QComboBox()
                else:
                    self.combo = CheckableComboBox()
                    self.combo_model = CheckableSqlTableModel()
                    set_table(self.combo_model, dropdown_table)
                self.combo.setModel(self.combo_model)
            self.combo.setModelColumn(get_name_column(dropdown_table))
            if dropdown_table in SQLUtils.many_editable[self.table].values():
                many_to_many_table = f'{self.table}_{dropdown_table}'
                selected_id = self.model.index(model_index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole)
                populate_combo_checks(many_to_many_table, self.combo, selected_id)
            if dropdown_table in SQLUtils.one_editable[self.table].values():
                selected_id = self.model.index(model_index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole)
                dropdown_id_header = get_headers(dropdown_table)[0]
                if dropdown_id_header in self.table_headers:
                    # The id header of the dropdown table is in the current table
                    populate_model_checks(self.combo_model, [selected_id], self.table)
                else:
                    for key, values in SQLUtils.one_editable.items():
                        if dropdown_id_header in get_headers(key):
                            for view in SQLUtils.views:
                                # Use views because ids for samples, aliquots, spots, and analyses are joined in the views
                                if 'Edit' in view:
                                    if get_headers(key)[0] == get_headers(view)[0]:
                                        selected_ids = []
                                        query = QtS.QSqlQuery()
                                        if not query.exec(f'SELECT {get_headers(key)[0]} FROM {view} WHERE {self.table_headers[0]} = {selected_id}'):
                                            logger_setup.get_logger().critical(f'Failed to get {dropdown_id_header} for {selected_id}: {query.lastError().text()}')
                                            return
                                        while query.next():
                                            selected_ids.append(query.value(0))
                                        populate_model_checks(self.combo_model, selected_ids, key)

                            if get_headers(key)[0] in self.view_headers:
                                selected_ids = self.model.index(model_index.row(), self.view_headers.index(get_headers(key)[0])).data(QtC.Qt.ItemDataRole.DisplayRole)
                                populate_model_checks(self.combo_model, selected_ids, key)
                            break
                self.combo.single_click = True
        selected_text = self.combo_index.data(QtC.Qt.ItemDataRole.DisplayRole)
        self.combo.setCurrentText(selected_text)
        if self.combo.currentText() == '':
            # Make sure there is no selected index
            self.combo.setCurrentIndex(-1)
        # print(f"Selected text: {selected_text}")
        self.edit_tableView.setIndexWidget(self.edit_tableView.selectedIndexes()[0], self.combo)
        self.combo.installEventFilter(self)
        self.combo.view().installEventFilter(self)
        self.combo.model_modifiable = True
        self.combo.closedOnLineEditClick = False
        if dropdown_table != 'Rejected':
            self.combo.enable_context_menu(True)
        # self.combo.activated.connect(self.destroy_dropdown)
        self.combo.setFocus()
        # print("showing popup")
        self.combo.showPopup()

    def destroy_dropdown(self):
        logger_setup.get_logger().info('Saving data from dropdown')
        self.edit_tableView: QtW.QTableView
        if self.combo is not None:
            combo = self.combo
        else:
            return
        model_index = self.proxy_model.mapToSource(self.combo_index)
        header = self.model.headerData(self.combo_index.column(), QtC.Qt.Orientation.Horizontal,
                                       QtC.Qt.ItemDataRole.DisplayRole)
        # If this is a many-to-many relationship, update the database
        if isinstance(combo, CheckableTreeCombobox):
            combo: CheckableTreeCombobox
            self.combo_model: CheckableTreeModel
            for key, values in SQLUtils.many_editable.items():
                for col_key in values.keys():
                    if header == col_key:
                        many_table = f'{key}_{values[header]}'
                        checked_items, partially_checked_items, checked_indices, partially_checked_indices = self.tree_model.traverse_checkable_tree(
                            QtC.QModelIndex())
                        item_id = None
                        if key == self.table:
                            item_id = self.model.index(model_index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole)
                        else:
                            # We need to get the ID of the item in the other table
                            other_id_header = get_headers(key)[0]
                            if other_id_header in self.show_cols:
                                other_id_col = self.show_cols.index(other_id_header)
                                item_id = self.model.index(model_index.row(), other_id_col).data(
                                    QtC.Qt.ItemDataRole.DisplayRole)
                            else:
                                logger_setup.get_logger().critical(f'Could not find {other_id_header} in {self.view}')
                        if item_id:
                            update = self.tree_model.update_db(many_table, checked_items, partially_checked_items,
                                                               [item_id])
                            if update is False:
                                logger_setup.get_logger().critical(
                                    f"Failed to update {many_table} for {self.table_headers[0]} {item_id}")
                            else:
                                logger_setup.get_logger().info(
                                    f"Updated {many_table} for {self.table_headers[0]} {item_id}")
                        break
        elif isinstance(combo, CheckableComboBox):
            combo: CheckableComboBox
            self.combo_model: CheckableSqlTableModel
            for key, values in SQLUtils.many_editable.items():
                if header in values.keys():
                    for col_key in values.keys():
                        if header == col_key:
                            many_table = f'{key}_{values[header]}'
                            item_id = None
                            if key == self.table:
                                item_id = self.model.index(model_index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole)
                            else:
                                # We need to get the ID of the item in the other table
                                other_id_header = get_headers(key)[0]
                                if other_id_header in self.show_cols:
                                    other_id_col = self.show_cols.index(other_id_header)
                                    item_id = self.model.index(model_index.row(), other_id_col).data(
                                        QtC.Qt.ItemDataRole.DisplayRole)
                                else:
                                    logger_setup.get_logger().critical(f'Could not find {other_id_header} in {self.view}')
                            if item_id:
                                update = self.combo_model.update_many_db(many_table, [item_id])
                                if update is False:
                                    logger_setup.get_logger().critical(
                                        f"Failed to update {many_table} for {self.table_headers[0]} {item_id}")
                                else:
                                    logger_setup.get_logger().info(
                                        f"Updated {many_table} for {self.table_headers[0]} {item_id}")
        if not self.model.setData(model_index, combo.currentText(), QtC.Qt.ItemDataRole.EditRole):
            logger_setup.get_logger().critical(f'Failed to set data: {self.model.last_error}')
        self.updated_timestamp = time.time()
        if self.edit_tableView.currentIndex() == self.combo_index:
            self.tabbed_from_editor = False
        # combo.activated.disconnect(self.destroy_dropdown)
        combo.removeEventFilter(self)
        combo.view().removeEventFilter(self)
        self.edit_tableView.setIndexWidget(self.combo_index, None)
        if self.combo is not None:
            self.combo = None
        self.combo_index = QtC.QModelIndex()
        logger_setup.get_logger().info('Data saved from dropdown')

    def set_selected_value_dialog(self, table, indexes):
        # Get the selected value from the indexes
        selected_value = ''
        current_values = []
        for index in indexes:
            model_index = self.proxy_model.mapToSource(index)
            current_values.append(model_index.data(QtC.Qt.ItemDataRole.DisplayRole))
        # Open dialog to set the selected values

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
            self.destroy_dropdown()
        if self.lineEdit is not None:
            self.destroy_lineedit()

    def on_row_change(self, selected, deselected):
        # Close and save the data from any open widgets
        if self.combo is not None:
            self.destroy_dropdown()
        if self.lineEdit is not None:
            self.destroy_lineedit()
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
            if not self.data_submit(deselected.row()):
                # There was an error submitting the changes

                QtC.QTimer.singleShot(0, highlight_error)
                return False
            else:
                self.updated = True
                return True

    def data_submit(self, row):
        logger_setup.get_logger().info('Submitting changes')
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
                    edit_table_col
                    item_id = self.retrieve_id(table, )
                sql_placeholder = ', '.join('?' for i in range(len(update_cols[table])))
                query.prepare(f'UPDATE {table} SET {sql_cols} = {sql_placeholder} WHERE {table_headers[0]} = {item_id}')
                for i in range(len(update_cols[table])):
                    query.addBindValue(update_col_values[table][i])
                if not query.exec():
                    logger_setup.get_logger().critical(f'Failed to update {table}: {query.lastError().text()}')
                    return False
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

    def retrieve_checked_ids(self, table, values):
        if not values:
            return []
        table_headers = get_headers(table)
        id_header = table_headers[0]
        query = QtS.QSqlQuery()
        ids = []
        for value in values:
            if not query.exec(f'SELECT {id_header} FROM {table} WHERE {get_name_column(table)} = "{value}"'):
                logger_setup.get_logger().critical(f'Failed to get {get_name_column(table)} for {value}: {query.lastError().text()}')
                return None
            if query.next():
                ids.append(query.value(0))
            else:
                return None
        return ids

    def add_popup(self):
        # if not self.add_pushButton.hasFocus():
        #     return
        if not self.model.submit():
            errtxt = f'Failed to save changes to {self.table}: {self.model.lastError().text()}'
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
            return
        # if self.table == 'Samples' or self.table == '"References"' or self.table == 'Aliquots' or self.table == 'UPbData':
        #     pass
        if self.table == '"References"' or self.table == 'References':
            dlg = NewReference()
        else:
            dlg = AddTags(self.model, self.table)
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
            self.find_new_rows()
        self.display_table()

    def rollback(self):
        rollback_savepoint('before_edit')
        self.reject()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        if self.edit_tableView.currentIndex().isValid() and not self.on_row_change(QtC.QModelIndex(), self.edit_tableView.currentIndex()):
            # There is a valid index selected and the row change failed
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

    def closeEvent(self, event: QtG.QCloseEvent):
        if not self.close_by_dialog:
            if self.updated:
                self.discard_question()
                event.ignore()
            else:
                logger_setup.get_logger().info(f'Closing {self.table} edit dialog')
                event.accept()
        else:
            logger_setup.get_logger().info(f'Closing {self.table} edit dialog')
            event.accept()

    def saveWindowState(self):
        settings.setValue("ui/EditSampleTable/pos", self.pos())
        settings.setValue("ui/EditSampleTable/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/EditSampleTable/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/EditSampleTable/size", defaultValue=QSize(810, 569)))

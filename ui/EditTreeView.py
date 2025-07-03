import os
import sys
import time
from operator import index, itemgetter

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import QPoint, QSize, QSortFilterProxyModel
from PyQt6.QtWidgets import QMessageBox
from PyQt6.uic import loadUi
import Functions.Text_manipulations as TxM
import logger_setup
from Functions.Widget_classes import (
    TreeModel, CheckableTreeCombobox, CheckableTreeModel, ReadableProxyModel, SQLiteTableModel, CheckableComboBox,
    CheckableSqlTableModel, CheckableSqlQueryModel, get_headers, get_name_column, set_table, populate_many_combo_checks,
    populate_model_checks, WordWrapDelegate, get_columns, get_readable_header, find_current_sub_items, get_id_from_name,
    add_tree_popup, save_expanded_state, restore_expanded_state, get_selected_tree_ids, TreeContextMenu,
    expand_collapse, get_name_from_id, get_view_from_table, columns_as_list_current, TreeSortFilterProxyModel, delete_data
)
from Functions import SQLUtils
from Functions.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint, SavepointManager
from Functions.Settings_manager import SettingsManager
from ui.EditView import EditView
from ui.New_reference import NewReference

settings = SettingsManager().settings
from Functions.Database_views import ViewQuery
from Functions.LoadingDialog_manager import LoadingDialogManager
from ui.AddTags import AddTags
from ui.AddTreeTags import AddTreeTags
from ui.EditTree import EditTree
from ui.EditTable import EditTable
from Functions.Widget_classes import find_tree_model
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
            if isinstance(self.widget, CheckableComboBox | CheckableTreeCombobox):
                self.widget.add_triggered.connect(parent_window.add_tag_popup)
                self.widget.edit_triggered.connect(parent_window.edit_tag_popup)
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
        if isinstance(self.widget, CheckableComboBox):
            self.widget.add_triggered.connect(self.add_popup)
            self.widget.edit_triggered.connect(self.edit_popup)
            self.widget.delete_triggered.connect(self.delete_item)
        elif isinstance(self.widget, CheckableTreeCombobox):
            self.widget.add_triggered.connect(self.add_popup)
            self.widget.edit_triggered.connect(self.edit_popup)
        self.loading_manager.close_loading_dialog('Loading', f'Loading...')

    def add_popup(self, combo: QtW.QComboBox, action: QtG.QAction | None = None):
        combo.blockSignals(True)
        logger_setup.get_logger().info(f"Add popup called")
        model = combo.model()
        if isinstance(combo.view(), QtW.QTreeView):
            if not isinstance(model, TreeModel):
                model, indexes = find_tree_model(model, None)
            if model:
                table = model.table
            else:
                logger_setup.get_logger().critical(f"Error adding new item")
                logger_setup.get_logger().debug(f"Error: No tree model found")
                combo.blockSignals(False)
                return
        elif isinstance(combo.model(), QSortFilterProxyModel):
            model = combo.model().sourceModel()
            table = model.tableName()
        else:
            table = combo.model().tableName()
        dlg = None
        if table in SQLUtils.user_viewable_trees:
            save_expanded_state(table, combo.view())
            dlg_args = add_tree_popup(combo.view(), action)
            self.loading_manager.show_loading_dialog('Loading', f'Opening add window for {table}...')
            if dlg_args:
                dlg = AddTreeTags(self, table, **dlg_args)
            else:
                dlg = AddTreeTags(self, table)
        elif table in ['References', '"References"']:
            table = 'References'
            self.loading_manager.show_loading_dialog('Loading', f'Opening add window for {table}...')
            dlg = NewReference(self)
        else:
            self.loading_manager.show_loading_dialog('Loading', f'Opening add window for {table}...')
            dlg = AddTags(self, table)
        if not dlg:
            combo.blockSignals(False)
            return
        logger_setup.get_logger().info(f"Showing {table} add dialog")
        dlg.exec()
        if dlg.updated:
            # Update this combo box
            self.parent().create_dropdown()
            self.widget = self.parent().combo
            combo.blockSignals(False)
        else:
            combo.blockSignals(False)
            return

    def edit_popup(self, combo: QtW.QComboBox, action: QtG.QAction | None = None):
        logger_setup.get_logger().info(f'Edit popup called')
        combo: QtW.QComboBox
        model = combo.model()
        if isinstance(combo.view(), QtW.QTreeView):
            if not isinstance(model, TreeModel):
                model, indexes = find_tree_model(model, None)
            if model:
                table = model.table
            else:
                logger_setup.get_logger().critical(f"Error editing table")
                logger_setup.get_logger().debug(f"Error: No tree model found")
                return
        elif isinstance(model, QtC.QSortFilterProxyModel):
            model = model.sourceModel()
            table = model.tableName()
        else:
            table = combo.model().tableName()
        combo.blockSignals(True)
        dlg = None
        if table in SQLUtils.user_viewable_trees:
            dlg = EditTree(self, table)
        elif table != get_view_from_table(table):
            dlg = EditView(self, table)
        else:
            dlg = EditTable(self, table)
        if dlg is None:
            combo.blockSignals(False)
            return
        logger_setup.get_logger().info(f"Showing {table} edit dialog")
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            # Update this combo box
            self.parent().create_dropdown()
            self.widget = self.parent().combo
            combo.blockSignals(False)
        else:
            combo.blockSignals(False)
            return

    def delete_item(self):
        combo = self.widget
        selected_ids = []
        for index in combo.view().selectedIndexes:
            id = combo.model().index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole)
            if id is not None:
                selected_ids.append(id)
        model = combo.model()
        table = None
        while not table:
            try:
                table = model.tableName()
            except AttributeError:
                model = model.sourceModel()
        if selected_ids:
            delete_data(table, selected_ids)
        else:
            return

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

class EditTreeView(QtW.QDialog):
    def __init__(self, parent_window, table_name, **kwargs):
        super().__init__(parent=parent_window)
        self.loading_manager = LoadingDialogManager.get_instance()
        self.loadWindowState()

        logger_setup.get_logger().info(f'Creating a new EditTreeView for {table_name}')
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "EditTree.ui")
        loadUi(sources_ui_file, self)
        self.setModal(True)
        self.setWindowTitle(f'Edit {TxM.add_spaces_camel(table_name)}')
        self.updated = False

        self.add_pushButton.hide()
        self.commit_pushButton.setAutoDefault(False)
        self.cancel_pushButton.setAutoDefault(False)

        self.parent_id: int = None
        self.parent_type: str = None
        self.table_item_ids: list = None
        for key, value in kwargs.items():
            setattr(self, key, value)
        if isinstance(self.parent_id, str):
            self.parent_id = int(self.parent_id)

        self.table = TxM.remove_spaces(table_name)
        self.msg = QtW.QMessageBox()
        self.edited_timer = QtC.QTimer(self)
        self.model = None
        self.tree_model = None
        self.proxy_model = None
        self.edited_indexes = []
        self.combo_tree_model = None
        self.name_column = None
        self.name_header = None
        self.show_cols = []
        self.where = ''
        if self.table == 'Aliquots':
            self.show_cols = settings.value('aliquot_edit_columns')
            self.parent_id_header = 'SampleID' if self.parent_type == 'Sample' else None
            if self.parent_id_header and self.parent_id:
                self.where = f' WHERE {self.parent_id_header} = {self.parent_id}'
            elif self.parent_id_header and self.table_item_ids:
                # If no parent ID header is set, get the list of parent IDs matching the item IDs
                if len(self.table_item_ids) == 1:
                    aliquot_where = f' WHERE AliquotID = {self.table_item_ids[0]}'
                elif len(self.table_item_ids) > 1:
                    aliquot_where = f' WHERE AliquotID IN {tuple(self.table_item_ids)}'
                else:
                    aliquot_where = f' WHERE AliquotID IS NULL'
                parent_ids = columns_as_list_current(
                    f'SELECT SampleID FROM Aliquots {aliquot_where}', ['SampleID'])[0]
                if len(parent_ids) == 1:
                    self.where = f' WHERE {self.parent_id_header} = {parent_ids[0]}'
                elif len(parent_ids) > 1:
                    self.where = f' WHERE {self.parent_id_header} IN {tuple(parent_ids)}'
            elif self.table_item_ids is not None:
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
        self.edit_index = QtC.QModelIndex()
        self.msg = QtW.QMessageBox(self)
        self.close_by_dialog = False
        self.tabbed_from_editor = False

        self.table_headers = get_headers(self.table)

        create_savepoint('before_edit')

        self.edit_treeView.selectionModel().currentChanged.connect(self.on_index_change)
        self.edit_treeView.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.edit_treeView.customContextMenuRequested.connect(self.show_context_menu)
        self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        self.cancel_pushButton.clicked.connect(self.rollback)
        self.edit_treeView.selectionModel().currentRowChanged.connect(self.on_row_change)
        self.edit_treeView.doubleClicked.connect(self.display_widget)
        self.search_lineEdit.returnPressed.connect(self.search)

        self.loading_manager.close_loading_dialog('Loading', f'Opening edit window for {self.table}...')
        logger_setup.get_logger().info(f'Finished opening edit window for {self.table}')

    def create_model(self):
        query_args = {'show_columns': self.show_cols, 'where': self.where,
                      'group_col': f'{self.show_cols[0]}', 'order_col': f'{self.name_header}'}
        view_query = ViewQuery(self.table, True, **query_args)
        table_query = view_query.table_query
        self.model = SQLiteTableModel(table_query)
        if self.model.last_error:
            logger_setup.get_logger().critical(f'Error displaying {self.table} table')
            logger_setup.get_logger().debug(f'Error: {self.model.last_error}')
            return
        self.model.set_table(self.table)
        if self.tree_model:
            self.tree_model.deleteLater()
        self.tree_model = TreeModel(self.model)
        # self.tree_model.save_state.connect(
        #     lambda: save_expanded_state(self.table, self.edit_treeView))
        # print('Created the tree model')
        self.display_tree()
        self.edit_treeView.selectionModel().currentChanged.connect(self.on_index_change)
        self.updated_timestamp = time.time()

    # def on_tree_edited(self):
    #     self.edited_timer.setSingleShot(True)
    #     self.edited_timer.timeout.connect(self.create_model)
    #     self.edited_timer.start(100)

    def search(self):
        self.search_lineEdit: QtW.QLineEdit
        self.tree_proxy_model.setRecursiveFilteringEnabled(True)
        search_expression = QtC.QRegularExpression(self.search_lineEdit.text(),
                                                   options=QtC.QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.tree_proxy_model.setFilterRegularExpression(search_expression)
        if self.search_lineEdit.text() != '':
            self.edit_treeView.expandAll()

    def optimizeVerticalResize(self, logical_index, old_size, new_size):
        """Trigger a delayed row height update when the user resizes the window vertically."""
        self.resize_timer.start(250)  # Add a slight delay to avoid excessive updates

    def resizeRowsOptimized(self):
        """Resize rows only when resizing stops."""
        self.edit_treeView.resizeRowsToContents()

    def show_context_menu(self, pos):
        """
        Show a context menu when right-clicking on a table or tree view
        :param pos: The position of the mouse click
        :return:
        """
        self.edit_treeView: QtW.QTreeView
        indexes = self.edit_treeView.selectedIndexes()
        if not indexes:
            return
        for index in indexes:
            if not index.isValid():
                return
        tree_menu = TreeContextMenu()
        tree_menu.set_view(self.edit_treeView, True, False, False)
        clear_action = tree_menu.addAction('Clear selected values')
        single_column = False
        for index in indexes:
            if index.column() != indexes[0].column():
                single_column = False
                break
            single_column = True
        if single_column:
            set_selected_action = tree_menu.addAction('Set selected values')
        else:
            set_selected_action = None
        action = tree_menu.exec(self.edit_treeView.viewport().mapToGlobal(pos))
        if action:
            self.tree_context_menu(action)

    def tree_context_menu(self, action: QtG.QAction):
        """
        Context menu for tree views
        :param action: The action selected from the context menu
        :return:
        """
        self.edit_treeView: QtW.QTreeView
        indexes = self.edit_treeView.selectedIndexes()
        if 'Add' in action.text() or 'Insert' in action.text():
            self.add_popup(action)
        elif 'Expand' in action.text() or 'Collapse' in action.text():
            expand_collapse(self.edit_treeView, action)
        elif 'Delete' in action.text():
            self.delete_item()
        elif 'Clear' in action.text():
            self.clear_data()
        elif 'Set selected' in action.text():
            self.determine_widget(indexes[0])
            if self.lineEdit:
                dlg = SetSelectedValues(self, self.lineEdit)
                if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
                    self.lineEdit = dlg.widget
                    self.loading_manager.show_loading_dialog('Loading', f'Loading...')
                    self.save_lineedit_data()
                    self.loading_manager.close_loading_dialog('Loading', f'Loading...')
                    # self.display_tree()
                else:
                    self.destroy_lineedit()
            elif self.combo:
                dlg = SetSelectedValues(self, self.combo)
                if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
                    self.combo = dlg.widget
                    self.loading_manager.show_loading_dialog('Loading', f'Loading...')
                    self.save_dropdown_data()
                    self.loading_manager.close_loading_dialog('Loading', f'Loading...')
                    # self.display_tree()
                else:
                    self.destroy_dropdown()

    def display_tree(self):
        logger_setup.get_logger().info(f'Displaying {self.table} table')
        self.loading_manager.show_loading_dialog('Loading', f'Displaying {self.table}...')
        self.name_column = get_name_column(self.table)
        self.name_header = get_headers(self.table)[self.name_column]
        self.proxy_model = TreeSortFilterProxyModel()
        if self.table_item_ids:
            self.proxy_model.filter_ids = self.table_item_ids
            self.proxy_model.filter_column = 1  # Tree ID column
        self.proxy_model.setSourceModel(self.tree_model)
        self.edit_treeView.setModel(self.proxy_model)
        self.edit_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
        for column in range(self.proxy_model.columnCount()):
            header = self.proxy_model.headerData(column, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            if 'ID' in header or 'Row' in header:
                self.edit_treeView.hideColumn(column)
            else:
                self.edit_treeView.resizeColumnToContents(column)
        self.edit_treeView.setSortingEnabled(False)
        self.edit_treeView.setDragEnabled(True)
        self.edit_treeView.setAcceptDrops(True)
        self.edit_treeView.setDropIndicatorShown(True)
        self.edit_treeView.setDragDropMode(QtW.QAbstractItemView.DragDropMode.InternalMove)
        self.edit_treeView.setDefaultDropAction(QtC.Qt.DropAction.MoveAction)
        self.edit_treeView.setSelectionMode(QtW.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.edit_treeView.setSelectionBehavior(QtW.QAbstractItemView.SelectionBehavior.SelectItems)
        restore_expanded_state(self.table, self.edit_treeView)
        # self.tree_model.save_state.connect(lambda: save_expanded_state(self.table, self.edit_treeView))

        # Optimize window resizing
        self.resize_timer = QtC.QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.resizeRowsOptimized)

        # # Connect resizing events
        # self.edit_treeView.horizontalHeader().sectionResized.connect(self.optimizeVerticalResize)

        self.loading_manager.close_loading_dialog('Loading', f'Displaying {self.table}...')
        logger_setup.get_logger().info(f'Display {self.table} table complete')
        # self.tree_model.dataEdited.connect(self.on_tree_edited)

    def display_widget(self):
        if len(self.edit_treeView.selectedIndexes()) == 0:
            logger_setup.get_logger().info(f'No indexes selected for {self.table}')
            return
        elif len(self.edit_treeView.selectedIndexes()) > 1:
            logger_setup.get_logger().error('Right-click to edit multiple selections')
            return
        tree_index = self.edit_treeView.selectedIndexes()[0]
        self.determine_widget(tree_index)
        if self.lineEdit is not None and self.edit_index.isValid():
            self.display_lineedit()
        elif self.combo is not None and self.combo_index.isValid():
            self.display_dropdown()

    def determine_widget(self, tree_index):
        logger_setup.get_logger().info(f'Determining {self.table} widget')
        if not tree_index.isValid():
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
        header = self.tree_model.headerData(tree_index.column(), QtC.Qt.Orientation.Horizontal,
                                       QtC.Qt.ItemDataRole.DisplayRole)
        if header == self.name_header:
            # The column is the name column for the table. This should be edited with a line edit.
            self.create_lineedit()
            return
        header = header.replace(' ', '')
        self.dropdown_table = ''
        columns = None
        if header in SQLUtils.many_editable[self.table].keys():
            columns = SQLUtils.many_editable[self.table]
        elif header in SQLUtils.one_editable[self.table].keys():
            columns = SQLUtils.one_editable[self.table]
        elif header in SQLUtils.non_editable[self.table]:
            logger_setup.get_logger().error(f'{get_readable_header(header)} is not editable')
            return
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
        if len(self.edit_treeView.selectedIndexes()) > 1:
            self.edit_index = QtC.QModelIndex()
            text_items = []
            for tree_index in self.edit_treeView.selectedIndexes():
                item_text = tree_index.data(QtC.Qt.ItemDataRole.DisplayRole)
                if item_text not in text_items:
                    text_items.append(item_text)
            if len(text_items) == 1:
                self.lineEdit.setText(text_items[0])
            elif len(text_items) > 1:
                self.lineEdit.setText('-')
            else:
                self.lineEdit.setText('')
        else:
            self.edit_index = self.edit_treeView.selectedIndexes()[0]
            tree_index = self.edit_index
            # self.lineEdit.setValidator(QtG.QRegularExpressionValidator(QtC.QRegularExpression("[0-9]*")))
            if not tree_index.data(QtC.Qt.ItemDataRole.DisplayRole):
                self.lineEdit.setText('')
            else:
                self.lineEdit.setText(str(tree_index.data(QtC.Qt.ItemDataRole.DisplayRole)))
                self.lineEdit.selectAll()

    def display_lineedit(self):
        self.lineEdit.returnPressed.connect(self.save_lineedit_data)
        self.lineEdit.editingFinished.connect(self.save_lineedit_data)
        self.edit_treeView.setIndexWidget(self.edit_treeView.selectedIndexes()[0], self.lineEdit)
        self.lineEdit.setFocus()

    def save_lineedit_data(self):
        logger_setup.get_logger().info('Saving data from line edit')
        if self.lineEdit is not None:
            edit_text = self.lineEdit.text()
            if not self.edit_index.isValid():
                proxy_indexes =  self.edit_treeView.selectedIndexes()
            else:
                proxy_indexes = [self.edit_index]
            tree_indexes = []
            for proxy_index in proxy_indexes:
                tree_index = self.proxy_model.mapToSource(proxy_index)
                tree_indexes.append(tree_index)

            header = self.proxy_model.headerData(proxy_indexes[0].column(), QtC.Qt.Orientation.Horizontal,
                                                QtC.Qt.ItemDataRole.DisplayRole)
            col = None
            table = None
            for key, value in SQLUtils.table_attributes_dict.items():
                if header in value:
                    col = value.index(header)
                    table = key
                    break
            if col is None or table is None:
                logger_setup.get_logger().critical(f'Could not find {get_readable_header(header)} in table attributes')
                self.destroy_lineedit()
                return False
            ids = []
            for tree_index in proxy_indexes:
                id = self.tree_model.index(tree_index.row(), 1, tree_index.parent()).data(QtC.Qt.ItemDataRole.DisplayRole)
                if id not in ids:
                    ids.append(id)
            query = QtS.QSqlQuery()
            if len(ids) == 1:
                sql_where_str = f'= {ids[0]}'
            elif len(ids) > 1:
                sql_where_str = f'IN {tuple(ids)}'
            else:
                logger_setup.get_logger().error('No ids found to update')
                self.destroy_lineedit()
                return False
            if not query.exec(f'UPDATE {table} SET {header} = "{edit_text}" WHERE {self.table_headers[0]} {sql_where_str}'):
                logger_setup.get_logger().critical(f'Failed to update {get_readable_header(header)} for {ids}: {query.lastError().text()}')
                self.destroy_lineedit()
                return False
            for tree_index in tree_indexes:
                if not self.tree_model.setData(tree_index, edit_text, QtC.Qt.ItemDataRole.EditRole):
                    logger_setup.get_logger().critical(f'Failed to set data in the table')
                    self.destroy_lineedit()
                    return
            for index in proxy_indexes:
                if index in self.edited_indexes:
                    self.edited_indexes.remove(index)
            if self.edit_treeView.currentIndex() == self.edit_index:
                self.tabbed_from_editor = False
            logger_setup.get_logger().info('Data saved from line edit')
            self.updated = True
            # self.on_tree_edited()
            self.destroy_lineedit()
            # self.display_tree()
            return True

    def destroy_lineedit(self):
        try:
            self.lineEdit.editingFinished.disconnect(self.save_lineedit_data)
            self.lineEdit.returnPressed.disconnect(self.save_lineedit_data)
        except TypeError:
            pass
        self.edit_treeView.setIndexWidget(self.edit_index, None)
        self.lineEdit = None
        self.edit_index = QtC.QModelIndex()
        self.edit_treeView.setFocus()

    def create_dropdown(self):
        logger_setup.get_logger().info(f'Displaying dropdown for {self.dropdown_table}')
        if len(self.edit_treeView.selectedIndexes()) > 1:
            self.combo_index = QtC.QModelIndex()
            proxy_indexes = self.edit_treeView.selectedIndexes()
        else:
            self.combo_index = self.edit_treeView.selectedIndexes()[0]
            proxy_indexes = [self.combo_index]
        self.combo_model = QtS.QSqlTableModel()
        self.combo = QtW.QComboBox()
        header = self.proxy_model.headerData(proxy_indexes[0].column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        header = header.replace(' ', '')
        set_table(self.combo_model, self.dropdown_table)
        if self.dropdown_table in SQLUtils.user_viewable_trees:
            self.combo = CheckableTreeCombobox()
            self.combo_tree_model = CheckableTreeModel()
            self.combo_tree_model.setSourceModel(self.combo_model)
            self.combo.setModel(self.combo_tree_model)
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
        for proxy_index in proxy_indexes:
            selected_id = self.proxy_model.index(proxy_index.row(), 1, proxy_index.parent()).data(QtC.Qt.ItemDataRole.DisplayRole)
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
        if header in SQLUtils.not_null[self.table]:
            self.combo.not_null = True
        selected_text = self.combo_index.data(QtC.Qt.ItemDataRole.DisplayRole)
        self.combo.setCurrentText(selected_text)
        if self.combo.currentText() == '':
            # Make sure there is no selected index
            self.combo.setCurrentIndex(-1)
        # print(f"Selected text: {selected_text}")

    def display_dropdown(self):
        self.edit_treeView.setIndexWidget(self.edit_treeView.selectedIndexes()[0], self.combo)
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
        logger_setup.get_logger().info('Saving data from dropdown')
        self.edit_treeView: QtW.QTableView
        if self.combo is not None:
            combo = self.combo
        else:
            return False
        data_changed = False
        updated = False
        if not self.combo_index.isValid():
            proxy_indexes = self.edit_treeView.selectedIndexes()
        else:
            proxy_indexes = [self.combo_index]
        selected_ids = []
        for proxy_index in proxy_indexes:
            if not self.proxy_model.data(proxy_index, QtC.Qt.ItemDataRole.DisplayRole) and combo.currentText() == '':
                pass
            elif self.proxy_model.data(proxy_index, QtC.Qt.ItemDataRole.DisplayRole) != combo.currentText():
                data_changed = True
            item_id = self.proxy_model.index(proxy_index.row(), 1, proxy_index.parent()).data(QtC.Qt.ItemDataRole.DisplayRole)
            if item_id not in selected_ids:
                selected_ids.append(item_id)
        if not selected_ids:
            logger_setup.get_logger().critical('No selected ids found')
            self.destroy_dropdown()
            return False
        if not data_changed:
            logger_setup.get_logger().info('No data changed in the dropdown')
            self.destroy_dropdown()
            return True
        # Figure out which table to update and which IDs to update
        edit_table, edit_ids = self.determine_edit_table(selected_ids)
        if isinstance(combo.model(), QSortFilterProxyModel):
            # If the model is a proxy model, we need to get the source model
            combo_model = combo.model().sourceModel()
        else:
            combo_model = combo.model()
        if edit_table and edit_ids:
            # Save points are in these methods
            if '_' in edit_table:
                # Many-to-many table
                if not combo_model.update_many_table(edit_table, edit_ids):
                    self.destroy_dropdown()
                    return False
                updated = True
            else:
                if isinstance(self.combo_model,
                              CheckableSqlTableModel | CheckableSqlQueryModel | CheckableTreeModel):
                    if not combo_model.update_other_table(edit_table, edit_ids):
                        self.destroy_dropdown()
                        return False
                    if combo_model.tableName() == 'Samples' and edit_table == 'Aliquots':
                        # Moved aliquot to another sample
                        aliquot_name = get_name_from_id(edit_table, edit_ids[0])
                        sample_name = get_name_from_id(combo_model.tableName(), combo_model.checked_ids[0])
                        self.msg.information(self, 'Success', f'Moved aliquot {aliquot_name} to sample {sample_name}',
                                             QtW.QMessageBox.StandardButton.Ok)
                else:
                    clicked_id = get_id_from_name(self.combo_model.tableName(), combo.currentText())
                    if not clicked_id:
                        logger_setup.get_logger().error(f'No ID found for {combo.currentText()}')
                        self.destroy_dropdown()
                        return False
                    header = self.tree_model.headerData(proxy_indexes[0].column(), QtC.Qt.Orientation.Horizontal,
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
                        logger_setup.get_logger().critical(f'Failed to update {get_readable_header(header)} for {len(edit_ids)} {edit_table}')
                        logger_setup.get_logger().debug(f'Query: {query.lastQuery()}')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        rollback_savepoint('before_edit_id')
                        self.destroy_dropdown()
                        return False
                    release_savepoint('before_edit_id')
                updated = True
        if updated:
            for proxy_index in proxy_indexes:
                tree_index = self.proxy_model.mapToSource(proxy_index)
                new_text = self.determine_update_text(tree_index, combo_model, edit_table)
                if not self.tree_model.setData(tree_index, new_text, QtC.Qt.ItemDataRole.EditRole):
                    logger_setup.get_logger().critical(f'Failed to set data in the table')
                    self.destroy_dropdown()
                    return False
                print(f'New text: {self.tree_model.data(tree_index, QtC.Qt.ItemDataRole.DisplayRole)}')
                if proxy_index in self.edited_indexes:
                    self.edited_indexes.remove(proxy_index)
        self.updated_timestamp = time.time()
        # if self.edit_treeView.currentIndex() == self.combo_index:
        #     self.tabbed_from_editor = False
        self.combo = combo
        logger_setup.get_logger().info('Data saved from dropdown')
        self.destroy_dropdown()
        return True

    def destroy_dropdown(self):
        # combo.activated.disconnect(self.save_dropdown_data)
        try:
            self.combo.view().removeEventFilter(self)
        except TypeError:
            pass
        try:
            self.combo.add_triggered.disconnect(self.add_tag_popup)
            self.combo.edit_triggered.disconnect(self.edit_tag_popup)
        except TypeError:
            pass
        self.edit_treeView.setIndexWidget(self.combo_index, None)
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
                            aliquot_ids, spot_ids, upb_analysis_ids = find_current_sub_items(selected_ids)
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

    def determine_update_text(self, model_index: QtC.QModelIndex, combo_model, edit_table: str):
        if self.combo.currentText() == '-':
            # If the current text is '-', data were partially changed, so we need to compare the current and new selections
            old_text = model_index.data(QtC.Qt.ItemDataRole.DisplayRole)
            if not old_text:
                old_values = []
            else:
                old_values = old_text.split('; ')
            if isinstance(combo_model, CheckableTreeModel):
                checked_ids, partially_checked_ids, checked_indices, partially_checked_indices = (
                    combo_model.traverse_checkable_tree(QtC.QModelIndex()))
            elif isinstance(combo_model, CheckableSqlTableModel | CheckableSqlQueryModel):
                checked_ids, partially_checked_ids = combo_model.return_checked_ids()
            else:
                return self.combo.currentText()
            if '_' in edit_table:
                name_table = edit_table.split('_')[1]
            else:
                name_table = edit_table
            checked_names = []
            for checked_id in checked_ids:
                name = get_name_from_id(name_table, checked_id)
                if name and name not in checked_names:
                    checked_names.append(name)
            partially_checked_names = []
            for partially_checked_id in partially_checked_ids:
                name = get_name_from_id(name_table, partially_checked_id)
                if name and name not in partially_checked_names:
                    partially_checked_names.append(name)
            new_values = []
            for value in old_values:
                # Only add values that are checked or partially checked
                if (value in checked_names or value in partially_checked_names) and value not in new_values:
                    new_values.append(value)
            for value in checked_names:
                # Add any new checked values that were not in the old values
                if value not in new_values and value not in new_values:
                    new_values.append(value)
            if new_values:
                return '; '.join(new_values)
            else:
                return self.combo.currentText()
        else:
            # If the current text is not '-', we can just return it
            return self.combo.currentText()

    def set_selected_value_dialog(self, table, indexes):
        # Get the selected value from the indexes
        selected_value = ''
        current_values = []
        for tree_index in indexes:
            current_values.append(tree_index.data(QtC.Qt.ItemDataRole.DisplayRole))
        # Open dialog to set the selected values

    def clear_data(self):
        logger_setup.get_logger().info('Clearing selected values')
        if self.lineEdit is not None:
            self.save_lineedit_data()
        if self.combo is not None:
            self.save_dropdown_data()
        indexes = self.edit_treeView.selectedIndexes()
        columns = {}
        rows = []
        for tree_index in indexes:
            header = self.model.headerData(tree_index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            if header in SQLUtils.not_null[self.table]:
                logger_setup.get_logger().error(f'{get_readable_header(header)} cannot be empty')
                return
            query, virtual, stored, columns = get_columns(self.table)
            if f'"{header}"' in virtual or f'"{header}"' in stored:
                logger_setup.get_logger().error(f'{get_readable_header(header)} is auto-generated and not editable')
                return
            if header not in columns.keys():
                columns[header] = []
            rows.append(tree_index.row())
            id = self.tree_model.index(tree_index.row(), 1, tree_index.parent()).data(QtC.Qt.ItemDataRole.DisplayRole)
            if id not in columns[header]:
                columns[header].append(id)
        if not columns:
            logger_setup.get_logger().error('No selected IDs found')
            return
        create_savepoint('before_clear')
        for column, ids in columns.items():
            # Set the selection to a single column
            edit_indexes = []
            for tree_index in indexes:
                header = self.tree_model.headerData(tree_index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
                if header == column:
                    edit_indexes.append(tree_index)
            if not edit_indexes:
                logger_setup.get_logger().error('No indexes found to clear')
                rollback_savepoint('before_clear')
                return
            if edit_indexes != self.edit_treeView.selectedIndexes():
                # The indexes we need to edit are not the same as the currently selected indexes, so we need to update the selection
                # Disconnect the selection model to prevent methods from triggering
                try:
                    self.edit_treeView.selectionModel().currentChanged.disconnect(self.on_index_change)
                except TypeError:
                    pass
                # Clear the selection
                self.edit_treeView.selectionModel.clearSelection()
                selection = QtC.QItemSelection()
                # Select the indexes to edit
                for index in edit_indexes:
                    selection.select(index, index)
                self.edit_treeView.selectionModel.select(selection, QtC.QItemSelectionModel.SelectionFlag.Select)
                # Reconnect the selection model signal
                self.edit_treeView.selectionModel().selectionChanged.connect(self.on_index_change)
            # Determine which widget to create and display
            self.determine_widget(tree_index)
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

    def delete_item(self):
        save_expanded_state(self.table, self.edit_treeView)
        tree_indexes = []
        for tree_index in self.edit_treeView.selectedIndexes():
            if tree_index.column() == 0 and tree_index not in tree_indexes:
                tree_indexes.append(tree_index)
        item_ids = get_selected_tree_ids(self.tree_model, tree_indexes)[0]
        if not item_ids:
            return

        # Look for any children of the selected items
        def get_children(item_id):
            delete_children = []
            children = self.tree_model.find_children(item_id)
            if children:
                for child in children:
                    if child not in delete_children:
                        delete_children.append(child)
                        delete_children.extend(get_children(child))
            return delete_children

        all_children = []
        for item_id in item_ids:
            children_ids = get_children(item_id)
            if children_ids:
                all_children.extend(children_ids)
        if self.delete_question(item_ids, all_children):
            for item_id in item_ids:
                item = self.tree_model.find_id_in_tree(item_id)
                parent_id = item.data(1)
                parent_row = item.data(2)
                self.tree_model.removeItem(item_id, parent_row, parent_id)
            self.updated = True

    def delete_question(self, item_ids, children: list):
        save_expanded_state(self.table, self.edit_treeView)
        if children:
            child_string = f' and all {len(children)} children {self.table}'
        else:
            child_string = ''
        msg_box = QtW.QMessageBox()
        msg_box.setIcon(QtW.QMessageBox.Icon.Question)
        if self.table == 'Aliquots':
            # Aliquots have a special case where they are related to Samples, Spots, and UPbAnalyses
            aliquot_spot_ids, aliquot_upb_ids = find_current_sub_items(item_ids, self.table)
            child_spot_ids, child_upb_analysis_ids = find_current_sub_items(children, self.table)
            total_spot_ids = aliquot_spot_ids + child_spot_ids
            total_upb_ids = aliquot_upb_ids + child_upb_analysis_ids
            msg_box.setText(f'Are you sure you want to delete these {self.table}{child_string}?\n'
                            f'Associated with {len(total_spot_ids)} spots and {len(total_upb_ids)} U-Pb analyses')
        else:
            msg_box.setText(f'Are you sure you want to delete these {self.table}{child_string}?')
        msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

    def on_index_change(self, selected, deselected):
        # Close and save the data from any open widgets
        if selected == deselected:
            return
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
                tree_index = self.tree_model.index(self.edited_indexes[0].row(), column, self.edited_indexes[0].parent())
                if tree_index.isValid():
                    self.edit_treeView.selectionModel().select(tree_index, QtC.QItemSelectionModel.SelectionFlag.Select)
                    self.edit_treeView.scrollTo(tree_index)
            else:
                tree_index_left = self.tree_model.index(self.edited_indexes[0].row(), 0, self.edited_indexes[0].parent())
                tree_index_right = self.tree_model.index(self.edited_indexes[0].row(), self.edited_indexes[0].columnCount() - 1, self.edited_indexes[0].parent())
                selection = QtC.QItemSelection(tree_index_left, tree_index_right)
                self.edit_treeView.selectionModel().select(selection,
                                                            QtC.QItemSelectionModel.SelectionFlag.ClearAndSelect | QtC.QItemSelectionModel.SelectionFlag.Rows)
                self.edit_treeView.scrollTo(tree_index_left)
            self.edit_treeView.setFocus()

        # Check if the row has changed and if the model has been edited
        if selected.parent() != deselected.parent() or selected.row() != deselected.row():
            if not self.edited_indexes:
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
        row = self.edited_indexes[0].row()
        parent = self.edited_indexes[0].parent()
        row_id = self.tree_model.index(row, 1, parent).data(QtC.Qt.ItemDataRole.DisplayRole)
        row_id_header = self.table_headers[0]
        update_cols = {}
        update_col_values = {}
        where_col_ids = {}
        for key in SQLUtils.one_editable.keys():
            update_cols[key] = []
            update_col_values[key] = []
            where_col_ids[key] = []
        query = QtS.QSqlQuery()
        for tree_index in self.edited_indexes:
            header = self.tree_model.headerData(tree_index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            header_found = False
            if header in ['SampleName', 'AliquotName', 'SpotName', 'ColumnName'] and not header_found:
                if header.split('Name')[0] in self.table :
                    # This is the name column for this table
                    text = tree_index.data(QtC.Qt.ItemDataRole.DisplayRole)
                    update_cols[self.table].append(header)
                    update_col_values[self.table].append(text)
                    header_found = True
                else:
                    # We need to look at two tables
                    other_table = f'{header.split("Name")[0]}s'
                    other_name_header = header
                    other_id_header = get_headers(other_table)[0]
                    other_item_name = tree_index.data(QtC.Qt.ItemDataRole.DisplayRole)
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
                                text = tree_index.data(QtC.Qt.ItemDataRole.DisplayRole)
                                if text == '' or text is None:
                                    id = 'Null'
                                else:
                                    id = self.retrieve_id(values[header], text)
                                    if not id:
                                        continue
                                update_cols[key].append(header)
                                update_col_values[key].append(id)
                                if key != self.table:
                                    logger_setup.get_logger().critical(f'Unexpected table {key} for header {header}')
                                    logger_setup.get_logger().debug(f'This scenario has not been tested yet')
                                    return False
                                header_found = True
                                continue
                if not header_found:
                    # header is editable but does not need to be converted to an ID
                    text = tree_index.data(QtC.Qt.ItemDataRole.DisplayRole)
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
                    logger_setup.get_logger().debug(f'Failed query: {query.lastQuery()}')
                    return False
                logger_setup.get_logger().info(f'Updated {sql_cols} to {', '.join(str(val) for val in update_col_values[table])} in {table} where {table_headers[0]} = {item_id}')
        logger_setup.get_logger().info('Changes submitted')
        self.edited_indexes = []
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

    # def retrieve_checked_ids(self, table, values):
    #     if not values:
    #         return []
    #     table_headers = get_headers(table)
    #     id_header = table_headers[0]
    #     query = QtS.QSqlQuery()
    #     ids = []
    #     for value in values:
    #         if not query.exec(f'SELECT {id_header} FROM {table} WHERE {get_name_column(table)} = "{value}"'):
    #             logger_setup.get_logger().critical(f'Failed to get {get_name_column(table)} for {value}: {query.lastError().text()}')
    #             return None
    #         if query.next():
    #             ids.append(query.value(0))
    #         else:
    #             return None
    #     return ids

    def add_popup(self, action: QtG.QAction | None = None):
        dlg_args = add_tree_popup(self.edit_treeView, action)
        if dlg_args:
            dlg = AddTreeTags(self, self.table, **dlg_args)
        else:
            dlg = AddTreeTags(self, self.table)
        if not dlg:
            return
        self.loading_manager.show_loading_dialog('Loading', f'Opening add window for {self.table}...')
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
        # self.on_tree_edited()
        # self.display_tree()

    def add_tag_popup(self, combo: QtW.QComboBox, action: QtG.QAction | None = None):
        model = combo.model()
        if isinstance(combo.view(), QtW.QTreeView):
            if not isinstance(model, TreeModel):
                model, indexes = find_tree_model(model, None)
            if model:
                table = model.table
            else:
                logger_setup.get_logger().critical(f"Error editing table")
                logger_setup.get_logger().debug(f"Error: No tree model found")
                return
        elif isinstance(model, QtC.QSortFilterProxyModel):
            model = model.sourceModel()
            table = model.tableName()
        else:
            table = combo.model().tableName()
        logger_setup.get_logger().info(f'Add called for {table}')
        dlg = None
        if table in SQLUtils.user_viewable_trees:
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
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
            # Clear and recreate this combo box
            self.destroy_dropdown()
            self.display_widget()
            self.combo.showPopup()

    def edit_tag_popup(self):
        combo = self.sender()
        model = combo.model()
        if isinstance(model, QtC.QSortFilterProxyModel):
            model = model.sourceModel()
        if isinstance(combo.view(), QtW.QTreeView):
            if not isinstance(model, TreeModel):
                model, indexes = find_tree_model(model, None)
            if model:
                table = model.table
            else:
                logger_setup.get_logger().critical(f"Error editing table")
                logger_setup.get_logger().debug(f"Error: No tree model found")
                return
        else:
            table = model.tableName()
        if table in SQLUtils.user_viewable_trees:
            dlg = EditTree(self, table)
        elif table != get_view_from_table(table):
            dlg = EditView(self, table)
        else:
            dlg = EditTable(self, table)
        if dlg is None:
            return
        logger_setup.get_logger().info(f"Showing {table} edit dialog")
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
            # Clear and recreate this combo box
            self.destroy_dropdown()
            self.display_widget()
            self.combo.showPopup()

    def rollback(self):
        save_expanded_state(self.table, self.edit_treeView)
        rollback_savepoint('before_edit')
        self.updated = False
        self.reject()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        if not self.on_row_change(QtC.QModelIndex(), self.edit_treeView.currentIndex()):
            logger_setup.get_logger().critical('Failed to save changes')
            return
        else:
            release_savepoint('before_edit')
            save_expanded_state(self.table, self.edit_treeView)
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
        self.saveWindowState()
        if not self.close_by_dialog:
            if not self.on_row_change(QtC.QModelIndex(), self.edit_treeView.currentIndex()):
                logger_setup.get_logger().critical('Failed to save changes')
                self.discard_question()
            elif self.updated:
                self.discard_question()
                event.ignore()
            else:
                logger_setup.get_logger().info(f'Closing {self.table} edit dialog')
                event.accept()
        else:
            logger_setup.get_logger().info(f'Closing {self.table} edit dialog')
            event.accept()

    def saveWindowState(self):
        settings.setValue("ui/EditTreeView/pos", self.pos())
        settings.setValue("ui/EditTreeView/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/EditTreeView/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/EditTreeView/size", defaultValue=QSize(810, 569)))

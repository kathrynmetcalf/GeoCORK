import os
import sys
from pathlib import Path
import sqlite3
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6.uic import loadUi

import logger_setup
from Functions.Database_manager import update_database
from Functions.Settings_manager import settings
from Functions.LoadingDialog_manager import LoadingDialogManager
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Widget_classes import (TreeModel, TreeContextMenu, expand_collapse, save_expanded_state, restore_expanded_state,
                                      get_headers, get_name_column, description_column, set_table
                                      )
import Functions.Text_manipulations as TxM
from Functions.Check_triggers import validate_insert, validate_update, update_modified_timestamp

class AddTreeTags(QtW.QDialog):
    # def __init__(self, table: str, add_item: str = 'child', item_id=None, parent_id=None, parent_row=None, *argv):
    def __init__(self, parent_window, table: str, **kwargs):
        super().__init__(parent_window)

        logger_setup.get_logger().info(f'Starting AddTreeTags dialog for {table}...')
        self.loading_manager = LoadingDialogManager.get_instance()
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "AddTreeTags.ui")
        loadUi(sources_ui_file, self)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | QtC.Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle(f'Add tags to {TxM.add_spaces_camel(table)}')
        self.updated = False

        self.table = table
        self.source_model = QtS.QSqlTableModel()
        set_table(self.source_model, self.table)
        self.id_header = self.source_model.record().fieldName(0)
        self.parent_id_header = self.source_model.record().fieldName(1)
        self.parent_row_header = self.source_model.record().fieldName(2)
        self.item_name_header = self.source_model.record().fieldName(3)
        self.tree_model = TreeModel(self.source_model)
        self.tree_proxy_model = QtC.QSortFilterProxyModel()
        self.tree_proxy_model.setSourceModel(self.tree_model)
        self.table_name = TxM.add_spaces_camel(self.table)
        self.selectTags_label.setText(self.table_name)
        self.cancel_pushButton.setAutoDefault(False)

        self.msg = QtW.QMessageBox(self)
        self.add_item: str = 'child'
        self.item_id: int = None
        self.parent_id: int = None
        self.parent_row: int = None
        for key, value in kwargs.items():
            setattr(self, key, value)
        # if add_item is not one of the keys, set it to 'child'
        if 'add_item' not in kwargs.keys():
            self.add_item = 'child'
        self.columns = get_headers(self.table)
        self.name_column = self.columns[get_name_column(self.table)]
        self.description_column = self.columns[description_column(self.table)]
        self.existing_names = []

        self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.tree_proxy_model.setFilterKeyColumn(0)   # search first column only, look for distinct names
        # self.newName_lineEdit.textChanged.connect(self.search)

        self.close_by_dialog = False
        self.clear_warning()
        self.display_tags()
        create_savepoint('before_add')
        self.tree_model.dataEdited.connect(self.update_proxy)
        self.tree_model.save_state.connect(lambda: save_expanded_state(self.table, self.tree_model, self.tags_treeView))
        self.ok_pushButton.clicked.connect(self.add_tree_tag)
        self.cancel_pushButton.clicked.connect(self.discard_question)
        self.finish_pushButton.clicked.connect(self.commit)
        self.loading_manager.close_loading_dialog('Loading', f'Opening add window for {self.table}...')

    def add_label(self):
        if self.add_item == 'child':
            query = QtS.QSqlQuery()
            if self.parent_id:
                query.prepare(
                f'SELECT * FROM {self.table} WHERE {self.id_header} = {self.parent_id}')
                if not query.exec():
                    logger_setup.get_logger().error(f'Error selecting {self.id_header} {self.parent_id}: {query.lastError().text()}')
                    return
                query.next()
                parent_name = query.value(3)
            else:
                parent_name = 'top level'
            if self.item_id:
                query.prepare(
                f'SELECT * FROM {self.table} WHERE {self.id_header} = {self.item_id}')
                if not query.exec():
                    logger_setup.get_logger().error(f'Error selecting {self.id_header} {self.item_id}: {query.lastError().text()}')
                    return
                query.next()
                item_name = query.value(3)
            else:
                item_name = 'new item'
            if self.parent_row:
                row_name = f'row {self.parent_row + 1}'
            else:
                row_name = 'new row'
            self.adding_label.setText(f'Adding {item_name} to {parent_name} at {row_name}')
        else:
            self.adding_label.setText('Adding new parent item')

    def display_tags(self):
        self.tags_treeView.setModel(self.tree_model)
        self.tags_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
        self.tags_treeView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tags_treeView.hideColumn(1)  # Don't show ID column
        self.tags_treeView.hideColumn(2)  # Don't show parent ID column
        self.tags_treeView.hideColumn(3)  # Don't show parent row column
        restore_expanded_state(self.table, self.tree_model, self.tags_treeView)
        self.add_label()

        # Get a list of the existing tag names
        self.existing_names = []
        query = QtS.QSqlQuery()
        query.prepare(f'SELECT {self.name_column} FROM {self.table}')
        if not query.exec():
            logger_setup.get_logger().critical(
                f'Error selecting display column from {self.table}: {query.lastError().text()}')
            return False
        while query.next():
            self.existing_names.append(query.value(0))
        completer = QtW.QCompleter(self.existing_names)
        completer.setFilterMode(QtC.Qt.MatchFlag.MatchStartsWith)
        completer.setCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QtW.QCompleter.CompletionMode.PopupCompletion)
        self.newName_lineEdit.setCompleter(completer)

        restore_expanded_state(self.table, self.tree_model, self.tags_treeView)

    def show_context_menu(self, pos):
        menu = TreeContextMenu()
        # Only allow expanding and collapsing, no delete, add, or edit
        menu.set_view(self.tags_treeView, False, False, False)
        action = menu.exec(self.tags_treeView.viewport().mapToGlobal(pos))
        if action and ('Expand' in action.text() or 'Collapse' in action.text()):
            expand_collapse(self.tags_treeView, action)

    def clear_warning(self):
        self.warning_label.hide()

    def search(self):
        self.newName_lineEdit: QtW.QLineEdit
        self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.tree_proxy_model.setRecursiveFilteringEnabled(True)
        search_expression = QtC.QRegularExpression(self.newName_lineEdit.text())
        self.tree_proxy_model.setFilterRegularExpression(search_expression)

    def add_tree_tag(self):
        save_expanded_state(self.table, self.tree_model, self.tags_treeView)
        name = self.newName_lineEdit.text()
        description = self.newDescription_lineEdit.text()
        if self.parent_id == 'Null':
            if not self.tree_model.insertItem(name, description, None, self.parent_row):
                return False
            logger_setup.get_logger().info(f'Added {name} to top level of {self.table}')
        else:
            if not self.tree_model.insertItem(name, description, self.parent_id, self.parent_row):
                return False
            logger_setup.get_logger().info(f'Added {name} to {self.parent_id} in {self.table}')
        if self.add_item == 'parent': # Need to update the parent of all new child ids to the newly-added item
            query = QtS.QSqlQuery()
            query.prepare(
                f'SELECT * FROM {self.table} WHERE {self.item_name_header} = "{name}"')
            if not query.exec():
                logger_setup.get_logger().error(f'Error selecting {self.item_name_header} {name}: {query.lastError().text()}')
                return
            query.next()
            new_parent_id = query.value(0)
            if isinstance(new_parent_id, int):
                pID = f'= {new_parent_id}'
            else:  # If the parent ID is not an integer
                pID = 'IS NULL'
            for child in range(len(self.new_child_ids)):
                if not self.tree_model.moveItem(self.new_child_ids[child], self.new_parent_rows[child], pID):
                    return False
            logger_setup.get_logger().info(f'Updated parent of {self.new_child_ids} to {new_parent_id} in {self.table}')
        self.updated = True
        if self.parent_id:
            # Add it to the settings list of expanded items
            expanded_ids = settings.value(f'expanded_ids_{self.table}', [])
            expanded_ids.add(self.parent_id)
            settings.setValue(f'expanded_ids_{self.table}', expanded_ids)
        save_expanded_state(self.table, self.tree_model, self.tags_treeView)
        self.update_proxy()
        self.newName_lineEdit.clear()
        self.newDescription_lineEdit.clear()
        return True

    def update_proxy(self):
        if self.tree_proxy_model.sourceModel() == self.tree_model:
            self.tree_model.deleteLater()
        self.tree_model = TreeModel(self.source_model)
        self.tree_model.dataEdited.connect(self.update_proxy)
        self.tree_proxy_model.setSourceModel(self.tree_model)
        self.display_tags()

    def discard_question(self):
        msg_box = QtW.QMessageBox()
        msg_box.setIcon(QtW.QMessageBox.Icon.Question)
        msg_box.setText('Are you sure you want to discard all changes?')
        msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            self.rollback()
        else:
            pass

    def rollback(self):
        rollback_savepoint('before_add')
        save_expanded_state(self.table, self.tree_model, self.tags_treeView)
        self.reject()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        if self.newName_lineEdit.text():
            if not self.add_tree_tag():
                return False
        release_savepoint('before_add')
        logger_setup.get_logger().info(f'Changes committed to {self.table}')
        save_expanded_state(self.table, self.tree_model, self.tags_treeView)
        # Check if there is another existing savepoint. If not, go ahead and update the database
        if not SavepointManager.get_instance().active_savepoints():
            logger_setup.get_logger().info('No active save points - updating the database')
            update_database()
        self.accept()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def closeEvent(self, event: QtG.QCloseEvent):
        if not self.close_by_dialog:
            if self.updated:
                self.discard_question()
                event.ignore()
            else:
                logger_setup.get_logger().info(f'Closing {self.table} add dialog')
                event.accept()
        else:
            logger_setup.get_logger().info(f'Closing {self.table} add dialog')
            event.accept()


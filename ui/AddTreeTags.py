import os
import sys

from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import QPoint, QSize, QSortFilterProxyModel
from PyQt6.uic import loadUi

import Functions.Text_manipulations as TxM
import logger_setup
from Functions.Database_manager import update_database
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.Widget_classes import (TreeModel, TreeContextMenu, expand_collapse, save_expanded_state,
                                      restore_expanded_state, show_loading_dialog, close_loading_dialog,
                                      get_headers, get_name_column, description_column, set_table, ReadableProxyModel,
                                      get_id_from_name
                                      )


class AddTreeTags(QtW.QDialog):
    """
    A dialog window for adding tags to a tree table in the database. It can be used to add child items to an existing
    parent item, or to add a new parent item. The dialog allows the user to enter a name and description for the new
    item, and to select the parent item if applicable. The dialog also displays the existing items in the tree view,
    allowing the user to see the hierarchy of items and to select where to add the new item. A completer is provided for
    the name field to avoid duplicates, and a warning label is shown if a duplicate name is entered.
    """

    def __init__(self, parent_window, table: str, **kwargs):
        super().__init__(parent_window)
        logger_setup.get_logger().info(f'Starting AddTreeTags dialog for {table}...')
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "AddTreeTags.ui")
        loadUi(sources_ui_file, self)
        self.setModal(True)
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
        self.tree_proxy_model = ReadableProxyModel()
        self.tree_proxy_model.setSourceModel(self.tree_model)
        self.table_name = TxM.add_spaces_camel(self.table)
        self.selectTags_label.setText(self.table_name)
        self.cancel_pushButton.setAutoDefault(False)
        self.ok_pushButton.setAutoDefault(True)

        self.msg = QtW.QMessageBox(self)
        self.add_item: str = 'child'
        self.parent_id: int | None = None
        self.parent_row: int | None = None
        self.item_ids: list[int] = []
        self.old_parent_ids: list[int] = []
        self.old_parent_rows: list[int] = []
        for key, value in kwargs.items():
            setattr(self, key, value)
        # if add_item is not one of the keys, set it to 'child'
        if 'add_item' not in kwargs.keys():
            self.add_item = 'child'
        self.columns = get_headers(self.table)
        self.name_column = self.columns[get_name_column(self.table)]
        self.description_column = self.columns[description_column(self.table)]
        self.existing_names = set()

        self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.tree_proxy_model.setFilterKeyColumn(0)  # search first column only, look for distinct names
        # self.newName_lineEdit.textChanged.connect(self.search)

        self.close_by_dialog = False
        self.clear_warning()
        self.display_tags()
        create_savepoint('before_add')
        self.tree_model.dataEdited.connect(self.update_proxy)
        # self.tree_model.save_state.connect(lambda: save_expanded_state(self.table, self.tags_treeView))
        self.ok_pushButton.clicked.connect(self.add_tree_tag)
        self.cancel_pushButton.clicked.connect(self.discard_question)
        self.finish_pushButton.clicked.connect(self.commit)

        close_loading_dialog('Loading', f'Opening add window for {self.table}...')

    def add_label(self):
        """
        Adds a label to the dialog indicating what is being added. The label is based on the type of item being added
        (parent or child) and the current state of the dialog (whether a parent ID or item ID is set).
        :return:
        """
        if self.add_item == 'child':
            query = QtS.QSqlQuery()
            if self.parent_id:
                query.prepare(
                    f'SELECT * FROM {self.table} WHERE {self.id_header} = {self.parent_id}')
                if not query.exec():
                    logger_setup.get_logger().error(
                        f'Error selecting {self.id_header} {self.parent_id}: {query.lastError().text()}')
                    return
                query.next()
                parent_name = query.value(3)
            else:
                parent_name = 'top level'
            # if self.item_id:
            #     query.prepare(
            #         f'SELECT * FROM {self.table} WHERE {self.id_header} = {self.item_id}')
            #     if not query.exec():
            #         logger_setup.get_logger().error(
            #             f'Error selecting {self.id_header} {self.item_id}: {query.lastError().text()}')
            #         return
            #     query.next()
            #     item_name = query.value(3)
            # else:
            #     item_name = 'new item'
            if self.parent_row:
                row_name = f'row {self.parent_row + 1}'
            else:
                row_name = 'new row'
            self.adding_label.setText(f'Adding new item to {parent_name} at {row_name}')
        else:
            self.adding_label.setText('Adding new parent item')

    def display_tags(self):
        """
        Displays the existing tags in the tree view.
        """
        show_loading_dialog('Loading', f'Loading {self.table}...')
        self.tags_treeView.setModel(self.tree_proxy_model)
        self.tags_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
        self.tags_treeView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tags_treeView.hideColumn(1)  # Don't show ID column
        self.tags_treeView.hideColumn(2)  # Don't show parent ID column
        self.tags_treeView.hideColumn(3)  # Don't show parent row column
        restore_expanded_state(self.table, self.tags_treeView)
        self.add_label()

        # Get a list of the existing tag names
        self.existing_names = []
        query = QtS.QSqlQuery()
        query.prepare(f'SELECT {self.name_column} FROM {self.table}')
        if not query.exec():
            logger_setup.get_logger().critical(
                f'Error selecting display column from {self.table}: {query.lastError().text()}')
            close_loading_dialog('Loading', f'Loading {self.table}...')
            return False
        self.existing_names = set()
        while query.next():
            self.existing_names.add(query.value(0))
        completer = QtW.QCompleter(self.existing_names)
        completer.setFilterMode(QtC.Qt.MatchFlag.MatchStartsWith)
        completer.setCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QtW.QCompleter.CompletionMode.PopupCompletion)
        self.newName_lineEdit.setCompleter(completer)

        restore_expanded_state(self.table, self.tags_treeView)
        close_loading_dialog('Loading', f'Loading {self.table}...')

    def show_context_menu(self, pos: QtC.QPoint):
        """
        Shows the context menu for the tree view. Allows the user to expand or collapse the tree.
        :param pos:
        :return:
        """
        menu = TreeContextMenu()
        # Only allow expanding and collapsing, no delete, add, or edit
        menu.set_view(self.tags_treeView, False, False, False)
        action = menu.exec(self.tags_treeView.viewport().mapToGlobal(pos))
        if action:
            if action and ('Expand' in action.text() or 'Collapse' in action.text()):
                expand_collapse(self.tags_treeView, action)

    def clear_warning(self):
        """
        Hide the warning label if it is visible. Warning label is used when a duplicate name is entered.
        """
        self.warning_label.hide()

    def search(self):
        """
        Searches the tree view for items that match the text in the newName_lineEdit. The search is case-insensitive
        and uses a regular expression to match the text. The search is applied to the first column of the tree view.
        :return:
        """
        self.newName_lineEdit: QtW.QLineEdit
        self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.tree_proxy_model.setRecursiveFilteringEnabled(True)
        search_expression = QtC.QRegularExpression(self.newName_lineEdit.text())
        self.tree_proxy_model.setFilterRegularExpression(search_expression)

    def add_tree_tag(self) -> bool:
        """
        Adds a new tag to the tree view. If the add_item is 'child', it adds a child item to the selected parent item.
        If the add_item is 'parent', it adds a new parent item to the tree view. The name and description are taken from
        the newName_lineEdit and newDescription_lineEdit fields. If the name already exists, a warning label is shown
        and the function returns without adding the item. If the parent_ids is 'Null', it adds the item to the top level
        of the tree view. If the parent_ids is not 'Null', it adds the item to the specified parent item. If the add_item
        is 'parent', it updates the parent of all new child IDs to the newly-added item. The function returns True if
        the item was added successfully, or False if there was an error. It also updates the tree model and clears the
        newName_lineEdit and newDescription_lineEdit fields after adding the item. The function also updates the
        settings with the expanded state of the tree view and the parent ID of the newly-added item.
        :return: True if the item was added successfully, False otherwise.
        """
        show_loading_dialog('Adding item', f'Adding {self.newName_lineEdit.text()} to {self.table}...')
        save_expanded_state(self.table, self.tags_treeView)
        name = self.newName_lineEdit.text()
        description = self.newDescription_lineEdit.text()
        if self.add_item == 'child':
            if not self.parent_id or self.parent_id == 'Null':
                if not self.tree_model.insertItem(name, description, None, self.parent_row):
                    close_loading_dialog('Adding item', f'Adding {self.newName_lineEdit.text()} to {self.table}...')
                    return False
                logger_setup.get_logger().info(f'Added {name} to top level of {self.table}')
            else:
                if not self.tree_model.insertItem(name, description, self.parent_id, self.parent_row):
                    close_loading_dialog('Adding item', f'Adding {self.newName_lineEdit.text()} to {self.table}...')
                    return False
                logger_setup.get_logger().info(f'Added {name} to {self.parent_id} in {self.table}')
        elif self.add_item == 'parent':  # Need to update the parent of all new child ids to the newly-added item
            # Find the top-level parent ID in the list of old parent IDs
            top_parent_id, top_parent_row = self.tree_model.top_node(self.old_parent_ids)
            parent_id = top_parent_id
            parent_row = top_parent_row
            if not parent_id and not parent_row:
                # find all old parent IDs that are None or not integers and get the smallest row index
                parent_row = min((row for row, pid in zip(self.old_parent_rows, self.old_parent_ids) if pid is None or not isinstance(pid, int)), default=None)
            if not self.tree_model.insertItem(name, description, parent_id, parent_row):
                close_loading_dialog('Adding item', f'Adding {self.newName_lineEdit.text()} to {self.table}...')
                return False
            logger_setup.get_logger().info(f'Added new parent {name} to {self.table}')
            new_parent_id = get_id_from_name(self.table, name)
            if not new_parent_id or not isinstance(new_parent_id, int):
                # If the parent ID is None or not an integer, set it to NULL
                pID = 'IS NULL'
            else:  # If the parent ID is an integer
                pID = f'= {new_parent_id}'
            parent_row = 0
            for child in range(len(self.item_ids)):
                # Move only if the child currently has the old parent ID
                current_parent_ID = self.old_parent_ids[child] if isinstance(self.old_parent_ids[child], int) else None
                if current_parent_ID == parent_id:
                    if not self.tree_model.moveItem(self.item_ids[child], parent_row, pID):
                        close_loading_dialog('Adding item', f'Adding {self.newName_lineEdit.text()} to {self.table}...')
                        return False
                    parent_row += 1
            logger_setup.get_logger().info(f'Updated parent of {self.item_ids} to {new_parent_id} in {self.table}')
            if new_parent_id:
                # Add the new parent ID to the list of expanded IDs in the settings
                expanded_ids = settings.value(f'expanded_ids_{self.table}', [])
                expanded_ids.add(new_parent_id)
                settings.setValue(f'expanded_ids_{self.table}', expanded_ids)
        self.updated = True
        if self.parent_id:
            # Add it to the settings list of expanded items
            expanded_ids = settings.value(f'expanded_ids_{self.table}', [])
            expanded_ids.add(self.parent_id)
            settings.setValue(f'expanded_ids_{self.table}', expanded_ids)
        save_expanded_state(self.table, self.tags_treeView)
        # self.source_model.dataChanged.emit()
        self.update_proxy()
        self.newName_lineEdit.clear()
        self.newDescription_lineEdit.clear()
        close_loading_dialog('Adding item', f'Adding {name} to {self.table}...')
        return True

    def update_proxy(self):
        """
        Rebuilds the tree and updates the proxy model to reflect the changes made in the tree model. This is necessary
        to ensure that the tree view displays the most up-to-date information after adding or editing items in the database.
        :return:
        """
        if self.tree_proxy_model.sourceModel() == self.tree_model:
            self.tree_model.deleteLater()
        self.source_model.select()
        self.tree_model = TreeModel(self.source_model)
        self.tree_model.dataEdited.connect(self.update_proxy)
        self.tree_proxy_model.setSourceModel(self.tree_model)
        self.display_tags()

    def discard_question(self):
        """
        Displays a confirmation dialog asking the user if they want to discard all changes made in the dialog.
        :return:
        """
        self.cancel_pushButton.blockSignals(True)
        if self.updated:
            msg_box = QtW.QMessageBox()
            msg_box.setIcon(QtW.QMessageBox.Icon.Question)
            msg_box.setText('Are you sure you want to discard all changes?')
            msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
            response = msg_box.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                self.rollback()
            else:
                self.cancel_pushButton.blockSignals(False)
        else:
            logger_setup.get_logger().info(f'No changes made to {self.table}, closing dialog')
            self.rollback()


    def rollback(self):
        """
        Rolls back the changes to the database. Rejects the dialog and closes the window.
        """
        rollback_savepoint('before_add')
        self.updated = False
        save_expanded_state(self.table, self.tags_treeView)
        self.reject()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        """
        Commits the changes to the database. If there is an active savepoint, it is released.
        """
        if self.newName_lineEdit.text():
            if not self.add_tree_tag():
                return False
        release_savepoint('before_add')
        logger_setup.get_logger().info(f'Changes committed to {self.table}')
        save_expanded_state(self.table, self.tags_treeView)
        # Check if there is another existing savepoint. If not, go ahead and update the database
        if not SavepointManager.get_instance().active_savepoints():
            logger_setup.get_logger().info('No active save points - updating the database')
            if not update_database():
                logger_setup.get_logger().critical(f'Error updating and displaying the database')
                self.close_by_dialog = True
                self.close()
        self.accept()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def closeEvent(self, event: QtG.QCloseEvent):
        """
        Overridden close event to handle the user closing the dialog. If there are unsaved changes, it prompts the user
        to confirm whether they want to discard the changes or not before proceeding. If the dialog was closed by the
        user and no updates were made, it releases the savepoint and closes. If the dialog was closed by the dialog itself
        (e.g., after committing or discarding changes), it also releases the savepoint.
        :param QCloseEvent event:
        """
        if not self.close_by_dialog:
            if self.updated:
                self.discard_question()
                event.ignore()
            else:
                logger_setup.get_logger().info(f'Closing {self.table} add dialog')
                release_savepoint('before_add')
                event.accept()
        else:
            logger_setup.get_logger().info(f'Closing {self.table} add dialog')
            release_savepoint('before_add')
            event.accept()

    def saveWindowState(self):
        """
        Saves the current window state to the settings. This includes the position and size of the dialog.
        :return:
        """
        settings.setValue("ui/AddTreeTags/geometry", self.pos())
        settings.setValue("ui/AddTreeTags/size", self.size())

    def restoreWindowState(self):
        """
        Restores the window state from the settings. This includes the position and size of the dialog.
        :return:
        """
        self.move(settings.value("ui/AddTreeTags/geometry", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/AddTreeTags/size", defaultValue=QSize(400, 300)))


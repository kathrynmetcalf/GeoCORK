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
from Functions.Database_views import ViewQuery
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.Widget_classes import (close_loading_dialog, get_headers, get_name_column, update_modified_timestamp,
                                      bulk_update_parent_row)


class AddDataItem(QtW.QDialog):
    """Dialog for adding Samples, Aliquots, Grains, Spots, or Analyses with description"""
    def __init__(self, table: str, parent=None, **kwargs):
        super().__init__(parent)
        if not table:
            logger_setup.get_logger().critical('Error adding item: No table provided')
            logger_setup.get_logger().debug('No table provided to AddDataItem dialog')
            return
        self.table = table
        self.parent_data_id = None
        self.parent_table = None
        self.add_item: str = 'child'
        self.parent_id: int | None = None
        self.parent_row: int | None = None
        self.item_ids: list[int] = []
        self.old_parent_ids: list[int] = []
        self.old_parent_rows: list[int] = []
        for key, value in kwargs.items():
            setattr(self, key, value)
        if table != 'Samples' and not self.parent_data_id:
            logger_setup.get_logger().critical(f'Error adding {table} item: Unclear data chain')
            logger_setup.get_logger().debug(f'No parent data ID provided to AddDataItem dialog for {table} item')
        if table == 'Spots' and not self.parent_table:
            logger_setup.get_logger().critical(f'Error adding {table} item: Unclear data chain')
            logger_setup.get_logger().debug('No parent table provided for adding {table} item')
            return
        if table == 'Aliquots' and not self.parent_table:
            self.parent_table = 'Samples'
        elif table == 'Grains' and not self.parent_table:
            self.parent_table = 'Aliquots'
        elif table == 'UPbAnalyses' and not self.parent_table:
            self.parent_table = 'Spots'
        self.item_name = ''
        self.item_description = ''
        self.existing_names = set()

        self.setWindowTitle(f'Add {self.table}')
        self.setModal(True)
        self.updated = False
        self.close_by_dialog = False
        self.ids_added = []
        self.ids_updated = []

        self.info_text = QtW.QLabel(
            f'Use the regular edit window to modify {self.table} metadata.\nThis only adds {self.table} with a name and description.')
        # self.info_layout = QtW.QHBoxLayout()
        self.input_layout = QtW.QHBoxLayout()
        self.name_label = QtW.QLabel('Name:')
        self.name_lineEdit = QtW.QLineEdit()
        self.description_label = QtW.QLabel('Description:')
        self.description_lineEdit = QtW.QLineEdit()
        self.buttonBox = QtW.QDialogButtonBox()
        self.cancel_pushButton = QtW.QPushButton('Cancel')
        self.commit_pushButton = QtW.QPushButton('Commit')
        self.buttonBox.addButton(self.cancel_pushButton, QtW.QDialogButtonBox.ButtonRole.RejectRole)
        self.buttonBox.addButton(self.commit_pushButton, QtW.QDialogButtonBox.ButtonRole.AcceptRole)
        self.input_layout.addWidget(self.name_label)
        self.input_layout.addWidget(self.name_lineEdit)
        self.input_layout.addWidget(self.description_label)
        self.input_layout.addWidget(self.description_lineEdit)
        self.layout = QtW.QVBoxLayout(self)
        self.layout.addWidget(self.info_text)
        self.layout.addLayout(self.input_layout)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        self.headers = get_headers(self.table)
        self.parent_headers = []
        self.parent_data_id_header = ''
        self.parent_name_header = ''
        if self.parent_table:
            self.parent_headers = get_headers(self.parent_table)
            self.parent_data_id_header = self.parent_headers[0]
            self.parent_name_header = self.parent_headers[get_name_column(self.parent_table)]
        self.name_header = self.headers[get_name_column(self.table)]
        self.description_header = [header for header in self.headers if 'Description' in header][0]

        self.update_completer()

        create_savepoint('before_add')

        self.commit_pushButton.clicked.connect(self.commit)
        self.cancel_pushButton.clicked.connect(self.discard_question)
        close_loading_dialog('Loading', f'Opening add window for {self.table}...')

    def update_completer(self):
        """Update the completer for the name line edit based on existing items in the table"""
        logger_setup.get_logger().info('Updating completer')
        query = QtS.QSqlQuery()
        # Get a list of the existing tag names
        query.prepare(f'SELECT {self.name_header} FROM {self.table}')
        if not query.exec():
            logger_setup.get_logger().critical(
                f'Error selecting display column from {self.table}: {query.lastError().text()}')
            return
        self.existing_names = set()
        while query.next():
            self.existing_names.add(query.value(0))
        completer = QtW.QCompleter(self.existing_names)
        list_model = QtC.QStringListModel(sorted(self.existing_names, key=str.casefold))
        list_proxy_model = QtC.QSortFilterProxyModel()
        list_proxy_model.setSourceModel(list_model)
        list_proxy_model.setSortCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        completer.setModel(list_proxy_model)
        completer.setFilterMode(QtC.Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        completer.setModelSorting(QtW.QCompleter.ModelSorting.CaseInsensitivelySortedModel)
        completer.setCompletionMode(QtW.QCompleter.CompletionMode.PopupCompletion)
        logger_setup.get_logger().info('Completer updated')

    def add_data_item(self) -> bool:
        """
        Adds the new item to the database.
        Returns True if the item was added successfully, False if there was an error (e.g., duplicate name).
        """
        if self.table == 'Aliquots':
            logger_setup.get_logger().critical(f'Error adding table item: {self.table} is a tree')
            return False
        logger_setup.get_logger().info(f'Adding {self.table} item {self.name_lineEdit.text()}')
        name = self.name_lineEdit.text()
        description = self.description_lineEdit.text()
        if not name:
            logger_setup.get_logger().error(f'Error adding {self.table} item: Name cannot be empty')
            return False
        if name in self.existing_names:
            logger_setup.get_logger().error(f'Error adding {self.table}: Name must be unique')
            return False
        query = QtS.QSqlQuery()
        if self.parent_data_id:
            query.prepare(f'INSERT INTO {self.table} ({self.name_header}, {self.description_header}, {self.parent_data_id_header}) VALUES (:name, :description, :parent_data_id)')
            query.bindValue(':name', name)
            query.bindValue(':description', description if description else QtC.QVariant())
            query.bindValue(':parent_data_id', self.parent_data_id)
        else:
            query.prepare(f'INSERT INTO {self.table} ({self.name_header}, {self.description_header}) VALUES (:name, :description)')
            query.bindValue(':name', name)
            query.bindValue(':description', description if description else QtC.QVariant())
        if not query.exec():
            logger_setup.get_logger().critical(f'Error adding {self.table} item: {name}')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
            return False
        logger_setup.get_logger().info(f'Successfully added {name} to {self.table}')
        self.ids_added.append(query.lastInsertId())
        self.updated = True
        logger_setup.get_logger().info(f'Added {self.table} item: {name}')
        return True

    def add_tree_data_item(self):
        """
        Adds a new item to the aliquot tree table. Checks if any other items need to be moved or updated.
        """
        if not self.table == 'Aliquots':
            logger_setup.get_logger().critical(f'Error adding tree item: {self.table} is not a tree table')
            return False
        query = QtS.QSqlQuery()
        name = self.name_lineEdit.text()
        description = self.description_lineEdit.text()
        if self.parent_id in ['', 'NULL', None] or not isinstance(self.parent_id, int):
            sql_parent = 'IS NULL'
        else:
            sql_parent = f'= {self.parent_id}'
        if self.add_item == 'child':
            query.prepare(f'SELECT {self.headers[0]}, {self.headers[2]} FROM {self.table} WHERE {self.headers[1]} {sql_parent}')
            if not query.exec():
                logger_setup.get_logger().critical(f'Error adding {self.table} item: {name}')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                return False
            parent_rows = {}
            while query.next():
                child_id = query.value(0)
                child_parent_row = query.value(1)
                parent_rows[child_parent_row] = child_id
            if not self.parent_row and self.parent_row != 0:
                self.parent_row = min(parent_rows.keys()) - 1 if parent_rows else 0
            if not parent_rows:
                # If there are no existing child items for the parent, insert the new item with parent_row 0
                query.prepare(
                    f'INSERT INTO {self.table} ({self.name_header}, {self.description_header}, {self.headers[1]}, {self.headers[2]}, {self.parent_data_id_header}) VALUES (:name, :description, :parent_id, :parent_row, :parent_data_id)')
                query.bindValue(':name', name)
                query.bindValue(':description', description if description else QtC.QVariant())
                query.bindValue(':parent_id', self.parent_id if self.parent_id and isinstance(self.parent_id,
                                                                                              int) else QtC.QVariant())
                query.bindValue(':parent_row', 0)
                query.bindValue(':parent_data_id', self.parent_data_id)
                if not query.exec():
                    logger_setup.get_logger().critical(f'Error adding {self.table} item: {name}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                    return False
                logger_setup.get_logger().info(f'Successfully added {name} to {self.table}')
                self.ids_added.append(query.lastInsertId())
            elif self.parent_row > max(parent_rows.keys()):
                # Insert the new item at the end
                query.prepare(
                    f'INSERT INTO {self.table} ({self.name_header}, {self.description_header}, {self.headers[1]}, {self.headers[2]}, {self.parent_data_id_header}) VALUES (:name, :description, :parent_id, :parent_row, :parent_data_id)')
                query.bindValue(':name', name)
                query.bindValue(':description', description if description else QtC.QVariant())
                query.bindValue(':parent_id', self.parent_id if self.parent_id and isinstance(self.parent_id,
                                                                                              int) else QtC.QVariant())
                query.bindValue(':parent_row', len(parent_rows))
                query.bindValue(':parent_data_id', self.parent_data_id)
                if not query.exec():
                    logger_setup.get_logger().critical(f'Error adding {self.table} item: {name}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                    return False
                logger_setup.get_logger().info(f'Successfully added {name} to {self.table}')
                self.ids_added.append(query.lastInsertId())
            else:
                # If the new item is being inserted in the middle, create a space for the new item
                result, updated_ids = bulk_update_parent_row(self.table, self.parent_id, 1, None)
                if not result:
                    logger_setup.get_logger().critical(f'Error adding {self.table} item: {name}')
                    return False
                if updated_ids:
                    self.ids_updated.extend(updated_ids)
                # Insert the new item at the gap
                query.prepare(
                    f'INSERT INTO {self.table} ({self.name_header}, {self.description_header}, {self.headers[1]}, {self.headers[2]}, {self.parent_data_id_header}) VALUES (:name, :description, :parent_id, :parent_row, :parent_data_id)')
                query.bindValue(':name', name)
                query.bindValue(':description', description if description else QtC.QVariant())
                query.bindValue(':parent_id', self.parent_id if self.parent_id and isinstance(self.parent_id,
                                                                                              int) else QtC.QVariant())
                query.bindValue(':parent_row', self.parent_row)
                query.bindValue(':parent_data_id', self.parent_data_id)
                if not query.exec():
                    logger_setup.get_logger().critical(f'Error adding {self.table} item: {name}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                    return False
                logger_setup.get_logger().info(f'Successfully added {name} to {self.table} at row {len(parent_rows)+1}')
                self.ids_added.append(query.lastInsertId())
        elif self.add_item == 'parent':  # Need to update the parent of all new child ids to the newly-added item
            # find top level parent ID and parent row for all items being moved
            top_parent_id, top_parent_row = self.top_node()
            if not top_parent_id and not top_parent_row:
                # find all old parent IDs that are None or not integers and get the smallest row index
                parent_row = min((row for row, pid in zip(self.old_parent_rows, self.old_parent_ids) if pid is None or not isinstance(pid, int)), default=None)
            query.prepare(
                f'INSERT INTO {self.table} ({self.name_header}, {self.description_header}, {self.headers[1]}, {self.headers[2]}, {self.parent_data_id_header}) VALUES (:name, :description, :parent_id, :parent_row, :parent_data_id)')
            query.bindValue(':name', name)
            query.bindValue(':description', description)
            query.bindValue(':parent_id', top_parent_id if top_parent_id and isinstance(top_parent_id, int) else QtC.QVariant())
            query.bindValue(':parent_row', top_parent_row if top_parent_row is not None else QtC.QVariant())
            query.bindValue(':parent_data_id', self.parent_data_id)
            if not query.exec():
                logger_setup.get_logger().critical(f'Error adding {self.table} item: {name}')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                return False
            logger_setup.get_logger().info(f'Added new parent {name} to {self.table}')
            self.ids_added.append(query.lastInsertId())
            new_parent_id = query.lastInsertId()
            parent_row = 0
            for child in range(len(self.item_ids)):
                # Move only if the child currently has the old parent ID
                current_parent_ID = self.old_parent_ids[child] if isinstance(self.old_parent_ids[child],
                                                                             int) else None
                if current_parent_ID in self.item_ids:
                    # If the current parent ID is one of the items being moved, leave it as a child of this parent
                    continue
                if current_parent_ID != new_parent_id:
                    query.prepare(
                        f'UPDATE {self.table} SET {self.headers[1]} = :parent_id, {self.headers[2]} = :parent_row WHERE {self.headers[0]} = :child_id')
                    query.bindValue(':parent_id', new_parent_id if new_parent_id and isinstance(new_parent_id,
                                                                                                int) else QtC.QVariant())
                    query.bindValue(':parent_row', parent_row)
                    query.bindValue(':child_id', self.item_ids[child])
                    if not query.exec():
                        logger_setup.get_logger().critical(f'Error adding {self.table} item: {name}')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                        return False
                    if self.item_ids[child] not in self.ids_added and self.item_ids[child] not in self.ids_updated:
                        self.ids_updated.append(self.item_ids[child])
                    parent_row += 1
            logger_setup.get_logger().info(f'Updated parent of {self.item_ids} to {new_parent_id} in {self.table}')
        self.updated = True
        return True

    def top_node(self):
        query = QtS.QSqlQuery()
        def get_depth(depth_id):
            depth = 0
            while depth_id is not None:
                query.prepare(f"SELECT {self.headers[1]} FROM {self.table} WHERE {self.headers[0]} = :id")
                query.bindValue(':id', depth_id)
                if not query.exec():
                    logger_setup.get_logger().critical(f'Error adding {self.table} item: {self.name_lineEdit.text()}')
                    logger_setup.get_logger().debug(f'Error finding depth of {self.table} item ID {depth_id}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                    return None
                if not query.next():
                    logger_setup.get_logger().critical(f'Error adding {self.table} item: {self.name_lineEdit.text()}')
                    logger_setup.get_logger().debug(f'Error finding depth of {self.table} item ID {depth_id}: No record found')
                    return None
                depth_parent_id = query.value(0)
                if depth_parent_id == '':
                    break
                depth_id = depth_parent_id
                depth += 1
            return depth

        if len(self.item_ids) == 0:
            logger_setup.get_logger().debug(f'No item IDs provided, returning None')
            return None, None
        if '' in self.item_ids:
            logger_setup.get_logger().debug(f'Empty item ID found, referencing root. Returning None')
            return None, None
        depths = {}
        for item_id in self.item_ids:
            depths[item_id] = get_depth(item_id)
        # If there is a tie for minimum depth, break it by the minimum parent row
        min_depth = min(depths.values())
        candidates = [item_id for item_id, depth in depths.items() if depth == min_depth]
        if len(candidates) > 1:
            top_parent_row = None
            top_parent_id = None
            for item_id in candidates:
                query.prepare(f"SELECT {self.headers[1]}, {self.headers[2]} FROM {self.table} WHERE {self.headers[0]} = :id")
                query.bindValue(':id', item_id)
                if not query.exec():
                    logger_setup.get_logger().critical(f'Error adding {self.table} item: {self.name_lineEdit.text()}')
                    logger_setup.get_logger().debug(f'Error finding parent row of {self.table} item ID {item_id}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                    continue
                if not query.next():
                    logger_setup.get_logger().critical(f'Error adding {self.table} item: {self.name_lineEdit.text()}')
                    logger_setup.get_logger().debug(f'Error finding parent row of {self.table} item ID {item_id}: No record found')
                    continue
                parent_id = query.value(0)
                parent_row = query.value(1)
                if top_parent_row is None or parent_row < top_parent_row:
                    top_parent_row = parent_row
                    top_parent_id = parent_id
        else:
            top_item_id = candidates[0]
            query.prepare(f'SELECT {self.headers[1]}, {self.headers[2]} FROM {self.table} WHERE {self.headers[0]} = :id')
            query.bindValue(':id', top_item_id)
            if not query.exec():
                logger_setup.get_logger().critical(f'Error adding {self.table} item: {self.name_lineEdit.text()}')
                logger_setup.get_logger().debug(f'Error finding parent row of {self.table} item ID {top_item_id}')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                return None, None
            if not query.next():
                logger_setup.get_logger().critical(f'Error adding {self.table} item: {self.name_lineEdit.text()}')
                logger_setup.get_logger().debug(f'Error finding parent row of {self.table} item ID {top_item_id}: No record found')
                return None, None
            top_parent_id = query.value(0)
            top_parent_row = query.value(1)
        if top_parent_id == '':
            top_parent_id = 'NULL'
        return top_parent_id, top_parent_row

    def discard_question(self):
        """
        Displays a confirmation dialog asking the user if they want to discard all changes made in the dialog.
        :return:
        """
        self.cancel_pushButton.blockSignals(True)
        if self.updated or self.name_lineEdit.text() or self.description_lineEdit.text():
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
        self.reject()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        """
        Commits the changes to the database. If there is an active savepoint, it is released.
        """
        if self.name_lineEdit.text():
            if self.table == 'Aliquots' and not self.add_tree_data_item():
                return
            elif self.table != 'Aliquots' and not self.add_data_item():
                return
        release_savepoint('before_add')
        logger_setup.get_logger().info(f'Changes committed to {self.table}')
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

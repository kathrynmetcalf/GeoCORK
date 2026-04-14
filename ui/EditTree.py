import os
import sys
import time

from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import QPoint, QSize
from PyQt6.QtCore import QRegularExpression
from PyQt6.uic import loadUi

import Functions.Text_manipulations as TxM
import logger_setup
from Functions.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint
from Functions.Settings_manager import SettingsManager
from ui.Merge import MergeDialog

settings = SettingsManager().settings
from Functions.Widget_classes import (
    set_table, TreeModel, TreeContextMenu, get_selected_tree_ids, expand_collapse, save_expanded_state,
    add_tree_popup, TreeSortFilterProxyModel, delete_data, show_loading_dialog, close_loading_dialog,
    restore_expanded_state
)
from ui.AddTreeTags import AddTreeTags


class EditTree(QtW.QDialog):
    """
    Opens an EditTable dialog used to edit a table in the database.
    """

    def __init__(self, parent_window, table_name, **kwargs):
        super().__init__(parent=parent_window)

        logger_setup.get_logger().info(f'Opening {table_name} tree edit dialog')
        start_edit_tree_time = time.time()
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "EditTree.ui")
        loadUi(sources_ui_file, self)
        self.setModal(True)
        self.updated = False

        self.table_name = table_name
        self.table_item_ids: list = []
        for key, value in kwargs.items():
            setattr(self, key, value)



        # Set the model and table
        self.table = TxM.remove_spaces(table_name)
        logger_setup.get_logger().info(f'Setting up {table_name} tree model')
        # self.model = SQLiteTableModel(f'SELECT * FROM {self.table}')
        self.model = QtS.QSqlTableModel()
        set_table(self.model, self.table)
        self.total_records = self.model.rowCount()
        self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnFieldChange)
        self.tree_model = TreeModel(self.model)
        self.setWindowTitle(f'Edit {table_name}')
        self.add_pushButton.setText(f'Add {table_name}')
        logger_setup.get_logger().info('Setting up proxy model')
        self.tree_proxy_model = TreeSortFilterProxyModel()
        self.tree_proxy_model.setSourceModel(self.tree_model)
        self.tree_proxy_model.setFilterKeyColumn(-1)  # search all columns

        logger_setup.get_logger().info('Connecting signals')
        self.edit_treeView.setUniformRowHeights(True)
        self.edit_treeView.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.edit_treeView.customContextMenuRequested.connect(self.show_context_menu)

        self.msg = QtW.QMessageBox(self)

        self.display_tree()
        create_savepoint('before_edit')

        self.close_by_dialog = False
        self.search_lineEdit.returnPressed.connect(self.search)
        self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit_question)
        self.cancel_pushButton.clicked.connect(self.discard_question)
        self.tree_model.dataChanged.connect(self.set_updated)

        close_loading_dialog('Loading', f'Opening edit window for {self.table_name}...')
        logger_setup.get_logger().info(
            f'Opened {table_name} tree edit dialog in {time.time() - start_edit_tree_time} seconds')

    def set_updated(self):
        """
        Sets the updated flag to True when the data in the model is changed.
        This is used to determine if the user has made changes to the data.
        """
        self.updated = True

    def search(self):
        self.search_lineEdit: QtW.QLineEdit
        self.tree_proxy_model.setRecursiveFilteringEnabled(True)
        search_expression = QtC.QRegularExpression(self.search_lineEdit.text(),
                                                   options=QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.tree_proxy_model.setFilterRegularExpression(search_expression)
        if self.search_lineEdit.text() != '':
            self.edit_treeView.expandAll()

    def show_context_menu(self, pos):
        """
        Show a context menu when right-clicking on a table or tree view
        :param pos: The position of the mouse click
        :return:
        """
        self.edit_treeView: QtW.QTreeView
        tree_menu = TreeContextMenu()
        if self.table == 'Ages':
            tree_menu.set_view(self.edit_treeView, False, False, False)
        else:
            tree_menu.set_view(self.edit_treeView, True, True, False)
        action = tree_menu.exec(self.edit_treeView.viewport().mapToGlobal(pos))
        if action:
            self.tree_context_menu(action)

    def tree_context_menu(self, action: QtG.QAction):
        """
        Context menu for tree views
        :param action: The action selected from the context menu
        :return:
        """
        if 'Add' in action.text() or 'Insert' in action.text():
            self.add_popup(action)
        elif 'Expand' in action.text() or 'Collapse' in action.text():
            expand_collapse(self.edit_treeView, action)
        elif 'Merge' in action.text():
            self.merge_items()
        elif 'Delete' in action.text():
            self.delete_item()

    def display_tree(self):
        logger_setup.get_logger().info(f'Displaying {self.model.rowCount()} {self.table_name}...')
        start_display_tree_time = time.time()
        show_loading_dialog('Loading', f'Displaying {self.model.rowCount()} {self.table_name}...')
        self.edit_treeView.setModel(self.tree_proxy_model)
        self.edit_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
        start_hide_columns_time = time.time()
        self.edit_treeView.hideColumn(1)  # don't show ID column
        self.edit_treeView.hideColumn(2)  # don't show parent ID column
        self.edit_treeView.hideColumn(3)  # don't show parent row column
        self.edit_treeView.model().update_visible_columns()
        logger_setup.get_logger().info(f'Hid columns in {time.time() - start_hide_columns_time} seconds')
        self.edit_treeView.setSortingEnabled(False)
        self.edit_treeView.setDragEnabled(True)
        self.edit_treeView.setAcceptDrops(True)
        self.edit_treeView.setDropIndicatorShown(True)
        self.edit_treeView.setDragDropMode(QtW.QAbstractItemView.DragDropMode.InternalMove)
        self.edit_treeView.setDefaultDropAction(QtC.Qt.DropAction.MoveAction)
        self.edit_treeView.setSelectionMode(QtW.QAbstractItemView.SelectionMode.ExtendedSelection)
        restore_expanded_state(self.table, self.edit_treeView)
        self.tree_model.dataEdited.connect(self.update_proxy)

        self.page_info_label.setText(f'{self.total_records} {self.table_name}')

        close_loading_dialog('Loading', f'Displaying {self.model.rowCount()} {self.table_name}...')
        logger_setup.get_logger().info(
            f'Displayed {self.model.rowCount()} {self.table_name} tree in {time.time() - start_display_tree_time} seconds')

    def update_proxy(self):
        save_expanded_state(self.table, self.edit_treeView)
        if self.sender() == self.tree_model:
            self.updated = True
        if self.tree_proxy_model.sourceModel() == self.tree_model:
            self.tree_model.deleteLater()
        self.total_records = self.model.rowCount()
        self.tree_model = TreeModel(self.model)
        self.tree_model.dataEdited.connect(self.update_proxy)
        self.tree_proxy_model.setSourceModel(self.tree_model)
        self.display_tree()

    def add_popup(self, action: QtG.QAction | None = None):
        save_expanded_state(self.table, self.edit_treeView)
        dlg_args = add_tree_popup(self.edit_treeView, action)
        show_loading_dialog('Loading', f'Opening add window for {self.table}...')
        if dlg_args:
            dlg = AddTreeTags(self, self.table, **dlg_args)
        else:
            dlg = AddTreeTags(self, self.table)
        if not dlg:
            return
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
        self.update_proxy()

    def add_parent(self, item_ids: list, parent_ids: list, parent_rows: list):
        """
        Add a parent to the selected items. This is used when adding a new item to the tree.
        :param item_ids:
        :param parent_ids:
        :param parent_rows:
        :return:
        """
        n_item = 0
        new_child_ids = []
        new_parent_rows = []
        for item in range(len(item_ids)):
            item_id = item_ids[item]
            parent_id = parent_ids[item]
            if not parent_id in item_ids:
                # This is a child of the new parent, not a grandchild or lower
                new_child_ids.append(item_id)
                new_parent_rows.append(n_item)
                n_item += 1
        # Find the top child and get its parent and parent row, that will become the position of the new parent
        output = self.tree_model.top_node(new_child_ids)
        parent_id = output[0]
        row = output[1]
        self.add_popup(None, parent_id, row, 'parent', new_child_ids, new_parent_rows)

    def merge_items(self):
        """
        Merge the selected items in the tree view. The user will be prompted to select which item to keep.
        All other items will be merged into the selected item. Children of the merged items will be re-assigned to the kept item.
        """
        save_expanded_state(self.table, self.edit_treeView)
        tree_indexes = []
        for view_index in self.edit_treeView.selectedIndexes():
            tree_index = self.tree_proxy_model.mapToSource(view_index)
            if tree_index.column() == 0 and tree_index not in tree_indexes:
                tree_indexes.append(self.tree_proxy_model.mapToSource(view_index))
        ids_to_merge = list(get_selected_tree_ids(tree_indexes))
        if len(ids_to_merge) < 2:
            logger_setup.get_logger().error('At least two records must be selected to merge')
            return
        if MergeDialog(self.table, ids_to_merge, self).exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
            self.update_proxy()

    def delete_item(self):
        """
        Delete the selected items from the tree view. If there are any children of the selected items, they will be deleted
        """
        save_expanded_state(self.table, self.edit_treeView)
        tree_indexes = []
        for view_index in self.edit_treeView.selectedIndexes():
            tree_index = self.tree_proxy_model.mapToSource(view_index)
            if tree_index.column() == 0 and tree_index not in tree_indexes:
                tree_indexes.append(self.tree_proxy_model.mapToSource(view_index))
        item_ids = list(get_selected_tree_ids(tree_indexes))
        if not item_ids:
            return

        if delete_data(self.table, item_ids):
            self.updated = True
            self.update_proxy()

    def commit_question(self):
        msg_box = QtW.QMessageBox()
        msg_box.setIcon(QtW.QMessageBox.Icon.Question)
        msg_box.setText('Are you sure you want to commit all changes to the database?')
        msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            self.commit()
            self.updated = True
        else:
            pass

    def discard_question(self):
        """
        Asks the user if they want to discard changes. If they do, the changes are rolled back.
        :return:
        """
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
                pass
        else:
            logger_setup.get_logger().info(f'Closing {self.table} edit dialog without changes')
            release_savepoint('before_edit')
            self.close_by_dialog = True
            self.close()
            self.close_by_dialog = False

    def rollback(self):
        """
        Rolls back the changes to the database. Rejects the dialog and closes the the window.
        """
        rollback_savepoint('before_edit')
        self.updated = False
        save_expanded_state(self.table, self.edit_treeView)
        self.reject()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        """
        Commits the changes to the database. If there is an active savepoint, it is released.
        """
        release_savepoint('before_edit')
        save_expanded_state(self.table, self.edit_treeView)
        self.accept()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def closeEvent(self, event: QtG.QCloseEvent):
        """
        Overridden close event to handle the case where the user tries to close the dialog
        :param QCloseEvent event:
        """
        if not self.close_by_dialog:
            if self.updated:
                self.discard_question()
                event.ignore()
            else:
                logger_setup.get_logger().info(f'Closing {self.table} edit dialog')
                release_savepoint('before_edit')
                event.accept()
        else:
            logger_setup.get_logger().info(f'Closing {self.table} edit dialog')
            release_savepoint('before_edit')
            event.accept()

    def saveWindowState(self):
        settings.setValue("ui/EditTree/pos", self.pos())
        settings.setValue("ui/EditTree/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/EditTree/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/EditTree/size", defaultValue=QSize(810, 569)))

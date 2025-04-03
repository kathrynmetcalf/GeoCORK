import os
import sys
import time

from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import QRegularExpression, QSortFilterProxyModel
from PyQt6.uic import loadUi

import Functions.Text_manipulations as TxM
import logger_setup
from Functions.Database_manager import update_database
from Functions.LoadingDialog_manager import LoadingDialogManager
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Widget_classes import (
    set_table, TreeModel, TreeContextMenu, get_selected_tree_ids, expand_collapse, save_expanded_state,
    restore_expanded_state, add_tree_popup, ReadableProxyModel
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
        self.loading_manager = LoadingDialogManager.get_instance()
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
        self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnFieldChange)
        self.tree_model = TreeModel(self.model)
        self.setWindowTitle(f'Edit {table_name}')
        self.add_pushButton.setText(f'Add {table_name}')
        logger_setup.get_logger().info('Setting up proxy model')
        self.tree_proxy_model = ReadableProxyModel()
        self.tree_proxy_model.setSourceModel(self.tree_model)
        self.tree_proxy_model.setFilterKeyColumn(-1)  # search all columns

        logger_setup.get_logger().info('Connecting signals')
        self.edit_treeView.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.edit_treeView.customContextMenuRequested.connect(self.show_context_menu)

        self.msg = QtW.QMessageBox(self)
        self.display_tree()
        create_savepoint('before_edit')

        self.close_by_dialog = False
        self.search_lineEdit.editingFinished.connect(self.search)
        self.tree_model.save_state.connect(
            lambda: save_expanded_state(self.table, self.tree_proxy_model, self.edit_treeView))
        self.tree_model.dataEdited.connect(self.update_proxy)
        self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        self.cancel_pushButton.clicked.connect(self.discard_question)

        self.loading_manager.close_loading_dialog('Loading', f'Opening edit window for {self.table_name}...')
        logger_setup.get_logger().info(
            f'Opened {table_name} tree edit dialog in {time.time() - start_edit_tree_time} seconds')

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
        elif 'Delete' in action.text():
            self.delete_item()

    def display_tree(self):
        logger_setup.get_logger().info(f'Displaying {self.table_name}...')
        start_display_tree_time = time.time()
        self.loading_manager.show_loading_dialog('Loading', f'Displaying {self.table_name}...')
        self.edit_treeView.setModel(self.tree_proxy_model)
        self.edit_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
        self.edit_treeView.hideColumn(1)  # don't show ID column
        self.edit_treeView.hideColumn(2)  # don't show parent ID column
        self.edit_treeView.hideColumn(3)  # don't show parent row column
        self.edit_treeView.setSortingEnabled(False)
        self.edit_treeView.setDragEnabled(True)
        self.edit_treeView.setAcceptDrops(True)
        self.edit_treeView.setDropIndicatorShown(True)
        self.edit_treeView.setDragDropMode(QtW.QAbstractItemView.DragDropMode.InternalMove)
        self.edit_treeView.setDefaultDropAction(QtC.Qt.DropAction.MoveAction)
        self.edit_treeView.setSelectionMode(QtW.QAbstractItemView.SelectionMode.ExtendedSelection)
        restore_expanded_state(self.table, self.tree_proxy_model, self.edit_treeView)

        self.loading_manager.close_loading_dialog('Loading', f'Displaying {self.table_name}...')
        logger_setup.get_logger().info(
            f'Displayed {self.table_name} tree in {time.time() - start_display_tree_time} seconds')

    def update_proxy(self):
        if self.sender() == self.tree_model:
            self.updated = True
        if self.tree_proxy_model.sourceModel() == self.tree_model:
            self.tree_model.deleteLater()
        self.tree_model = TreeModel(self.model)
        self.tree_model.dataEdited.connect(self.update_proxy)
        self.tree_proxy_model.setSourceModel(self.tree_model)
        self.display_tree()

    def add_popup(self, action: QtG.QAction | None = None):
        save_expanded_state(self.table, self.tree_proxy_model, self.edit_treeView)
        dlg_args = add_tree_popup(self.edit_treeView, self.tree_model, action)
        self.loading_manager.show_loading_dialog('Loading', f'Opening add window for {self.table}...')
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

    def delete_item(self):
        """
        Delete the selected items from the tree view. If there are any children of the selected items, they will be deleted
        """
        save_expanded_state(self.table, self.tree_proxy_model, self.edit_treeView)
        tree_indexes = []
        for view_index in self.edit_treeView.selectedIndexes():
            tree_index = self.tree_proxy_model.mapToSource(view_index)
            if tree_index.column() == 0 and tree_index not in tree_indexes:
                tree_indexes.append(self.tree_proxy_model.mapToSource(view_index))
        item_ids = get_selected_tree_ids(self.tree_model, tree_indexes)[0]
        if not item_ids:
            return

        # Look for any children of the selected items
        def get_children(item_id):
            """
            Get all children of the selected item. This is a recursive function that will get all children of the selected
            :param item_id:
            :return:
            """
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
        if self.delete_question(all_children):
            for item_id in item_ids:
                item = self.tree_model.find_id_in_tree(item_id)
                parent_id = item.data(1)
                parent_row = item.data(2)
                self.tree_model.removeItem(item_id, parent_row, parent_id)
            self.updated = True
            self.update_proxy()

    def delete_question(self, children: list):
        """
        Promote the user with a question to delete the selected items and all children.
        :param list children: list of children ids to be deleted
        :return:
        """
        save_expanded_state(self.table, self.tree_proxy_model, self.edit_treeView)
        msg_box = QtW.QMessageBox()
        msg_box.setIcon(QtW.QMessageBox.Icon.Question)
        msg_box.setText(f'Are you sure you want to delete these items and all {len(children)} children?')
        msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

    def discard_question(self):
        """
        Asks the user if they want to discard changes. If they do, the changes are rolled back.
        :return:
        """
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
        """
        Rolls back the changes to the database. Rejects the dialog and closes the the window.
        """
        rollback_savepoint('before_edit')
        save_expanded_state(self.table, self.tree_proxy_model, self.edit_treeView)
        self.reject()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        """
        Commits the changes to the database. If there is an active savepoint, it is released.
        """
        release_savepoint('before_edit')
        save_expanded_state(self.table, self.tree_proxy_model, self.edit_treeView)
        # Check if there is another existing savepoint. If not, go ahead and update the database
        if not SavepointManager.get_instance().active_savepoints():
            update_database()
        self.accept()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def close(self):
        if not self.close_by_dialog:
            if self.updated:
                self.discard_question()
            else:
                logger_setup.get_logger().info(f'Closing {self.table} edit dialog')
                super().close()
        else:
            logger_setup.get_logger().info(f'Closing {self.table} edit dialog')
            super().close()

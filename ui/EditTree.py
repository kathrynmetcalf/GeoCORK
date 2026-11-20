import time

from PyQt6 import QtCore, QtGui, QtWidgets, QtSql
from PyQt6.QtCore import QPoint, QSize
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtWidgets import QDialogButtonBox

import Functions.Text_manipulations as TxM
from util.database.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint
from Functions.Settings_manager import SettingsManager
from ui.Merge import MergeDialog

from Functions.Widget_classes import (
    set_table, get_selected_tree_ids, expand_collapse, save_expanded_state,
    add_tree_popup,
    restore_expanded_state
)
from ui.AddTreeTags import AddTreeTags

import logger_setup
from util.widgets.context_menus import TreeContextMenu
from util.widgets.models.TrackExpandedTreeView import TrackExpandedTreeView
from util.widgets.models.TreeModel import TreeModel
from util.widgets.models.TreeSortFilterProxyModel import TreeSortFilterProxyModel

from util.loading_dialog_manager import show_loading_dialog, close_loading_dialog

settings = SettingsManager().settings


class EditTree(QtWidgets.QDialog):
    """
    Opens an EditTable dialog used to edit a table in the database.
    """

    def __init__(self, parent_window, table_name, **kwargs):
        super().__init__(parent=parent_window)

        logger_setup.get_logger().info(f'Opening {table_name} tree edit dialog')
        start_edit_tree_time = time.time()
        self.setWindowTitle(f'Edit {table_name}')

        self.build_ui(table_name)
        self.loadWindowState()

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
        self.model = QtSql.QSqlTableModel()
        set_table(self.model, self.table)
        self.total_records = self.model.rowCount()
        self.model.setEditStrategy(QtSql.QSqlTableModel.EditStrategy.OnFieldChange)
        self.tree_model = TreeModel(self.model)

        logger_setup.get_logger().info('Setting up proxy model')
        self.tree_proxy_model = TreeSortFilterProxyModel()
        self.tree_proxy_model.setSourceModel(self.tree_model)
        self.tree_proxy_model.setFilterKeyColumn(-1)  # search all columns

        logger_setup.get_logger().info('Connecting signals')
        self.edit_treeView.setUniformRowHeights(True)
        self.edit_treeView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.edit_treeView.customContextMenuRequested.connect(self.show_context_menu)

        self.msg = QtWidgets.QMessageBox(self)

        self.display_tree()
        create_savepoint('before_edit')

        self.close_by_dialog = False
        self.search_lineEdit.returnPressed.connect(self.search)
        self.add_pushButton.clicked.connect(self.add_popup)
        self.tree_model.dataChanged.connect(self.set_updated)

        close_loading_dialog('Loading', f'Opening edit window for {self.table_name}...')
        logger_setup.get_logger().info(
            f'Opened {table_name} tree edit dialog in {time.time() - start_edit_tree_time} seconds')

    def build_ui(self, table_name):
        self.main_layout = QtWidgets.QVBoxLayout(self)

        # ---- Top row: Add button, search ----
        self.top_layout = QtWidgets.QHBoxLayout()

        self.add_pushButton = QtWidgets.QPushButton(f'Add {TxM.add_spaces_camel(table_name)}')
        self.add_pushButton.setObjectName('add_pushButton')
        self.add_pushButton.setAutoDefault(False)
        self.top_layout.addWidget(self.add_pushButton)

        self.horizontalSpacer_2 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.top_layout.addItem(self.horizontalSpacer_2)

        self.label_2 = QtWidgets.QLabel('Search:')
        self.label_2.setObjectName('label_2')
        self.top_layout.addWidget(self.label_2)

        self.search_lineEdit = QtWidgets.QLineEdit()
        self.search_lineEdit.setObjectName('search_lineEdit')
        self.search_lineEdit.setPlaceholderText('search this page')
        self.top_layout.addWidget(self.search_lineEdit)

        self.main_layout.addLayout(self.top_layout)

        # ---- Tree ----
        self.edit_treeView = TrackExpandedTreeView()
        self.edit_treeView.setObjectName('edit_treeView')
        self.edit_treeView.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.AnyKeyPressed
            | QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked
            | QtWidgets.QAbstractItemView.EditTrigger.EditKeyPressed)
        self.main_layout.addWidget(self.edit_treeView)

        # ---- Paging / navigation row ----
        self.bottom_layout = QtWidgets.QHBoxLayout()

        self.page_info_label = QtWidgets.QLabel('placeholder')
        self.page_info_label.setObjectName('page_info_label')
        self.bottom_layout.addWidget(self.page_info_label)

        self.main_layout.addLayout(self.bottom_layout)

        # ---- Bottom row: Cancel / Commit ----
        self.buttonBox = QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        self.buttonBox.accepted.connect(self.commit_question)
        self.buttonBox.rejected.connect(self.discard_question)

        self.main_layout.addWidget(self.buttonBox)

    def set_updated(self):
        """
        Sets the updated flag to True when the data in the model is changed.
        This is used to determine if the user has made changes to the data.
        """
        self.updated = True

    def search(self):
        self.search_lineEdit: QtWidgets.QLineEdit
        self.tree_proxy_model.setRecursiveFilteringEnabled(True)
        search_expression = QtCore.QRegularExpression(self.search_lineEdit.text(),
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
        self.edit_treeView: QtWidgets.QTreeView
        tree_menu = TreeContextMenu()
        if self.table == 'Ages':
            tree_menu.set_view(self.edit_treeView, False, False, False)
        else:
            tree_menu.set_view(self.edit_treeView, True, True, False)
        action = tree_menu.exec(self.edit_treeView.viewport().mapToGlobal(pos))
        if action:
            self.tree_context_menu(action)

    def tree_context_menu(self, action: QtGui.QAction):
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
        self.tree_proxy_model = TreeSortFilterProxyModel()
        self.tree_proxy_model.setSourceModel(self.tree_model)
        self.edit_treeView.setModel(self.tree_proxy_model)
        self.edit_treeView.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
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
        self.edit_treeView.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.edit_treeView.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.edit_treeView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        restore_expanded_state(self.table, self.edit_treeView)
        self.tree_model.dataEdited.connect(self.save_expanded)
        self.tree_model.modelReset.connect(self.update_proxy)

        self.page_info_label.setText(f'{self.total_records} {self.table_name}')

        close_loading_dialog('Loading', f'Displaying {self.model.rowCount()} {self.table_name}...')
        logger_setup.get_logger().info(
            f'Displayed {self.model.rowCount()} {self.table_name} tree in {time.time() - start_display_tree_time} seconds')

    def save_expanded(self):
        save_expanded_state(self.table, self.edit_treeView)
        if self.sender() == self.tree_model:
            self.updated = True

    def update_proxy(self):
        logger_setup.get_logger().info(f'Displaying {self.model.rowCount()} {self.table_name}...')
        show_loading_dialog('Loading', f'Displaying {self.model.rowCount()} {self.table_name}...')
        self.total_records = self.model.rowCount()
        self.edit_treeView.expand_from_ids()
        close_loading_dialog('Loading', f'Displaying {self.model.rowCount()} {self.table_name}...')

    def add_popup(self, action: QtGui.QAction | None = None):
        save_expanded_state(self.table, self.edit_treeView)
        dlg_args = add_tree_popup(self.edit_treeView, action)
        show_loading_dialog('Loading', f'Opening add window for {self.table}...')
        if dlg_args:
            dlg = AddTreeTags(self, self.table, **dlg_args)
        else:
            dlg = AddTreeTags(self, self.table)
        if not dlg:
            return
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.updated = True
            self.tree_model.dataEdited.emit()
            self.update_proxy()

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
        if MergeDialog(self.table, ids_to_merge, self).exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.updated = True
            self.tree_model.dataEdited.emit()
            self.update_proxy()

    def delete_item(self):
        """
        Delete the selected items from the tree view. If there are any children of the selected items, they will be deleted
        """
        save_expanded_state(self.table, self.edit_treeView)
        item_ids = []
        for view_index in self.edit_treeView.selectedIndexes():
            id_index = self.tree_proxy_model.index(view_index.row(), 1, view_index.parent())
            item_id = id_index.data(QtCore.Qt.ItemDataRole.DisplayRole)
            if item_id not in item_ids:
                item_ids.append(item_id)
        if len(item_ids) == 0:
            return
        if self.tree_model.removeItems(item_ids):
            self.updated = True
            self.update_proxy()

    def commit_question(self):
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Icon.Question)
        msg_box.setText('Are you sure you want to commit all changes to the database?')
        msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response == QtWidgets.QMessageBox.StandardButton.Yes:
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
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Icon.Question)
            msg_box.setText('Are you sure you want to discard all changes?')
            msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
            response = msg_box.exec()
            if response == QtWidgets.QMessageBox.StandardButton.Yes:
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

    def closeEvent(self, event: QtGui.QCloseEvent):
        """
        Overridden close event to handle the case where the user tries to close the dialog
        :param QCloseEvent event:
        """
        self.saveWindowState()
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

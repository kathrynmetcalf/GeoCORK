import time

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import QSortFilterProxyModel
from PyQt6.QtGui import QAction

import logger_setup
from util.database.database_helper import find_tree_model, show_column
from util.loading_dialog_manager import show_loading_dialog, close_loading_dialog
from util.widgets.context_menus import TreeContextMenu
from util.widgets.models.proxy_models import TreeSortFilterProxyModel
from util.widgets.models.tree_models import CheckableTreeModel
from util.widgets.views.tree_views import CheckableTreeView, TrackExpandedTreeView, expand_collapse, \
    restore_expanded_state, save_expanded_state


class TreeComboBox(QtWidgets.QComboBox):
    """
    Custom QComboBox subclass that displays a tree structure in the dropdown list. This class extends QComboBox to provide
    functionality for displaying a tree view of items in the dropdown list. It allows users to search for items by typing
    in the line edit, and it uses a TreeSortFilterProxyModel to filter the items based on the text entered. The tree view
    supports context menus for editing, adding, and expanding/collapsing items. The combo box can be used to select items
    from a tree structure, making it suitable for hierarchical data representation.
    """
    closing = QtCore.pyqtSignal()
    edit_triggered = QtCore.pyqtSignal(QtWidgets.QComboBox)
    add_triggered = QtCore.pyqtSignal(QtWidgets.QComboBox, QAction)
    delete_triggered = QtCore.pyqtSignal(QtWidgets.QComboBox)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.proxy_model = None
        self.tree_model = None
        self.setEditable(True)
        self.lineEdit().setPlaceholderText("Search")
        self.lineEdit().setReadOnly(False)
        self.treeView = TrackExpandedTreeView()
        self.treeView.setUniformRowHeights(True)
        self.treeView.setRootIsDecorated(True)
        self.closedOnLineEditClick = False
        self.checkable = False
        self.expand_collapse = False
        self.popup_shown = False
        self.typing = False
        self.context_menu = False
        self.setView(self.treeView)
        self.treeView.viewport().installEventFilter(self)
        self.treeView.setWindowFlags(QtCore.Qt.WindowType.Popup)
        self.treeView.setFocusProxy(self.lineEdit())
        self.treeView.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        # self.lineEdit().installEventFilter(self)
        self.lineEdit().setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.lineEdit().textEdited.connect(self.update_filter)
        self.setCompleter(None)

    def start_typing(self):
        """
        Start typing in the line edit, which will grab the keyboard focus and allow the user to type in the search box.
        :return:
        """
        if not self.typing:
            save_expanded_state(self.tree_model.tableName(), self.treeView)
            self.typing = True
            self.lineEdit().grabKeyboard()

    def stop_typing(self):
        """
        Stop typing in the line edit, which will release the keyboard focus and clear the search filter.
        :return:
        """
        if self.typing:
            self.typing = False
            self.lineEdit().releaseKeyboard()
            self.proxy_model.setFilterRegularExpression('')
            if isinstance(self.tree_model, CheckableTreeModel):
                if isinstance(self.view(), CheckableTreeView):
                    self.view().expand_all_checked()
            else:
                restore_expanded_state(self.tree_model.tableName(), self.treeView)

    def set_text(self, text: str):
        """
        Set the text of the line edit to the given text. This method is used to update the line edit text when the user
        selects an item from the tree view or when the text is set programmatically. It checks if the combo box is not
        currently typing before setting the text to avoid conflicts with user input. If the model is checkable, the
        subclass CheckableTreeModel will handle the check state of items, and this method will set the text
        :param text: text to set as the text of the line edit
        :return:
        """
        if not self.checkable and not self.typing:
            self.lineEdit().setText(text)

    def setModel(self, model: CheckableTreeModel | QSortFilterProxyModel):
        """
        Set the model for the tree view in the combo box. This method overrides the default setModel method to set
        a TreeSortFilterProxyModel as the source model for the tree view. The proxy model allows for filtering of items
        based on the text entered in the line edit. It also sets the filter case sensitivity to case-insensitive and
        enables recursive filtering. The first column is shown, and all other columns are hidden by default.
        :param model:
        :return:
        """
        start_set_model_time = time.time()
        self.tree_model, indexes = find_tree_model(model, None)
        if not self.tree_model:
            logger_setup.get_logger().info(f'No checkable tree model found in {self.objectName()}')
            return
        self.proxy_model = TreeSortFilterProxyModel(self, self.treeView)
        self.proxy_model.setSourceModel(model)
        self.proxy_model.setDynamicSortFilter(False)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        self.treeView.setUniformRowHeights(True)
        # self.blockSignals(True)
        super().setModel(self.proxy_model)
        # self.blockSignals(False)
        show_column(self, 0)
        self.treeView.resizeColumnToContents(0)
        self.treeView.setMinimumWidth(self.treeView.sizeHint().width())
        self.treeView.setSortingEnabled(False)
        logger_setup.get_logger().debug(
            f'Set model for tree combobox in {time.time() - start_set_model_time:.2f} seconds')

    def update_filter(self, text: str):
        """
        Update the filter of the proxy model based on the text entered in the line edit. This method is called whenever
        the text in the line edit is edited by typing. It sets the filter regular expression of the proxy model
        to match (case-insensitive) the text entered by the user. If the text is not empty, it expands all items in
        the tree view to show all matching items. This allows users to search for items in the tree structure by typing.
        :param text: text to filter the items in the tree view
        :return:
        """
        self.start_typing()
        # logger_setup.get_logger().debug(f'Setting filter to: {text}')
        search_expression = QtCore.QRegularExpression(text,
                                                      options=QtCore.QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        self.proxy_model.setFilterRegularExpression(search_expression)
        if text != "":
            self.treeView.expandAll()
        self.showPopup()

    def enable_context_menu(self, show_context_menu: bool):
        """
        Enable or disable the context menu for the tree view in the combo box. If show_context_menu is True, it sets
        the context menu policy to CustomContextMenu and connects the customContextMenuRequested signal to the
        show_context_menu method. If show_context_menu is False, it sets the context menu policy to NoContextMenu.
        :param show_context_menu: True or False to enable or disable the context menu
        :return:
        """
        self.context_menu = show_context_menu
        if self.context_menu:
            self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            self.customContextMenuRequested.connect(self.show_context_menu)
        else:
            self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.NoContextMenu)

    def show_context_menu(self, pos):
        """
        Show the context menu for the tree view in the combo box. This method is called when the user right-clicks
        on the tree view. It creates a TreeContextMenu and sets the view to the tree view. The context menu includes
        options for editing, adding, expanding/collapsing items, and other actions based on the current table of the model.
        If the model is an Aliquots table, it sets the view to the tree view with specific options. The action selected
        in the context menu is processed, and signals are emitted for editing or adding items. The popup is shown after
        the context menu is executed to ensure that the user can continue interacting with the combo box.
        :param pos:
        :return:
        """
        menu = TreeContextMenu()
        if not self.tree_model:
            logger_setup.get_logger().info(f'No checkable tree model found in {self.objectName()}')
            return
        if self.tree_model.tableName() == 'Aliquots':
            menu.set_view(self.treeView, False, False)
        else:
            menu.set_view(self.treeView, False)
        action = menu.exec(self.mapToGlobal(pos))
        if action:
            if action.text() == 'Edit':
                self.edit_triggered.emit(self)
                logger_setup.get_logger().info(f'Edit triggered for combo box')
            elif 'Add' in action.text() or 'Insert' in action.text():
                self.add_triggered.emit(self, action)
                logger_setup.get_logger().info(f'Add triggered for combo box')
            elif 'Expand' in action.text() or 'Collapse' in action.text():
                expand_collapse(self.treeView, action)
            elif 'Delete' in action.text():
                self.delete_triggered.emit(self, action)
                logger_setup.get_logger().info(f'Delete triggered for combo box')
            self.showPopup()

    def set_line_edit_text(self, text: str):
        """
        Set the text of the line edit to the given text. This method is only called when the user is not currently typing.
        :param text: text to set as the text of the line edit
        :return:
        """
        if not self.typing:
            self.lineEdit().setText(text)

    def setCurrentText(self, text: str):
        """
        Set the current text of the combo box to the given text. The text is only set if the user is not currently typing.
        :param text: text to set as the current text of the combo box
        :return:
        """
        if not self.typing:
            super().setCurrentText(text)

    def setCurrentIndex(self, index: int):
        """
        Set the current index of the combo box to the given index. The index is only set if the user is not currently typing.
        :param index: row index to set as the current index of the combo box
        :return:
        """
        if not self.typing:
            super().setCurrentIndex(index)

    def setEditText(self, text: str):
        """
        Set the text of the line edit to the given text. This method is used to update the line edit text when the user
        selects an item from the tree view or when the text is set programmatically. It checks if the combo box is not
        currently typing before setting the text to avoid conflicts with user input.
        :param text: String to set as the current text of the combo box
        :return:
        """
        if not self.typing:
            self.lineEdit().setText(text)

    def showPopup(self):
        """
        Show the popup for the combo box. This method is called to display the dropdown list of items in the combo box.
        If the model is a tree model and the user is not typing, it restores the expanded state of the tree view before
        showing the popup. It resizes the columns to fit the contents and sets the width and height of the tree view to
        fit the size hint for the name column. The popup_shown flag is set to True to indicate that the popup is
        currently shown. If the tree model has no items, it does not show the popup.
        :return:
        """
        if not self.tree_model:
            return
        if self.tree_model.rowCount(QtCore.QModelIndex()) == 0:
            return
        show_loading_dialog('Loading', f'Loading {self.tree_model.sourceModel().rowCount()} items...')
        if not self.typing:
            if isinstance(self.tree_model, CheckableTreeModel):
                if isinstance(self.view(), CheckableTreeView):
                    self.view().expand_all_checked()
            else:
                restore_expanded_state(self.tree_model.table, self.treeView)
        self.treeView.resizeColumnToContents(0)
        # print(self.treeView.sizeHintForColumn(0))
        if self.treeView.width() < self.treeView.sizeHintForColumn(0):
            self.treeView.setFixedWidth(self.treeView.sizeHintForColumn(0))
        if self.treeView.height() < self.treeView.sizeHint().height():
            self.treeView.setFixedHeight(self.treeView.sizeHint().height())
        close_loading_dialog('Loading', f'Loading {self.tree_model.sourceModel().rowCount()} items...')
        super().showPopup()
        # logger_setup.get_logger().debug(f'Popup showed: {self.treeView.isVisible()}')
        self.popup_shown = True

    def hidePopup(self):
        """
        Hide the popup for the combo box. This method is called to hide the dropdown view in the combo box only if it
        is shown. It checks if the user has clicked outside the view or if the expand/collapse action was triggered to
        keep the popup open when expanding/collapsing or selecting multiple items is allowed. When hiding, it saves the
        expanded state of the tree view if the model is a tree model and the user is not typing. This ensures that the
        expansions to show filtered items do not overwrite the user's expanded state. The typing state is stopped and the
        closing signal is emitted to notify that the popup is being closed.
        :return:
        """
        if self.popup_shown:
            if self.treeView.rect().contains(self.treeView.mapFromGlobal(QtGui.QCursor.pos())):
                # Check if the cursor is still on the view
                if self.expand_collapse:
                    # The click was an expand/collapse action and should not close the popup
                    return
            super().hidePopup()
            if self.tree_model and not self.typing:
                save_expanded_state(self.tree_model.table, self.treeView)
            self.popup_shown = False
            self.stop_typing()

    def focusOutEvent(self, event):
        """
        Handle the focus out event for the combo box. This method is called when the combo box loses focus. If the event
        is a focus out event, it hides the popup to ensure that the dropdown list is not visible when the combo box
        loses focus.
        :param event:
        :return:
        """
        if event == QtCore.QEvent.Type.FocusOut:
            self.hidePopup()
        super().focusOutEvent(event)

    def eventFilter(self, obj, event):
        """
        Filter events for the combo box and its view. This method is used to handle mouse button press events on the
        combo box and its view. It checks if the event is a mouse button press on the line edit or the view's viewport.
        If the event is a right-click on the line edit, it shows the context menu if it is enabled. If the event is a
        left-click on the view's viewport, it checks if the expand/collapse action was triggered. If it was, it expands
        or collapses the item at the clicked position without selecting it. If the event is a right-click on the view's
        viewport, it shows the context menu if it is enabled. Other events are passed to the superclass.
        :param obj:
        :param event:
        :return:
        """
        if obj == self.treeView.viewport():
            if event.type() == QtCore.QEvent.Type.MouseButtonPress:
                # If the user clicks on the expand/collapse button, do not select the item, only expand/collapse

                index = self.treeView.indexAt(event.pos())
                if not index.isValid():
                    super().eventFilter(obj, event)
                # Define the rectangle for the item and the expand/collapse button
                item_rect = self.treeView.visualRect(index)
                option = QtWidgets.QStyleOptionViewItem()
                option.initFrom(self.treeView)
                option.rect = item_rect
                option.state = QtWidgets.QStyle.StateFlag.State_Enabled
                if self.treeView.model().hasChildren(index):
                    option.state |= QtWidgets.QStyle.StateFlag.State_Children
                if self.treeView.isExpanded(index):
                    option.state |= QtWidgets.QStyle.StateFlag.State_Open

                expand_button_rect = self.treeView.style().subElementRect(
                    QtWidgets.QStyle.SubElement.SE_TreeViewDisclosureItem,
                    option, self.treeView)
                if expand_button_rect.contains(event.pos()):
                    self.stop_typing()
                    self.set_text(index.data(QtCore.Qt.ItemDataRole.DisplayRole))
                    self.expand_collapse = False
                    self.hidePopup()
                    return True
                else:
                    self.stop_typing()
                    if self.treeView.isExpanded(index):
                        self.treeView.collapse(index)
                    else:
                        self.treeView.expand(index)
                    # save_expanded_state(model.table, self.treeView)
                    self.expand_collapse = True
                    self.showPopup()
                    return True
            return super().eventFilter(obj, event)
        return super().eventFilter(obj, event)

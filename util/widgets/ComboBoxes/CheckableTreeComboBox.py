from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtGui import QAction

from util import geocork_logger
from util.loading_dialog_manager import show_loading_dialog, close_loading_dialog
from util.widgets.ComboBoxes.TreeComboBox import TreeComboBox
from util.widgets.context_menus import TreeContextMenu
from util.widgets.models.tree_models import CheckableTreeModel
from util.widgets.views.tree_views import CheckableTreeView, save_expanded_state, expand_collapse


class CheckableTreeComboBox(TreeComboBox):
    """
    Custom QComboBox subclass that displays a checkable tree structure in the dropdown list. This class extends TreeCombobox
    to provide functionality checkable tree models. It allows users to select multiple items from the
    dropdown list by checking the checkboxes next to each item. Closing the dropdown will emit a signal similar to editing
    finished that can be connected to a slot for further processing. A proxy model filter allows the user can search for
    items by typing in the line edit. The view supports a context menu for editing, adding, and deleting items.
    Setting single_click to True will upon click uncheck all items except the one clicked, forcing the user to select
    only one item at a time.
    """
    closing = QtCore.pyqtSignal()
    edit_triggered = QtCore.pyqtSignal(QtWidgets.QComboBox)
    add_triggered = QtCore.pyqtSignal(QtWidgets.QComboBox, QAction)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.checkable = True
        self.single_click = False
        self.closedOnLineEditClick = False
        self.clicked = False
        self.edited = False
        self.treeView = CheckableTreeView()
        # show the empty root item in the combo box
        self.treeView.setRootIsDecorated(True)
        self.treeView.setWindowFlags(QtCore.Qt.WindowType.Popup)
        self.treeView.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.treeView.viewport().installEventFilter(self)
        self.treeView.setFocusProxy(self.lineEdit())
        self.setView(self.treeView)
        self.lineEdit().setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.lineEdit().textChanged.connect(self.le_text_changed)
        self.context_menu = False

    def le_text_changed(self):
        """
        Handle text changes in the line edit. This method is called whenever the text in the line edit is changed while
        not typing to make sure that it reflects the current state of the tree view.
        :return:
        """
        # print(f'{self.objectName()} line edit text changed: {self.lineEdit().text()}')
        if not self.typing:
            self.update_line_edit()

    def setModel(self, model: CheckableTreeModel):
        """
        Set the model for the checkable tree combo box. This method overrides the TreeCombobox setModel method to ensure
        connect the dataChanged signal of the model to the update_line_edit method to update the line edit text whenever
        the data in the model changes. It also expands all checked items in the tree view to show the hierarchy of checked
        items.
        :param model: CheckableTreeModel to be set as the model for the checkable tree combo box
        :return:
        """
        super().setModel(model)
        if self.tree_model and isinstance(self.tree_model, CheckableTreeModel):
            self.tree_model.checksChanged.connect(self.update_line_edit)

    def set_single_click(self, single_click):
        """
        Set whether the checkable tree combo box should allow single-click selection. If single_click is True, clicking
        on an item will uncheck all other items and select only the clicked item. If single_click is False, multiple items
        can be selected.
        :param single_click:
        :return:
        """
        self.single_click = single_click

    def update_line_edit(self):
        """
        Update the line edit text based on the checked items in the tree view. This method is called whenever the data
        in the model changes or when the user interacts with the tree view. It retrieves the checked items from the tree
        model and updates the line edit text accordingly. If there are partially checked items, the line edit is set to a
        dash ('-'). If there are fully checked items, the line edit is set to a semicolon-separated list of their names.
        If no items are checked, the line edit is set to the placeholder text. This ensures that the line edit always
        reflects the current state of the tree view and provides a clear indication of the selected items.
        :return:
        """
        current_line_edit_text = self.lineEdit().text()
        if not self.tree_model:
            geocork_logger.get_logger().info(f'No checkable tree model found in {self.objectName()}')
            return
        if self.tree_model.partially_checked_ids:
            # At least one item is partially checked, so the line edit should be a dash
            self.lineEdit().setText('-')
        elif self.tree_model.checked_ids:
            new_text = self.tree_model.selected_items_string()
            if new_text and new_text != current_line_edit_text:
                self.lineEdit().setText(new_text)
        else:
            # No items are checked, so the line edit should be set to the placeholder text
            self.lineEdit().setText('')
        # logger_setup.get_logger().debug(f'Line edit text updated to {self.lineEdit().text()}')

    def clear_all_checks(self):
        """
        Clear all checks in the checkable tree combo box. This method traverses the tree model and unchecks all items
        in the tree view.
        :return:
        """
        if not self.tree_model or not isinstance(self.tree_model, CheckableTreeModel):
            return
        self.tree_model.clear_checks()

    def check_all(self):
        """
        Check all items in the checkable tree combo box. This method finds the tree model and calls its check_all method.
        :return:
        """
        # traverse the tree and check all items
        if not self.tree_model or not isinstance(self.tree_model, CheckableTreeModel):
            return
        self.tree_model.check_all()

    def show_context_menu(self, pos):
        """
        Show the context menu for the checkable tree combo box. This method is called when the user right-clicks on
        the checkable tree view or the line edit. It creates a TreeContextMenu and passes the tree view. The context menu
        includes options for editing, adding, expanding/collapsing items, and other actions based on the current table of
        the model. The action selected in the context menu is processed, and signals are emitted for editing or adding
        items. The popup is shown after the context menu is executed to ensure that the user can continue interacting
        with the combo box.
        :param pos:
        :return:
        """
        menu = TreeContextMenu()
        if not self.tree_model:
            geocork_logger.get_logger().info(f'No checkable tree model found in {self.objectName()}')
            return
        if self.tree_model.tableName() == 'Aliquots':
            menu.set_view(self.treeView, False, False)
        else:
            menu.set_view(self.treeView, False)
        action = menu.exec(self.mapToGlobal(pos))
        if action:
            if action.text() == 'Edit':
                geocork_logger.get_logger().info(f'Edit triggered for checkable tree combo box')
                self.edit_triggered.emit(self)
            elif 'Add' in action.text() or 'Insert' in action.text():
                geocork_logger.get_logger().info(f'Add triggered for checkable tree combo box')
                self.add_triggered.emit(self, action)
            elif 'Expand' in action.text() or 'Collapse' in action.text():
                expand_collapse(self.treeView, action)
            elif 'Check all' in action.text():
                self.check_all()
            elif 'Clear all checks' in action.text():
                self.clear_all_checks()

    def showPopup(self):
        """
        Show the popup for the checkable tree combo box. This method is called to display the dropdown list of items in
        the checkable tree combo box. If the model is a tree model and the user is not typing, it expands the parents of
        checked items to show the hierarchy of checked items.
        :return:
        """
        show_loading_dialog('Loading', f'Loading {self.tree_model.sourceModel().rowCount()} items...')
        geocork_logger.get_logger().info(
            f'Showing popup for checkable tree combo box with {self.tree_model.sourceModel().rowCount()} items')
        super().showPopup()
        if not self.clicked:
            # If the user has not clicked on an item yet, expand all checked items. After the first click, the
            # user's expanded state is saved and restored when the popup is shown again.
            self.treeView.expand_all_checked()
        close_loading_dialog('Loading', f'Loading {self.tree_model.sourceModel().rowCount()} items...')

    def hidePopup(self):
        """
        Hide the popup for the checkable tree combo box. This method is called to hide the dropdown view in the combo box
        only if it is shown. It checks if the user has clicked outside the view or if the expand/collapse action was
        triggered to keep the popup open when expanding/collapsing or selecting multiple items is allowed. When hiding, it
        saves the expanded state of the tree view if the model is a tree model and the user is not typing. This ensures that
        the expansions to show filtered items do not overwrite the user's expanded state. The typing state is stopped and the
        closing signal is emitted to notify that the popup is being closed. If the popup is already hidden, it does nothing.
        :return:
        """
        if self.popup_shown:
            # Check if the cursor is still over the view or the combo box and the combo box has focus, if so, do not hide the popup
            if (self.treeView.rect().contains(self.treeView.mapFromGlobal(QtGui.QCursor.pos()))
                or self.rect().contains(self.mapFromGlobal(QtGui.QCursor.pos()))) and self.hasFocus():
                if not self.single_click:
                    return
                if self.expand_collapse:
                    # The click was an expand/collapse action and should not close the popup
                    return
            QtWidgets.QComboBox.hidePopup(self)
            if self.tree_model and not self.typing and self.clicked:
                # Only save the expanded state if the user clicked on an item, the model is a tree model, and the user is not typing
                save_expanded_state(self.tree_model.table, self.treeView)
            self.popup_shown = False
            self.clicked = False
            self.stop_typing()
            self.closing.emit()
            self.update_line_edit()

    def eventFilter(self, obj, event):
        """
        Filter events for the viewport of the checkable tree combo box. This method is used to handle mouse button press
        events on the viewport of the tree view. If the event is a left-click on the viewport, it checks if the
        expand/collapse button was clicked. If it was, it expands or collapses the item at the clicked position. If not,
        it toggles the check state of the item at the clicked position. If the event is a right-click on the viewport,
        it shows the context menu if it is enabled. Other events are passed to the superclass.
        :param obj:
        :param event:
        :return:
        """
        if obj == self.treeView.viewport():
            if event.type() == QtCore.QEvent.Type.MouseButtonPress and event.button() == QtCore.Qt.MouseButton.LeftButton:
                index = self.treeView.indexAt(event.pos())
                if not index.isValid():
                    super().eventFilter(obj, event)
                self.clicked = True
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
                    # This returns true when the expand/collapse icon is NOT clicked
                    if self.single_click:
                        # Was the only selected item unchecked? If so, set the current index to the root before clearing all checks
                        if not self.tree_model:
                            geocork_logger.get_logger().info(f'No checkable tree model found in {self.objectName()}')
                            return True
                        checked_indices, partially_checked_indices = self.tree_model.traverse_checkable_tree(
                            QtCore.QModelIndex())
                        for model_index in checked_indices:
                            if model_index == index or (model_index.row() == index.row()
                                                        and model_index.column() == index.column()
                                                        and model_index.parent() == index.parent()):
                                self.treeView.setCurrentIndex(QtCore.QModelIndex())
                                break
                        self.tree_model.blockSignals(True)
                        self.clear_all_checks()
                        self.tree_model.blockSignals(False)
                        self.treeView.toggle_check_state(index)
                        self.stop_typing()
                        self.set_line_edit_text(index.data(QtCore.Qt.ItemDataRole.DisplayRole))
                        self.expand_collapse = True
                        self.hidePopup()
                        self.closing.emit()
                    else:
                        self.treeView.toggle_check_state(self.treeView.currentIndex())
                        self.stop_typing()
                        self.update_line_edit()
                        self.expand_collapse = False
                        self.showPopup()
                    return True
                else:
                    self.stop_typing()
                    if self.treeView.isExpanded(index):
                        self.treeView.collapse(index)
                    else:
                        self.treeView.expand(index)
                    self.expand_collapse = True
                    self.showPopup()
                    return True
            elif event.type() == QtCore.QEvent.Type.MouseButtonPress and event.button() == QtCore.Qt.MouseButton.RightButton:
                self.stop_typing()
                self.show_context_menu(event.pos())
                return True
            return super().eventFilter(obj, event)
        return super().eventFilter(obj, event)

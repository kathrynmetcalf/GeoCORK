import time

from PyQt6 import QtCore, QtWidgets, QtGui

from util import logger
import util.Text_manipulations as TxM
from util.database.database_helper import get_name_column, get_view_from_table, show_column
from util.loading_dialog_manager import show_loading_dialog, close_loading_dialog
from util.widgets.context_menus import TreeContextMenu
from util.widgets.models.proxy_models import ReadableProxyModel
from util.widgets.models.query_models import CheckableSqlQueryModel
from util.widgets.models.table_models import CheckableSQLiteTableModel, CheckableSqlTableModel, SampleAgeTableModel
from util.widgets.models.tree_models import CheckableTreeModel


class CheckableComboBox(QtWidgets.QComboBox):
    """
    A QComboBox subclass that allows for checkable items in the dropdown list. This class extends QComboBox to provide
    functionality for displaying a list of items with checkboxes. It allows users to select multiple items from the
    dropdown list by checking the checkboxes next to each item. Closing the dropdown will emit a signal similar to editing
    finished that can be connected to a slot for further processing. A proxy model filter allows the user to search for
    items by typing in the line edit. The view supports a context menu for editing, adding, and deleting items.
    Setting single_click to True will upon click uncheck all items except the one clicked, forcing the user to select
    only one item at a time.
    Setting not_null to True will prevent the user from unchecking all items, ensuring that at least one item is always selected.
    """
    closing = QtCore.pyqtSignal()
    edit_triggered = QtCore.pyqtSignal(QtWidgets.QComboBox)
    add_triggered = QtCore.pyqtSignal(QtWidgets.QComboBox)
    delete_triggered = QtCore.pyqtSignal(QtWidgets.QComboBox)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setPlaceholderText("Search")
        self.lineEdit().setReadOnly(False)
        self.model_modifiable = False
        self.single_click = False
        self.not_null = False
        self.typing = False
        self.proxy_model = None
        # self.tableView = QtWidgets.QTableView()
        # self.setView(self.tableView)
        self.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.context_menu = False
        self.name_col = None
        self.table = ''
        self.popup_shown = False

        self.only_select_deselect = False
        """Used to only show select and deselect all for Sample, Aliquot, Spot, UPbAnalyses table. Used mainly for the exporter widget"""

        self.view().setFocusProxy(self.lineEdit())
        self.view().setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.lineEdit().setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.lineEdit().textEdited.connect(self.update_filter)
        self.lineEdit().textChanged.connect(self.le_text_changed)
        self.view().viewport().installEventFilter(self)
        self.lineEdit().installEventFilter(self)

    def le_text_changed(self):
        """
        Handle text changes in the line edit. This method is called whenever the text in the line edit is changed while
        not typing to make sure that it reflects the current state of the tree view.
        :return:
        """
        # print(f'{self.objectName()} line edit text changed: {self.lineEdit().text()}')
        if not self.typing:
            self.update_line_edit()

    def start_typing(self):
        """
        Start typing in the line edit, which will grab the keyboard focus and allow the user to type in the search box.
        :return:
        """
        self.typing = True
        self.lineEdit().grabKeyboard()

    def stop_typing(self):
        """
        Stop typing in the line edit, which will release the keyboard focus and clear the search filter.
        :return:
        """
        self.typing = False
        self.lineEdit().releaseKeyboard()
        self.proxy_model.setFilterRegularExpression('')

    def update_line_edit(self):
        """
        Update the line edit text with the names of the checked items. This method uses the checkable model's selected_items_string method.
        :return:
        """
        current_line_edit_text = self.lineEdit().text()
        source_model = self.source_model()
        if isinstance(source_model,
                      CheckableSqlTableModel | CheckableSqlQueryModel | CheckableSQLiteTableModel | SampleAgeTableModel):
            if source_model.partially_checked_ids:
                # At least one item is partially checked, so the line edit should be a dash
                self.lineEdit().setText('-')
            elif source_model.checked_ids:
                new_text = source_model.selected_items_string()
                if new_text and new_text != current_line_edit_text:
                    self.lineEdit().setText(new_text)
            else:
                # No items are checked, so the line edit should be set blank. Any placeholder text will be shown grayed out
                self.lineEdit().setText("")
            # logger_setup.get_logger().debug(f'Line edit text updated to {self.lineEdit().text()}')
        else:
            # Step through the model and get the checked items, then set the line edit text to the names of the checked items
            checked_names = []
            for row in range(source_model.rowCount()):
                index = source_model.index(row, 0)
                if source_model.data(index, QtCore.Qt.ItemDataRole.CheckStateRole) == QtCore.Qt.CheckState.Checked:
                    checked_name = source_model.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
                    if checked_name is not None and checked_name not in checked_names:
                        checked_names.append(checked_name)
            if checked_names:
                self.lineEdit().setText('; '.join(sorted(checked_names)))
            else:
                self.lineEdit().setText('')

    def set_line_edit_text(self, text: str):
        """
        Set the text of the line edit to the given text. This method is used to check if the user is typing in the line edit
        and only update the text if they are not currently typing.
        :param text: string to set as the text of the line edit
        :return:
        """
        if not self.typing:
            self.lineEdit().setText(text)

    def setCurrentText(self, text: str):
        """
        Set the current text of the combo box to the given text. The text is only set if the user is not currently typing.
        :param text: String to set as the current text of the combo box
        :return:
        """
        if not self.typing:
            # Get the index of the text in the combo box
            index = self.findText(text)
            if index != -1:
                super().setCurrentIndex(index)

    def setCurrentIndex(self, index: int):
        """
        Set the current index of the combo box to the given index. The index is only set if the user is not currently typing.
        :param index: row index to set as the current index of the combo box
        :return:
        """
        if not self.typing:
            super().setCurrentIndex(index)

    def source_model(self):
        """
        Get the model of the combo box. If a proxy model is set, it returns the source model of the proxy model.
        :return: checkable model
        """
        if self.proxy_model:
            return self.proxy_model.sourceModel()
        else:
            return super().model()

    def setModel(self,
                 model: CheckableSqlTableModel | CheckableSqlQueryModel | SampleAgeTableModel | QtCore.QSortFilterProxyModel):
        """
        Set the model for the combo box. If a proxy model is provided, it sets the source model of the proxy model.
        :param model: checkable model or proxy model
        :return:
        """
        start_set_model_time = time.time()
        if isinstance(model, QtCore.QSortFilterProxyModel):
            self.proxy_model = model
            model = model.sourceModel()
        else:
            self.proxy_model = ReadableProxyModel()
            self.proxy_model.setSourceModel(model)
        model.checksChanged.connect(self.update_line_edit)
        self.table = model.tableName()
        model.blockSignals(True)
        super().setModel(self.proxy_model)
        model.blockSignals(False)

        column = model.headerData(0, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole)
        if isinstance(column, int):
            self.table = None
            self.name_col = None
            return
        if isinstance(model, CheckableSqlQueryModel | CheckableSQLiteTableModel):
            self.name_col = get_name_column(get_view_from_table(self.table))
        else:
            self.name_col = get_name_column(self.table)
        if self.name_col:
            self.proxy_model.setFilterKeyColumn(self.name_col)
            show_column(self, self.name_col)
        self.view().setModel(self.proxy_model)
        self.view().setMinimumWidth(self.view().sizeHint().width())
        logger.get_logger().debug(
            f'Set model for {self.table} combo box in {time.time() - start_set_model_time:.2f} seconds')

    def update_filter(self, text: str):
        """
        Update the filter of the proxy model based on the text entered in the line edit. This method is called whenever
        the text in the line edit is edited by typing. It sets the filter regular expression of the proxy model
        to match (case-insensitive) the text entered by the user.
        :param text: string to filter the items in the combo box
        :return:
        """
        self.start_typing()
        # logger_setup.get_logger().debug(f'Setting filter to: {text}')
        show_loading_dialog('Loading', 'Updating search...')
        search_expression = QtCore.QRegularExpression(text,
                                                      options=QtCore.QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.proxy_model.setFilterRegularExpression(search_expression)
        self.lineEdit().setText(text)
        close_loading_dialog('Loading', 'Updating search...')
        self.showPopup()

    def enable_context_menu(self, show_context_menu: bool, only_select_deselect=False):
        """
        Enable or disable the context menu for the combo box. If show_context_menu is True and the model is modifiable,
        it sets the context menu policy to CustomContextMenu and connects the customContextMenuRequested signal to
        the contextMenuEvent method. If show_context_menu is False or the model is not modifiable, it disables the context menu.
        :param show_context_menu:
        :return:
        """
        self.context_menu = show_context_menu
        self.only_select_deselect = only_select_deselect
        if self.context_menu and self.model_modifiable:
            self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            # self.customContextMenuRequested.connect(self.contextMenuEvent)
        else:
            self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.NoContextMenu)

    def contextMenuEvent(self, event):
        """
        Handle the context menu event for the combo box. This method is called when the user right-clicks on the combo box.
        It creates a context menu with options to edit, add, clear all checks, select all, and delete items based on the
        current table of the combo box. Actions are processed based on the user's selection in the context menu and
        emit signals for editing, adding, and deleting items to be handled by the parent widget.
        :param event:
        :return:
        """
        menu = TreeContextMenu()
        if self.table == '"References"':
            table = 'References'
        else:
            table = self.table
        if self.table in ('Samples', 'Aliquots', 'Spots', 'UPbAnalyses',
                          'FilterGroups') and self.model().rowCount() != 0:
            if self.only_select_deselect:
                edit_action = None
                add_action = None
                clear_all_action = menu.addAction("Clear All Checks")
                select_all_action = menu.addAction("Check All")
                delete_action = None
            else:
                # Check if the parent window at any level is class SampleInformation
                if self.table == 'Samples':
                    parent = self.parent()
                    while parent is not None:
                        if parent.__class__.__name__ == 'SampleInformation':
                            break
                        parent = parent.parent()
                    if parent is not None:
                        edit_action = None
                    else:
                        edit_action = menu.addAction(f"Edit {TxM.add_spaces_camel(table)}")
                else:
                    edit_action = menu.addAction(f"Edit {TxM.add_spaces_camel(table)}")
                add_action = None
                clear_all_action = menu.addAction("Clear All Checks")
                select_all_action = menu.addAction("Check All")
                delete_action = menu.addAction(f"Delete checked {TxM.add_spaces_camel(table)}")
        elif self.table in ('Samples', 'Aliquots', 'Spots', 'UPbAnalyses'):
            edit_action = None
            add_action = None
            clear_all_action = None
            select_all_action = None
            delete_action = None
        elif self.model().rowCount() != 0:
            edit_action = menu.addAction(f"Edit {TxM.add_spaces_camel(table)}")
            add_action = menu.addAction(f"Add {TxM.add_spaces_camel(table)}")
            clear_all_action = menu.addAction("Clear All Checks")
            select_all_action = menu.addAction("Check All")
            delete_action = menu.addAction(f"Delete checked {TxM.add_spaces_camel(table)}")
        else:
            edit_action = None
            add_action = menu.addAction(f"Add {TxM.add_spaces_camel(table)}")
            clear_all_action = None
            select_all_action = None
            delete_action = None
        action = menu.exec(self.mapToGlobal(event.pos()))
        if not action:
            return
        if action == edit_action:
            self.edit_triggered.emit(self)
        elif action == add_action:
            self.add_triggered.emit(self)
        elif action == clear_all_action:
            self.clear_all_checks()
        elif action == select_all_action:
            self.check_all()
        elif action == delete_action:
            self.delete_triggered.emit(self)
        event.accept()

    def set_single_click(self, single_click: bool):
        """
        Set whether the combo box should allow single-click selection of items. If single_click is True, clicking on an
        item will uncheck all other items and select only the clicked item. If single_click is False, clicking on an
        item will toggle its check state without affecting other items.
        :param single_click: True or False
        :return:
        """
        self.single_click = single_click

    def clear_all_checks(self):
        """
        Clear all checks in the combo box. This method iterates through all rows in the model and sets the check state
        of each item to Unchecked. It also clears the text in the line edit to indicate that no items are selected.
        :return:
        """
        if not self.source_model():
            return
        source_model = self.source_model()
        if not isinstance(source_model, CheckableSqlTableModel | CheckableSqlQueryModel | CheckableSQLiteTableModel):
            return
        source_model.clear_checks()
        self.lineEdit().setText("")
        logger.get_logger().info(f'Cleared all checks in {self.table} combo box')

    def check_all(self):
        """
        Set all items in the combo box to Checked. This method iterates through all rows in the model and sets
        the check state of each item to Checked. It also updates the line edit text to show the names of all checked items.
        :return:
        """
        if not self.source_model() or not isinstance(self.source_model(),
                                                     CheckableSqlTableModel | CheckableSqlQueryModel | CheckableSQLiteTableModel):
            return
        self.source_model().check_all()

    def showPopup(self):
        """
        Show the popup for the combo box. This method is called to display the dropdown list of items in the combo box.
        The popup is shown only if there are items in the model. It sets the width of the view to fit the width of the
        combo box or the size hint for the name column, whichever is larger. It also sets the height of the view to
        fit the size hint of the view. The popup_shown flag is set to True to indicate that the popup is currently shown.
        :return:
        """
        if self.proxy_model.rowCount() == 0:
            return
        start_time = time.time()
        show_loading_dialog('Loading', f'Loading {self.proxy_model.rowCount()} items...')
        width_hint = self.view().sizeHintForColumn(
            self.name_col) if self.name_col is not None else self.view().sizeHint().width()
        checkbox_width = self.style().pixelMetric(
            QtWidgets.QStyle.PixelMetric.PM_IndicatorWidth) + 4  # Add some padding for the checkbox
        total_width = width_hint + checkbox_width
        if self.width() > total_width:
            self.view().setFixedWidth(self.width())
        else:
            self.view().setFixedWidth(total_width)
        self.view().setFixedHeight(self.view().sizeHint().height())
        close_loading_dialog('Loading', f'Loading {self.proxy_model.rowCount()} items...')
        super().showPopup()
        logger.get_logger().debug(f'Popup shown in {self.table} combo box in {time.time() - start_time} seconds')
        self.popup_shown = True

    def hidePopup(self):
        """
        Hide the popup for the combo box. This method is called to hide the dropdown view in the combo box only if it
        is shown. It checks if the user has clicked outside the view or if the single_click mode is enabled to keep the
        popup open when selecting multiple items is allowed. If the popup is shown, it hides the popup and emits the
        closing signal.
        :return:
        """
        if self.popup_shown:
            logger.get_logger().info(f'Popup hiding in {self.table} combo box')
            if not self.single_click:
                # Check if the cursor is still over the view, if so, do not hide the popup
                if self.view().rect().contains(self.view().mapFromGlobal(QtGui.QCursor.pos())):
                    return
            super().hidePopup()
            self.closing.emit()
            self.popup_shown = False
            self.stop_typing()

    def eventFilter(self, obj, event):
        """
        Filter events for the combo box and its view. This method is used to handle mouse button press events on the
        combo box and its view. It checks if the event is a mouse button press on the line edit or the view's viewport.
        If the event is a right-click on the line edit, it shows the context menu if it is enabled. If the event is a
        left-click on the view's viewport, it checks if single_click mode is enabled. If it is, it clears all checks
        and sets the current index to the clicked item, updating the line edit text accordingly. If the event is a right-click
        on the view's viewport, it shows the context menu if it is enabled. Other events are passed to the superclass.
        :param obj:
        :param event:
        :return:
        """
        if obj == self.lineEdit():
            if event.type() == QtCore.QEvent.Type.MouseButtonPress and event.button() == QtCore.Qt.MouseButton.RightButton:
                if self.context_menu:
                    self.stop_typing()
                    self.contextMenuEvent(event)
                    return True
            return super().eventFilter(obj, event)

        if obj == self.view().viewport():
            if self.proxy_model:
                proxy_index = self.view().currentIndex()
                source_index = self.proxy_model.mapToSource(proxy_index)
                source_model = self.proxy_model.sourceModel()
            else:
                source_index = self.view().currentIndex()
                source_model = self.model()
            if event.type() == QtCore.QEvent.Type.MouseButtonPress and event.button() == QtCore.Qt.MouseButton.LeftButton:
                if self.single_click:
                    # Was the only selected item unchecked? If so, set the current index to -1 before clearing all checks
                    if isinstance(source_model, CheckableTreeModel):
                        clicked_id = source_model.index(source_index.row(), 1, source_index.parent()).data(
                            QtCore.Qt.ItemDataRole.DisplayRole)
                    else:
                        clicked_id = source_model.index(source_index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole)
                    if clicked_id in source_model.checked_ids:
                        if self.not_null:
                            logger.get_logger().error(f'{source_model.headerData(self.name_col,
                                                                                 QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole)} cannot be blank')
                            return True
                        source_model.clear_checks()
                        self.stop_typing()
                        self.set_line_edit_text('')
                        self.view().setCurrentIndex(QtCore.QModelIndex())
                        self.hidePopup()
                        return True
                    source_model.update_model_checks({clicked_id}, set())
                    self.stop_typing()
                    self.set_line_edit_text(source_index.data(QtCore.Qt.ItemDataRole.DisplayRole))
                    self.hidePopup()
                    return True
                else:
                    # Get model index from view index
                    index = source_model.index(source_index.row(), self.name_col)
                    if source_model.data(index, QtCore.Qt.ItemDataRole.CheckStateRole) == QtCore.Qt.CheckState.Checked:
                        source_model.setData(index, QtCore.Qt.CheckState.Unchecked,
                                             QtCore.Qt.ItemDataRole.CheckStateRole)
                    elif (source_model.data(index, QtCore.Qt.ItemDataRole.CheckStateRole) in
                          (QtCore.Qt.CheckState.Unchecked, QtCore.Qt.CheckState.PartiallyChecked)):
                        source_model.setData(index, QtCore.Qt.CheckState.Checked, QtCore.Qt.ItemDataRole.CheckStateRole)
                    self.stop_typing()
                    self.update_line_edit()
                    self.showPopup()
                    return True
            elif event.type() == QtCore.QEvent.Type.MouseButtonPress and event.button() == QtCore.Qt.MouseButton.RightButton:
                if self.context_menu:
                    self.stop_typing()
                    self.contextMenuEvent(event)
                    event.accept()
                    return True
            return super().eventFilter(obj, event)

        return super().eventFilter(obj, event)

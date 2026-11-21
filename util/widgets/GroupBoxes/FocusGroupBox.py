from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QGroupBox

from util import logger
from util.widgets.ComboBoxes.CheckableComboBox import CheckableComboBox
from util.widgets.ComboBoxes.CheckableTreeComboBox import CheckableTreeComboBox
from util.widgets.models.query_models import CheckableSqlQueryModel
from util.widgets.models.table_models import CheckableSQLiteTableModel, CheckableSqlTableModel
from util.widgets.models.tree_models import CheckableTreeModel


class FocusGroupBox(QGroupBox):
    """
    A QGroupBox subclass that emits a signal when it loses focus. This is useful for detecting when the user has
    clicked outside the group box or switched focus to another widget. Some data require validation to ensure that
    values have units set, etc. Only once editing within the group box is finished should validation and errors be
    processed. This class also tracks whether any child widgets have been edited to prevent unnecessary updates when
    the group box loses focus without any changes.
    """
    focusLost = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(FocusGroupBox, self).__init__(parent)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.focus_lost_timer = QtCore.QTimer(self)
        self.focus_lost_timer.setSingleShot(True)
        self.focus_lost_timer.timeout.connect(self.check_focus_state)
        self.initial_values = []
        self.edited = False
        self.installEventFilter(self)
        self.reset_edited()

    def reset_edited(self):
        """
        Reset the edited state of the group box and reconnect child signals. This is useful when the changes have been
        processed and the group box is ready for new edits.
        :return:
        """
        self.edited = False
        self.connect_child_signals()

    def connect_child_signals(self):
        """
        Connect signals for child widgets to track changes. This method iterates through all child widgets of the group
        box and connects their edit signals to the set_edited method. It also stores the initial values of the child widgets
        to compare against later. This allows the group box to detect if any child widget has been edited, and thus
        whether the group box itself has been edited. The initial values are stored in a list of pairs, where each pair
        contains the child widget and its initial value. The signals are disconnected first to avoid duplicate connections.
        This is useful for ensuring that the group box can accurately track changes made to its child widgets.
        Currently supports QLineEdit, QComboBox, CheckableComboBox, CheckableTreeCombobox, and QCheckBox.
        :return:
        """
        self.initial_values = []
        for child in self.findChildren(QtWidgets.QWidget):
            if isinstance(child, QtWidgets.QLineEdit):
                if isinstance(child.parent(), QtWidgets.QComboBox):
                    continue
                try:
                    child.editingFinished.disconnect()
                except TypeError:
                    pass
                self.initial_values.append([child, child.text()])
                child.editingFinished.connect(lambda ch=child: self.set_edited(ch))
            elif isinstance(child, CheckableComboBox | CheckableTreeComboBox):
                try:
                    child.currentTextChanged.disconnect()
                except TypeError:
                    pass
                try:
                    child.model().checksChanged.disconnect()
                except TypeError:
                    pass
                except AttributeError:
                    pass
                if isinstance(child.model(),
                              CheckableSqlTableModel | CheckableSqlQueryModel | CheckableSQLiteTableModel | CheckableTreeModel):
                    self.initial_values.append([child, child.model().return_checked_ids()])
                    child.model().checksChanged.connect(lambda ch=child: self.set_edited(ch))
                else:
                    self.initial_values.append([child, child.currentText()])
                    child.currentTextChanged.connect(lambda ch=child: self.set_edited(ch))
            elif isinstance(child, QtWidgets.QComboBox):
                try:
                    child.activated.disconnect()
                except TypeError:
                    pass
                self.initial_values.append([child, child.currentIndex()])
                child.activated.connect(lambda ch=child: self.set_edited(ch))
            elif isinstance(child, QtWidgets.QCheckBox):
                try:
                    child.stateChanged.disconnect()
                except TypeError:
                    pass
                self.initial_values.append([child, child.isChecked()])
                child.stateChanged.connect(lambda ch=child: self.set_edited(ch))
            child.installEventFilter(self)

    def disconnect_child_signals(self):
        """
        Disconnect signals for child widgets to prevent memory leaks and unwanted behavior. This method iterates through
        all child widgets of the group box and disconnects their signals that were connected in connect_child_signals.
        It also removes the event filter from each child widget.
        :return:
        """
        for child in self.findChildren(QtWidgets.QWidget):
            if isinstance(child, QtWidgets.QLineEdit):
                try:
                    child.editingFinished.disconnect()
                except TypeError:
                    pass
            elif isinstance(child, CheckableComboBox | CheckableTreeComboBox):
                try:
                    child.currentTextChanged.disconnect()

                except TypeError:
                    pass
                try:
                    child.add_triggered.disconnect()
                except TypeError:
                    pass
                try:
                    child.edit_triggered.disconnect()
                except TypeError:
                    pass
            elif isinstance(child, QtWidgets.QComboBox):
                try:
                    child.activated.disconnect()
                except TypeError:
                    pass
            elif isinstance(child, QtWidgets.QCheckBox):
                try:
                    child.stateChanged.disconnect()
                except TypeError:
                    pass
            child.removeEventFilter(self)

    def set_edited(self, child: QtWidgets.QWidget):
        """
        Set the edited state of the group box based on the child's current value compared to its initial value. This method
        checks if the current value of the child widget differs from its initial value stored in self.initial_values. If
        the values differ, it sets the edited state of the group box to True and logs the change. This is useful for
        tracking changes made to the child widgets and determining if the group box needs to be updated. The method also
        handles different types of child widgets, including QLineEdit, CheckableComboBox, CheckableTreeCombobox,
        :param child:
        :return:
        """
        if not isinstance(child, QtWidgets.QWidget):
            if isinstance(child, str) and isinstance(self.sender(), CheckableComboBox):
                child = self.sender().lineEdit()
            else:
                child = self.sender()
        if isinstance(child, QtWidgets.QLineEdit) and isinstance(child.parent(), QtWidgets.QComboBox):
            # The line edit of the combo box completer has been triggered, but wait until the index changes
            return
        initial_value = None
        for pair in self.initial_values:
            if pair[0] == child:
                initial_value = pair[1]
                break
        if initial_value is None:
            return
        if isinstance(child, QtWidgets.QLineEdit):
            if child.text() != initial_value:
                logger.get_logger().info(f'{child.objectName()} was edited')
                self.edited = True
        elif isinstance(child, CheckableComboBox | CheckableTreeComboBox):
            if isinstance(child.model(),
                          CheckableSqlTableModel | CheckableSqlQueryModel | CheckableSQLiteTableModel | CheckableTreeModel):
                if child.model().return_checked_ids() != initial_value:
                    self.edited = True
            else:
                if child.currentText() != initial_value:
                    self.edited = True
        elif isinstance(child, QtWidgets.QComboBox):
            if child.currentIndex() != initial_value:
                self.edited = True
        elif isinstance(child, QtWidgets.QCheckBox):
            if child.isChecked() != initial_value:
                self.edited = True

    def eventFilter(self, obj, event):
        """
        Event filter to set a delay when focus is lost to allow other widgets to process their focus and edit events.
        :param obj:
        :param event:
        :return:
        """
        if event.type() == QtCore.QEvent.Type.FocusOut:
            self.focus_lost_timer.start(100)
        return super().eventFilter(obj, event)

    def check_focus_state(self, child: QtWidgets.QWidget = None):
        """
        Check if the group box or any of its children has focus. If not, emit the focusLost signal. This method is called
        when the focus lost timer times out, indicating that the group box has lost focus. It checks if any child widget
        has focus. If no child has focus, it emits the focusLost signal to notify that the group box has lost focus.
        If a specific child is provided, it checks that child's focus state instead.
        :param child: widget within the group box to check the focus state of, if None checks all children
        :return:
        """
        if child is not None:
            # If a specific child is provided, check its focus state
            has_focus = child.hasFocus()
        has_focus = self.any_child_has_focus()
        if not has_focus:
            logger.get_logger().info(f'{self.objectName()} has lost focus')
            if self.edited:
                logger.get_logger().info(f'{self.objectName()} was edited and needs to be updated')
                self.focusLost.emit()

    def any_child_has_focus(self):
        """
        Check if any child widget of the group box has focus. This method iterates through all child widgets of the group
        box and checks if any of them has focus. If at least one child has focus, it returns True; otherwise, it returns
        False. This is useful for determining if the group box itself has focus or if any of its child widgets are being
        edited. It helps to avoid unnecessary signals when working within a group box.
        :return: True if any child has focus, False otherwise
        """
        for child in self.findChildren(QtWidgets.QWidget):
            if child.hasFocus():
                return True
        return False

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS

class FocusGroupBox(QtW.QGroupBox):
    focusLost = QtC.pyqtSignal()
    def __init__(self, parent=None):
        super(FocusGroupBox, self).__init__(parent)
        self.setFocusPolicy(QtC.Qt.FocusPolicy.NoFocus)
        self.installEventFilter(self)
        self.install_children_event_filter()
        self.focus_lost_timer = QtC.QTimer(self)
        self.focus_lost_timer.setSingleShot(True)
        self.focus_lost_timer.timeout.connect(self.check_focus_state)

    def install_children_event_filter(self):
        for child in self.findChildren(QtW.QWidget):
            child.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QtC.QEvent.Type.FocusOut:
            self.focus_lost_timer.start(0)
        return super().eventFilter(obj, event)

    def check_focus_state(self, child=None):
        has_focus = self.any_child_has_focus()
        if not has_focus:
            print(f'{self.objectName()} has lost focus')
            self.focusLost.emit()

    def any_child_has_focus(self):
        for child in self.findChildren(QtW.QWidget):
            if child.hasFocus():
                return True
        return False
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

    def install_children_event_filter(self):
        for child in self.findChildren(QtW.QWidget):
            child.installEventFilter(self)
            print(f"{self.title} child installed")
        for child in self.findChildren(QtW.QGroupBox):
            child.installEventFilter(self)
            print(f"{self.title} child installed")

    def eventFilter(self, obj, event):
        if event.type() == QtC.QEvent.Type.FocusOut:
            QtW.QApplication.instance().processEvents()
            self.check_focus_state()
        return super().eventFilter(obj, event)

    def check_focus_state(self, child=None):
        has_focus = self.any_child_has_focus()
        if not has_focus:
            self.focusLost.emit()

    def any_child_has_focus(self):
        for child in self.findChildren(QtW.QWidget):
            try:
                if child.any_child_has_focus():
                    return True
            except AttributeError:
                pass
            if child.hasFocus():
                return True
        return False
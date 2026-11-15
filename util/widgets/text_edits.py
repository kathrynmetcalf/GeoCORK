from PyQt6 import QtWidgets, QtCore


class EditingTextEdit(QtWidgets.QTextEdit):
    """
    A QTextEdit subclass that emits a signal when editing is finished. This is useful for detecting when the user has
    finished editing the text in the QTextEdit, such as when they click outside of it or press Enter. The signal is
    not emitted when the application loses focus, to avoid incomplete edits being processed.
    """
    editingFinished = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._isApplicationFocused = True
        QtWidgets.QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.ApplicationDeactivate:
            self._isApplicationFocused = False
        elif event.type() == QtCore.QEvent.Type.ApplicationActivate:
            self._isApplicationFocused = True
        return super().eventFilter(obj, event)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self._isApplicationFocused:
            # Only emit if the application is focused, not if the whole application has lost focus
            self.editingFinished.emit()


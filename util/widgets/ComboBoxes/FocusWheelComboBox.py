from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox


class FocusWheelComboBox(QComboBox):
    """
    A QComboBox that ignores mouse wheel events when focused, so the user can't accidentally
    scroll away from the intended selection.
    """
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, e):
        e.ignore()
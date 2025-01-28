from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QLineEdit


class QLineEditLabel(QWidget):
    def __init__(self, label_name=None, parent=None, objectName=None):
        super().__init__()
        self.setParent(parent)
        self.setObjectName(objectName)
        layout = QVBoxLayout()
        layout.setObjectName(objectName + '_layout')
        layout.setSpacing(0)
        self.setLayout(layout)
        self.lineedit = QLineEdit()

        self.label = QLabel(parent=self, text=label_name)
        self.label.setObjectName(objectName + '_label')

        layout.addWidget(self.label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.lineedit, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.lineedit.setMinimumWidth(self.label.width())

    def addItems(self, setparam):
        self.combobox.addItems(setparam)
        self.label.adjustSize()



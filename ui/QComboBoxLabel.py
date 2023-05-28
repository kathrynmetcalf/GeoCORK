import typing

from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QWidget, QComboBox, QLabel, QVBoxLayout, QCheckBox


class QComboBoxLabel(QWidget):
    def __init__(self, label_name=None, parent=None, objectName=None, include_checkbox=False):
        super().__init__()
        self.setParent(parent)
        self.setObjectName(objectName)
        layout = QVBoxLayout()
        layout.setObjectName(objectName + '_layout')
        layout.setSpacing(0)
        self.setLayout(layout)
        self.combobox = QComboBox(parent=self, objectName=objectName + '_combobox')

        self.label = QLabel(parent=self, text=label_name)
        self.label.setObjectName(objectName + '_label')

        layout.addWidget(self.label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        if include_checkbox:
            self.checkbox = QCheckBox("Inverse?", parent=self)
            layout.addWidget(self.checkbox, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.combobox, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.combobox.setMinimumWidth(self.label.width())

    def addItems(self, setparam):
        self.combobox.addItems(setparam)
        self.label.adjustSize()



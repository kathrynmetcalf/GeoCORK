from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextOption


class FontDelegate(QtWidgets.QStyledItemDelegate):
    """
    Custom delegate to display text with a custom font.
    """
    def initStyleOption(self, option, index):
        """Initializes the options of the delegate"""
        super().initStyleOption(option, index)
        font = index.data(QtCore.Qt.ItemDataRole.FontRole)
        if font:
            option.font = font

class WordWrapDelegate(QtWidgets.QStyledItemDelegate):
    """
    Custom delegate to enable word wrap in QTableView.
    """
    def initStyleOption(self, option, index):
        """Initializes the options of the delegate"""
        super().initStyleOption(option, index)
        option.textElideMode = Qt.TextElideMode.ElideNone  # Do not cut text
        option.wrapMode = QTextOption.WrapMode.WordWrap  # Allow word wrap
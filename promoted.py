import sys
from PyQt5 import QtWidgets as QtW  # all windows
from PyQt5 import QtCore as QtC  # more low-level stuff
from PyQt5 import QtGui as QtG  # font and color classes, etc.


class TreeCombo(QtW.QComboBox):
    def __init__(self, *args, **kwargs):
        QtW.QComboBox.__init__(self)
        self.setView(QtW.QTreeView())
        # self.view().setHeaderHidden(True)

    def showPopup(self):
        self.view().expandAll()
        # self.view().setMinimumWidth(500)
        QtW.QComboBox.showPopup(self)
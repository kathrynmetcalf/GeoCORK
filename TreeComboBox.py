from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


class TreeComboBox(QComboBox):
    def __init__(self, *args):
        super().__init__(*args)

        self.__skip_next_hide = False

        tree_view = QTreeView(self)
        tree_view.setFrameShape(QFrame.NoFrame)
        tree_view.setEditTriggers(tree_view.NoEditTriggers)
        tree_view.setAlternatingRowColors(True)
        tree_view.setSelectionBehavior(tree_view.SelectRows)
        tree_view.setItemsExpandable(True)
        tree_view.setWordWrap(True)
        tree_view.setAllColumnsShowFocus(True)
        self.setView(tree_view)

        self.view().viewport().installEventFilter(self)

    def showPopup(self):
        self.setRootModelIndex(QModelIndex())
        super().showPopup()

    def hidePopup(self):
        self.setRootModelIndex(self.view().currentIndex().parent())
        self.setCurrentIndex(self.view().currentIndex().row())
        if self.__skip_next_hide:
            self.__skip_next_hide = False
        else:
            super().hidePopup()

    def selectIndex(self, index):
        self.setRootModelIndex(index.parent())
        self.setCurrentIndex(index.row())

    def eventFilter(self, object, event):
        if event.type() == QEvent.MouseButtonPress and object is self.view().viewport():
            index = self.view().indexAt(event.pos())
            self.__skip_next_hide = not self.view().visualRect(index).contains(event.pos())
        return False


app = QApplication([])

combo = TreeComboBox()
# combo.resize(200, 30)

# parent_item = QStandardItem('Item 1')
# parent_item.appendRow([QStandardItem('Child'), QStandardItem('Yesterday')])
# model = QStandardItemModel()
# model.appendRow([parent_item, QStandardItem('Today')])
# model.appendRow([QStandardItem('Item 2'), QStandardItem('Today')])
# model.setHeaderData(0, Qt.Horizontal, 'Name', Qt.DisplayRole)
# model.setHeaderData(1, Qt.Horizontal, 'Date', Qt.DisplayRole)

model = QStandardItemModel()
model.appendRow([QStandardItem('Phanerozoic'), QStandardItem(541), QStandardItem(0)])
model.appendRow([QStandardItem('Proterozoic'), QStandardItem(2500), QStandardItem(541)])

# Will display combo box with 3 columns and headers, but no ages
model.setHeaderData(0, Qt.Horizontal, 'Name', Qt.DisplayRole)
model.setHeaderData(1, Qt.Horizontal, 'Max', Qt.DisplayRole)
model.setHeaderData(2, Qt.Horizontal, 'Min', Qt.DisplayRole)

combo.setModel(model)

combo.show()
app.exec_()
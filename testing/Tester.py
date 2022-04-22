import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

data = [ (("Cat A",False), [(("Thing 1",True), []),(("Thing 2",True), [])]),
    (("Cat B",False), [(("Thing 3",True), []), (("Thing 4",True), [])])]

class MyComboBox(QComboBox):
    def __init__(self):
        super(QComboBox,self).__init__()
        self.setView(QTreeView())

        self.view().setHeaderHidden(True)

    def showPopup(self):
        self.view().expandAll()
        QComboBox.showPopup(self)

class Window(QWidget):
    def __init__(self):

        QWidget.__init__(self)

        self.model = QStandardItemModel()
        self.addItems(self.model, data)

        self.combo = MyComboBox()
        self.combo.setModel(self.model)
        self.combo.adjustSize()

        layout = QVBoxLayout()
        layout.addWidget(self.combo)
        self.setLayout(layout)

        # I can choose which combobox item to select here, but I am unable to
        #choose child items
        #self.combo.setCurrentIndex(1)

    def addItems(self, parent, elements):
        for text, children in elements:
            item = QStandardItem(text[0])
            # root items are not selectable, users pick from child items
            # item.setSelectable(text[1])
            parent.appendRow(item)
            if children:
                self.addItems(item, children)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
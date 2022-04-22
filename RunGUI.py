import sys
from PyQt5 import QtWidgets as QtW  # all windows
from PyQt5 import QtCore as QtC  # more low-level stuff
from PyQt5 import QtGui as QtG  # font and color classes, etc.
from PyQt5.uic import loadUi
# import any other class you need
# from lxml import etree as ET
import xml.etree.ElementTree as ET


class MainWindow(QtW.QWidget):  # know what you chose for your window, that has to be your super class

    def __init__(self, *arg, **kwargs):   # dunder (__) methods
        super().__init__(*arg, **kwargs)  # need to call super, pass all args into the super class (QWidget

        # Define any widgets here

        # self.ui = Ui_SampleDataForm()  # create instance
        # self.ui.setupUi(self)  # build it
        xml_file = "GeologicTime_Ages.xml"
        self.tree = ET.parse(xml_file)
        self.model = QtG.QStandardItemModel()
        self.treeToModel()
        # self.Oldest_comboBox.setView(QtW.QTreeView())
        # self.model.setHeaderData(0, QtC.Qt.Horizontal, 'Name')
        # self.model.setHorizontalHeaderLabels(['Name', 'Ma', 'Ma'])
        self.Oldest_comboBox.setModel(self.model)
        self.Youngest_comboBox.setModel(self.model)

        # self.printOldestAgeTree(f)
        # self.printYoungestAgeTree(f)
        self.Oldest_comboBox.itemClicked.connect(self.onOldestAgeClicked)
        # self.Youngest_comboBox.itemClicked.connect(self.onYoungestAgeClicked)

        # End widgets here
        self.show()  # show the window when done, used for making a top-level window

    # Define any methods here

    def treeToModelAges(self):
        root = self.tree.getroot()
        for eon in root.findall('Eon'):
            eon_item = QtG.QStandardItem(eon.get('name'))
            for era in eon.findall('Era'):
                era_item = QtG.QStandardItem(era.get('name'))
                for period in era.findall('Period'):
                    period_item = QtG.QStandardItem(period.get('name'))
                    for epoch in period.findall('Epoch'):
                        epoch_item = QtG.QStandardItem(epoch.get('name'))
                        for age in epoch.findall('Age'):
                            age_item = QtG.QStandardItem(age.get('name'))
                            old = QtG.QStandardItem(age.get('oldest'))
                            young = QtG.QStandardItem(age.get('youngest'))
                            epoch_item.appendRow([age_item, old, young])
                        old = QtG.QStandardItem(epoch.get('oldest'))
                        young = QtG.QStandardItem(epoch.get('youngest'))
                        period_item.appendRow([epoch_item, old, young])
                    old = QtG.QStandardItem(period.get('oldest'))
                    young = QtG.QStandardItem(period.get('youngest'))
                    era_item.appendRow([period_item, old, young])
                old = QtG.QStandardItem(era.get('oldest'))
                young = QtG.QStandardItem(era.get('youngest'))
                eon_item.appendRow([era_item, old, young])
            old = QtG.QStandardItem(eon.get('oldest'))
            young = QtG.QStandardItem(eon.get('youngest'))
            self.model.appendRow([eon_item, old, young])

    def treeToModel(self):
        root = self.tree.getroot()
        for eon in root.findall('Eon'):
            eon_item = QtG.QStandardItem(eon.get('name'))
            for era in eon.findall('Era'):
                era_item = QtG.QStandardItem(era.get('name'))
                for period in era.findall('Period'):
                    period_item = QtG.QStandardItem(period.get('name'))
                    for epoch in period.findall('Epoch'):
                        epoch_item = QtG.QStandardItem(epoch.get('name'))
                        for age in epoch.findall('Age'):
                            age_item = QtG.QStandardItem(age.get('name'))
                            epoch_item.appendRow(age_item)
                        period_item.appendRow(epoch_item)
                    era_item.appendRow(period_item)
                eon_item.appendRow(era_item)
            self.model.appendRow(eon_item)


    # When the user clicks on an item in the Oldest Age combobox
    def onOldestAgeClicked(self):
        item = self.Oldest_comboBox.currentItem()
        root = self.tree.getroot()
        parent = item.parent()
        print(parent)
        # Find every instance of the selected text, must have same parent
        # for x in root.findall(f'.//{parent.text(0)}/{item.text(0)}'):
        #     oldest = x.get('oldest')
        #     self.OldestAge_lineEdit.setText(oldest)

    # When the user clicks on an item in the Youngest Age tree menu
    # def onYoungestAgeClicked(self):
    #     item = self.YoungestAge_treeWidget.currentItem()
    #     root = self.tree.getroot()
    #     parent = item.parent()
    #     # Find every instance of the selected text, must have same parent
    #     for x in root.findall(f'.//{parent.text(0)}/{item.text(0)}'):
    #         youngest = x.get('youngest')
    #         self.YoungestAge_lineEdit.setText(youngest)

    # End methods here


if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    app = QtW.QApplication(sys.argv)  # pass command line arguments
    w = MainWindow()
    sys.exit(app.exec())  # runs event loop, pass exit status to the system

import sys

import PyQt6.QtCore
from PyQt6.QtCore import QSize, QRect, Qt, QCoreApplication, QMetaObject
from PyQt6.QtWidgets import QDialogButtonBox, QWidget, QGridLayout, QTableView, QComboBox, QLabel, QApplication, QDialog


# noinspection PyArgumentList
class ImportWizardDialog(QDialog):
    DEFAULT_LABEL_ALIGNMENT: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter

    def __init__(self):
        super().__init__()

        self.buttonBox = None

        self.gridLayoutWidget = None
        self.gridLayout = None

        self.tableView = None

        self.gridLayoutWidget_2 = QWidget(self)
        self.gridLayoutWidget_2.setObjectName(u"gridLayoutWidget_2")
        self.gridLayoutWidget_2.setGeometry(QRect(10, 493, 1001, 121))
        self.gridLayout_2 = QGridLayout(self.gridLayoutWidget_2)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)

        # todo rename all to _best_age_combobox
        self.comboBox = QComboBox(self.gridLayoutWidget_2, objectName='comboBox')
        self.comboBox_2 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_2')
        self.comboBox_3 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_3')
        self.comboBox_4 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_4')
        self.comboBox_5 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_5')
        self.comboBox_6 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_6')
        self.comboBox_7 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_7')
        self.comboBox_8 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_8')
        self.comboBox_9 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_9')
        self.comboBox_10 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_10')
        self.comboBox_11 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_11')
        self.comboBox_12 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_12')
        self.comboBox_13 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_13')
        self.comboBox_14 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_14')
        self.comboBox_15 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_15')
        self.comboBox_16 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_16')
        self.comboBox_17 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_17')
        self.comboBox_18 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_18')
        self.comboBox_19 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_19')
        self.comboBox_20 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_20')

        self.label = QLabel(self.gridLayoutWidget_2, objectName='label',
                            alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_2 = QLabel(self.gridLayoutWidget_2, objectName='label_2',
                              alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_3 = QLabel(self.gridLayoutWidget_2, objectName='label_3',
                              alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_4 = QLabel(self.gridLayoutWidget_2, objectName='label_4',
                              alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_5 = QLabel(self.gridLayoutWidget_2, objectName='label_5',
                              alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_6 = QLabel(self.gridLayoutWidget_2, objectName='label',
                              alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_7 = QLabel(self.gridLayoutWidget_2, objectName='label',
                              alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_8 = QLabel(self.gridLayoutWidget_2, objectName='label',
                              alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_9 = QLabel(self.gridLayoutWidget_2, objectName='label',
                              alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_10 = QLabel(self.gridLayoutWidget_2, objectName='label',
                               alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_11 = QLabel(self.gridLayoutWidget_2, objectName='label',
                               alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_12 = QLabel(self.gridLayoutWidget_2, objectName='label',
                               alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_13 = QLabel(self.gridLayoutWidget_2, objectName='label',
                               alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_14 = QLabel(self.gridLayoutWidget_2, objectName='label',
                               alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_15 = QLabel(self.gridLayoutWidget_2, objectName='label',
                               alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_16 = QLabel(self.gridLayoutWidget_2, objectName='label',
                               alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_17 = QLabel(self.gridLayoutWidget_2, objectName='label',
                               alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_18 = QLabel(self.gridLayoutWidget_2, objectName='label',
                               alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_19 = QLabel(self.gridLayoutWidget_2, objectName='label',
                               alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.label_20 = QLabel(self.gridLayoutWidget_2, objectName='label',
                               alignment=self.DEFAULT_LABEL_ALIGNMENT)

        self.setup_ui()

    def setup_ui(self):
        if not self.objectName():
            self.setObjectName(u"ImportWizardDialog")

        self.resize(1024, 720)
        self.setMinimumSize(QSize(1024, 720))
        self.setMaximumSize(QSize(1024, 720))

        # button box setup
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(410, 660, 161, 32))
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.rejected)

        self.tableView = QTableView(self)
        self.tableView.setObjectName(u"tableView")
        self.tableView.setGeometry(QRect(10, 10, 1000, 480))

        self.add_labels()
        self.add_combo_boxes()

        self.re_translate_ui(self)

        self.show()

    @PyQt6.QtCore.pyqtSlot()
    def accepted(self) -> None:
        super().accepted()

    @PyQt6.QtCore.pyqtSlot()
    def rejected(self) -> None:
        super().rejected()

    def add_combo_boxes(self):
        row, col = 1, 0
        combo_box: QComboBox
        for combo_box in self.gridLayoutWidget_2.findChildren(QComboBox).__iter__():
            combo_box.addItem(str(row) + str(col))
            combo_box.addItem(str(combo_box.objectName()))
            if col >= 10:
                row = 3
                col = 0
            self.gridLayout_2.addWidget(combo_box, row % 4, col % 10)
            col += 1

    def add_labels(self):
        row, col = 0, 0
        label: QLabel
        for label in self.gridLayoutWidget_2.findChildren(QLabel).__iter__():
            label.setText(str(row) + str(col))
            if col >= 10:
                row = 2
                col = 0
            self.gridLayout_2.addWidget(label, row % 4, col % 10)
            col += 1

    def re_translate_ui(self, dialog):
        dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))

        self.label.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_6.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_7.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_8.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_9.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_10.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_11.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_12.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_13.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_14.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_15.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_16.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_17.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_18.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_19.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
        self.label_20.setText(QCoreApplication.translate("Dialog", u"Best Age", None))

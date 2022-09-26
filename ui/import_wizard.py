import sys

import PyQt6.QtCore
from PyQt6.QtCore import QSize, QRect, Qt, QCoreApplication, QMetaObject
from PyQt6.QtWidgets import QDialogButtonBox, QWidget, QGridLayout, QTableView, QComboBox, QLabel, QApplication, QDialog


# noinspection PyArgumentList
class ImportWizardDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.buttonBox = None

        self.gridLayoutWidget = None
        self.gridLayout = None

        self.tableView = None

        self.gridLayoutWidget_2 = None
        self.gridLayout_2 = None

        # todo rename all to _best_age_combobox
        self.comboBox = None
        self.comboBox_2 = None
        self.comboBox_3 = None
        self.comboBox_4 = None
        self.comboBox_5 = None
        self.comboBox_6 = None
        self.comboBox_7 = None
        self.comboBox_8 = None
        self.comboBox_9 = None
        self.comboBox_10 = None
        self.comboBox_11 = None
        self.comboBox_12 = None
        self.comboBox_13 = None
        self.comboBox_14 = None
        self.comboBox_15 = None
        self.comboBox_16 = None
        self.comboBox_17 = None
        self.comboBox_18 = None
        self.comboBox_19 = None
        self.comboBox_20 = None

        self.label = None
        self.label_2 = None
        self.label_3 = None
        self.label_4 = None
        self.label_5 = None
        self.label_6 = None
        self.label_7 = None
        self.label_8 = None
        self.label_9 = None
        self.label_10 = None
        self.label_11 = None
        self.label_12 = None
        self.label_13 = None
        self.label_14 = None
        self.label_15 = None
        self.label_16 = None
        self.label_17 = None
        self.label_18 = None
        self.label_19 = None
        self.label_20 = None

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

        self.gridLayoutWidget_2 = QWidget(self)
        self.gridLayoutWidget_2.setObjectName(u"gridLayoutWidget_2")
        self.gridLayoutWidget_2.setGeometry(QRect(10, 493, 1001, 121))
        self.gridLayout_2 = QGridLayout(self.gridLayoutWidget_2)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)

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
        self.comboBox = QComboBox(self.gridLayoutWidget_2, objectName='comboBox')
        self.gridLayout_2.addWidget(self.comboBox, 3, 0, 1, 1)

        self.comboBox_2 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_2')
        self.gridLayout_2.addWidget(self.comboBox_2, 3, 1, 1, 1)

        self.comboBox_3 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_3')
        self.gridLayout_2.addWidget(self.comboBox_3, 3, 2, 1, 1)

        self.comboBox_4 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_4')
        self.gridLayout_2.addWidget(self.comboBox_4, 3, 3, 1, 1)

        self.comboBox_5 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_5')
        self.gridLayout_2.addWidget(self.comboBox_5, 3, 4, 1, 1)

        self.comboBox_6 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_6')
        self.gridLayout_2.addWidget(self.comboBox_6, 3, 7, 1, 1)

        self.comboBox_7 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_7')
        self.gridLayout_2.addWidget(self.comboBox_7, 3, 8, 1, 1)

        self.comboBox_8 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_8')
        self.gridLayout_2.addWidget(self.comboBox_8, 3, 10, 1, 1)

        self.comboBox_9 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_9')
        self.gridLayout_2.addWidget(self.comboBox_9, 3, 12, 1, 1)

        self.comboBox_10 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_10')
        self.gridLayout_2.addWidget(self.comboBox_10, 3, 13, 1, 1)

        self.comboBox_11 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_11')
        self.gridLayout_2.addWidget(self.comboBox_11, 7, 0, 1, 1)

        self.comboBox_12 = QComboBox(parent=self.gridLayoutWidget_2, objectName='comboBox_12')
        self.gridLayout_2.addWidget(self.comboBox_12, 7, 1, 1, 1)

        self.comboBox_13 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_13')
        self.gridLayout_2.addWidget(self.comboBox_13, 7, 2, 1, 1)

        self.comboBox_14 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_14')
        self.gridLayout_2.addWidget(self.comboBox_14, 7, 3, 1, 1)

        self.comboBox_15 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_15')
        self.gridLayout_2.addWidget(self.comboBox_15, 7, 4, 1, 1)

        self.comboBox_16 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_16')
        self.gridLayout_2.addWidget(self.comboBox_16, 7, 7, 1, 1)

        self.comboBox_17 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_17')
        self.gridLayout_2.addWidget(self.comboBox_17, 7, 8, 1, 1)

        self.comboBox_18 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_18')
        self.gridLayout_2.addWidget(self.comboBox_18, 7, 10, 1, 1)

        self.comboBox_19 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_19')
        self.gridLayout_2.addWidget(self.comboBox_19, 7, 12, 1, 1)

        self.comboBox_20 = QComboBox(self.gridLayoutWidget_2, objectName='comboBox_20')
        self.gridLayout_2.addWidget(self.comboBox_20, 7, 13, 1, 1)

    def add_labels(self):
        self.label = QLabel(self.gridLayoutWidget_2, objectName='label')
        self.label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label, 1, 0, 1, 1)

        self.label_2 = QLabel(self.gridLayoutWidget_2, objectName='label_2')
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_2, 1, 1, 1, 1)

        self.label_3 = QLabel(self.gridLayoutWidget_2, objectName='label_3')
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_3, 1, 2, 1, 1)

        self.label_4 = QLabel(self.gridLayoutWidget_2, objectName='label_4')
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_4, 1, 3, 1, 1)

        self.label_5 = QLabel(self.gridLayoutWidget_2, objectName='label_5')
        self.label_5.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_5, 1, 4, 1, 1)

        self.label_6 = QLabel(self.gridLayoutWidget_2, objectName='label_6')
        self.label_6.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_6, 1, 7, 1, 1)

        self.label_7 = QLabel(self.gridLayoutWidget_2, objectName='label_7')
        self.label_7.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_7, 1, 8, 1, 1)

        self.label_8 = QLabel(self.gridLayoutWidget_2, objectName='label_8')
        self.label_8.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_8, 1, 10, 1, 1)

        self.label_9 = QLabel(self.gridLayoutWidget_2, objectName='label_9')
        self.label_9.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_9, 1, 12, 1, 1)

        self.label_10 = QLabel(self.gridLayoutWidget_2, objectName='label_10')
        self.label_10.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_10, 1, 13, 1, 1)

        self.label_11 = QLabel(self.gridLayoutWidget_2, objectName='label_11')
        self.label_11.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_11, 6, 0, 1, 1)

        self.label_12 = QLabel(self.gridLayoutWidget_2, objectName='label_12')
        self.label_12.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_12, 6, 1, 1, 1)

        self.label_13 = QLabel(self.gridLayoutWidget_2, objectName='label_13')
        self.label_13.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_13, 6, 2, 1, 1)

        self.label_14 = QLabel(self.gridLayoutWidget_2, objectName='label_14')
        self.label_14.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_14, 6, 3, 1, 1)

        self.label_15 = QLabel(self.gridLayoutWidget_2, objectName='label_15')
        self.label_15.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_15, 6, 4, 1, 1)

        self.label_16 = QLabel(self.gridLayoutWidget_2, objectName='label_16')
        self.label_16.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_16, 6, 7, 1, 1)

        self.label_17 = QLabel(self.gridLayoutWidget_2, objectName='label_17')
        self.label_17.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_17, 6, 8, 1, 1)

        self.label_18 = QLabel(self.gridLayoutWidget_2, objectName='label_18')
        self.label_18.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_18, 6, 10, 1, 1)

        self.label_19 = QLabel(self.gridLayoutWidget_2, objectName='19')
        self.label_19.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_19, 6, 12, 1, 1)

        self.label_20 = QLabel(self.gridLayoutWidget_2, objectName='label_20')
        self.label_20.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout_2.addWidget(self.label_20, 6, 13, 1, 1)

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



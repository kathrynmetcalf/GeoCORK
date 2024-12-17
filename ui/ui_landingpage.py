# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'landingpage.ui'
##
## Created by: Qt User Interface Compiler version 6.8.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QLabel, QListView,
    QListWidget, QListWidgetItem, QPushButton, QSizePolicy,
    QSpacerItem, QWidget)

class Ui_LandingPage(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(750, 701)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.listWidget = QListWidget(Form)
        self.listWidget.setObjectName(u"listWidget")
        self.listWidget.setMinimumSize(QSize(150, 200))
        self.listWidget.setMaximumSize(QSize(350, 16777215))
        self.listWidget.setResizeMode(QListView.Adjust)

        self.gridLayout.addWidget(self.listWidget, 1, 0, 1, 1)

        self.label = QLabel(Form)
        self.label.setObjectName(u"label")
        self.label.setMaximumSize(QSize(200, 25))
        self.label.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.settings_button = QPushButton(Form)
        self.settings_button.setObjectName(u"settings_button")

        self.gridLayout_3.addWidget(self.settings_button, 3, 1, 1, 1)

        self.newdatabase_button = QPushButton(Form)
        self.newdatabase_button.setObjectName(u"newdatabase_button")

        self.gridLayout_3.addWidget(self.newdatabase_button, 1, 1, 1, 1)

        self.opendatabase_button = QPushButton(Form)
        self.opendatabase_button.setObjectName(u"opendatabase_button")

        self.gridLayout_3.addWidget(self.opendatabase_button, 2, 1, 1, 1)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer_4, 4, 1, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(100, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer_3, 0, 1, 1, 1)


        self.gridLayout.addLayout(self.gridLayout_3, 1, 2, 3, 2)

        self.github_button = QPushButton(Form)
        self.github_button.setObjectName(u"github_button")
        self.github_button.setMinimumSize(QSize(25, 25))
        self.github_button.setMaximumSize(QSize(25, 25))
        self.github_button.setStyleSheet(u"border: none")

        self.gridLayout.addWidget(self.github_button, 4, 5, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(25, 25, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 1, 1, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label.setText(QCoreApplication.translate("Form", u"GeoChronology Database", None))
        self.settings_button.setText(QCoreApplication.translate("Form", u"Settings", None))
        self.newdatabase_button.setText(QCoreApplication.translate("Form", u"New", None))
        self.opendatabase_button.setText(QCoreApplication.translate("Form", u"Open", None))
        self.github_button.setText("")
    # retranslateUi


import sys
from pathlib import Path

import PyQt6.QtCore
import pandas
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import QSize, QRect, Qt, QCoreApplication, QMetaObject
from PyQt6.QtWidgets import QDialogButtonBox, QWidget, QVBoxLayout, QTableView, QComboBox, QLabel, QApplication, \
    QDialog, QTabWidget, QTableWidgetItem, QTableWidget, QFileDialog, QGroupBox
import pandas as pd
from ui.preferences import FlowLayout
from pandas.core.interchange import dataframe


# noinspection PyArgumentList
class ImportWizardDialog(QDialog):
    DEFAULT_LABEL_ALIGNMENT: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter

    def __init__(self, filename):
        super().__init__()
        if not self.objectName():
            self.setObjectName(u"ImportWizardDialog")
        self.df: dataframe = None
        self.resize(1024, 850)
        # self.setMinimumSize(QSize(1024, 850))
        # self.setMaximumSize(QSize(1024, 850))
        split_filename = filename.split('/')
        self.setWindowTitle(split_filename[len(split_filename) - 1])

        self.top_layout = QVBoxLayout(self)
        self.top_layout.setObjectName(u"top_level")
        self.top_layout.setContentsMargins(0, 0, 0, 0)

        # table widget + selected label
        self.selected_table_widget_item_label = QLabel(self,
                                                       objectName='selected_table_widget_item_label',
                                                       alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.top_layout.addWidget(self.selected_table_widget_item_label)

        self.tableWidget = QTableWidget(self)
        self.tableWidget.setObjectName(u"tableWidget")
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget.itemSelectionChanged.connect(
            lambda: self.selected_table_widget_item_label.setText(self.tableWidget.selectedItems()[0].text()))
        self.populate_table_widget(file=filename)
        self.top_layout.addWidget(self.tableWidget)
        # ------------------------------#

        # tab widget
        self.tabWidget = QTabWidget(self)
        self.tabWidget.setObjectName(u"tabWidget")
        self.top_layout.addWidget(self.tabWidget)
        # ------------------------------#

        # button box setup
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.rejected.connect(self.rejected)
        self.top_layout.addWidget(self.buttonBox, Qt.AlignmentFlag.AlignCenter)
        # ------------------------------#

        # ---Main Info Tab---#
        self.tab_main_info = QWidget(self.tabWidget)
        self.tab_main_info.setObjectName(u"tab_main_info")
        self.tabWidget.addTab(self.tab_main_info, "Main Info")

        self.flowlayout_main_info = FlowLayout(margin=10)
        self.flowlayout_main_info.setObjectName(u"flowlayout_main_info")
        self.tab_main_info.setLayout(self.flowlayout_main_info)
        self.flowlayout_main_info.heightChanged.connect(self.tab_main_info.setMinimumHeight)
        # ---END Main Info Tab---#

        # sample id
        self.sample_id_combobox = QComboBox(self.tab_main_info, objectName='sample_id_combobox')
        # self.sample_id_label = QLabel(self.tab_main_info, objectName='sample_id_label',
        #                               alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.sample_id_combobox.setToolTip('Sample ID Selector')
        self.flowlayout_main_info.addWidget(self.sample_id_combobox)

        # location data
        self.location_data_combobox = QComboBox(self.tab_main_info, objectName='location_data_combobox')
        # self.location_data_label = QLabel(self.tab_main_info, objectName='location_data_label',
        #                                   alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.location_data_combobox.setToolTip('Location Data Selector')
        self.flowlayout_main_info.addWidget(self.location_data_combobox)

        # location data units
        self.location_data_units_combobox = QComboBox(self.tab_main_info,
                                                      objectName='location_data_units_combobox')
        # self.location_data_units_label = QLabel(self.tab_main_info,
        #                                         objectName='location_data_units_label',
        #                                         alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.location_data_units_combobox.setToolTip('Location Units Selector')
        self.flowlayout_main_info.addWidget(self.location_data_units_combobox)

        # elevation data
        self.elevation_data_combobox = QComboBox(self.tab_main_info,
                                                 objectName='elevation_data_combobox')
        # self.elevation_data_label = QLabel(self.tab_main_info, objectName='elevation_data_label',
        #                                    alignment=self.DEFAULT_LABEL_ALIGNMENT)

        self.elevation_data_combobox.setToolTip('Elevation Data Selector')
        self.flowlayout_main_info.addWidget(self.elevation_data_combobox)

        # elevation data error
        self.elevation_data_error_combobox = QComboBox(self.tab_main_info,
                                                       objectName='elevation_data_error_combobox')
        # self.elevation_data_error_label = QLabel(self.tab_main_info,
        #                                          objectName='elevation_data_error_label',
        #                                          alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.elevation_data_error_combobox.setToolTip('Elevation Data Error Selector')
        self.flowlayout_main_info.addWidget(self.elevation_data_error_combobox)

        # # elevation data units
        # self.elevation_data_units_combobox = QComboBox(self.tab_main_info,
        #                                                objectName='elevation_data_units_combobox')
        # # self.elevation_data_units_label = QLabel(self.tab_main_info,
        # #                                          objectName='elevation_data_units_label',
        # #                                          alignment=self.DEFAULT_LABEL_ALIGNMENT)
        #
        # # height depth data
        # self.height_depth_data_combobox = QComboBox(self.tab_main_info,
        #                                             objectName='height_depth_combobox')
        # # self.height_depth_data_label = QLabel(self.tab_main_info, objectName='height_depth_label',
        # #                                       alignment=self.DEFAULT_LABEL_ALIGNMENT)
        #
        # # height depth error
        # self.height_depth_error_combobox = QComboBox(self.tab_main_info,
        #                                              objectName='height_depth_error_combobox')
        # # self.height_depth_error_label = QLabel(self.tab_main_info,
        # #                                        objectName='height_depth_error_label',
        # #                                        alignment=self.DEFAULT_LABEL_ALIGNMENT)
        #
        # # height depth units
        # self.height_depth_units_combobox = QComboBox(self.tab_main_info,
        #                                              objectName='height_depth_units_combobox')
        # # self.height_depth_units_label = QLabel(self.tab_main_info,
        # #                                        objectName='height_depth_units_label',
        # #                                        alignment=self.DEFAULT_LABEL_ALIGNMENT)

        self.combo_boxes_object_names = "best_age_sigma_combobox", "concord_discord_combobox", "accepted_rejected_combobox", \
            'Pb207_Pb206_age_combobox', "Pb207_Pb206_age_sigma_combobox", "Pb207_U238_age_combobox", \
            "Pb207_U238_age_sigma_combobox", "Pb206_U238_age_combobox", "Pb206_U238_age_sigma_combobox", \
            "Pb208_Th232_age_combobox", "Pb208_Th232_age_sigma_combobox", "Pb207_Pb206_ratio_combobox", \
            "Pb207_Pb206_ratio_sigma_combobox", "Pb207_U238_ratio_combobox", "Pb207_U238_ratio_sigma_combobox", \
            "Pb206_U238_ratio_combobox", "Pb206_U238_ratio_sigma_combobox", "Pb208_Th232_ratio_combobox", \
            "Pb208_Th232_ratio_sigma_combobox", "sample_id_combobox", "location_data_combobox", \
            "location_data_units_combobox", "elevation_data_combobox", "elevation_data_error_combobox", \
            "elevation_data_units_combobox", "height_depth_combobox", "height_depth_error_combobox", \
            "height_depth_units_combobox",

        self.add_labels()
        self.add_combo_boxes()
        self.re_translate_ui()

        # self.master_dict = {
        #     self.sample_id_combobox.objectName(): "Sample Name",
        #     self.best_age_combobox.objectName(): "Average Age",
        #     self.best_age_sigma_combobox.objectName(): "Average Age Error",
        #     self.height_depth_data_combobox.objectName(): "Height Depth",
        #     self.height_depth_error_combobox.objectName(): "Height Depth Error",
        #     self.height_depth_units_combobox.objectName(): "Height Depth Unit",
        #     self._Uppm_combobox.objectName(): "U ppm"
        # }

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        super().resizeEvent(a0)
        # self.resize(a0.size().shrunkBy(PyQt6.QtCore.QMargins(10, 10, 10, 10)))
        # print(self.tabWidget.rect().__str__())
        self.flowlayout_main_info.setGeometry(self.rect())
        # self.grid_layout_ages.setGeometry(self.tabWidget.rect())
        # self.grid_layout_ratios_age.setGeometry(self.tabWidget.rect())
        # self.grid_layout_ratios.setGeometry(self.tabWidget.rect())

    @PyQt6.QtCore.pyqtSlot()
    def accepted(self) -> None:
        map = dict()
        for combo_box in self.findChildren(QComboBox).__iter__():
            combo_box: QComboBox
            if combo_box.currentText() == "N/A":
                continue
            # map[self.master_dict.get(combo_box.objectName())] = combo_box.currentIndex() - 1
        # for key in map:

        super().accept()

    @PyQt6.QtCore.pyqtSlot()
    def rejected(self) -> None:
        self.hide()

    def add_combo_boxes(self):
        col_num = 7
        for tab in self.tabWidget.findChildren(QWidget).__iter__():
            if tab.objectName().__contains__("tab_"):
                for grid_layout_widget in tab.findChildren(QWidget).__iter__():
                    if (grid_layout_widget.__class__ is not QComboBox) and (grid_layout_widget.__class__ is not QLabel):
                        row, col = 1, 0
                        combo_box: QComboBox
                        for combo_box in grid_layout_widget.findChildren(QComboBox).__iter__():
                            combo_box.addItem("N/A")
                            for num in range(1, self.tableWidget.columnCount()):
                                combo_box.addItem(str(num))
                                # combo_box.setFixedWidth(125)
                                # combo_box.setFixedHeight(25)
                            if col >= col_num:
                                row += 2
                                col = 0

                            grid_layout = grid_layout_widget.findChild(FlowLayout)
                            grid_layout.addWidget(combo_box)
                            col += 1

    def add_labels(self):
        col_num = 7
        for tab in self.tabWidget.findChildren(QWidget).__iter__():
            if tab.objectName().__contains__("tab_"):
                for grid_layout_widget in tab.findChildren(QWidget).__iter__():
                    if (grid_layout_widget.__class__ is not QComboBox) and (grid_layout_widget.__class__ is not QLabel):
                        row, col = 0, 0
                        label: QLabel
                        for label in grid_layout_widget.findChildren(QLabel).__iter__():
                            label.setText(label.objectName())
                            # label.setFixedWidth(125)
                            # label.setFixedHeight(25)
                            if col >= col_num:
                                row += 2
                                col = 0

                            grid_layout = grid_layout_widget.findChild(FlowLayout)
                            grid_layout.addWidget(label)
                            col += 1

    def populate_table_widget(self, file):
        self.df = pd.read_excel(file)
        if self.df.size == 0:
            return

        self.df.fillna('', inplace=True)
        self.tableWidget.setRowCount(self.df.shape[0])
        self.tableWidget.setColumnCount(self.df.shape[1])

        # returns pandas array object
        for row in self.df.iterrows():
            values = row[1]
            for col_index, value in enumerate(values):
                if isinstance(value, (float, int)):
                    value = '{0:5,.5f}'.format(value)
                # print(value.font.strike==True)
                tableItem = QTableWidgetItem(value)

                self.tableWidget.setItem(row[0], col_index, tableItem)

        self.tableWidget.resizeColumnsToContents()
        for column in range(0, self.tableWidget.columnCount()):
            if self.tableWidget.columnWidth(column) >= 75:
                self.tableWidget.setColumnWidth(column, 75)
        self.tableWidget.resizeRowsToContents()
        self.tableWidget.selectRow(6)

    def re_translate_ui(self):
        self.setWindowTitle(QCoreApplication.translate("Dialog", u"Import Wizard", None))

        label: QLabel
        for label in self.findChildren(QLabel).__iter__():
            text = label.objectName().replace('_', ' ').replace('label', '')
            label.setText(QCoreApplication.translate("Dialog", text, None))

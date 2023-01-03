import sys
from pathlib import Path

import PyQt6.QtCore
from PyQt6 import QtWidgets
from PyQt6.QtCore import QSize, QRect, Qt, QCoreApplication, QMetaObject
from PyQt6.QtWidgets import QDialogButtonBox, QWidget, QGridLayout, QTableView, QComboBox, QLabel, QApplication, \
    QDialog, QTabWidget, QTableWidgetItem, QTableWidget, QFileDialog
import pandas as pd


# noinspection PyArgumentList
class ImportWizardDialog(QDialog):
    DEFAULT_LABEL_ALIGNMENT: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter

    def __init__(self, filename):
        super().__init__()
        if not self.objectName():
            self.setObjectName(u"ImportWizardDialog")

        self.resize(1024, 720)
        self.setMinimumSize(QSize(1024, 720))
        self.setMaximumSize(QSize(1024, 720))
        split_filename = filename.split('/')
        self.setWindowTitle(split_filename[len(split_filename)-1])

        # button box setup
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(410, 660, 161, 32))
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.rejected)

        # table widget + selected label
        self.tableWidget = QTableWidget(self)
        self.tableWidget.setObjectName(u"tableWidget")
        self.tableWidget.setGeometry(QRect(12, 50, 1000, 440))
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.selected_table_widget_item_label = QLabel(self, objectName='selected_table_widget_item_label',
                                                       alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.selected_table_widget_item_label.setGeometry(QRect(12, 10, 1000, 35))
        self.tableWidget.itemSelectionChanged.connect(
            lambda: self.selected_table_widget_item_label.setText(self.tableWidget.selectedItems()[0].text()))
        self.populate_table_widget(file=filename)

        self.tabWidget = QTabWidget(self)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(12, 500, 1000, 200))

        self.tab_names_array = []

        # ---Main Info Tab---#
        self.tab_main_info = QWidget(self.tabWidget)
        self.tab_main_info.setObjectName(u"tab_main_info")
        self.tabWidget.addTab(self.tab_main_info, "Main Info")
        self.tab_names_array.append(self.tab_main_info.objectName())

        self.grid_layout_widget_main_info = QWidget(self.tab_main_info)
        self.grid_layout_widget_main_info.setObjectName(u"grid_layout_widget_main_info")
        self.grid_layout_widget_main_info.setGeometry(QRect(10, 10, 975, 150))

        self.grid_layout_main_info = QGridLayout(self.grid_layout_widget_main_info)
        self.grid_layout_main_info.setObjectName(u"grid_layout_main_info")
        self.grid_layout_main_info.setContentsMargins(0, 0, 0, 0)
        # ---END Main Info Tab---#

        # ---Ages Tab---#
        self.tab_main_info = QWidget(self.tabWidget)
        self.tab_main_info.setObjectName(u"tab_ages")
        self.tabWidget.addTab(self.tab_main_info, "Ages")
        self.tab_names_array.append(self.tab_main_info.objectName())

        self.grid_layout_widget_ages = QWidget(self.tab_main_info)
        self.grid_layout_widget_ages.setObjectName(u"grid_layout_widget_ages")
        self.grid_layout_widget_ages.setGeometry(QRect(10, 10, 975, 150))

        self.grid_layout_ages = QGridLayout(self.grid_layout_widget_ages)
        self.grid_layout_ages.setObjectName(u"grid_layout_ages")
        self.grid_layout_ages.setContentsMargins(0, 0, 0, 0)
        # ---END Ages Tab---#

        # ---Isotope Ratios Tab---#
        self.tab_ratios = QWidget(self.tabWidget)
        self.tab_ratios.setObjectName(u"tab_ratios")
        self.tabWidget.addTab(self.tab_ratios, "Isotope Ratios")
        self.tab_names_array.append(self.tab_ratios.objectName())

        self.grid_layout_widget_ratios = QWidget(self.tab_ratios)
        self.grid_layout_widget_ratios.setObjectName(u"grid_layout_widget_ages_ratios")
        self.grid_layout_widget_ratios.setGeometry(QRect(10, 10, 975, 150))

        self.grid_layout_ratios = QGridLayout(self.grid_layout_widget_ratios)
        self.grid_layout_ratios.setObjectName(u"grid_layout_ratios")
        self.grid_layout_ratios.setContentsMargins(0, 0, 0, 0)
        # ---END Isotope Ratios Tab---#

        # ---Isotope Ages Tab---#
        self.tab_ratios_age = QWidget(self.tabWidget)
        self.tab_ratios_age.setObjectName(u"tab_ratios_age")
        self.tabWidget.addTab(self.tab_ratios_age, "Isotope Ages")
        self.tab_names_array.append(self.tab_ratios_age.objectName())

        self.grid_layout_widget_ratios_age = QWidget(self.tab_ratios_age)
        self.grid_layout_widget_ratios_age.setObjectName(u"grid_layout_widget_ages_ratios_age")
        self.grid_layout_widget_ratios_age.setGeometry(QRect(10, 10, 975, 150))

        self.grid_layout_ratios_age = QGridLayout(self.grid_layout_widget_ratios_age)
        self.grid_layout_ratios_age.setObjectName(u"grid_layout_ratios_age")
        self.grid_layout_ratios_age.setContentsMargins(0, 0, 0, 0)
        # ---END Isotope Ages Tab---#

        # sample id
        self.sample_id_combobox = QComboBox(self.grid_layout_widget_main_info, objectName='sample_id_combobox')
        self.sample_id_label = QLabel(self.grid_layout_widget_main_info, objectName='sample_id_label',
                                      alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # location data
        self.location_data_combobox = QComboBox(self.grid_layout_widget_main_info, objectName='location_data_combobox')
        self.location_data_label = QLabel(self.grid_layout_widget_main_info, objectName='location_data_label',
                                          alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # location data units
        self.location_data_units_combobox = QComboBox(self.grid_layout_widget_main_info,
                                                      objectName='location_data_units_combobox')
        self.location_data_units_label = QLabel(self.grid_layout_widget_main_info,
                                                objectName='location_data_units_label',
                                                alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # elevation data
        self.elevation_data_combobox = QComboBox(self.grid_layout_widget_main_info,
                                                 objectName='elevation_data_combobox')
        self.elevation_data_label = QLabel(self.grid_layout_widget_main_info, objectName='elevation_data_label',
                                           alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # elevation data error
        self.elevation_data_error_combobox = QComboBox(self.grid_layout_widget_main_info,
                                                       objectName='elevation_data_error_combobox')
        self.elevation_data_error_label = QLabel(self.grid_layout_widget_main_info,
                                                 objectName='elevation_data_error_label',
                                                 alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # elevation data units
        self.elevation_data_units_combobox = QComboBox(self.grid_layout_widget_main_info,
                                                       objectName='elevation_data_units_combobox')
        self.elevation_data_units_label = QLabel(self.grid_layout_widget_main_info,
                                                 objectName='elevation_data_units_label',
                                                 alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # height depth data
        self.height_depth_data_combobox = QComboBox(self.grid_layout_widget_main_info,
                                                    objectName='height_depth_combobox')
        self.height_depth_data_label = QLabel(self.grid_layout_widget_main_info, objectName='height_depth_label',
                                              alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # height depth error
        self.height_depth_error_combobox = QComboBox(self.grid_layout_widget_main_info,
                                                     objectName='height_depth_error_combobox')
        self.height_depth_error_label = QLabel(self.grid_layout_widget_main_info,
                                               objectName='height_depth_error_label',
                                               alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # height depth units
        self.height_depth_units_combobox = QComboBox(self.grid_layout_widget_main_info,
                                                     objectName='height_depth_units_combobox')
        self.height_depth_units_label = QLabel(self.grid_layout_widget_main_info,
                                               objectName='height_depth_units_label',
                                               alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # element ratio Pb207/Pb206
        self._Pb207_Pb206_ratio_combobox = QComboBox(self.grid_layout_widget_ratios,
                                                     objectName='Pb207_Pb206_ratio_combobox')
        self._Pb207_Pb206_ratio_label = QLabel(self.grid_layout_widget_ratios, objectName='Pb207_Pb206_ratio_label',
                                               alignment=self.DEFAULT_LABEL_ALIGNMENT)

        self._Pb207_Pb206_ratio_sigma_combobox = QComboBox(self.grid_layout_widget_ratios,
                                                           objectName='Pb207_Pb206_ratio_sigma_combobox')
        self._Pb207_Pb206_ratio_sigma_label = QLabel(self.grid_layout_widget_ratios,
                                                     objectName='Pb207_Pb206_ratio_sigma_label',
                                                     alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # element ratio Pb207/U238
        self.Pb207_U238_ratio_combobox = QComboBox(self.grid_layout_widget_ratios,
                                                   objectName='Pb207_U238_ratio_combobox')
        self.Pb207_U238_ratio_label = QLabel(self.grid_layout_widget_ratios, objectName='Pb207_U238_ratio_label',
                                             alignment=self.DEFAULT_LABEL_ALIGNMENT)

        self.Pb207_U238_ratio_sigma_combobox = QComboBox(self.grid_layout_widget_ratios,
                                                         objectName='Pb207_U238_ratio_sigma_combobox')
        self.Pb207_U238_ratio_sigma_label = QLabel(self.grid_layout_widget_ratios,
                                                   objectName='Pb207_U238_ratio_sigma_label',
                                                   alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # element ratio Pb206/U238
        self.Pb206_U238_ratio_combobox = QComboBox(self.grid_layout_widget_ratios,
                                                   objectName='Pb206_U238_ratio_combobox')
        self.Pb206_U238_ratio_label = QLabel(self.grid_layout_widget_ratios, objectName='Pb206_U238_ratio_label',
                                             alignment=self.DEFAULT_LABEL_ALIGNMENT)

        self.Pb206_U238_ratio_sigma_combobox = QComboBox(self.grid_layout_widget_ratios,
                                                         objectName='Pb206_U238_ratio_sigma_combobox')
        self.Pb206_U238_ratio_sigma_label = QLabel(self.grid_layout_widget_ratios,
                                                   objectName='Pb206_U238_ratio_sigma_label',
                                                   alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # element ratio Pb208/Th232
        self.Pb208_Th232_ratio_combobox = QComboBox(self.grid_layout_widget_ratios,
                                                    objectName='Pb208_Th232_ratio_combobox')
        self.Pb208_Th232_ratio_label = QLabel(self.grid_layout_widget_ratios, objectName='Pb208_Th232_ratio_label',
                                              alignment=self.DEFAULT_LABEL_ALIGNMENT)

        self.Pb208_Th232_ratio_sigma_combobox = QComboBox(self.grid_layout_widget_ratios,
                                                          objectName='Pb208_Th232_ratio_sigma_combobox')
        self.Pb208_Th232_ratio_sigma_label = QLabel(self.grid_layout_widget_ratios,
                                                    objectName='Pb208_Th232_ratio_sigma_label',
                                                    alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # ------------------------------------------------------------------------------------------------------------ #

        # best ages
        self.best_age_combobox = QComboBox(self.grid_layout_widget_ratios_age, objectName='best_age_combobox')
        self.best_age_label = QLabel(self.grid_layout_widget_ratios_age, objectName='best_age_label',
                                     alignment=self.DEFAULT_LABEL_ALIGNMENT)

        self.best_age_sigma_combobox = QComboBox(self.grid_layout_widget_ratios_age,
                                                 objectName='best_age_sigma_combobox')
        self.best_age_sigma_label = QLabel(self.grid_layout_widget_ratios_age, objectName='best_age_sigma_label',
                                           alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # concordiance/discord
        self.concord_discord_combobox = QComboBox(self.grid_layout_widget_ratios_age,
                                                  objectName='concord_discord_combobox')
        self.concord_discord_label = QLabel(self.grid_layout_widget_ratios_age, objectName='concord_discord_label',
                                            alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # accepted rejected
        self.accepted_rejected_combobox = QComboBox(self.grid_layout_widget_ratios_age,
                                                    objectName='accepted_rejected_combobox')
        self.accepted_rejected_label = QLabel(self.grid_layout_widget_ratios_age, objectName='accepted_rejected_label',
                                              alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # element age Pb207/Pb206
        self.Pb207_Pb206_age_combobox = QComboBox(self.grid_layout_widget_ratios_age,
                                                  objectName='Pb207_Pb206_age_combobox')
        self.Pb207_Pb206_age_label = QLabel(self.grid_layout_widget_ratios_age, objectName='Pb207_Pb206_age_label',
                                            alignment=self.DEFAULT_LABEL_ALIGNMENT)

        self.Pb207_Pb206_age_sigma_combobox = QComboBox(self.grid_layout_widget_ratios_age,
                                                        objectName='Pb207_Pb206_age_sigma_combobox')
        self.Pb207_Pb206_age_sigma_label = QLabel(self.grid_layout_widget_ratios_age,
                                                  objectName='Pb207_Pb206_age_sigma_label',
                                                  alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # element age Pb207/U238
        self.Pb207_U238_age_combobox = QComboBox(self.grid_layout_widget_ratios_age,
                                                 objectName='Pb207_U238_age_combobox')
        self.Pb207_U238_age_label = QLabel(self.grid_layout_widget_ratios_age, objectName='Pb207_U238_age_label',
                                           alignment=self.DEFAULT_LABEL_ALIGNMENT)

        self.Pb207_U238_age_sigma_combobox = QComboBox(self.grid_layout_widget_ratios_age,
                                                       objectName='Pb207_U238_age_sigma_combobox')
        self.Pb207_U238_age_sigma_label = QLabel(self.grid_layout_widget_ratios_age,
                                                 objectName='Pb207_U238_age_sigma_label',
                                                 alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # element age Pb206/U238
        self.Pb206_U238_age_combobox = QComboBox(self.grid_layout_widget_ratios_age,
                                                 objectName='Pb206_U238_age_combobox')
        self.Pb206_U238_age_label = QLabel(self.grid_layout_widget_ratios_age, objectName='Pb206_U238_age_label',
                                           alignment=self.DEFAULT_LABEL_ALIGNMENT)

        self.Pb206_U238_age_sigma_combobox = QComboBox(self.grid_layout_widget_ratios_age,
                                                       objectName='Pb206_U238_age_sigma_combobox')
        self.Pb206_U238_age_sigma_label = QLabel(self.grid_layout_widget_ratios_age,
                                                 objectName='Pb206_U238_age_sigma_label',
                                                 alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # element age Pb208/Th232
        self.Pb208_Th232_age_combobox = QComboBox(self.grid_layout_widget_ratios_age,
                                                  objectName='Pb208_Th232_age_combobox')
        self.Pb208_Th232_age_label = QLabel(self.grid_layout_widget_ratios_age, objectName='Pb208_Th232_age_label',
                                            alignment=self.DEFAULT_LABEL_ALIGNMENT)

        self.Pb208_Th232_age_sigma_combobox = QComboBox(self.grid_layout_widget_ratios_age,
                                                        objectName='Pb208_Th232_age_sigma_combobox')
        self.Pb208_Th232_age_sigma_label = QLabel(self.grid_layout_widget_ratios_age,
                                                  objectName='Pb208_Th232_age_sigma_label',
                                                  alignment=self.DEFAULT_LABEL_ALIGNMENT)

        # for combo_box in self.grid_layout_widget_ages.findChildren(QGridLayout).__iter__():
        #     print(combo_box.objectName() + " = " + combo_box.__repr__())

        self.add_labels()
        self.add_combo_boxes()

    @PyQt6.QtCore.pyqtSlot()
    def accepted(self) -> None:
        super().accepted()

    @PyQt6.QtCore.pyqtSlot()
    def rejected(self) -> None:
        self.hide()

    def add_combo_boxes(self):
        for tab in self.tabWidget.findChildren(QWidget).__iter__():
            if tab.objectName().__contains__("tab_"):
                for grid_layout_widget in tab.findChildren(QWidget).__iter__():
                    if (grid_layout_widget.__class__ is not QComboBox) and (grid_layout_widget.__class__ is not QLabel):
                        row, col = 1, 0
                        combo_box: QComboBox
                        for combo_box in grid_layout_widget.findChildren(QComboBox).__iter__():
                            combo_box.addItem(str(row) + str(col))
                            combo_box.addItem(str(combo_box.objectName()))
                            if col >= 10:
                                row = 3
                                col = 0

                            grid_layout = (grid_layout_widget.findChild(QGridLayout))
                            grid_layout.addWidget(combo_box, row % 4, col % 10)
                            col += 1

    def add_labels(self):
        for tab in self.tabWidget.findChildren(QWidget).__iter__():
            if tab.objectName().__contains__("tab_"):
                for grid_layout_widget in tab.findChildren(QWidget).__iter__():
                    if (grid_layout_widget.__class__ is not QComboBox) and (grid_layout_widget.__class__ is not QLabel):
                        row, col = 0, 0
                        label: QLabel
                        for label in grid_layout_widget.findChildren(QLabel).__iter__():
                            label.setText(label.objectName())
                            if col >= 10:
                                row = 2
                                col = 0

                            grid_layout = (grid_layout_widget.findChild(QGridLayout))
                            grid_layout.addWidget(label, row % 4, col % 10)
                            col += 1

    def populate_table_widget(self, file):
        df = pd.read_excel(file)
        if df.size == 0:
            return

        df.fillna('', inplace=True)
        self.tableWidget.setRowCount(df.shape[0])
        self.tableWidget.setColumnCount(df.shape[1])

        # returns pandas array object
        for row in df.iterrows():
            values = row[1]
            for col_index, value in enumerate(values):
                if isinstance(value, (float, int)):
                    value = '{0:5,.5f}'.format(value)
                tableItem = QTableWidgetItem(str(value))
                self.tableWidget.setItem(row[0], col_index, tableItem)

        self.tableWidget.resizeColumnsToContents()
        for column in range(0, self.tableWidget.columnCount()):
            if self.tableWidget.columnWidth(column) >= 75:
                self.tableWidget.setColumnWidth(column, 75)
        self.tableWidget.resizeRowsToContents()

    def re_translate_ui(self, dialog):
        dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))

        self._best_age_label.setText(QCoreApplication.translate("Dialog", u"Best Age", None))
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

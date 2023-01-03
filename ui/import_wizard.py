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
    DEFAULT_LABEL_ALIGNMENT: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter

    def __init__(self, filename):
        super().__init__()
        if not self.objectName():
            self.setObjectName(u"ImportWizardDialog")

        self.resize(1024, 850)
        self.setMinimumSize(QSize(1024, 850))
        self.setMaximumSize(QSize(1024, 850))
        split_filename = filename.split('/')
        self.setWindowTitle(split_filename[len(split_filename) - 1])

        # top level grid
        self.grid_layout_widget_top_level = QWidget(self)
        self.grid_layout_widget_top_level.setObjectName(u"grid_layout_widget_top_level")
        self.grid_layout_widget_top_level.setGeometry(QRect(10, 10, 1004, 830))

        self.grid_layout_top_level = QGridLayout(self.grid_layout_widget_top_level)
        self.grid_layout_top_level.setObjectName(u"grid_layout_top_level")
        self.grid_layout_top_level.setContentsMargins(0, 0, 0, 0)
        self.grid_layout_top_level.setRowMinimumHeight(2, 500)
        self.grid_layout_top_level.setColumnMinimumWidth(0, 800)

        # table widget + selected label
        self.selected_table_widget_item_label = QLabel(self.grid_layout_widget_top_level,
                                                       objectName='selected_table_widget_item_label',
                                                       alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.grid_layout_top_level.addWidget(self.selected_table_widget_item_label, 1, 0)

        self.tableWidget = QTableWidget(self.grid_layout_widget_top_level)
        self.tableWidget.setObjectName(u"tableWidget")
        self.grid_layout_top_level.addWidget(self.tableWidget, 2, 0)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget.itemSelectionChanged.connect(
            lambda: self.selected_table_widget_item_label.setText(self.tableWidget.selectedItems()[0].text()))
        self.populate_table_widget(file=filename)

        self.tabWidget = QTabWidget(self.grid_layout_widget_top_level)
        self.tabWidget.setObjectName(u"tabWidget")
        self.grid_layout_top_level.addWidget(self.tabWidget, 3, 0)

        # button box setup
        self.buttonBox = QDialogButtonBox(self.grid_layout_widget_top_level)
        self.buttonBox.setObjectName(u"buttonBox")
        self.grid_layout_top_level.addWidget(self.buttonBox, 4, 0, Qt.AlignmentFlag.AlignCenter)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.rejected)

        # ---Main Info Tab---#
        self.tab_main_info = QWidget(self.tabWidget)
        self.tab_main_info.setObjectName(u"tab_main_info")
        self.tabWidget.addTab(self.tab_main_info, "Main Info")

        self.grid_layout_widget_main_info = QWidget(self.tab_main_info)
        self.grid_layout_widget_main_info.setObjectName(u"grid_layout_widget_main_info")

        self.grid_layout_main_info = QGridLayout(self.grid_layout_widget_main_info)
        self.grid_layout_main_info.setObjectName(u"grid_layout_main_info")
        # ---END Main Info Tab---#

        # ---Ages Tab---#
        self.tab_main_ages = QWidget(self.tabWidget)
        self.tab_main_ages.setObjectName(u"tab_ages")
        self.tabWidget.addTab(self.tab_main_ages, "Ages")

        self.grid_layout_widget_ages = QWidget(self.tab_main_ages)
        self.grid_layout_widget_ages.setObjectName(u"grid_layout_widget_ages")

        self.grid_layout_ages = QGridLayout(self.grid_layout_widget_ages)
        self.grid_layout_ages.setObjectName(u"grid_layout_ages")
        # ---END Ages Tab---#

        # ---Isotope Ratios Tab---#
        self.tab_ratios = QWidget(self.tabWidget)
        self.tab_ratios.setObjectName(u"tab_ratios")
        self.tabWidget.addTab(self.tab_ratios, "Isotope Ratios")

        self.grid_layout_widget_ratios = QWidget(self.tab_ratios)
        self.grid_layout_widget_ratios.setObjectName(u"grid_layout_widget_ages_ratios")

        self.grid_layout_ratios = QGridLayout(self.grid_layout_widget_ratios)
        self.grid_layout_ratios.setObjectName(u"grid_layout_ratios")
        # ---END Isotope Ratios Tab---#

        # ---Isotope Ages Tab---#
        self.tab_ratios_age = QWidget(self.tabWidget)
        self.tab_ratios_age.setObjectName(u"tab_ratios_age")
        self.tabWidget.addTab(self.tab_ratios_age, "Isotope Ages")

        self.grid_layout_widget_ratios_age = QWidget(self.tab_ratios_age)
        self.grid_layout_widget_ratios_age.setObjectName(u"grid_layout_widget_ages_ratios_age")

        self.grid_layout_ratios_age = QGridLayout(self.grid_layout_widget_ratios_age)
        self.grid_layout_ratios_age.setObjectName(u"grid_layout_ratios_age")
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

        self.add_labels()
        self.add_combo_boxes()
        self.re_translate_ui()

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
                            for num in range(1, self.tableWidget.columnCount()):
                                combo_box.addItem(str(num))
                                combo_box.setFixedWidth(125)
                                combo_box.setFixedHeight(25)
                            if col >= 9:
                                row += 2
                                col = 0

                            grid_layout = grid_layout_widget.findChild(QGridLayout)
                            grid_layout.addWidget(combo_box, row, col % 9, Qt.AlignmentFlag.AlignCenter)
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
                            label.setFixedWidth(125)
                            label.setFixedHeight(25)
                            if col >= 9:
                                row += 2
                                col = 0

                            grid_layout = grid_layout_widget.findChild(QGridLayout)
                            grid_layout.addWidget(label, row, col % 9, Qt.AlignmentFlag.AlignCenter)
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

    def re_translate_ui(self):
        self.setWindowTitle(QCoreApplication.translate("Dialog", u"Import Wizard", None))

        label: QLabel
        for label in self.findChildren(QLabel).__iter__():
            text = label.objectName().replace('_', ' ').replace('label', '')
            label.setText(QCoreApplication.translate("Dialog", text, None))

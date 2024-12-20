import sqlite3
import sys
import time
from pathlib import Path

import PyQt6.QtCore
import pandas
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import QSize, QRect, Qt, QCoreApplication, QMetaObject
from PyQt6.QtWidgets import QDialogButtonBox, QWidget, QVBoxLayout, QTableView, QComboBox, QLabel, QApplication, \
    QDialog, QTabWidget, QTableWidgetItem, QTableWidget, QFileDialog, QGroupBox, QScrollArea, QCheckBox, QLineEdit
import pandas as pd

from ui.QComboBoxLabel import QComboBoxLabel
from ui.QLineEditLabel import QLineEditLabel
from ui.FlowLayout import FlowLayout
from pandas.core.interchange import dataframe
import Functions.Check_triggers as Ct


# noinspection PyArgumentList
class ImportWizardDialog(QDialog):
    DEFAULT_LABEL_ALIGNMENT: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter

    def __init__(self, filename, database):
        super().__init__()
        self.db_file = database

        self.df = pandas.DataFrame
        if not self.objectName():
            self.setObjectName(u'ImportWizardDialog')
        self.df: dataframe = None
        self.resize(1024, 850)
        # self.setMinimumSize(QSize(1024, 850))
        # self.setMaximumSize(QSize(1024, 850))
        split_filename = filename.split('/')
        self.setWindowTitle(split_filename[len(split_filename) - 1])

        self.top_layout = QVBoxLayout(self)
        self.top_layout.setObjectName(u'top_level')
        self.top_layout.setContentsMargins(10, 10, 10, 10)
        self.top_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # table widget + selected label
        self.selected_table_widget_item_label = QLabel(self,
                                                       objectName='selected_table_widget_item_label',
                                                       alignment=self.DEFAULT_LABEL_ALIGNMENT)
        self.top_layout.addWidget(self.selected_table_widget_item_label)

        self.tableWidget = QTableWidget(self)
        self.tableWidget.setObjectName(u'tableWidget')
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget.itemSelectionChanged.connect(
            lambda: self.selected_table_widget_item_label.setText(self.tableWidget.selectedItems()[0].text()))
        self.populate_table_widget(file=filename)
        self.top_layout.addWidget(self.tableWidget)
        self.tableWidget.setMinimumHeight(500)
        # ------------------------------#

        self.checkboxes_widget = QWidget(self)
        self.flowlayout_checkboxes = FlowLayout(margin=25)
        self.flowlayout_checkboxes.setObjectName(u'flowlayout_checkboxes')
        self.checkboxes_widget.setLayout(self.flowlayout_checkboxes)
        self.flowlayout_checkboxes.heightChanged.connect(self.checkboxes_widget.setMinimumHeight)

        self.checkbox_linebyline = QCheckBox('Multiple Samples in File?', parent=self.checkboxes_widget)
        self.flowlayout_checkboxes.addWidget(self.checkbox_linebyline)

        self.top_layout.addWidget(self.checkboxes_widget)
        self.checkboxes_widget.setFixedHeight(50)

        # tab widget
        self.tabWidget = QTabWidget(self)
        self.tabWidget.setObjectName(u'tabWidget')
        self.top_layout.addWidget(self.tabWidget)
        self.tabWidget.setMaximumHeight(300)
        # ------------------------------#

        # button box setup
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setObjectName(u'buttonBox')
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.rejected.connect(self.rejected)
        self.top_layout.addWidget(self.buttonBox, Qt.AlignmentFlag.AlignHCenter)
        self.top_layout.setAlignment(self.buttonBox, Qt.AlignmentFlag.AlignHCenter)
        # ------------------------------#

        # ---Main Info Tab---#
        self.tab_main_info = QWidget(self.tabWidget)
        self.tab_main_info.setObjectName(u'tab_main_info')

        self.flowlayout_main_info = FlowLayout(margin=10)
        self.flowlayout_main_info.setObjectName(u'flowlayout_main_info')
        self.tab_main_info.setLayout(self.flowlayout_main_info)
        self.flowlayout_main_info.heightChanged.connect(self.tab_main_info.setMinimumHeight)

        self.scroll_tab_main_info = QScrollArea()
        self.scroll_tab_main_info.setWidget(self.tab_main_info)
        self.scroll_tab_main_info.setWidgetResizable(True)
        self.tabWidget.addTab(self.scroll_tab_main_info, 'Main Info')
        # ---END Main Info Tab---#

        # --- MAIN INFO --- #
        # sample id
        self.sample_id_lineedit = QLineEditLabel(label_name='Sample Id', parent=self.tab_main_info,
                                                 objectName='sample_id_combobox')
        self.sample_id_lineedit.setToolTip('Sample ID Selector')
        self.flowlayout_main_info.addWidget(self.sample_id_lineedit)

        # aliqout id
        self.aliqout_id_lineedit = QLineEditLabel(label_name='Aliqout Id', parent=self.tab_main_info,
                                                  objectName='aliqout_id_combobox')
        self.aliqout_id_lineedit.setToolTip('Aliquot ID Selector')
        self.flowlayout_main_info.addWidget(self.aliqout_id_lineedit)

        # analysis id
        self.analysis_id_combobox = QComboBoxLabel(label_name='Analysis Id', parent=self.tab_main_info,
                                                   objectName='analysis_id_combobox')
        self.analysis_id_combobox.setToolTip('Analysis ID Selector')
        self.flowlayout_main_info.addWidget(self.analysis_id_combobox)

        # analysis id row start
        self.analysis_row_start_lineedit = QLineEditLabel(label_name='Analysis Row # Start', parent=self.tab_main_info,
                                                          objectName='analysis__row_start_combobox')
        self.analysis_row_start_lineedit.setToolTip('Analysis Row # Start')
        self.flowlayout_main_info.addWidget(self.analysis_row_start_lineedit)

        # location data
        self.location_data_combobox = QComboBoxLabel(label_name='Location Data', parent=self.tab_main_info,
                                                     objectName='location_data_combobox')
        self.location_data_combobox.setToolTip('Location Data Selector')
        self.flowlayout_main_info.addWidget(self.location_data_combobox)

        # location data units
        self.location_data_units_combobox = QComboBoxLabel(label_name='Location Data Units', parent=self.tab_main_info,
                                                           objectName='location_data_units_combobox')
        self.location_data_units_combobox.setToolTip('Location Units Selector')
        self.flowlayout_main_info.addWidget(self.location_data_units_combobox)

        # elevation data
        self.elevation_data_combobox = QComboBoxLabel(label_name='Elevation Data', parent=self.tab_main_info,
                                                      objectName='elevation_data_combobox')
        self.elevation_data_combobox.setToolTip('Elevation Data Selector')
        self.flowlayout_main_info.addWidget(self.elevation_data_combobox)

        # elevation data error
        self.elevation_data_error_combobox = QComboBoxLabel(label_name='Elevation Data Error',
                                                            parent=self.tab_main_info,
                                                            objectName='elevation_data_error_combobox')
        self.elevation_data_error_combobox.setToolTip('Elevation Data Error Selector')
        self.flowlayout_main_info.addWidget(self.elevation_data_error_combobox)

        # elevation data units
        self.elevation_data_units_combobox = QComboBoxLabel(label_name='Elevation Data Units',
                                                            parent=self.tab_main_info,
                                                            objectName='elevation_data_units_combobox')
        self.elevation_data_units_combobox.setToolTip('Elevation Data Units Selector')
        self.flowlayout_main_info.addWidget(self.elevation_data_units_combobox)

        # height depth data
        self.height_depth_data_combobox = QComboBoxLabel(label_name='Height Depth Data', parent=self.tab_main_info,
                                                         objectName='height_depth_combobox')
        self.height_depth_data_combobox.setToolTip('Height Depth Data Selector')
        self.flowlayout_main_info.addWidget(self.height_depth_data_combobox)

        # height depth error
        self.height_depth_error_combobox = QComboBoxLabel(label_name='Height Depth Error', parent=self.tab_main_info,
                                                          objectName='height_depth_error_combobox')
        self.height_depth_error_combobox.setToolTip('Height Depth Error Selector')
        self.flowlayout_main_info.addWidget(self.height_depth_error_combobox)

        # height depth units
        self.height_depth_units_combobox = QComboBoxLabel(label_name='Height Depth Units', parent=self.tab_main_info,
                                                          objectName='height_depth_units_combobox')
        self.height_depth_units_combobox.setToolTip('Height Depth Units Selector')
        self.flowlayout_main_info.addWidget(self.height_depth_units_combobox)

        # --- END MAIN INFO --- #

        # ---Ratio Info Tab---#
        self.tab_ratio = QWidget(self.tabWidget)
        self.tab_ratio.setObjectName(u'tab_ratio')

        self.flowlayout_ratio = FlowLayout(margin=10)
        self.flowlayout_ratio.setObjectName(u'flowlayout_ratio')
        self.tab_ratio.setLayout(self.flowlayout_ratio)
        self.flowlayout_ratio.heightChanged.connect(self.tab_ratio.setMinimumHeight)

        self.scroll_tab_ratios = QScrollArea()
        self.scroll_tab_ratios.setWidget(self.tab_ratio)
        self.scroll_tab_ratios.setWidgetResizable(True)
        self.tabWidget.addTab(self.scroll_tab_ratios, 'Ratios')
        # ---END Ratio Info Tab---#

        # --- Ratio --- #

        # element ratio Pb206/Pb204
        self.Pb206_Pb204_ratio_combobox = QComboBoxLabel(label_name='Pb206/Pb204 Ratio', parent=self.tab_ratio,
                                                         objectName='Pb206_Pb204_ratio_combobox',
                                                         include_checkbox=True)
        self.Pb206_Pb204_ratio_combobox.setToolTip('Pb206/Pb204 Ratio Selector')
        self.flowlayout_ratio.addWidget(self.Pb206_Pb204_ratio_combobox)

        # element ratio U/Th
        self.U_Th_ratio_combobox = QComboBoxLabel(label_name='U/Th Ratio', parent=self.tab_ratio,
                                                  objectName='U_Th_ratio_combobox', include_checkbox=True)
        self.U_Th_ratio_combobox.setToolTip('U/Th Ratio Selector')
        self.flowlayout_ratio.addWidget(self.U_Th_ratio_combobox)

        # element ratio Pb206/Pb207
        self.Pb206_Pb207_ratio_combobox = QComboBoxLabel(label_name='Pb206/Pb207 Ratio', parent=self.tab_ratio,
                                                         objectName='Pb206_Pb207_ratio_combobox')
        self.Pb206_Pb207_ratio_combobox.setToolTip('Pb206/Pb207 Ratio Selector')
        self.flowlayout_ratio.addWidget(self.Pb206_Pb207_ratio_combobox)

        self.Pb206_Pb207_ratio_sigma_combobox = QComboBoxLabel(label_name='Pb206/Pb207 Ratio Sigma',
                                                               parent=self.tab_ratio,
                                                               objectName='Pb206_Pb207_ratio_sigma_combobox')
        self.Pb206_Pb207_ratio_sigma_combobox.setToolTip('Pb206/Pb207 Ratio Sigma Selector')
        self.flowlayout_ratio.addWidget(self.Pb206_Pb207_ratio_sigma_combobox)

        # element ratio Pb207/U235
        self.Pb207_U235_ratio_combobox = QComboBoxLabel(label_name='Pb207/U235 Ratio', parent=self.tab_ratio,
                                                        objectName='Pb207_U235_ratio_combobox')
        self.Pb207_U235_ratio_combobox.setToolTip('Pb207/U235 Ratio Selector')
        self.flowlayout_ratio.addWidget(self.Pb207_U235_ratio_combobox)

        self.Pb207_U235_ratio_sigma_combobox = QComboBoxLabel(label_name='Pb207/U235 Ratio Sigma',
                                                              parent=self.tab_ratio,
                                                              objectName='Pb207_U235_ratio_sigma_combobox')
        self.Pb207_U235_ratio_sigma_combobox.setToolTip('Pb207/U235 Sigma Ratio Selector')
        self.flowlayout_ratio.addWidget(self.Pb207_U235_ratio_sigma_combobox)

        # element ratio Pb206/U238
        self.Pb206_U238_ratio_combobox = QComboBoxLabel(label_name='Pb206/U238 Ratio', parent=self.tab_ratio,
                                                        objectName='Pb206_U238_ratio_combobox')
        self.Pb206_U238_ratio_combobox.setToolTip('Pb206/U238 Ratio Selector')
        self.flowlayout_ratio.addWidget(self.Pb206_U238_ratio_combobox)

        self.Pb206_U238_ratio_sigma_combobox = QComboBoxLabel(label_name='Pb206/U238 Ratio Sigma',
                                                              parent=self.tab_ratio,
                                                              objectName='Pb206_U238_ratio_sigma_combobox')
        self.Pb206_U238_ratio_sigma_combobox.setToolTip('Pb206/U238 Sigma Ratio Selector')
        self.flowlayout_ratio.addWidget(self.Pb206_U238_ratio_sigma_combobox)

        # # element ratio Pb208/Th232
        # self.Pb208_Th232_ratio_combobox = QComboBoxLabel(label_name='Pb208/Th232 Ratio', parent=self.tab_ratio,
        #                                                  objectName='Pb208_Th232_ratio_combobox')
        # self.Pb208_Th232_ratio_combobox.setToolTip('Pb207/Th232 Sigma Ratio Selector')
        # self.flowlayout_ratio.addWidget(self.Pb208_Th232_ratio_combobox)
        #
        # self.Pb208_Th232_ratio_sigma_combobox = QComboBoxLabel(label_name='Pb208/Th232 Ratio Sigma',
        #                                                        parent=self.tab_ratio,
        #                                                        objectName='Pb208_Th232_ratio_sigma_combobox')
        # self.Pb208_Th232_ratio_sigma_combobox.setToolTip('Pb207/Th232 Sigma Ratio Selector')
        # self.flowlayout_ratio.addWidget(self.Pb208_Th232_ratio_sigma_combobox)

        # --- END Ratio --- #

        # ---Ages Info Tab---#
        self.tab_ages = QWidget(self.tabWidget)
        self.tab_ages.setObjectName(u'tab_ages')

        self.flowlayout_ages = FlowLayout(margin=5)
        self.flowlayout_ages.setObjectName(u'flowlayout_ages')
        self.tab_ages.setLayout(self.flowlayout_ages)
        self.flowlayout_ages.heightChanged.connect(self.tab_ages.setMinimumHeight)

        self.scroll_tab_ages = QScrollArea()
        self.scroll_tab_ages.setWidget(self.tab_ages)
        self.scroll_tab_ages.setWidgetResizable(True)
        self.tabWidget.addTab(self.scroll_tab_ages, 'Ages')
        # ---END Ages Info Tab---#

        # best ages
        self.best_age_combobox = QComboBoxLabel(label_name='Best Ages', parent=self.tab_ages,
                                                objectName='best_age_combobox')
        self.best_age_combobox.setToolTip('Best Age Selector')
        self.flowlayout_ages.addWidget(self.best_age_combobox)

        self.best_age_sigma_combobox = QComboBoxLabel(label_name='Best Age Sigma', parent=self.tab_ages,
                                                      objectName='best_age_sigma_combobox')
        self.best_age_sigma_combobox.setToolTip('Best Age Sigma Selector')
        self.flowlayout_ages.addWidget(self.best_age_sigma_combobox)

        # concordance/discord
        self.concord_discord_combobox = QComboBoxLabel(label_name='Concordance/Discordance', parent=self.tab_ages,
                                                       objectName='concord_discord_combobox')
        self.concord_discord_combobox.addItems({'Concordance', 'Discordance'})
        self.concord_discord_combobox.setToolTip('Concordance/Discordance Sigma Selector')
        self.flowlayout_ages.addWidget(self.concord_discord_combobox)

        # accepted rejected
        self.accepted_rejected_combobox = QComboBoxLabel(label_name='Accepted/Rejected', parent=self.tab_ages,
                                                         objectName='accepted_rejected_combobox')
        self.accepted_rejected_combobox.addItems({'Accepted', 'Rejected'})
        self.accepted_rejected_combobox.setToolTip('Accepted/Rejected Selector')
        self.flowlayout_ages.addWidget(self.accepted_rejected_combobox)

        # element age Pb206/Pb207
        self.Pb206_Pb207_age_combobox = QComboBoxLabel(label_name='Pb206/Pb207 Age', parent=self.tab_ages,
                                                       objectName='Pb206_Pb207_age_combobox')
        self.Pb206_Pb207_age_combobox.setToolTip('Pb207/Pb206 Age Selector')
        self.flowlayout_ages.addWidget(self.Pb206_Pb207_age_combobox)

        self.Pb206_Pb207_age_sigma_combobox = QComboBoxLabel(label_name='Pb206/Pb207 Age Sigma', parent=self.tab_ages,
                                                             objectName='Pb206_Pb207_age_sigma_combobox')
        self.Pb206_Pb207_age_sigma_combobox.setToolTip('Pb206/Pb207 Age Sigma Selector')
        self.flowlayout_ages.addWidget(self.Pb206_Pb207_age_sigma_combobox)

        # element age Pb207/U235
        self.Pb207_U235_age_combobox = QComboBoxLabel(label_name='Pb207/U235 Age', parent=self.tab_ages,
                                                      objectName='Pb207_U235_age_combobox')
        self.Pb207_U235_age_combobox.setToolTip('Pb207/U235 Age Selector')
        self.flowlayout_ages.addWidget(self.Pb207_U235_age_combobox)

        self.Pb207_U235_age_sigma_combobox = QComboBoxLabel(label_name='Pb207/U235 Age Sigma', parent=self.tab_ages,
                                                            objectName='Pb207_U235_age_sigma_combobox')
        self.Pb207_U235_age_sigma_combobox.setToolTip('Pb207/U235 Age Sigma Selector')
        self.flowlayout_ages.addWidget(self.Pb207_U235_age_sigma_combobox)

        # element age Pb206/U238
        self.Pb206_U238_age_combobox = QComboBoxLabel(label_name='Pb206/U238 Age', parent=self.tab_ages,
                                                      objectName='Pb206_U238_age_combobox')
        self.Pb206_U238_age_combobox.setToolTip('Pb206/U238 Age Selector')
        self.flowlayout_ages.addWidget(self.Pb206_U238_age_combobox)

        self.Pb206_U238_age_sigma_combobox = QComboBoxLabel(label_name='Pb206/U238 Age Sigma', parent=self.tab_ages,
                                                            objectName='Pb206_U238_age_sigma_combobox')
        self.Pb206_U238_age_sigma_combobox.setToolTip('Pb206/U238 Age Sigma Selector')
        self.flowlayout_ages.addWidget(self.Pb206_U238_age_sigma_combobox)

        # # element age Pb208/Th232
        # self.Pb208_Th232_age_combobox = QComboBoxLabel(label_name='Pb207/Th232 Age', parent=self.tab_ages,
        #                                                objectName='Pb208_Th232_age_combobox')
        # self.Pb208_Th232_age_combobox.setToolTip('Pb206/Th232 Age Selector')
        # self.flowlayout_ages.addWidget(self.Pb208_Th232_age_combobox)
        #
        # self.Pb208_Th232_age_sigma_combobox = QComboBoxLabel(label_name='Pb207/Th232 Age Sigma', parent=self.tab_ages,
        #                                                      objectName='Pb208_Th232_age_sigma_combobox')
        # self.Pb208_Th232_age_sigma_combobox.setToolTip('Pb206/Th232 Age Sigma Selector')
        # self.flowlayout_ages.addWidget(self.Pb208_Th232_age_sigma_combobox)

        self.combo_boxes_object_names = 'best_age_sigma_combobox', 'concord_discord_combobox', 'accepted_rejected_combobox', \
            'Pb207_Pb206_age_combobox', 'Pb207_Pb206_age_sigma_combobox', 'Pb207_U238_age_combobox', \
            'Pb207_U238_age_sigma_combobox', 'Pb206_U238_age_combobox', 'Pb206_U238_age_sigma_combobox', \
            'Pb208_Th232_age_combobox', 'Pb208_Th232_age_sigma_combobox', 'Pb207_Pb206_ratio_combobox', \
            'Pb207_Pb206_ratio_sigma_combobox', 'Pb207_U238_ratio_combobox', 'Pb207_U238_ratio_sigma_combobox', \
            'Pb206_U238_ratio_combobox', 'Pb206_U238_ratio_sigma_combobox', 'Pb208_Th232_ratio_combobox', \
            'Pb208_Th232_ratio_sigma_combobox', 'sample_id_combobox', 'location_data_combobox', \
            'location_data_units_combobox', 'elevation_data_combobox', 'elevation_data_error_combobox', \
            'elevation_data_units_combobox', 'height_depth_combobox', 'height_depth_error_combobox', \
            'height_depth_units_combobox',

        # self.add_labels()
        self.fill_combo_boxes()
        self.findRowsWhereData()
        self.assignTestValues()

    def assignTestValues(self):
        self.sample_id_lineedit.lineedit.setText(time.time().__str__())
        self.aliqout_id_lineedit.lineedit.setText((time.time() + 1).__str__())
        self.analysis_id_combobox.combobox.setCurrentText("1")

        self.U_Th_ratio_combobox.combobox.setCurrentText("3")
        self.Pb207_U235_ratio_combobox.combobox.setCurrentText("4")
        self.Pb207_U235_ratio_sigma_combobox.combobox.setCurrentText("5")
        self.Pb206_U238_ratio_combobox.combobox.setCurrentText("6")
        self.Pb206_U238_ratio_sigma_combobox.combobox.setCurrentText("7")
        self.Pb206_Pb207_ratio_combobox.combobox.setCurrentText("8")
        self.Pb206_Pb207_ratio_sigma_combobox.combobox.setCurrentText("9")

        self.Pb207_U235_age_combobox.combobox.setCurrentText("10")
        self.Pb207_U235_age_sigma_combobox.combobox.setCurrentText("11")
        self.Pb206_U238_age_combobox.combobox.setCurrentText("12")
        self.Pb206_U238_age_sigma_combobox.combobox.setCurrentText("13")
        self.Pb206_Pb207_age_combobox.combobox.setCurrentText("14")
        self.Pb206_Pb207_age_sigma_combobox.combobox.setCurrentText("15")

        self.best_age_combobox.combobox.setCurrentText("16")
        self.best_age_sigma_combobox.combobox.setCurrentText("17")

        self.concord_discord_combobox.combobox.setCurrentText("N/A")
        self.accepted_rejected_combobox.combobox.setCurrentText("N/A")

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        self.flowlayout_main_info.setGeometry(self.rect())

    def findRowsWhereData(self):
        # returns pandas array object
        count = 0
        done = False
        for row in self.df.iterrows():
            values = row[1]
            count += 1
            for col_index, value in enumerate(values):
                if isinstance(value, (float, int)):
                    value = '{0:5,.5f}'.format(value)
                    done = True
                    self.analysis_row_start_lineedit.lineedit.setText(str(count))
                    print(count)
                    break
            if done:
                break

    def int_or_none(self, str):
        if str == '' or str == 'N/A':
            return 'NULL'
        else:
            return int(str) - 1

    @PyQt6.QtCore.pyqtSlot()
    def accepted(self) -> None:
        for combo_box in self.findChildren(QComboBox).__iter__():
            combo_box: QComboBox
            if combo_box.currentText() == 'N/A':
                combo_box.setCurrentText('')

        conn = sqlite3.connect(self.db_file)

        with conn:
            c = conn.cursor()
            print(self.sample_id_lineedit.lineedit.text())
            if self.sample_id_lineedit.lineedit.text() != "":
                c.execute(
                    '''INSERT INTO Samples (SampleName) 
                    Values ('{}');'''.format(self.sample_id_lineedit.lineedit.text()).__str__())
            else:
                error = QDialog()
                error.show()
            if self.aliqout_id_lineedit.lineedit.text() != "":
                c.execute(
                    '''Insert into Aliquots (AliquotName, SampleID) 
                    VALUES ('{}', {});'''.format(self.aliqout_id_lineedit.lineedit.text(), c.lastrowid).__str__())
                c.execute(
                    '''Insert into Spots (SpotName, AliquotID) 
                    VALUES ('{}', {});'''.format("test", c.lastrowid).__str__())
            spot_last_id = c.lastrowid
            count = 1
            for row in self.df.iterrows():
                if count < int(self.analysis_row_start_lineedit.lineedit.text()):
                    count += 1
                    continue
                row = row[1].array

                datatuple = ('NULL',
                             'NULL',
                             'NULL',
                             'NULL',
                             'NULL',
                             # Pb206204Pb=row[self.int_or_none(self.Pb206_Pb204_ratio_combobox.combobox.currentText())],
                             row[self.int_or_none(self.U_Th_ratio_combobox.combobox.currentText())],

                             row[self.int_or_none(self.Pb206_Pb207_ratio_combobox.combobox.currentText())],
                             row[self.int_or_none(self.Pb206_Pb207_ratio_sigma_combobox.combobox.currentText())],

                             row[self.int_or_none(self.Pb207_U235_ratio_combobox.combobox.currentText())],
                             row[self.int_or_none(self.Pb207_U235_ratio_sigma_combobox.combobox.currentText())],

                             row[self.int_or_none(self.Pb206_U238_ratio_combobox.combobox.currentText())],
                             row[self.int_or_none(self.Pb206_U238_ratio_sigma_combobox.combobox.currentText())],
                             'NULL',
                             row[
                                 self.int_or_none(self.Pb206_Pb207_age_combobox.combobox.currentText())],
                             row[
                                 self.int_or_none(self.Pb206_Pb207_age_sigma_combobox.combobox.currentText())],

                             row[
                                 self.int_or_none(self.Pb207_U235_age_combobox.combobox.currentText())],
                             row[
                                 self.int_or_none(self.Pb207_U235_age_sigma_combobox.combobox.currentText())],

                             row[
                                 self.int_or_none(self.Pb206_U238_age_combobox.combobox.currentText())],
                             row[
                                 self.int_or_none(self.Pb206_U238_age_sigma_combobox.combobox.currentText())],

                             row[self.int_or_none(self.best_age_combobox.combobox.currentText())],
                             row[self.int_or_none(self.best_age_sigma_combobox.combobox.currentText())],
                             'NULL',
                             'NULL',
                             'NULL',
                             'NULL')

                c.execute('''
                INSERT INTO
                    UPBData
                    (SpotID,
                    SourceID,
                    LabFacilityID,
                    UPbAnalysisMethodID,
                    "206Pb/204Pb",
                    "U/Th",
                    "206Pb/207Pb",
                    "206Pb/207Pberror",
                    "207Pb/235U",
                    "207Pb/235Uerror",
                    "206Pb/238U",
                    "206Pb/238Uerror",
                    ErrorCorr,
                    "206Pb/207PbAge",
                    "206Pb/207PbAgeError",
                    "207Pb/235UAge",
                    "207Pb/235UAgeError",
                    "206Pb/238UAge",
                    "206Pb/238UAgeError",
                    BestAge,
                    Error,
                    Conc,
                    SpotSize,
                    SpotSizeUnit,
                    Accepted)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);''', datatuple)
        self.done(0)

    @PyQt6.QtCore.pyqtSlot()
    def rejected(self) -> None:
        self.done(0)

    def fill_combo_boxes(self):
        for tab in self.tabWidget.findChildren(QWidget).__iter__():
            if tab.objectName().__contains__('tab_'):
                combo_box: QComboBoxLabel
                for combo_box in tab.findChildren(QComboBoxLabel).__iter__():
                    combo_box.combobox.addItem('N/A')
                    for num in range(1, self.tableWidget.columnCount() + 1):
                        combo_box.combobox.addItem(str(num))

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
        self.setWindowTitle(QCoreApplication.translate('Dialog', u'Import Wizard', None))

        label: QLabel
        for label in self.findChildren(QLabel).__iter__():
            text = label.objectName().replace('_', ' ').replace('label', '')
            label.setText(QCoreApplication.translate('Dialog', text, None))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = ImportWizardDialog(sys.argv[1])
    dialog.exec()

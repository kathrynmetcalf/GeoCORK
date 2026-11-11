"""'Table Displays' tab of the Settings dialog."""
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import QRect
from PyQt6.QtGui import QFont, QFontDatabase

from ui.SelectColumns import SelectColumns
from ui.settings.SettingsCore import (settings, update_setting, update_stylesheet)
from ui.settings.UnitsFormatsTab import fixed_height
from Functions.LoadingDialog_manager import LoadingDialogManager

class TableDisplaysTab(QtW.QWidget):
    """
    Column selection per view, displayed analyses, fonts and checkable combobox scalars.
    """
    title = 'Table Displays'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('display_tab')
        self.setSizePolicy(QtW.QSizePolicy.Policy.MinimumExpanding, QtW.QSizePolicy.Policy.MinimumExpanding)
        self.build_ui()

    def build_ui(self):
        layout = QtW.QHBoxLayout(self)
        layout.setObjectName('horizontalLayout_3')

        self.column_verticalLayout = QtW.QVBoxLayout()
        self.column_verticalLayout.setObjectName('column_verticalLayout')
        self.select_columns = SelectColumns()
        self.column_verticalLayout.addWidget(self.select_columns)
        layout.addLayout(self.column_verticalLayout)

        right = QtW.QVBoxLayout()
        right.setObjectName('verticalLayout_9')

        # Display analyses (children are absolutely positioned, as in Settings.ui)
        self.analysis_display_groupBox = QtW.QGroupBox('Display Analyses', self)
        self.analysis_display_groupBox.setObjectName('analysis_display_groupBox')
        self.analysis_display_groupBox.setSizePolicy(QtW.QSizePolicy.Policy.Preferred,
                                                     QtW.QSizePolicy.Policy.Preferred)
        self.analysis_display_groupBox.setMinimumSize(0, 90)

        analysis_layout = QtW.QVBoxLayout(self.analysis_display_groupBox)

        self.upb_checkBox = QtW.QCheckBox('U-Pb Analyses', self.analysis_display_groupBox)
        self.upb_checkBox.setObjectName('upb_checkBox')

        self.geochem_checkBox = QtW.QCheckBox('Geochemical Analyses', self.analysis_display_groupBox)
        self.geochem_checkBox.setObjectName('geochem_checkBox')

        analysis_layout.addWidget(self.upb_checkBox)
        analysis_layout.addWidget(self.geochem_checkBox)

        right.addWidget(self.analysis_display_groupBox)

        grid = QtW.QGridLayout()
        grid.setObjectName('gridLayout_6')

        def label(name: str, text: str, wrap: bool = False) -> QtW.QLabel:
            widget = QtW.QLabel(text, self)
            widget.setObjectName(name)
            widget.setMaximumSize(100, 16777215)
            widget.setWordWrap(wrap)
            setattr(self, name, widget)
            return widget

        self.fontComboBox = fixed_height(QtW.QFontComboBox(self))
        self.fontComboBox.setObjectName('fontComboBox')
        self.font_size_comboBox = fixed_height(QtW.QComboBox(self))
        self.font_size_comboBox.setObjectName('font_size_comboBox')
        self.table_font_size_comboBox = fixed_height(QtW.QComboBox(self))
        self.table_font_size_comboBox.setObjectName('table_font_size_comboBox')
        self.combobox_height_scalar_spinbox = self._scalar_spinbox('combobox_height_scalar_spinbox')
        self.combobox_width_scalar_spinbox = self._scalar_spinbox('combobox_width_scalar_spinbox')

        grid.addWidget(label('font_label', 'Font:'), 0, 0)
        grid.addWidget(self.fontComboBox, 0, 1)
        grid.addWidget(label('font_size_label', 'Font size:'), 1, 0)
        grid.addWidget(self.font_size_comboBox, 1, 1)
        grid.addWidget(label('table_font_size_label', 'Table font size:'), 2, 0)
        grid.addWidget(self.table_font_size_comboBox, 2, 1)
        grid.addWidget(label('combobox_height_label', 'Combobox Height Scalar:', True), 3, 0)
        grid.addWidget(self.combobox_height_scalar_spinbox, 3, 1)
        grid.addWidget(label('combobox_width_label', 'Combobox Width Scalar:', True), 4, 0)
        grid.addWidget(self.combobox_width_scalar_spinbox, 4, 1)
        right.addLayout(grid)

        right.addItem(QtW.QSpacerItem(17, 13, QtW.QSizePolicy.Policy.Minimum, QtW.QSizePolicy.Policy.Expanding))
        layout.addLayout(right)

    def _scalar_spinbox(self, name: str) -> QtW.QDoubleSpinBox:
        spinbox = fixed_height(QtW.QDoubleSpinBox(self))
        spinbox.setObjectName(name)
        spinbox.setMinimum(1.0)
        spinbox.setMaximum(5.0)
        spinbox.setSingleStep(0.1)
        return spinbox

    def tab_order(self) -> list[QtW.QWidget]:
        return []

    def connect_signals(self):
        # Connected twice in the original dialog, kept as-is
        self.upb_checkBox.stateChanged.connect(self.update_analysis_display)
        self.geochem_checkBox.stateChanged.connect(self.update_analysis_display)

        self.upb_checkBox.stateChanged.connect(self.update_analysis_display)
        self.geochem_checkBox.stateChanged.connect(self.update_analysis_display)

    def populate(self):
        if 'UPbAnalyses' in settings.value('display_analyses'):
            self.upb_checkBox.setChecked(True)
        else:
            self.upb_checkBox.setChecked(False)
        if 'GeoChemicalAnalyses' in settings.value('display_analyses'):
            self.geochem_checkBox.setChecked(True)
        else:
            self.geochem_checkBox.setChecked(False)

        self.select_columns.populate_stack()

        self.combobox_height_scalar_spinbox.setValue(float(settings.value('checkable_combobox_height_scalar')))
        self.combobox_width_scalar_spinbox.setValue(float(settings.value('checkable_combobox_width_scalar')))

        # List of font sizes to populate the font size comboboxes
        font_sizes = [str(i) for i in range(6, 21)]
        self.font_size_comboBox.addItems(font_sizes)
        self.font_size_comboBox.setCurrentText(str(int(settings.value('font_size'))))
        self.table_font_size_comboBox.addItems(font_sizes)
        self.table_font_size_comboBox.setCurrentText(str(int(settings.value('table_font_size'))))

        # If the default font is not in the font family list, add it
        if settings.value('font_family') not in QFontDatabase.families():
            self.fontComboBox.addItems([settings.value('font_family')])
        if settings.value('default_font_family') not in QFontDatabase.families():
            self.fontComboBox.addItems([settings.value('default_font_family')])
        self.fontComboBox.setCurrentFont(QFont(settings.value('font_family')))

        # self.lazy_batch_comboBox.addItems(['100', '250', '500', '1000', '2500', '5000', '10000'])
        # self.lazy_batch_comboBox.setCurrentText(str(settings.value('lazy_loading_batch_size')))
        # if settings.value('lazy_loading_enabled') == 'true':
        #     self.lazy_checkBox.setChecked(True)
        #     self.lazy_batch_comboBox.setEnabled(True)
        # else:
        #     self.lazy_checkBox.setChecked(False)
        #     self.lazy_batch_comboBox.setEnabled(False)

    def save(self) -> bool:
        """
        Saves column selections and style settings.
        :return: True if the stylesheet was updated
        """
        self.select_columns.save_list_states()

        # Style sheet related values
        self.combobox_height_scalar_spinbox: QtW.QDoubleSpinBox
        style_settings = {'checkable_combobox_height_scalar': self.combobox_height_scalar_spinbox.value(),
                          'checkable_combobox_width_scalar': self.combobox_width_scalar_spinbox.value(),
                          'font_size': float(self.font_size_comboBox.currentText()),
                          'table_font_size': float(self.table_font_size_comboBox.currentText()),
                          'font_family': self.fontComboBox.currentFont().family()}
        # Updating the style sheet takes time, so only do it if necessary
        stylesheet_updated = False
        for key, value in style_settings.items():
            if settings.value(key) != value:
                update_setting('checkable_combobox_height_scalar', self.combobox_height_scalar_spinbox.value())
                update_setting('checkable_combobox_width_scalar', self.combobox_width_scalar_spinbox.value())

                update_setting('font_size', float(self.font_size_comboBox.currentText()))
                update_setting('table_font_size', float(self.table_font_size_comboBox.currentText()))
                update_setting('font_family', self.fontComboBox.currentFont().family())

                LoadingDialogManager().show_loading_dialog('Updating', 'Updating style...')
                update_stylesheet()
                LoadingDialogManager().close_loading_dialog('Updating', 'Updating style...')
                stylesheet_updated = True
                break
        return stylesheet_updated

    def update_analysis_display(self):
        display_analyses = settings.value('display_analyses')
        if self.upb_checkBox.isChecked() and 'UPbAnalyses' not in display_analyses:
            display_analyses.append('UPbAnalyses')
        elif not self.upb_checkBox.isChecked() and 'UPbAnalyses' in display_analyses:
            display_analyses.remove('UPbAnalyses')
        if self.geochem_checkBox.isChecked() and 'GeoChemicalAnalyses' not in display_analyses:
            display_analyses.append('GeoChemicalAnalyses')
        elif not self.geochem_checkBox.isChecked() and 'GeoChemicalAnalyses' in display_analyses:
            display_analyses.remove('GeoChemicalAnalyses')
        if display_analyses != settings.value('display_analyses'):
            settings.setValue('display_analyses', display_analyses)

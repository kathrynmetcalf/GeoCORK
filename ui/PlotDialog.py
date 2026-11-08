from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtWidgets as QtW

import logger_setup
from Functions.Plot_data import DATA_PROVIDERS, Option
from Functions.Plot_types import PLOT_TYPES
from Functions.Settings_manager import SettingsManager

settings = SettingsManager().settings


class PlotDialog(QtW.QDialog):
    """
    Floating, non-modal plot window driven by a list of SampleIDs. Plot types and data providers come from the
    PLOT_TYPES / DATA_PROVIDERS registries; their Option lists build the option forms, so adding a plot needs no
    changes here.
    """

    def __init__(self, parent=None):
        super().__init__(parent, QtC.Qt.WindowType.Tool)
        self.setWindowTitle('Sample plots')
        self.resize(760, 620)
        self.sample_ids: list[int] = []
        self.values: dict[tuple[str, str], object] = {}
        """(owner key, option name): value, kept while the dialog is open so switching plots preserves settings"""
        self.frame = None

        self.plot_comboBox = QtW.QComboBox()
        model = QtG.QStandardItemModel()
        for category in dict.fromkeys(plot.category for plot in PLOT_TYPES.values()):
            header = QtG.QStandardItem(category)
            header.setFlags(QtC.Qt.ItemFlag.NoItemFlags)
            header.setFont(QtG.QFont(header.font().family(), -1, QtG.QFont.Weight.Bold))
            model.appendRow(header)
            for name, plot in PLOT_TYPES.items():
                if plot.category == category:
                    model.appendRow(QtG.QStandardItem(f'    {name}'))
        self.plot_comboBox.setModel(model)

        self.data_box = QtW.QGroupBox('Data')
        self.plot_box = QtW.QGroupBox('Plot')
        self.data_form = QtW.QFormLayout(self.data_box)
        self.plot_form = QtW.QFormLayout(self.plot_box)

        side = QtW.QVBoxLayout()
        side.addWidget(QLabel('Choose plot type:'))
        side.addWidget(self.plot_comboBox)
        side.addWidget(self.data_box)
        side.addWidget(self.plot_box)
        side.addStretch()

        side_widget = QtW.QWidget()
        side_widget.setLayout(side)
        side_widget.setMaximumWidth(300)

        self.figure = Figure(layout='constrained')
        self.canvas = FigureCanvasQTAgg(self.figure)

        self.status_label = QtW.QLabel()
        self.status_label.setWordWrap(True)

        self.detritalpy_label = QLabel('Geochronology plots created using <a href="https://github.com/grsharman/detritalPy">detritalPy</a>')
        self.detritalpy_label.setTextFormat(Qt.TextFormat.RichText)
        self.detritalpy_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.detritalpy_label.setOpenExternalLinks(True)
        self.detritalpy_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.detritalpy_label.setFixedWidth(300)

        footer = QtW.QHBoxLayout()
        footer.addWidget(self.status_label)
        footer.addWidget(self.detritalpy_label)

        footer_widget = QtW.QWidget()
        footer_widget.setLayout(footer)


        plot_area = QtW.QVBoxLayout()
        plot_area.addWidget(NavigationToolbar2QT(self.canvas, self))
        plot_area.addWidget(self.canvas, 1)
        plot_area.addWidget(footer_widget)

        layout = QtW.QHBoxLayout(self)
        layout.addWidget(side_widget)
        layout.addLayout(plot_area, 1)

        self.timer = QtC.QTimer(self, singleShot=True, interval=250)
        self.timer.timeout.connect(self.redraw)
        self.plot_comboBox.currentIndexChanged.connect(self.plot_changed)
        last = settings.value('plot_dialog_plot', 'Kernel density estimate (KDE)')
        index = self.plot_comboBox.findText(f'    {last}')
        self.plot_comboBox.setCurrentIndex(index if index >= 0 else 1)
        self.plot_changed()

    @property
    def plot(self):
        return PLOT_TYPES[self.plot_comboBox.currentText().strip()]

    @property
    def provider(self):
        return DATA_PROVIDERS[self.plot.data]

    def set_samples(self, sample_ids: list[int]):
        self.sample_ids = list(sample_ids)
        self.timer.start()

    def reload(self):
        """Discard cached data (database changed) and redraw."""
        for provider in DATA_PROVIDERS.values():
            provider.clear_cache()
        self.timer.start()

    def plot_changed(self):
        settings.setValue('plot_dialog_plot', self.plot.name)
        self.build_form(self.data_form, self.provider.key, self.provider.options)
        self.build_form(self.plot_form, self.plot.name, self.plot.options)
        self.data_box.setTitle(self.provider.label)
        self.timer.start()

    def build_form(self, form: QtW.QFormLayout, owner: str, options: list[Option]):
        while form.rowCount():
            form.removeRow(0)
        for option in options:
            value = self.values.setdefault((owner, option.name), option.default)
            if option.kind == 'bool':
                widget = QtW.QCheckBox()
                widget.setChecked(bool(value))
                widget.toggled.connect(lambda v, k=(owner, option.name): self.set_value(k, v))
            elif option.kind == 'choice':
                widget = QtW.QComboBox()
                widget.setMinimumWidth(100)
                widget.addItems(option.choices)
                widget.setCurrentText(str(value))
                widget.currentTextChanged.connect(lambda v, k=(owner, option.name): self.set_value(k, v))
            elif option.kind in ('float', 'int'):
                widget = QtW.QDoubleSpinBox() if option.kind == 'float' else QtW.QSpinBox()
                widget.setRange(option.minimum, option.maximum)
                widget.setValue(value)
                widget.setKeyboardTracking(False)
                widget.valueChanged.connect(lambda v, k=(owner, option.name): self.set_value(k, v))
            else:
                widget = QtW.QLineEdit(str(value))
                widget.editingFinished.connect(lambda w=widget, k=(owner, option.name): self.set_value(k, w.text()))
            widget.setToolTip(option.tooltip)
            form.addRow(option.label, widget)

    def set_value(self, key: tuple, value):
        self.values[key] = value
        self.timer.start()

    def options_for(self, owner: str, options: list[Option]) -> dict:
        return {option.name: self.values.get((owner, option.name), option.default) for option in options}

    def redraw(self):
        self.figure.clear()
        self.frame = None
        if not self.sample_ids:
            message = 'Select samples on the map to plot'
        else:
            try:
                self.frame = self.provider.load(self.sample_ids, self.options_for(self.provider.key, self.provider.options))
                if self.frame.empty:
                    message = f'No {self.provider.label} for the {len(self.sample_ids)} selected samples'
                else:
                    message = self.plot.draw(self.figure, self.frame, self.options_for(self.plot.name, self.plot.options))
            except Exception as error:  # a plot failing (e.g. optimized bandwidth on one grain) must not close the window
                logger_setup.get_logger().exception(f'Error drawing {self.plot.name}')
                self.figure.clear()
                message = f'Could not draw {self.plot.name}: {error}'
        if not self.figure.axes:
            self.figure.text(0.5, 0.5, message, ha='center', va='center', color='0.4', wrap=True)
        self.status_label.setText(message)
        self.canvas.draw_idle()


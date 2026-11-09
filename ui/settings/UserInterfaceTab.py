"""'User Interface Settings' tab of the Settings dialog: tooltips, theme colors and Import Wizard colors."""
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import Qt

import logger_setup
from ui.settings.SettingsCore import (settings, update_setting, apply_color_palette, ColorButton, COLOR_MODES,
                          COLOR_THEME_MODES, THEME_COLOR_ROLES, IMPORTER_COLOR_ROLES,
                          DEFAULT_THEME_COLORS, DEFAULT_IMPORTER_COLORS, theme_color_key,
                          importer_color_key)


class UserInterfaceTab(QtW.QWidget):
    """
    Display settings (tooltips) and the color settings built in code.
    """
    title = 'User Interface Settings'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('ui_tab')
        layout = QtW.QVBoxLayout(self)
        layout.setObjectName('verticalLayout_8')

        self.groupBox = QtW.QGroupBox('Display Settings', self)
        self.groupBox.setObjectName('groupBox')
        grid = QtW.QGridLayout(self.groupBox)
        grid.setObjectName('gridLayout_7')
        self.display_tooltips_checkBox = QtW.QCheckBox('Display Tooltips', self.groupBox)
        self.display_tooltips_checkBox.setObjectName('display_tooltips_checkBox')
        grid.addWidget(self.display_tooltips_checkBox, 0, 0)
        layout.addWidget(self.groupBox)

        # Color widgets are built in code and added to this tab
        self.build_color_settings()

    def tab_order(self) -> list[QtW.QWidget]:
        return []

    def connect_signals(self):
        self.custom_theme_colors_checkBox.checkStateChanged.connect(self.update_color_widget_states)
        self.reset_colors_pushButton.clicked.connect(self.reset_color_fields)

    def populate(self):
        self.display_tooltips_checkBox.setChecked(settings.value('display_tooltips', type=bool))

        self.populate_color_fields()

    def save(self, stylesheet_updated: bool):
        # Color settings, update_stylesheet() already applies the palette
        if self.save_color_settings() and not stylesheet_updated:
            apply_color_palette()

        # if self.lazy_checkBox.isChecked():
        #     update_setting('lazy_loading_enabled', 'true')
        #     update_setting('lazy_loading_batch_size', int(self.lazy_batch_comboBox.currentText()))
        # else:
        #     update_setting('lazy_loading_enabled', 'false')
        #
        # update_setting('display_tooltips', self.display_tooltips_checkBox.isChecked())

    def build_color_settings(self):
        """
        Builds the Theme Colors and Import Wizard Colors group boxes and adds them to the User Interface Settings tab.
        Color buttons are stored in self.theme_color_buttons / self.importer_color_buttons keyed by setting key.
        """
        self.theme_color_buttons = {}
        self.importer_color_buttons = {}
        self.theme_preview_labels = {}
        mode_titles = {'light': 'Light mode', 'dark': 'Dark mode'}

        # Theme colors
        theme_groupBox = QtW.QGroupBox('Theme Colors', self)
        theme_groupBox.setObjectName('theme_colors_groupBox')
        theme_grid = QtW.QGridLayout(theme_groupBox)

        theme_grid.addWidget(QtW.QLabel('Color mode:'), 0, 0)
        self.color_mode_comboBox = QtW.QComboBox(theme_groupBox)
        self.color_mode_comboBox.setObjectName('color_mode_comboBox')
        self.color_mode_comboBox.addItems(COLOR_THEME_MODES)
        self.color_mode_comboBox.setMinimumHeight(25)
        self.color_mode_comboBox.setToolTip('System follows the operating system light/dark preference')
        theme_grid.addWidget(self.color_mode_comboBox, 0, 1, 1, 2)

        self.custom_theme_colors_checkBox = QtW.QCheckBox('Use custom text and fill colors', theme_groupBox)
        self.custom_theme_colors_checkBox.setObjectName('custom_theme_colors_checkBox')
        self.custom_theme_colors_checkBox.setToolTip('When unchecked, the default colors of the system style are used')
        theme_grid.addWidget(self.custom_theme_colors_checkBox, 1, 0, 1, 3)

        for col, mode in enumerate(COLOR_MODES, start=1):
            header = QtW.QLabel(f'<b>{mode_titles[mode]}</b>')
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            theme_grid.addWidget(header, 2, col)
        row = 3
        for role, label in THEME_COLOR_ROLES.items():
            theme_grid.addWidget(QtW.QLabel(f'{label}:'), row, 0)
            for col, mode in enumerate(COLOR_MODES, start=1):
                key = theme_color_key(mode, role)
                button = ColorButton(DEFAULT_THEME_COLORS[mode][role], theme_groupBox)
                button.setObjectName(f'{key}_button')
                button.colorChanged.connect(self.update_color_previews)
                self.theme_color_buttons[key] = button
                theme_grid.addWidget(button, row, col)
            row += 1
        theme_grid.addWidget(QtW.QLabel('Preview:'), row, 0)
        for col, mode in enumerate(COLOR_MODES, start=1):
            preview = QtW.QLabel('Sample text', theme_groupBox)
            preview.setObjectName(f'theme_{mode}_preview_label')
            preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            preview.setMinimumHeight(25)
            self.theme_preview_labels[mode] = preview
            theme_grid.addWidget(preview, row, col)
        theme_grid.setColumnStretch(1, 1)
        theme_grid.setColumnStretch(2, 1)

        # Import Wizard colors
        importer_groupBox = QtW.QGroupBox('Import Wizard Colors', self)
        importer_groupBox.setObjectName('importer_colors_groupBox')
        importer_grid = QtW.QGridLayout(importer_groupBox)
        description = QtW.QLabel('Colors used to highlight headers and cells in the Import Wizard. The set used '
                                 'follows the active color mode.', importer_groupBox)
        description.setWordWrap(True)
        importer_grid.addWidget(description, 0, 0, 1, 3)
        for col, mode in enumerate(COLOR_MODES, start=1):
            header = QtW.QLabel(f'<b>{mode_titles[mode]}</b>')
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            importer_grid.addWidget(header, 1, col)
        row = 2
        for role, label in IMPORTER_COLOR_ROLES.items():
            importer_grid.addWidget(QtW.QLabel(f'{label}:'), row, 0)
            for col, mode in enumerate(COLOR_MODES, start=1):
                key = importer_color_key(mode, role)
                button = ColorButton(DEFAULT_IMPORTER_COLORS[mode][role], importer_groupBox)
                button.setObjectName(f'{key}_button')
                button.colorChanged.connect(self.update_color_previews)
                self.importer_color_buttons[key] = button
                importer_grid.addWidget(button, row, col)
            row += 1
        importer_grid.setColumnStretch(1, 1)
        importer_grid.setColumnStretch(2, 1)

        reset_layout = QtW.QHBoxLayout()
        reset_layout.addStretch()
        self.reset_colors_pushButton = QtW.QPushButton('Reset Colors to Defaults', self)
        self.reset_colors_pushButton.setObjectName('reset_colors_pushButton')
        self.reset_colors_pushButton.setToolTip('Resets only the color fields, click Apply or OK to save')
        reset_layout.addWidget(self.reset_colors_pushButton)

        colors_layout = QtW.QHBoxLayout()
        colors_layout.addWidget(theme_groupBox, 1, Qt.AlignmentFlag.AlignTop)
        colors_layout.addWidget(importer_groupBox, 1, Qt.AlignmentFlag.AlignTop)

        ui_layout = self.layout()
        ui_layout.addLayout(colors_layout)
        ui_layout.addLayout(reset_layout)
        ui_layout.addStretch()

    def populate_color_fields(self):
        """
        Populates the color widgets with the stored color settings.
        """
        mode = settings.value('color_theme_mode', 'System')
        self.color_mode_comboBox.setCurrentText(mode if mode in COLOR_THEME_MODES else 'System')
        self.custom_theme_colors_checkBox.setChecked(settings.value('custom_theme_colors') == 'true')
        for key, button in {**self.theme_color_buttons, **self.importer_color_buttons}.items():
            button.set_color(settings.value(key, settings.value(f'default_{key}')))
        self.update_color_widget_states()
        self.update_color_previews()

    def reset_color_fields(self):
        """
        Resets the color widgets (not the stored settings) to the default colors. Saved with Apply/OK.
        """
        self.color_mode_comboBox.setCurrentText(settings.value('default_color_theme_mode', 'System'))
        self.custom_theme_colors_checkBox.setChecked(settings.value('default_custom_theme_colors') == 'true')
        for mode in COLOR_MODES:
            for role in THEME_COLOR_ROLES:
                self.theme_color_buttons[theme_color_key(mode, role)].set_color(DEFAULT_THEME_COLORS[mode][role])
            for role in IMPORTER_COLOR_ROLES:
                self.importer_color_buttons[importer_color_key(mode, role)].set_color(
                    DEFAULT_IMPORTER_COLORS[mode][role])
        self.update_color_widget_states()
        self.update_color_previews()

    def update_color_widget_states(self):
        """Enables the theme color buttons only when custom theme colors are turned on."""
        enabled = self.custom_theme_colors_checkBox.isChecked()
        for button in self.theme_color_buttons.values():
            button.setEnabled(enabled)
        for label in self.theme_preview_labels.values():
            label.setEnabled(enabled)

    def update_color_previews(self, *_):
        """
        Updates the theme preview labels (text over fill) and draws the importer swatch labels in that mode's
        importer text color so readability can be judged before saving.
        """
        for mode in COLOR_MODES:
            text = self.theme_color_buttons[theme_color_key(mode, 'text')].color()
            fill = self.theme_color_buttons[theme_color_key(mode, 'fill')].color()
            self.theme_preview_labels[mode].setStyleSheet(
                f'QLabel {{ color: {text}; background-color: {fill}; border: 1px solid #808080; border-radius: 3px; }}')

            importer_text = self.importer_color_buttons[importer_color_key(mode, 'text')].color()
            for role in IMPORTER_COLOR_ROLES:
                button = self.importer_color_buttons[importer_color_key(mode, role)]
                # Text colors are previewed as a swatch with contrasting label, fills with the importer text color
                button.set_text_color(None if role in ('text', 'disabled_text') else importer_text)

    def save_color_settings(self) -> bool:
        """
        Saves the color widgets to the settings.
        :return: True if any color setting changed
        :rtype: bool
        """
        new_values = {'color_theme_mode': self.color_mode_comboBox.currentText(),
                      'custom_theme_colors': 'true' if self.custom_theme_colors_checkBox.isChecked() else 'false'}
        for key, button in {**self.theme_color_buttons, **self.importer_color_buttons}.items():
            new_values[key] = button.color()
        changed = False
        for key, value in new_values.items():
            if str(settings.value(key)).lower() != str(value).lower():
                update_setting(key, value)
                changed = True
        if changed:
            logger_setup.get_logger().info('Color settings updated')
        return changed

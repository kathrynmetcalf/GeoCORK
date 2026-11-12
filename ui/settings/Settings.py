"""
Settings dialog builder. Each tab of the settings QTabWidget is its own class in ui/SettingsTabs/, and the shared
setting helpers live in ui/SettingsTabs/SettingsCore.py. Everything from SettingsCore is re-exported here so existing
imports such as `from ui.settings.Settings import get_importer_brushes, update_stylesheet` keep working.
Settings.ui is no longer used.
"""
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import QPoint, QSize, Qt

import logger_setup

from ui.settings.SettingsCore import settings, reset_to_default_settings
from ui.settings.UnitsFormatsTab import UnitsFormatsTab
from ui.settings.TableDisplaysTab import TableDisplaysTab
from ui.settings.AboutDatabaseTab import AboutDatabaseTab
from ui.settings.UserInterfaceTab import UserInterfaceTab


class SettingsDialog(QtW.QDialog):
    """
    SettingsDialog class allows the user to change the settings of the application. Builds the settings tabs and
    coordinates populating and saving them.
    """

    def __init__(self):
        super().__init__()
        logger_setup.get_logger().info('Opening settings dialog')
        self._tabs = []

        self.resize(800, 600)
        layout = QtW.QVBoxLayout(self)
        layout.setObjectName('verticalLayout_5')

        self.settings_tabWidget = QtW.QTabWidget(self)
        self.settings_tabWidget.setObjectName('settings_tabWidget')
        layout.addWidget(self.settings_tabWidget)

        # Tab order matches display_tab() indexes: 0 Units and Formats, 1 Table Displays, 2 About Database, 3 UI
        self.units_formats_tab = UnitsFormatsTab(self)
        self.display_tab_widget = TableDisplaysTab(self)
        self.about_db_tab = AboutDatabaseTab(self)
        self.ui_tab = UserInterfaceTab(self)
        self._tabs = [self.units_formats_tab, self.display_tab_widget, self.about_db_tab, self.ui_tab]
        for tab in self._tabs:
            self.settings_tabWidget.addTab(tab, tab.title)

        self.buttonBox = QtW.QDialogButtonBox(self)
        self.buttonBox.setObjectName('buttonBox')
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtW.QDialogButtonBox.StandardButton.Apply |
                                          QtW.QDialogButtonBox.StandardButton.Cancel |
                                          QtW.QDialogButtonBox.StandardButton.Ok |
                                          QtW.QDialogButtonBox.StandardButton.RestoreDefaults)
        layout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.set_tab_order()

        self.setWindowTitle('Settings')
        self.loadWindowState()
        self.settings_tabWidget.setCurrentIndex(0)
        self.updated = False

        self.populate_fields()

        for tab in self._tabs:
            tab.connect_signals()

        self.buttonBox.button(QtW.QDialogButtonBox.StandardButton.Ok).clicked.connect(self.update_settings_close)
        self.buttonBox.button(QtW.QDialogButtonBox.StandardButton.Cancel).clicked.connect(self.close)
        self.buttonBox.button(QtW.QDialogButtonBox.StandardButton.Apply).clicked.connect(self.update_settings)
        self.buttonBox.button(QtW.QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            self.restore_defaults)

    def __getattr__(self, name):
        """
        Backwards compatibility: widgets/methods that used to live on the dialog (e.g. dialog.select_columns,
        dialog.decimals_comboBox) are looked up on the tabs.
        """
        for tab in self.__dict__.get('_tabs', ()):
            if hasattr(tab, name):
                return getattr(tab, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def set_tab_order(self):
        """Keyboard tab order, as defined in Settings.ui"""
        chain = [self.settings_tabWidget]
        for tab in (self.units_formats_tab, self.about_db_tab):
            chain.extend(tab.tab_order())
        for first, second in zip(chain, chain[1:]):
            QtW.QWidget.setTabOrder(first, second)

    def display_tab(self, index):
        self.settings_tabWidget.setCurrentIndex(index)

    def populate_fields(self):
        """
        Populates all the fields with the current settings. This is called when the settings dialog is opened.
        """
        logger_setup.get_logger().info('Populating fields with the current settings')
        for tab in self._tabs:
            tab.populate()

    def update_settings(self):
        """
        Updates the settings to current values within each tab. Updates the database with new values of the About table.
        """
        # No longer using default settings
        from Functions.Widget_classes import show_loading_dialog, close_loading_dialog
        logger_setup.get_logger().info('Updating settings')
        show_loading_dialog('Updating', 'Updating settings...')
        settings.setValue('default_settings', 'false')

        if not self.units_formats_tab.save():
            return
        self.about_db_tab.save()
        stylesheet_updated = self.display_tab_widget.save()
        self.ui_tab.save(stylesheet_updated)

        self.populate_fields()
        close_loading_dialog('Updating', 'Updating settings...')
        logger_setup.get_logger().info('Updated settings successfully')
        self.updated = True

    def update_settings_close(self):
        """
        Updates the settings and closes the dialog.
        """
        self.update_settings()
        self.close()

    def restore_defaults(self):
        """
        Restores the default settings for the application. This is called when the user clicks the Restore Defaults
        """
        from Functions.Widget_classes import show_loading_dialog, close_loading_dialog
        show_loading_dialog('Restoring Default Settings', 'Currently updating settings...')
        logger_setup.get_logger().info('Restoring default settings')
        settings.setValue('default_settings', 'true')
        reset_to_default_settings()
        self.populate_fields()
        close_loading_dialog('Restoring Default Settings', 'Currently updating settings...')

    def close(self):
        self.saveWindowState()
        return super().close()

    def saveWindowState(self):
        settings.setValue("ui/SettingDialog/pos", self.pos())
        settings.setValue("ui/SettingDialog/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/SettingDialog/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/SettingDialog/size", defaultValue=QSize(800, 600)))
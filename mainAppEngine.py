
import signal
import sys

from PyQt6.QtWidgets import QApplication, QErrorMessage

from ui.LandingUI import LandingPage
from Functions.Settings_manager import settings
from ui.Settings import reset_to_default_settings, populate_app_defaults, check_missing_settings, default_settings
signal.signal(signal.SIGINT, signal.SIG_DFL)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Make sure that the default settings values are set
    default_settings()
    # Populate the default font family and font size based on the system settings
    populate_app_defaults()

    # #Optional: reset settings
    # settings.setValue('default_settings', 'true')

    # makes it so if 'default_settings' is ANYTHING but False, then it will be set to True and
    # default_settings() will be called. Makes sure that the default settings are set even on first launch (eg None)
    if settings.value('default_settings') != 'false':
        settings.setValue('default_settings', 'true')
        # Set all settings to the default values
        reset_to_default_settings()
    else:
        # Check if any settings are missing, and if so, set them to the default values
        check_missing_settings()

    landing_page = LandingPage()

    sys.exit(app.exec())

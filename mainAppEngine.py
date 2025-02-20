
import signal
import sys

from PyQt6.QtWidgets import QApplication, QErrorMessage, QStyleFactory

import logger_setup
from ui.LandingUI import LandingPage
from Functions.Settings_manager import settings
from ui.Settings import reset_to_default_settings, populate_app_defaults, check_missing_settings, default_settings
signal.signal(signal.SIGINT, signal.SIG_DFL)


if __name__ == "__main__":
    #force app to always load in light mode
    # sys.argv += ['-platform', 'windows:darkmode=1']
    app = QApplication(sys.argv)
    app.setApplicationName("GeoCORK")

    logger_setup.setup_async_logger()
    logger = logger_setup.get_logger()

    logger.info("Starting GeoCORK...")

    # Make sure that the default settings values are set
    default_settings()
    # Populate the default font family and font size based on the system settings
    populate_app_defaults()

    # #Optional: reset settings
    # settings.setValue('default_settings', 'true')

    # makes it so if 'default_settings' is ANYTHING but False, then it will be set to True and
    # default_settings() will be called. Makes sure that the default settings are set even on first launch (eg None)
    if settings.value('default_settings') != 'false':
        if settings.value('default_settings') == 'true':
            logger.info('Default settings are set True')
        else:
            logger.info('Default settings is set to something other than True or False, resetting to Default settings.')

        # Set all settings to the default values
        settings.setValue('default_settings', 'true')
        reset_to_default_settings()
    else:
        # Check if any settings are missing, and if so, set them to the default values
        logger.info('Default settings are set to False, checking for missing settings.')
        check_missing_settings()

    landing_page = LandingPage()

    exit_code = app.exec()

    logger_setup.stop_logger()

    sys.exit(exit_code)

import os
import signal
import sys
import platform
import traceback

from PyQt6.QtWidgets import QApplication

import logger_setup
from Functions.Widget_classes import TooltipFilter
from ui.LandingUI import LandingPage
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from ui.Settings import reset_to_default_settings, populate_app_defaults, check_missing_settings, default_settings
# signal.signal(signal.SIGINT, signal.SIG_DFL)


if __name__ == "__main__":
    #force app to always load in light mode
    if platform.system() == 'Windows':
        sys.argv += ['-platform', 'windows:darkmode=1']

    app = QApplication(sys.argv)
    app.setApplicationName("GeoCORK")

    app.aboutToQuit.connect(lambda: logger.info("GeoCORK is about to quit."))

    tooltip_filter = TooltipFilter(settings)
    app.installEventFilter(tooltip_filter)

    logger_setup.setup_async_logger()
    logger = logger_setup.get_logger()

    logger.info("Starting GeoCORK...")
    if os.path.isfile("temp.db"):
        os.remove("temp.db")

    # Make sure that the default settings values are set
    default_settings()
    # Populate the default font family and font size based on the system settings
    populate_app_defaults()

    # #Optional: reset settings
    settings.setValue('default_settings', 'false')

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

    start_filepath = None
    if os.path.isfile(sys.argv[-1]) and str(sys.argv[-1]).endswith('.db'):
        start_filepath = sys.argv[-1]
    landing_page = LandingPage(start_filepath)

    try:
        exit_code = app.exec()

    except Exception:
        raise

    finally:
        logger.info("GeoCORK has exited with code %s.", exit_code)
        logger_setup.stop_logger()

    sys.exit(exit_code)
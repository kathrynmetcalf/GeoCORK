
import signal
import sys

from PyQt6.QtWidgets import QApplication, QErrorMessage

from ui.LandingUI import LandingPage
from Functions.Settings_manager import settings
from ui.Settings import default_settings
signal.signal(signal.SIGINT, signal.SIG_DFL)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # makes it so if 'default_settings' is ANYTHING but False, then it will be set to True and
    # default_settings() will be called. Makes sure that the default settings are set even on first launch (eg None)
    if settings.value('default_settings', bool) is not False:
        settings.setValue('default_settings', True)
        default_settings()

    landing_page = LandingPage()

    sys.exit(app.exec())

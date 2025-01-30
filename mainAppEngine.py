
import signal
import sys

from PyQt6.QtWidgets import QApplication, QErrorMessage

from ui.LandingUI import LandingPage
from Functions.Settings_manager import settings
from ui.Settings import populate_app_defaults
signal.signal(signal.SIGINT, signal.SIG_DFL)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    settings.setValue('default_settings', True)
    populate_app_defaults()
    landing_page = LandingPage()

    sys.exit(app.exec())

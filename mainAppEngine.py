
import sys

from PyQt6.QtWidgets import QApplication
from Functions.Settings_manager import settings
from ui.Settings import default_settings
from ui.LandingUI import LandingPage

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    landing_page = LandingPage()

    sys.exit(app.exec())

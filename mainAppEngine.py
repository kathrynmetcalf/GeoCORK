
import signal
import sys

from PyQt6.QtWidgets import QApplication, QErrorMessage
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QAction
from Functions.Settings_manager import settings
from ui.Settings import default_settings, SettingsDialog
from ui.LandingUI import LandingPage

from ui.LandingUI import LandingPage

signal.signal(signal.SIGINT, signal.SIG_DFL)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    if not settings.contains("default_settings"):
        settings.setValue("default_settings", True)
    if bool(settings.value("default_settings")) is True:
        default_settings()

    landing_page = LandingPage()

    sys.exit(app.exec())

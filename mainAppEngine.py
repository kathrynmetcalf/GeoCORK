
import signal
import sys

from PyQt6.QtWidgets import QApplication, QErrorMessage

from ui.LandingUI import LandingPage

signal.signal(signal.SIGINT, signal.SIG_DFL)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    landing_page = LandingPage()

    sys.exit(app.exec())

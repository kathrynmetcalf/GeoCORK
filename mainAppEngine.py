
import sys

from PyQt6.QtWidgets import QApplication

from ui.LandingUI import LandingPage

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    landing_page = LandingPage()

    sys.exit(app.exec())

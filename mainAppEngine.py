
import sys

from PyQt6.QtWidgets import QApplication, QErrorMessage

from ui.LandingUI import LandingPage

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

def error_handler(type, value, traceback):
    QErrorMessage().showMessage(f"{''.join(traceback.format_exception(type, value, traceback))}")

if __name__ == "__main__":
    sys.excepthook = error_handler
    app = QApplication(sys.argv)

    landing_page = LandingPage()

    sys.exit(app.exec())

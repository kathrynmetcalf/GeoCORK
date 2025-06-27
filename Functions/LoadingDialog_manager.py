
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QLabel

import logger_setup
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC

class LoadingDialogManager:
    _instance= None

    def __init__(self):
        if LoadingDialogManager._instance is None:
            self.dialog = None
            self.layout = QtW.QHBoxLayout()
            self.messageLabel = None
            self.titles = []
            self.messages = []
            self.timer = QtC.QTimer()
            LoadingDialogManager._instance = self
            self.timer.setSingleShot(True)
            # self.timer.setInterval(1000)
            self.timer.timeout.connect(self.begin)

    @staticmethod
    def get_instance():
        if LoadingDialogManager._instance is None:
            LoadingDialogManager()
        return LoadingDialogManager._instance

    def show_loading_dialog(self, title: str, message: str):
        if message not in self.messages:
            self.messages.append(message)
            self.titles.append(title)
        # if not self.timer.isActive():
        if not self.dialog:
            # logger_setup.get_logger().info(f'Starting timer for {message}')
            # self.timer.start(1)  # Start the timer to show the dialog after  ms
            self.begin()
        else:
            # logger_setup.get_logger().info(f'Updating dialog with title: {title} and message: {message}')
            self.dialog.setWindowTitle(self.titles[-1])
            self.messageLabel.setText(self.messages[-1])
            self.update_dialog()

    def begin(self):
        if len(self.messages) == 0:
            # logger_setup.get_logger().info('No messages to display, returning')
            return
        # logger_setup.get_logger().info(f'{self.messages} for more than 1 second, loading dialog')
        self.dialog = QtW.QDialog()
        # Show the most recent title and message
        self.dialog.setWindowTitle(self.titles[-1])
        self.dialog.setMinimumSize(QSize(250, 75))
        self.layout = QtW.QHBoxLayout(self.dialog)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.messageLabel = QLabel(self.messages[-1], parent=self.dialog)
        self.messageLabel.setObjectName('messageLabel')
        self.layout.addWidget(self.messageLabel, alignment=Qt.AlignmentFlag.AlignCenter)

        self.dialog.setWindowFlags(QtC.Qt.WindowType.WindowStaysOnTopHint)
        self.dialog.show()
        self.dialog.adjustSize()
        QtW.QApplication.processEvents()

    def update_dialog(self):
        if self.dialog is not None:
            # logger_setup.get_logger().info('updating dialog')
            QtW.QApplication.processEvents()

    def close_loading_dialog(self, title: str, message: str):
        # logger_setup.get_logger().info(f'Closing loading dialog with title: {title} and message: {message}')
        # Check if the dialog exists and has the same title and message
        if len(self.messages) > 0:
            # Remove the title and message from the lists
            if message in self.messages:
                self.messages.remove(message)
                self.titles.remove(title)
        if self.dialog is not None:
            if len(self.messages) <= 1:
                # logger_setup.get_logger().info('Closing loading dialog')
                # self.timer.stop()
                self.dialog.close()
                self.dialog = None
            else:
                # logger_setup.get_logger().info(f'Updating loading dialog with next message: {self.messages[-1]}')
                # Update the dialog with the next title and message
                self.dialog.setWindowTitle(self.titles[-1])
                self.messageLabel.setText(self.messages[-1])
                self.update_dialog()
        else:
            return


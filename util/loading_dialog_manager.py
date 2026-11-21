from PyQt6 import QtWidgets, QtCore

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QLabel


def show_loading_dialog(title: str, message: str):
    """
    Show a loading dialog while the action is taking place. The loading dialog is managed by the
    LoadingDialogManager, which ensures that it is closed properly after the action is completed. The title and message
    of the loading dialog can be customized.
    :param title: Title of the loading dialog
    :param message: Message to display in the loading dialog
    :return:
    """
    loading_manager = LoadingDialogManager.get_instance()
    loading_manager.show_loading_dialog(title, message)


def close_loading_dialog(title: str, message: str):
    """
    Close the loading dialog with the given title and message. This ensures that the loading dialog is closed properly.
    :param title: Title of the loading dialog to close
    :param message: Message displayed in the loading dialog to close
    :return:
    """
    loading_manager = LoadingDialogManager.get_instance()
    loading_manager.close_loading_dialog(title, message)


class LoadingDialogManager:
    _instance = None

    def __init__(self):
        if LoadingDialogManager._instance is None:
            self.dialog = None
            self.layout = QtWidgets.QHBoxLayout()
            self.messageLabel = None
            self.titles = []
            self.messages = []
            self.timer = QtCore.QTimer()
            LoadingDialogManager._instance = self
            self.timer.setSingleShot(True)
            # self.timer.setInterval(1000)
            self.timer.timeout.connect(self.begin)

    @staticmethod
    def get_instance():
        if LoadingDialogManager._instance is None:
            LoadingDialogManager()
        return LoadingDialogManager._instance

    def begin(self):
        if len(self.messages) == 0:
            # logger_setup.get_logger().info('No messages to display, returning')
            return
        # logger_setup.get_logger().info(f'{self.messages} for more than 1 second, loading dialog')
        self.dialog = QtWidgets.QDialog()
        # Show the most recent title and message
        self.dialog.setWindowTitle(self.titles[-1])
        self.dialog.setMinimumSize(QSize(250, 75))
        self.dialog.setWindowFlags(
            self.dialog.windowFlags() | Qt.WindowType.Tool)  # Optional: Frameless and treated as a tool window
        self.layout = QtWidgets.QHBoxLayout(self.dialog)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)

        self.messageLabel = QLabel(self.messages[-1], parent=self.dialog)
        self.messageLabel.setObjectName('messageLabel')
        self.messageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.messageLabel, alignment=Qt.AlignmentFlag.AlignCenter)

        self.dialog.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.dialog.show()
        self.dialog.adjustSize()
        QtWidgets.QApplication.processEvents()

    def update_dialog(self):
        if self.dialog is not None:
            # logger_setup.get_logger().info('updating dialog')
            QtWidgets.QApplication.processEvents()

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
            self.dialog.adjustSize()
            # update_timer = QtCore.QTimer()
            # update_timer.setSingleShot(True)
            # update_timer.setInterval(1000)
            # update_timer.timeout.connect(self.update_dialog)
            # update_timer.start(0)
            QtWidgets.QApplication.processEvents()

    def close_loading_dialog(self, title: str, message: str):
        # logger_setup.get_logger().info(f'Closing loading dialog with title: {title} and message: {message}')
        # Check if the dialog exists and has the same title and message
        if len(self.messages) > 0:
            # Remove the title and message from the lists
            if message in self.messages:
                self.messages.remove(message)
                self.titles.remove(title)
        if self.dialog is not None:
            if len(self.messages) == 0:
                # logger_setup.get_logger().info('Closing loading dialog')
                # self.timer.stop()
                self.dialog.close()
                self.dialog = None
            else:
                # logger_setup.get_logger().info(f'Updating loading dialog with next message: {self.messages[-1]}')
                # Update the dialog with the next title and message
                self.dialog.setWindowTitle(self.titles[-1])
                self.messageLabel.setText(self.messages[-1])
                self.dialog.adjustSize()
                # update_timer = QtCore.QTimer()
                # update_timer.setSingleShot(True)
                # update_timer.setInterval(1000)
                # update_timer.timeout.connect(self.update_dialog)
                # update_timer.start(0)
                QtWidgets.QApplication.processEvents()
                QtWidgets.QApplication.processEvents()
        else:
            return

import builtins

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import QLabel, QStyle, QApplication

import logger_setup
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC

class LoadingDialogManager:
    _instance= None

    def __init__(self):
        if LoadingDialogManager._instance is None:
            # self.dialog = None
            self.dialog = None
            # self.thread = QtC.QThread()
            self.title = None
            self.message = None
            self.timer = QtC.QTimer()
            LoadingDialogManager._instance = self

    @staticmethod
    def get_instance():
        if LoadingDialogManager._instance is None:
            LoadingDialogManager()
        return LoadingDialogManager._instance

    def show_loading_dialog(self, title: str, message: str):
        if self.dialog is None:
            self.title = title
            self.message = message
            self.begin()
        else:
            return
        # self.timer.setSingleShot(True)
        # self.timer.setInterval(1000)
        # self.timer.timeout.connect(self.timeout)
        # logger_setup.get_logger().info(f'Starting timer for {message}')
        # self.timer.start()

    def begin(self):
        # logger_setup.get_logger().info(f'{self.message} for more than 1 second, loading dialog')
        self.dialog = QtW.QDialog()
        self.dialog.setWindowTitle(self.title)
        self.dialog.setFixedSize(QSize(250, 75))
        self.layout = QtW.QHBoxLayout(self.dialog)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.messageLabel = QLabel(self.message, parent=self.dialog)
        self.messageLabel.setObjectName('messageLabel')
        self.layout.addWidget(self.messageLabel, alignment=Qt.AlignmentFlag.AlignCenter)

        # self.dialog.setLabelText(self.message)
        # self.dialog.setBar(None)
        # self.dialog.setCancelButton(None)
        self.dialog.setWindowFlags(QtC.Qt.WindowType.WindowStaysOnTopHint)
        self.dialog.adjustSize()
        self.dialog.show()
        QtW.QApplication.processEvents()
        # self.timer.timeout.connect(self.update_dialog)
        # self.timer.start(1)
        # self.worker.moveToThread(self.thread)
        # self.thread.start()

    def update_dialog(self):
        if self.dialog is not None:
            logger_setup.get_logger().info('updating dialog')
            QtW.QApplication.processEvents()

    def close_loading_dialog(self, title: str, message: str):
        # Check if the dialog exists and has the same title and message
        if self.dialog is not None:
            if self.dialog.windowTitle() == title and self.dialog.findChild(QLabel, 'messageLabel').text() == message:
                # self.thread.quit()
                # self.thread.wait()
                self.dialog.close()
                self.dialog = None
                self.title = None
                self.message = None
        else:
            return

# class LoadingWorker(QtC.QObject):
#     def __init__(self):
#         super().__init__()
#         self.dialog = None
#
# class LoadingDialog(QtW.QDialog):
#     def __init__(self, title='Loading', message='Loading...'):
#         super().__init__()
#         self.setWindowTitle(title)
#         self.setLayout(QtW.QVBoxLayout())
#         self.message_label = QtW.QLabel(message)
#         self.layout().addWidget(self.message_label)
#         self.progress_bar = QtW.QProgressBar()
#         self.progress_bar.setRange(0, 0)
#         self.layout().addWidget(self.progress_bar)
#         # self.button_box = QtW.QDialogButtonBox(QtW.QDialogButtonBox.StandardButton.Cancel)
#         # self.layout().addWidget(self.button_box)
#         # self.button_box.rejected.connect(self.cancel)
#         self.setWindowFlags(self.windowFlags() | QtC.Qt.WindowType.WindowStaysOnTopHint)
#         self.setModal(True)

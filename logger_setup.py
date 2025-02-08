import logging
import logging.handlers
from datetime import datetime
from queue import Queue
import os

from PyQt6.QtCore import QSettings, QStandardPaths
from PyQt6.QtWidgets import QMessageBox

from Functions.Settings_manager import settings
from tzlocal import get_localzone

# Get the local timezone
local_timezone = get_localzone()

# Get the current timestamp in the local timezone
current_time = datetime.now(local_timezone)

# Format the timestamp
formatted_timestamp = current_time.strftime('%Y-%m-%d %H-%M-%S')

# Global references to the logger and queue listener
_logger = None
_queue_listener = None

# For convenience, define a constant for your logger’s name
class CustomLogger(logging.getLoggerClass()):
    """Custom logger that captures critical errors and shows a PyQt6 message box."""

    def critical(self, msg, *args, exc_info=None, stack_info=False, stacklevel=1, extra=None):
        QMessageBox.critical(None, 'Unexpected Critical Error', msg, QMessageBox.StandardButton.Ok)
        super().critical(msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra)

    def error(self, msg, *args, exc_info=None, stack_info=False, stacklevel=1, extra=None):
        QMessageBox.critical(None, 'Error', msg, QMessageBox.StandardButton.Ok)
        super().error(msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra)


def setup_async_logger():
    """
    Initializes the global logger and queue listener, setting the level
    from QSettings if available. Writes logs to both console and a file.
    """
    global _logger, _queue_listener
    LOGGER_NAME = "GeoCORKLogger"
    LOG_FILE = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation) + f"/logs/{formatted_timestamp}.log"  # The file to which we log
    log_dir = os.path.dirname(LOG_FILE)
    print("Log directory can be found at: ", log_dir)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    # If already set up, do nothing
    if _logger is not None:
        return

    # 1) Load the preferred log level from QSettings (default=INFO)
    saved_level_str = settings.value("debug_level", "DEBUG")
    numeric_level = getattr(logging, saved_level_str.upper(), logging.DEBUG)

    # 2) Create the global logger
    logging.setLoggerClass(CustomLogger)
    _logger = logging.getLogger(LOGGER_NAME)
    _logger.setLevel(numeric_level)

    # 3) Create the queue and attach a QueueHandler
    log_queue = Queue()
    queue_handler = logging.handlers.QueueHandler(log_queue)
    queue_handler.setLevel(numeric_level)
    _logger.addHandler(queue_handler)

    # Create a common formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(funcName)s: line %(lineno)d]: %(message)s"
    )

    # 4) Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)

    # 5) Create a file handler to save logs to a file
    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)

    # 6) Create and start a QueueListener in the background with both handlers
    _queue_listener = logging.handlers.QueueListener(log_queue, console_handler, file_handler)
    _queue_listener.start()


def get_logger() -> logging.Logger:
    """
    Returns the global logger instance. If it hasn't been set up yet, set it up now.
    """
    global _logger
    if _logger is None:
        setup_async_logger()
    return _logger


def set_logger_level(level_str: str):
    """
    Changes the global logger level at runtime and saves it to QSettings.
    """
    global _logger

    # Update QSettings
    settings = QSettings("MyCompany", "MyApp")
    settings.setValue("debug_level", level_str)

    # Convert string to numeric level
    numeric_level = getattr(logging, level_str.upper(), logging.INFO)

    # Update the logger's level
    if _logger is not None:
        _logger.setLevel(numeric_level)
        # Update each handler's level if you want them to match
        for handler in _logger.handlers:
            handler.setLevel(numeric_level)

        # Log a message indicating the level change
        _logger.info(f"Log level changed to: {level_str}")


def stop_logger():
    """
    Stops the queue listener so that all queued logs can be flushed.
    """
    global _queue_listener
    if _queue_listener:
        _queue_listener.stop()
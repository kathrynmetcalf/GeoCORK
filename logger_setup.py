import logging
import logging.handlers
import sys
import traceback
from datetime import datetime
from queue import Queue
import os

from PyQt6.QtCore import QSettings, QStandardPaths
from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtWidgets import QMessageBox, QApplication

import Savepoint_manager
from Functions.Settings_manager import SettingsManager
from Savepoint_manager import SavepointManager

settings = SettingsManager().settings
from tzlocal import get_localzone

# Get the local timezone
local_timezone = get_localzone()

# Get the current timestamp in the local timezone
current_time = datetime.now(local_timezone)

# Format the timestamp
formatted_timestamp = current_time.strftime('%Y-%m-%d %H.%M.%S')

# Global references to the logger and queue listener
_logger = None
_queue_listener = None

class CustomLogger(logging.getLoggerClass()):
    """Custom logger that captures critical errors and shows a PyQt6 message box."""

    def critical(self, msg, parent=None, *args, exc_info=None, stack_info=False, stacklevel=2, extra=None):
        button = QMessageBox.critical(parent,
                                      "Unexpected Critical Error",
                                      f"{msg}",
                                      buttons=QMessageBox.StandardButton.Ok,
                                      defaultButton=QMessageBox.StandardButton.Ok)

        super().critical(msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra)

    def error(self, msg, parent=None, *args, exc_info=None, stack_info=False, stacklevel=2, extra=None):
        button = QMessageBox.warning(parent,
                                      "Error",
                                      f"{msg}",
                                      buttons=QMessageBox.StandardButton.Ok,
                                      defaultButton=QMessageBox.StandardButton.Ok)

        super().error(msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra)


def setup_async_logger():
    """
    Initializes the global logger and queue listener, setting the level
    from QSettings if available. Writes logs to both console and a file.
    """
    global _logger, _queue_listener
    LOGGER_NAME = "GeoCORKLogger"
    LOG_FILE = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation) + f"/logs/{formatted_timestamp}.log"  # The file to which we log

    # Ensure the directory exists
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    if _logger is not None:
        return

    # Load the preferred log level from QSettings (default=INFO)
    settings.setValue("debug_level", "DEBUG")
    saved_level_str = settings.value("debug_level", "DEBUG")
    numeric_level = getattr(logging, saved_level_str.upper(), logging.DEBUG)

    # Create the global logger
    logging.setLoggerClass(CustomLogger)
    _logger = logging.getLogger(LOGGER_NAME)
    _logger.setLevel(numeric_level)

    # Create the queue and attach a QueueHandler
    log_queue = Queue()
    queue_handler = logging.handlers.QueueHandler(log_queue)
    queue_handler.setLevel(numeric_level)
    _logger.addHandler(queue_handler)

    # Create a common formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(funcName)s: line %(lineno)d]: %(message)s"
    )

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)

    # Create a file handler to save logs to a file
    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)

    # Create and start a QueueListener in the background with both handlers
    _queue_listener = logging.handlers.QueueListener(log_queue, console_handler, file_handler)
    _queue_listener.start()

    sys.excepthook = log_uncaught_exceptions


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

def _log_direct(level, message):
    # Bypass CustomLogger methods to avoid QMessageBox
    record = _logger.makeRecord(
        _logger.name, level, fn="", lno=0, msg=message, args=None, exc_info=None
    )
    for handler in _logger.handlers:
        handler.handle(record)

def log_uncaught_exceptions(exc_type, exc_value, exc_tb):
    """
    Called whenever an exception reaches the top of the interpreter.
    This guarantees the crash is logged before Python terminates.
    """
    message = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

    if _logger:
        _logger.critical(f"UNCAUGHT EXCEPTION:\n {message}")
        _logger.critical("Application will attempt to close gracefully.")
        # _log_direct(logging.CRITICAL, "UNCAUGHT EXCEPTION:\n" + message)

    # Force the listener to flush logs NOW
    try:
        if _queue_listener:
            _queue_listener.stop()
    except:
        pass

    try:
        savepoint_manager = SavepointManager.get_instance()

        if savepoint_manager is not None:
            if savepoint_manager.active_savepoints():
                _logger.critical("Active savepoints detected during crash, attempting to close application gracefully.")
                if len(savepoint_manager.active_savepoints_names > 0):
                    Savepoint_manager.rollback_savepoint[savepoint_manager.active_savepoints_names()[0]]
                QSqlDatabase().commit()
                QSqlDatabase().close()

        QApplication.quit()  # stops event loop
    except Exception:
        pass

    # Do NOT swallow exception — rethrow full crash
    sys.__excepthook__(exc_type, exc_value, exc_tb)
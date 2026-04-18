"""
sesar_logger.py
---------------
Dedicated logger for the SESAR → GeoCORK import pipeline.

Scope:
    Tracks everything from the moment ImportWizard hands off to ImportFromSesar
    through to the final import_staging_inplace() result. This includes API
    fetches, hierarchy exploration, JSON transforms, staging previews, and
    database inserts.

Why a separate logger?
    GeoCORK's main logger (Functions/logger_setup.py) handles application-wide
    events and pops up QMessageBoxes on errors. The SESAR pipeline already has
    its own user-facing error dialogs (via QMessageBox.critical in the UI
    files), so we don't want a second popup layer. We also don't want SESAR's
    per-IGSN chatter flooding the main GeoCORK console output when someone is
    doing a batch import of 50+ samples. Keeping the two loggers separate gives
    us:
      - A dedicated .log file per SESAR session (easy to hand to a collaborator
        for debugging)
      - No interference with GeoCORK's logger level or handlers
      - Freedom to time individual pipeline steps without the extra Qt overhead

Design mirror:
    Structure intentionally follows GeoCORK's logger_setup.py so anyone
    familiar with that file will recognize the patterns here:
      - Module-level singleton (_logger, _queue_listener)
      - setup_sesar_logger() / get_sesar_logger() / stop_sesar_logger()
      - Async QueueHandler + QueueListener pattern (UI-safe)
      - Logs written to QStandardPaths.AppDataLocation/logs/sesar_import/

Differences from GeoCORK's logger:
      - File-only handler by default (no console handler) — keeps the main
        GeoCORK console output clean. Flip _ENABLE_CONSOLE = True below if you
        want stdout mirroring during development.
      - No CustomLogger / QMessageBox layer — the UI files already show
        error popups, and doubling them would be confusing.
      - propagate = False — prevents log records from bubbling up to the
        root logger (which could otherwise cause duplicate file writes if
        the GeoCORK logger is ever reconfigured to add a root handler).

Timing helper:
    SesarTimer is a context manager around time.perf_counter() that logs
    start/end/duration at INFO level. Usage:

        with SesarTimer("SESAR API fetch", igsn=igsn):
            response = requests.get(...)

    Duration is always logged, even if an exception is raised inside the
    block — the exception message gets captured alongside the timing.
"""

import logging
import logging.handlers
import os
import time
import traceback
from contextlib import contextmanager
from datetime import datetime
from queue import Queue
from typing import Optional

from PyQt6.QtCore import QStandardPaths


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Name for getLogger() — lets us fetch the same logger from anywhere without
# re-initializing. Distinct from "GeoCORKLogger" so the two never collide.
_LOGGER_NAME = "SesarImportLogger"

# Subfolder within the GeoCORK app-data logs directory. Keeping SESAR logs in
# their own folder makes it trivial to zip them up and send to a collaborator
# without dragging along unrelated GeoCORK session logs.
_LOG_SUBFOLDER = "logs/sesar_import"

# Flip to True during development if you want log records echoed to stdout as
# well as the file. Kept False by default so normal users don't see SESAR
# chatter in the GeoCORK console.
_ENABLE_CONSOLE = False

# Default log level used the first time the logger is set up. DEBUG captures
# the most detail during the initial feature rollout; can be dialed back to
# INFO once the pipeline is stable.
_DEFAULT_LEVEL = logging.DEBUG

# Format mirrors GeoCORK's format but tags every line with [SESAR] so it's
# immediately obvious at a glance that these records came from this logger,
# not the main application logger.
_LOG_FORMAT = (
    "[%(asctime)s] [SESAR] [%(levelname)s] "
    "[%(filename)s:%(funcName)s: line %(lineno)d]: %(message)s"
)


# ---------------------------------------------------------------------------
# Module-level singletons (same pattern as logger_setup.py)
# ---------------------------------------------------------------------------

_logger: Optional[logging.Logger] = None
_queue_listener: Optional[logging.handlers.QueueListener] = None
_log_file_path: Optional[str] = None  # Kept around so callers can surface it


# ---------------------------------------------------------------------------
# Setup / teardown
# ---------------------------------------------------------------------------

def setup_sesar_logger() -> logging.Logger:
    """
    Initialize the SESAR logger and its background queue listener.

    Idempotent: calling this more than once is a no-op after the first call.
    This is important because multiple SESAR import sessions may start and
    stop within a single GeoCORK run, and we want them all writing to the
    same session log file rather than creating a new one each time.

    Returns:
        The initialized logger instance.
    """
    global _logger, _queue_listener, _log_file_path

    # Already set up — return the existing logger unchanged.
    if _logger is not None:
        return _logger

    # --- Resolve the log file path -----------------------------------------
    # Uses the same AppDataLocation root that GeoCORK's main logger uses, so
    # everything the app writes stays under a single user-visible folder.
    app_data_root = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation
    )
    log_dir = os.path.join(app_data_root, _LOG_SUBFOLDER)
    os.makedirs(log_dir, exist_ok=True)

    # Timestamp formatted identically to logger_setup.py so filenames sort
    # chronologically when both loggers' outputs sit in adjacent folders.
    timestamp = datetime.now().strftime("%Y-%m-%d %H.%M.%S")
    _log_file_path = os.path.join(log_dir, f"sesar_import_{timestamp}.log")

    # --- Build the logger --------------------------------------------------
    _logger = logging.getLogger(_LOGGER_NAME)
    _logger.setLevel(_DEFAULT_LEVEL)

    # Prevent messages from bubbling up to the root logger. Without this, if
    # the GeoCORK logger (or any other code) ever adds a handler to the root,
    # every SESAR record would be duplicated there too.
    _logger.propagate = False

    # --- Async queue + listener -------------------------------------------
    # Same pattern as logger_setup.py: the logger itself just drops records
    # into a Queue, and a background thread (QueueListener) pulls them out
    # and hands them to the real handlers. This keeps UI threads responsive
    # even when a big stack trace is being written to disk.
    log_queue: Queue = Queue()
    queue_handler = logging.handlers.QueueHandler(log_queue)
    queue_handler.setLevel(_DEFAULT_LEVEL)
    _logger.addHandler(queue_handler)

    formatter = logging.Formatter(_LOG_FORMAT)

    # File handler: where everything actually goes. Appends so re-opening
    # the same session logger doesn't truncate earlier records (though in
    # practice the singleton guard above prevents that from happening).
    file_handler = logging.FileHandler(_log_file_path, mode="a", encoding="utf-8")
    file_handler.setLevel(_DEFAULT_LEVEL)
    file_handler.setFormatter(formatter)

    # Optional console mirror for development.
    handlers: list[logging.Handler] = [file_handler]
    if _ENABLE_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(_DEFAULT_LEVEL)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    _queue_listener = logging.handlers.QueueListener(log_queue, *handlers)
    _queue_listener.start()

    # Kick things off with a session-start marker so a fresh log file always
    # has a clear "this is where things began" line at the top.
    _logger.info("=" * 70)
    _logger.info(f"SESAR import session started — log file: {_log_file_path}")
    _logger.info("=" * 70)

    return _logger


def get_sesar_logger() -> logging.Logger:
    """
    Return the SESAR logger, initializing it on first use.

    Lazy setup means callers can `from Sesar_Import.sesar_logger import
    get_sesar_logger` without worrying about import order — the logger won't
    actually touch the filesystem until someone logs their first message.
    """
    if _logger is None:
        return setup_sesar_logger()
    return _logger


def stop_sesar_logger() -> None:
    """
    Flush and stop the queue listener.

    Should be called on application shutdown (ideally hooked into whatever
    cleanup path GeoCORKMain uses) so any pending log records get written
    to disk before the process exits. Safe to call multiple times.
    """
    global _queue_listener, _logger
    if _queue_listener is not None:
        try:
            _logger.info("SESAR import session ending — flushing log queue.")
        except Exception:
            # If logging itself fails here there's nothing useful to do about
            # it — we're on the shutdown path. Swallow and move on.
            pass
        _queue_listener.stop()
        _queue_listener = None


def get_sesar_log_file_path() -> Optional[str]:
    """
    Return the absolute path of the currently active SESAR log file.

    Useful for surfacing "log saved to ..." messages in UI dialogs, or for
    letting the user copy the path into a bug report.
    """
    return _log_file_path


# ---------------------------------------------------------------------------
# Timing helper
# ---------------------------------------------------------------------------

@contextmanager
def SesarTimer(label: str, level: int = logging.INFO, **context):
    """
    Context manager that logs the start and duration of a named operation.

    Uses time.perf_counter() because it's the right clock for measuring
    short real-world durations (monotonic, highest available resolution) —
    time.time() would be wrong here because it can jump around if the system
    clock gets adjusted mid-operation.

    Any keyword arguments passed in (`igsn=`, `count=`, `db=`, etc.) are
    rendered into the log lines as "key=value" pairs so each timing record
    is self-describing without callers needing to format their own strings.

    The duration line is emitted whether the block succeeded or raised —
    on exception the line reads "FAILED" instead of "done" and the exception
    message is appended. The exception is re-raised afterwards so callers'
    own error handling still runs normally.

    Args:
        label:   Human-readable name for the operation (e.g., "SESAR API fetch").
        level:   Logging level for the start/end messages. Default INFO.
        context: Arbitrary key=value pairs to include in the log line.

    Example:
        with SesarTimer("SESAR API fetch", igsn=igsn):
            response = requests.get(url, params=params, timeout=15)
    """
    logger = get_sesar_logger()

    # Format the context dict into a single readable tail string.
    # Example: {"igsn": "ABC123", "count": 3} → " [igsn=ABC123, count=3]"
    ctx_str = ""
    if context:
        ctx_str = " [" + ", ".join(f"{k}={v}" for k, v in context.items()) + "]"

    logger.log(level, f"→ Starting: {label}{ctx_str}")
    start = time.perf_counter()

    try:
        yield
    except Exception as exc:
        # Compute duration even on failure so the log shows how long the
        # operation ran before it blew up. Useful for distinguishing a
        # timeout (slow) from a 400 (fast).
        elapsed = time.perf_counter() - start
        logger.error(
            f"✗ FAILED: {label}{ctx_str} after {elapsed:.3f}s "
            f"— {type(exc).__name__}: {exc}"
        )
        # Full traceback at DEBUG so it doesn't clutter INFO output, but is
        # still there when you dial the level down to investigate.
        logger.debug(traceback.format_exc())
        raise  # don't swallow — caller's own handler still needs to run
    else:
        elapsed = time.perf_counter() - start
        logger.log(level, f"✓ Finished: {label}{ctx_str} in {elapsed:.3f}s")


def log_sesar_event(message: str, level: int = logging.INFO, **context) -> None:
    """
    One-shot event logger with the same key=value context formatting as
    SesarTimer.

    Convenience for call sites that want the consistent "message [k=v, k=v]"
    style without wrapping anything in a timer. For example:

        log_sesar_event("Batch import confirmed", igsn_count=5)

    Keeps the log output uniformly scannable whether a line came from a
    timer or a plain event.
    """
    logger = get_sesar_logger()
    ctx_str = ""
    if context:
        ctx_str = " [" + ", ".join(f"{k}={v}" for k, v in context.items()) + "]"
    logger.log(level, f"{message}{ctx_str}")
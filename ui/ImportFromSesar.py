# ImportFromSesar.py
# Entry-point dialog for the IGSN-based import flow. Opened from ImportWizard.
#
# User flow:
#   1. User types an IGSN.
#   2. User clicks "Explore Hierarchy" (or presses Enter in the IGSN field)
#      — the dialog expands to reveal the SampleHierarchyWidget below.
#   3. SampleHierarchyWidget fetches the IGSN and its siblings from the SESAR
#      API, then lazy-loads children on expand. The user checks the samples
#      they want to import.
#   4. "Import Selected into GeoCORK" on SampleHierarchyWidget hands the
#      checked raw SESAR dicts to SesarImportWindow, which runs the
#      transform → preview → import pipeline without ever saving to disk.
#
# SampleHierarchyWidget features (bulk selection / download):
#   - Per-item checkboxes; Select All / Clear All buttons
#   - Selected-count label with color warning thresholds (orange at 10, red at 20)
#   - Batch import into GeoCORK, or per-item "Download IGSN Data" from the
#     right-click context menu (saves one JSON file per IGSN)
#   - Right-click menu also has Check / Uncheck actions
#
# Networking:
#   SampleHierarchyWidget uses synchronous requests.get() internally with an
#   in-memory cache. Acceptable because the explorer is separate from the
#   core import pipeline, and most expansions hit the cache.

import sys
import json
import requests
from pathlib import Path
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QTextEdit, QMessageBox,
                             QWidget, QSplitter, QTreeWidget, QTreeWidgetItem,
                             QMenu, QApplication, QProgressBar)
from PyQt6.QtGui import QAction

import pandas as pd

# ---------------------------------------------------------------------------
# Path bootstrap — ensure GeoCORK root is importable.
# ---------------------------------------------------------------------------
_UI_DIR       = Path(__file__).resolve().parent
_GEOCORK_ROOT = _UI_DIR.parent
if str(_GEOCORK_ROOT) not in sys.path:
    sys.path.insert(0, str(_GEOCORK_ROOT))

from ui.ImportFromSesarBuildWindow import SesarImportWindow


# ===========================================================================
# SampleHierarchyWidget
# Explores the parent / sibling / child relationships for a given IGSN.
# Uses its own synchronous requests.get() with an in-memory cache so that
# repeated expansions don't re-hit the network.
# ===========================================================================

class CheckableTreeWidgetItem(QTreeWidgetItem):
    #tree item with checkbox functionality
    
    def __init__(self, text):
        super().__init__()
        self.setText(0, text)
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.setCheckState(0, Qt.CheckState.Unchecked)


# ===========================================================================
# SiblingsFetchWorker
# Runs a single SESAR API fetch off the main thread so the UI can show a
# loading popup instead of freezing. Used by ImportFromSesar's Explore
# Hierarchy flow — i.e. the first (cold-cache) lookup for a given IGSN.
#
# Subsequent lazy-expand and per-IGSN save calls inside SampleHierarchyWidget
# still use the widget's own synchronous _fetch_sample_data() path, because
# those usually hit the in-memory cache and don't warrant the worker overhead.
# ===========================================================================

class SiblingsFetchWorker(QThread):
    """Background HTTP fetcher for a single IGSN lookup."""

    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)

    _URL = "https://app.geosamples.org/webservices/display.php"

    # Hard backstop on the underlying requests.get() call. Much longer than
    # any reasonable nag-prompt interval, so that if the user keeps clicking
    # "Keep Waiting" we don't get a spurious requests.Timeout racing against
    # the QTimer prompt. 600s = 10 minutes: effectively "don't interfere"
    # while still guaranteeing the worker thread eventually exits if the
    # socket is genuinely hung.
    _HARD_TIMEOUT_SECONDS = 600

    def __init__(self, igsn: str, parent=None):
        super().__init__(parent)
        self._igsn = igsn.strip()

        # When the UI cancels (user clicks X on the loading dialog, or the
        # nag prompt's Cancel button), we set this flag. The worker may still
        # be mid-flight inside requests.get() — we can't preempt that — but
        # once run() returns it checks this flag and suppresses the signal
        # emission so any late result doesn't trigger stale UI updates.
        self._cancelled = False

    def cancel(self) -> None:
        """Mark this worker as cancelled; late signals will be suppressed."""
        self._cancelled = True

    def run(self):
        try:
            response = requests.get(
                self._URL,
                params={"igsn": self._igsn},
                headers={"Accept": "application/json"},
                timeout=self._HARD_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.ConnectionError:
            if not self._cancelled:
                self.error.emit(
                    "Could not connect to the SESAR API.\n\n"
                    "Please check your internet connection and try again."
                )
            return
        except requests.exceptions.Timeout:
            if not self._cancelled:
                self.error.emit(
                    "The SESAR API did not respond within "
                    f"{self._HARD_TIMEOUT_SECONDS} seconds.\n\n"
                    "This usually means a server-side problem on SESAR's end. "
                    "Please try again later."
                )
            return
        except requests.exceptions.HTTPError as exc:
            if not self._cancelled:
                self.error.emit(f"SESAR API error: {exc}")
            return
        except Exception as exc:
            if not self._cancelled:
                self.error.emit(f"Unexpected error while fetching IGSN:\n\n{exc}")
            return

        # Success path — only emit if the UI still wants the result.
        if not self._cancelled:
            self.finished.emit(data)


# ===========================================================================
# SearchingDialog
# Modal loading popup shown while SiblingsFetchWorker is running.
#
# Design choices:
#   - No Cancel button. The user can dismiss it via the window X or Esc.
#   - Matches the visual style of GeoCORK's existing LoadingDialog (bold
#     title label + message label, no progress bar animation).
#   - Emits a single `cancelled` signal when the user dismisses it, so the
#     owner can tear down the worker + timer without this class needing
#     to know about them directly.
# ===========================================================================

class SearchingDialog(QDialog):
    """Modal 'Searching…' popup."""

    cancelled = pyqtSignal()

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Searching SESAR")
        self.setModal(True)
        self.setMinimumWidth(320)

        # Standard dialog frame so the window X is visible and usable.
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        self._label = QLabel(message)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        # Esc triggers QDialog.reject() by default. Funnel it through our
        # cancelled signal too, so Esc and the X button both reach the
        # same teardown path. closeEvent handles the X click; this handles
        # Esc (and any future programmatic reject() calls).
        self.rejected.connect(self.cancelled.emit)

    # --- Close (X button) ---------------------------------------------------

    def closeEvent(self, event):
        """
        User clicked the window X. Emit cancelled so the owner can tear
        down the worker and the nag timer, then let the close proceed.
        """
        self.cancelled.emit()
        super().closeEvent(event)

    # --- Helpers ------------------------------------------------------------

    def set_message(self, text: str) -> None:
        """Update the message text without recreating the dialog."""
        self._label.setText(text)


# ===========================================================================
# BatchSesarFetchWorker
# Runs an N-IGSN SESAR API fetch loop off the main thread so the UI can show
# a progress popup instead of freezing. Used by SampleHierarchyWidget's
# "Import Selected into GeoCORK" flow, which may fetch anywhere from 1 to
# dozens of IGSNs before handing the full raw-dict list to SesarImportWindow.
#
# Design notes:
#   - Accepts a shared cache dict (sibling_data) from SampleHierarchyWidget.
#     Already-cached IGSNs are skipped (no network call) but still emit a
#     progress tick so the UI counter advances smoothly.
#   - Emits `progress(current_index, total, igsn)` BEFORE each fetch so the
#     dialog can update "Current: <igsn>" before the request starts.
#   - Emits a single `finished(raw_list, failed_list)` at the end. Any
#     per-IGSN fetch failure is collected into failed_list rather than
#     aborting the whole batch — matches the behavior of the old synchronous
#     loop in _import_selected_to_geocork.
#   - Respects `_cancelled` between iterations. If the user clicks X on the
#     progress dialog mid-batch, the worker stops at the next iteration and
#     emits nothing (the UI-side cancellation handler tears everything down
#     without touching raw_data_list).
# ===========================================================================

class BatchSesarFetchWorker(QThread):
    """Background HTTP fetcher for a list of IGSNs."""

    # (current_index_1based, total_count, igsn_being_fetched)
    progress = pyqtSignal(int, int, str)
    # (list_of_raw_dicts_successfully_fetched, list_of_failed_igsns)
    finished = pyqtSignal(list, list)

    _URL = "https://app.geosamples.org/webservices/display.php"
    # Per-request timeout. Shorter than SiblingsFetchWorker's 600s because
    # we have N requests to get through and one hung request shouldn't
    # stall the entire batch for 10 minutes.
    _PER_REQUEST_TIMEOUT = 30

    def __init__(self, igsns: list, cache: dict, parent=None):
        """
        Parameters
        ----------
        igsns : list[str]
            The IGSNs to fetch, in display order.
        cache : dict
            Shared in-memory cache mapping igsn -> raw_data_dict. Read from
            for hits, written to for misses. This is the same dict owned by
            SampleHierarchyWidget.sibling_data, so cache entries added here
            remain available to subsequent explorer interactions.
        """
        super().__init__(parent)
        self._igsns     = list(igsns)
        self._cache     = cache
        self._cancelled = False

    def cancel(self) -> None:
        """Mark this worker as cancelled; the loop exits at the next iteration."""
        self._cancelled = True

    def run(self):
        total       = len(self._igsns)
        raw_list    = []
        failed_list = []

        for idx, igsn in enumerate(self._igsns, start=1):
            # Bail out at each iteration boundary if the UI cancelled.
            # We can't preempt a requests.get() mid-flight, but we can
            # avoid starting new ones.
            if self._cancelled:
                return

            # Emit progress BEFORE the fetch so the dialog can display
            # "Current: <igsn>" for the IGSN we're about to download.
            self.progress.emit(idx, total, igsn)

            # Cache hit — no network call needed.
            if igsn in self._cache:
                raw_list.append(self._cache[igsn])
                continue

            # Cache miss — fetch from SESAR.
            try:
                response = requests.get(
                    self._URL,
                    params={"igsn": igsn},
                    headers={"Accept": "application/json"},
                    timeout=self._PER_REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()
                self._cache[igsn] = data
                raw_list.append(data)
            except Exception:
                # Any failure — connection, HTTP error, timeout, bad JSON —
                # gets collected into failed_list so the UI can report the
                # full set of failures at the end instead of aborting the
                # first time something goes wrong.
                failed_list.append(igsn)

        # Final cancellation check — if the user clicked X right as the
        # last request returned, suppress the finished signal so we don't
        # trigger the preview window after the dialog is already gone.
        if self._cancelled:
            return

        self.finished.emit(raw_list, failed_list)


# ===========================================================================
# BatchDownloadDialog
# Modal progress popup shown while BatchSesarFetchWorker is downloading the
# selected IGSNs. Visually matches the screenshot spec: a header counter
# ("Downloading X of Y IGSNs…"), a current-IGSN label ("Current: …"),
# and a determinate progress bar.
#
# Like SearchingDialog, it emits a single `cancelled` signal when the user
# dismisses it (via X or Esc), so the owner can tear down the worker without
# this class needing to know about the worker directly.
# ===========================================================================

class BatchDownloadDialog(QDialog):
    """Modal 'Downloading N IGSNs…' popup with progress tracking."""

    cancelled = pyqtSignal()

    def __init__(self, total: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Downloading")
        self.setModal(True)
        self.setMinimumWidth(340)

        # Same window-flag stack as SearchingDialog for visual consistency:
        # visible title bar + X button, stays on top of the parent dialog.
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self._total = total

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        # Header: "Downloading X of Y IGSNs…"
        # Initialized at 1/total because progress.emit fires BEFORE each
        # fetch, so the very first tick will arrive as (1, total, igsn).
        self._header_label = QLabel(f"Downloading 1 of {total} IGSNs…")
        self._header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._header_label.setWordWrap(True)
        layout.addWidget(self._header_label)

        # Subheader: "Current: <igsn>"
        # Starts blank; filled in by the first update_progress call.
        self._current_label = QLabel("")
        self._current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._current_label.setWordWrap(True)
        layout.addWidget(self._current_label)

        # Determinate progress bar. Range is 0..total, so the bar fills
        # one notch per IGSN finished. We drive `setValue` from the
        # progress signal's current_index (1-based), which means the bar
        # sits one step ahead of visually-completed work — but since the
        # update arrives BEFORE the fetch, this actually matches the user's
        # intuition of "we're now working on item N".
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, total)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        # Funnel Esc (-> reject -> rejected signal) through our cancelled
        # signal so Esc and the X button both reach the same teardown path.
        self.rejected.connect(self.cancelled.emit)

    # --- Close (X button) ---------------------------------------------------

    def closeEvent(self, event):
        """User clicked the window X — emit cancelled before closing."""
        self.cancelled.emit()
        super().closeEvent(event)

    # --- Progress slot ------------------------------------------------------

    def update_progress(self, current: int, total: int, igsn: str) -> None:
        """
        Slot for BatchSesarFetchWorker.progress.

        Updates the header counter, the current-IGSN label, and the
        progress bar. `current` is 1-based (1..total).
        """
        self._header_label.setText(f"Downloading {current} of {total} IGSNs…")
        self._current_label.setText(f"Current: {igsn}")
        self._progress_bar.setValue(current)


class SampleHierarchyWidget(QWidget):
    """Widget for exploring IGSN parent/sibling/child relationships."""

    _URL = "https://app.geosamples.org/webservices/display.php"

    def __init__(self, parent=None, on_cancelled_callback=None):
        super().__init__(parent)
        self.current_igsn = None
        self.sibling_data = {}  # in-memory cache: igsn -> response dict
        # Forwarded from ImportFromSesar so that Back in PreviewWindow
        # re-shows the ImportFromSesar dialog correctly.
        self._on_cancelled_callback = on_cancelled_callback

        # ------------------------------------------------------------------
        # Batch-download state for "Import Selected into GeoCORK".
        #
        # Only one batch can be in flight at a time — the progress dialog
        # is modal, so the user can't click the Import button again until
        # the current batch finishes or is cancelled. So we only need one
        # slot each for the worker and the dialog.
        # ------------------------------------------------------------------
        self._batch_worker: BatchSesarFetchWorker | None = None
        self._batch_dialog: BatchDownloadDialog | None   = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Label showing which IGSN is currently displayed
        self.current_label = QLabel("No sample selected")
        layout.addWidget(self.current_label)

        #button layout for controls
        button_layout = QHBoxLayout()

        # Primary batch action: import all checked IGSNs into GeoCORK.
        # The disk-save path is still available via right-click context menu.
        self.download_selected_button = QPushButton("Import Selected into GeoCORK")
        self.download_selected_button.clicked.connect(self._import_selected_to_geocork)
        self.download_selected_button.setEnabled(False)
        button_layout.addWidget(self.download_selected_button)

        #select all button
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self._select_all)
        button_layout.addWidget(self.select_all_button)

        #clear all button
        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.clicked.connect(self._clear_all)
        button_layout.addWidget(self.clear_all_button)

        #selected count label
        self.selected_count_label = QLabel("Selected: 0")
        button_layout.addWidget(self.selected_count_label)

        layout.addLayout(button_layout)

        # Lazy-loading tree: top-level nodes are siblings; children expand on demand
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Sample Hierarchy")
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemChanged.connect(self._on_item_checked)
        layout.addWidget(self.tree)

        # Read-only text area for tabular relationship data
        self.table_text = QTextEdit()
        self.table_text.setReadOnly(True)
        layout.addWidget(self.table_text)

        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Checkbox helpers
    # ------------------------------------------------------------------
    
    def _get_checked_igsns(self):
        """collect all checked IGSNs from the tree"""
        checked_igsns = []
        
        def collect_checked(parent_item):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                igsn = child.text(0)
                if igsn != "No children found":
                    if child.checkState(0) == Qt.CheckState.Checked:
                        checked_igsns.append(igsn)
                    collect_checked(child)
        
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            igsn = item.text(0)
            if item.checkState(0) == Qt.CheckState.Checked:
                checked_igsns.append(igsn)
            collect_checked(item)
        
        return checked_igsns
    
    def _on_item_checked(self, item, column):
        """enable download button if any items are checked"""
        checked = self._get_checked_igsns()
        count = len(checked)
        self.download_selected_button.setEnabled(count > 0)
        self.selected_count_label.setText(f"Selected: {count}")
        
        #warning colors for rate limit awareness
        if count > 10:
            self.selected_count_label.setStyleSheet("color: orange")
        elif count > 20:
            self.selected_count_label.setStyleSheet("color: red")
        else:
            self.selected_count_label.setStyleSheet("")
    
    def _select_all(self):
        """check all IGSNs in the tree"""
        def select_all_items(parent_item):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                igsn = child.text(0)
                if igsn != "No children found":
                    child.setCheckState(0, Qt.CheckState.Checked)
                    select_all_items(child)
        
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setCheckState(0, Qt.CheckState.Checked)
            select_all_items(item)
        
        self.download_selected_button.setEnabled(True)
    
    def _clear_all(self):
        """uncheck all IGSNs in the tree"""
        def clear_all_items(parent_item):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                igsn = child.text(0)
                if igsn != "No children found":
                    child.setCheckState(0, Qt.CheckState.Unchecked)
                    clear_all_items(child)
        
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setCheckState(0, Qt.CheckState.Unchecked)
            clear_all_items(item)
        
        self.download_selected_button.setEnabled(False)
        self.selected_count_label.setText("Selected: 0")
        self.selected_count_label.setStyleSheet("")
    
    def _import_selected_to_geocork(self):
        """
        Fetch all checked IGSNs and pass the complete list of raw dicts to
        SesarImportWindow so they go through the normal transform → preview
        → import pipeline. Each IGSN becomes one independent sample in
        GeoCORK.

        The fetch itself runs on a background thread (BatchSesarFetchWorker)
        while a modal BatchDownloadDialog shows progress. This replaces the
        old synchronous loop that froze the UI while downloading.
        """
        checked_igsns = self._get_checked_igsns()
        if not checked_igsns:
            QMessageBox.warning(self, "No Selection",
                                "No IGSNs are checked for import.")
            return

        count = len(checked_igsns)
        if count <= 10:
            detail = "The following IGSNs will be imported:\n\n" + "\n".join(checked_igsns)
        else:
            detail = (
                f"The following IGSNs will be imported "
                f"(showing first 10 of {count}):\n\n"
                + "\n".join(checked_igsns[:10])
                + f"\n\n…and {count - 10} more"
            )

        confirm = QMessageBox(self)
        confirm.setWindowTitle("Confirm Batch Import")
        confirm.setIcon(QMessageBox.Icon.Question)
        confirm.setText(f"Import {count} IGSN(s) into GeoCORK?")
        confirm.setInformativeText(detail)
        confirm.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        confirm.setDefaultButton(QMessageBox.StandardButton.No)
        if confirm.exec() != QMessageBox.StandardButton.Yes:
            return

        # ------------------------------------------------------------------
        # Kick off the async download flow.
        #
        # Dialog + worker are both stored on self so the cancellation handler
        # (_on_batch_cancelled) can tear them down cleanly if the user
        # clicks X on the dialog partway through.
        #
        # The worker shares self.sibling_data as its cache — cache hits avoid
        # a network call but still emit a progress tick, and cache misses
        # populate the dict so subsequent explorer interactions see the data.
        # ------------------------------------------------------------------
        self._batch_dialog = BatchDownloadDialog(total=count, parent=self)
        self._batch_worker = BatchSesarFetchWorker(
            igsns=checked_igsns,
            cache=self.sibling_data,
            parent=self,
        )

        # Worker emits progress -> dialog updates counter/label/bar.
        self._batch_worker.progress.connect(self._batch_dialog.update_progress)
        # Worker emits finished -> we open the preview window (or show errors).
        self._batch_worker.finished.connect(self._on_batch_finished)
        # Dialog emits cancelled (X or Esc) -> we cancel the worker.
        self._batch_dialog.cancelled.connect(self._on_batch_cancelled)

        # Start the thread BEFORE exec'ing the dialog. exec() blocks this
        # method until the dialog is closed — either by us calling accept()
        # in _on_batch_finished, or by the user cancelling.
        self._batch_worker.start()
        self._batch_dialog.exec()

    def _on_batch_finished(self, raw_data_list, failed):
        """
        Slot for BatchSesarFetchWorker.finished.

        Called on the main thread once every IGSN has been attempted.
        Closes the progress dialog, reports any failures, and hands the
        successful raw dicts off to SesarImportWindow — the same handoff
        the old synchronous method did, just moved here.
        """
        # Close the progress dialog. accept() exits the exec() blocking
        # call in _import_selected_to_geocork, but we guard against None
        # in case cancellation beat us to the punch.
        if self._batch_dialog is not None:
            self._batch_dialog.accept()
            self._batch_dialog = None
        # Worker has already finished its run loop; drop the reference.
        self._batch_worker = None

        if failed:
            QMessageBox.warning(
                self, "Fetch Errors",
                f"Could not retrieve data for {len(failed)} IGSN(s):\n\n"
                + "\n".join(failed)
                + "\n\nThe rest will still be previewed."
            )

        if not raw_data_list:
            QMessageBox.critical(self, "No Data",
                                 "No data could be fetched for the selected IGSNs.")
            return

        # [SESAR DEBUG] Entry point into the batch-import handoff.
        # Shows (a) how many samples we have, (b) what parent we're about to
        # pass to SesarImportWindow, (c) whether that parent is visible.
        _dbg_parent = self.parent()
        print(f"[SESAR DEBUG] _import_selected_to_geocork: "
              f"raw_data_list len={len(raw_data_list)}, "
              f"parent={type(_dbg_parent).__name__ if _dbg_parent else None}, "
              f"parent.isVisible()="
              f"{_dbg_parent.isVisible() if _dbg_parent else 'N/A'}", flush=True)

        build_win = SesarImportWindow(
            raw_data_list=raw_data_list,
            parent=self.parent(),
            on_cancelled=self._on_cancelled_callback,
        )

    def _on_batch_cancelled(self):
        """
        Slot for BatchDownloadDialog.cancelled.

        User clicked X or pressed Esc on the progress dialog. Cancel the
        worker (it will stop at its next iteration boundary), drop our
        references, and do NOT open the preview window — the user is
        backing out of the whole batch.

        The worker may finish one more in-flight requests.get() before
        seeing the _cancelled flag, but its finished signal is suppressed
        inside run() so _on_batch_finished won't fire.
        """
        if self._batch_worker is not None:
            self._batch_worker.cancel()
            # We don't wait() here because the worker may be mid-request;
            # letting it finish naturally on its own thread is fine since
            # it won't emit any signals after cancel().
            self._batch_worker = None
        # Dialog is closing itself (closeEvent is what triggered us);
        # just drop the reference so future imports get a fresh one.
        self._batch_dialog = None

    # ------------------------------------------------------------------
    # Network helpers
    # ------------------------------------------------------------------

    def _fetch_sample_data(self, igsn):
        """Return cached data for *igsn*, fetching from SESAR if not yet cached."""
        if igsn in self.sibling_data:
            return self.sibling_data[igsn]

        try:
            response = requests.get(
                self._URL,
                params={"igsn": igsn},
                headers={"Accept": "application/json"},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            self.sibling_data[igsn] = data
            return data
        except Exception:
            return None

    def _save_sample_data(self, igsn, show_message=True):
        """Fetch *igsn* and write it to a local JSON file (context-menu action)."""
        data = self._fetch_sample_data(igsn)
        if not data:
            if show_message:
                QMessageBox.warning(self, "Download Failed", f"Could not fetch data for {igsn}")
            return False

        safe_igsn = igsn.replace("/", "_")
        filename  = f"sesar_{safe_igsn}.json"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            if show_message:
                QMessageBox.information(self, "Download Complete", f"Data saved to {filename}")
            return True
        except IOError as e:
            if show_message:
                QMessageBox.critical(self, "Save Failed", f"Could not save file: {e}")
            return False

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return

        igsn = item.text(0)
        if igsn == "No children found":
            return

        menu = QMenu()
        download_action = QAction("Download IGSN Data", self)
        download_action.triggered.connect(lambda: self._save_sample_data(igsn))
        menu.addAction(download_action)
        
        #add checkbox toggle options
        menu.addSeparator()
        check_action = QAction("Check this item", self)
        check_action.triggered.connect(lambda: item.setCheckState(0, Qt.CheckState.Checked))
        menu.addAction(check_action)
        
        uncheck_action = QAction("Uncheck this item", self)
        uncheck_action.triggered.connect(lambda: item.setCheckState(0, Qt.CheckState.Unchecked))
        menu.addAction(uncheck_action)
        
        menu.exec(self.tree.viewport().mapToGlobal(position))

    # ------------------------------------------------------------------
    # Data-extraction helpers
    # ------------------------------------------------------------------

    def _get_siblings_table(self, data):
        """Return a list of {ItemID, ParentID, ParentRow} dicts for siblings."""
        rows = []
        try:
            parent_igsn  = data.get("sample", {}).get("parent_igsn", None)
            sibling_info = data.get("sample", {}).get("siblings", {})
            sibling_data = sibling_info.get("samples", {}).get("sample", [])

            # Single sibling comes back as a dict, not a list
            if not isinstance(sibling_data, list):
                sibling_data = [sibling_data] if sibling_data else []

            for index, sibling in enumerate(sibling_data):
                if isinstance(sibling, dict) and "igsn" in sibling:
                    rows.append({
                        "ItemID":    sibling["igsn"],
                        "ParentID":  parent_igsn,
                        "ParentRow": index,
                    })
        except Exception:
            pass
        return rows

    def _add_current_sample_to_table(self, rows, current_igsn, parent_igsn):
        """Prepend the current sample row to the siblings list."""
        return [{"ItemID": current_igsn, "ParentID": parent_igsn, "ParentRow": None}] + rows

    def _get_children_table(self, data):
        """Return a list of {ItemID, ParentID, ParentRow} dicts for children."""
        rows = []
        try:
            current_igsn  = data.get("sample", {}).get("igsn")
            children_info = data.get("sample", {}).get("children", {})
            children_data = children_info.get("samples", {}).get("sample", [])

            # Single child comes back as a dict, not a list
            if not isinstance(children_data, list):
                children_data = [children_data] if children_data else []

            for index, child in enumerate(children_data):
                if isinstance(child, dict) and "igsn" in child:
                    rows.append({
                        "ItemID":    child["igsn"],
                        "ParentID":  current_igsn,
                        "ParentRow": index,
                    })
        except Exception:
            pass
        return rows

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def _display_table_text(self, rows, title):
        """Append a formatted relationship table to the text area."""
        if not rows:
            self.table_text.append(f"\nNo {title.lower()} found")
            return

        df   = pd.DataFrame(rows)
        text = f"\n{'='*60}\n{title}\n{'='*60}\n"
        text += f"\nTotal rows: {len(df)}\n"
        text += "\nIdx | ItemID                          | ParentID                      | ParentRow\n"
        text += "-" * 90 + "\n"

        for idx, row in df.iterrows():
            item_id    = row["ItemID"]
            parent_id  = row["ParentID"] if row["ParentID"] else "None"
            parent_row = row["ParentRow"] if pd.notna(row["ParentRow"]) else "None"
            text += f"{idx:<3} | {item_id:<30} | {parent_id:<30} | {parent_row}\n"

        self.table_text.append(text)

    # ------------------------------------------------------------------
    # Tree population / lazy loading
    # ------------------------------------------------------------------

    def _load_children_into_tree(self, parent_item, igsn):
        """Fetch children for *igsn* and populate *parent_item* in the tree."""
        data = self._fetch_sample_data(igsn)
        if not data:
            return

        children = self._get_children_table(data)
        parent_item.takeChildren()  # remove the placeholder dummy child

        if not children:
            no_child_item = QTreeWidgetItem(parent_item)
            no_child_item.setText(0, "No children found")
            self.table_text.append(f"\nNo children found for {igsn}")
        else:
            for child in children:
                child_item = CheckableTreeWidgetItem(child["ItemID"])
                parent_item.addChild(child_item)
                child_item.setData(0, Qt.ItemDataRole.UserRole, child)
                # Dummy child so the expand arrow is shown; replaced on expansion
                child_item.addChild(QTreeWidgetItem())
            self._display_table_text(children, f"CHILDREN OF {igsn}")

    def _on_item_expanded(self, item):
        """Load real children when the user expands a tree node for the first time."""
        if item.childCount() > 0 and item.child(0).text(0) == "":
            self._load_children_into_tree(item, item.text(0))

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def load_siblings(self, igsn):
        """Populate the tree and text area for *igsn* and its siblings."""
        self.current_igsn = igsn
        self.current_label.setText(f"Current Sample: {igsn}")
        self.table_text.clear()
        self.tree.clear()
        self.selected_count_label.setText("Selected: 0")
        self.download_selected_button.setEnabled(False)

        data = self._fetch_sample_data(igsn)
        if not data:
            self.table_text.append("Failed to fetch data")
            return

        parent_igsn          = data.get("sample", {}).get("parent_igsn", None)
        siblings             = self._get_siblings_table(data)
        siblings_with_current = self._add_current_sample_to_table(siblings, igsn, parent_igsn)

        if not siblings_with_current:
            self.table_text.append("No siblings found")
            return

        self._display_table_text(siblings_with_current, f"SIBLINGS TABLE (Current: {igsn})")

        for row in siblings_with_current:
            item = CheckableTreeWidgetItem(row["ItemID"])
            self.tree.addTopLevelItem(item)
            item.setData(0, Qt.ItemDataRole.UserRole, row)
            item.addChild(QTreeWidgetItem())  # dummy child for expand arrow


# ===========================================================================
# Main dialog
# ===========================================================================

class ImportFromSesar(QDialog):
    """
    Entry-point dialog for the IGSN-based import flow.
    Opened by ImportWizard.open_import_sesar().

    Workflow:
      1. User types an IGSN into the input field.
      2. User clicks "Explore Hierarchy" (or presses Enter in the IGSN field).
         The dialog expands and reveals the SampleHierarchyWidget below.
      3. SampleHierarchyWidget loads the IGSN's siblings and lazy-loads
         children on expand. The user checks the samples to import.
      4. "Import Selected into GeoCORK" inside SampleHierarchyWidget hands
         the checked raw SESAR dicts to SesarImportWindow for the
         transform → preview → import pipeline.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import from SESAR (IGSN)")
        # Dialog opens compact — just room for the title, IGSN input, and
        # buttons. It expands to ~850px tall when the user toggles Explore
        # Hierarchy on (handled in _on_explore_toggled).
        self.setMinimumSize(600, 200)
        self.setModal(True)

        # ------------------------------------------------------------------
        # State for the "Searching SESAR…" flow.
        #
        # Only one search can be in flight at a time — the Explore Hierarchy
        # button is disabled while one is active, and the user can't reach
        # _on_igsn_entered because the modal SearchingDialog blocks input to
        # the rest of the app. So we only need slots for one worker, one
        # dialog, and one nag-timer at a time.
        #
        # _pending_explore_igsn holds the IGSN we're currently fetching, so
        # that when the worker finishes we know which IGSN to hand to
        # SampleHierarchyWidget.load_siblings().
        # ------------------------------------------------------------------
        self._explore_worker: SiblingsFetchWorker | None = None
        self._explore_dialog: SearchingDialog | None     = None
        self._explore_nag_timer: QTimer | None           = None
        self._pending_explore_igsn: str | None           = None

        # ------------------------------------------------------------------
        # Root layout contains a vertical splitter so the hierarchy explorer
        # can expand below the top controls without disturbing them.
        # ------------------------------------------------------------------
        root_layout = QVBoxLayout()

        splitter = QSplitter(Qt.Orientation.Vertical)

        # ---- Top pane: IGSN input and action buttons -----------------------
        fetch_widget = QWidget()
        fetch_layout = QVBoxLayout()
        fetch_widget.setLayout(fetch_layout)

        # Title
        title_label = QLabel("Import Sample Data from SESAR")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fetch_layout.addWidget(title_label)

        # IGSN input row. Pressing Enter here is a shortcut for clicking
        # Explore Hierarchy — the single path forward from this dialog.
        igsn_layout = QHBoxLayout()
        igsn_label  = QLabel("IGSN:")
        self.igsn_input = QLineEdit()
        self.igsn_input.setPlaceholderText("e.g., 10.58052/IENWUC821")
        self.igsn_input.returnPressed.connect(self._on_igsn_entered)
        igsn_layout.addWidget(igsn_label)
        igsn_layout.addWidget(self.igsn_input)
        fetch_layout.addLayout(igsn_layout)

        # Button row
        button_layout = QHBoxLayout()

        # Shows/hides the SampleHierarchyWidget pane below
        self.explore_button = QPushButton("Explore Hierarchy")
        self.explore_button.setCheckable(True)
        self.explore_button.clicked.connect(self._on_explore_toggled)
        button_layout.addWidget(self.explore_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)

        fetch_layout.addLayout(button_layout)

        splitter.addWidget(fetch_widget)

        # ---- Bottom pane: hierarchy explorer (hidden by default) -----------
        self.explorer_widget = SampleHierarchyWidget(
            on_cancelled_callback=self._on_preview_cancelled
        )
        self.explorer_widget.setVisible(False)
        splitter.addWidget(self.explorer_widget)

        root_layout.addWidget(splitter)
        self.setLayout(root_layout)

    # ------------------------------------------------------------------
    # IGSN input handling
    # ------------------------------------------------------------------

    def _on_igsn_entered(self):
        """
        Called when the user presses Enter in the IGSN input field.

        Enter is a shortcut for clicking Explore Hierarchy: if it isn't
        already open we toggle it on (which loads the entered IGSN); if
        it's already open we reload it with the current IGSN value so the
        user can type a new IGSN and press Enter to re-explore.
        """
        if not self.explore_button.isChecked():
            # Not yet open — click the button. This fires clicked(True) which
            # routes through _on_explore_toggled and handles the "missing IGSN"
            # warning, the setVisible(True), and the resize-to-850 in one place.
            self.explore_button.click()
        else:
            # Already open — just reload with the new IGSN, matching the
            # behavior of _on_explore_toggled's "checked" branch but without
            # toggling the button off and on.
            igsn = self.igsn_input.text().strip()
            if not igsn:
                QMessageBox.warning(
                    self, "Missing IGSN",
                    "Please enter an IGSN."
                )
                return
            self.explorer_widget.load_siblings(igsn)

    def _on_preview_cancelled(self):
        """Called by SesarImportWindow when the user pressed Back."""
        self.show()

    # ------------------------------------------------------------------
    # Explore Hierarchy slot
    # ------------------------------------------------------------------

    # How long to wait before showing the "taking longer than expected"
    # nag prompt. Each time the user clicks Keep Waiting, the timer resets
    # and another interval of this length has to pass.
    _EXPLORE_NAG_INTERVAL_MS = 30_000   # 30 seconds

    def _on_explore_toggled(self, checked: bool):
        """
        Toggle the hierarchy explorer pane.

        On check-on, this kicks off an async fetch of the IGSN's siblings
        and shows a modal SearchingDialog while it runs. On check-off,
        it simply hides the explorer pane (no network activity to cancel
        at that point — the pane being visible means a previous fetch
        already completed successfully).
        """
        if not checked:
            # Hide-only path. If a fetch is still in flight we'd be in the
            # modal SearchingDialog, which the user can't interact with
            # the toggle-off from, so reaching here means nothing is
            # running and we just hide.
            self.explorer_widget.setVisible(False)
            return

        igsn = self.igsn_input.text().strip()
        if not igsn:
            QMessageBox.warning(
                self, "Missing IGSN",
                "Please enter an IGSN first, then click Explore Hierarchy."
            )
            self.explore_button.setChecked(False)
            return

        # If the IGSN is already in the SampleHierarchyWidget's cache, we
        # can skip the whole loading-dialog dance and render immediately.
        # This makes re-opening a previously-explored IGSN feel instant.
        if igsn in self.explorer_widget.sibling_data:
            self._show_hierarchy_for(igsn)
            return

        # Cold cache — run the async fetch with loading popup + nag timer.
        self._start_explore_fetch(igsn)

    # ------------------------------------------------------------------
    # Async Explore-Hierarchy flow
    # ------------------------------------------------------------------

    def _start_explore_fetch(self, igsn: str) -> None:
        """Spin up the worker, loading dialog, and nag timer for one search."""
        # Remember which IGSN we're fetching — the worker emits the raw
        # data dict on success, but not the IGSN, so we need our own copy.
        self._pending_explore_igsn = igsn

        # Disable the Explore button during the search so the user can't
        # double-click into two overlapping fetches.
        self.explore_button.setEnabled(False)

        # Build the modal "Searching…" popup.
        self._explore_dialog = SearchingDialog(
            f"Looking up samples for IGSN:\n{igsn}",
            parent=self,
        )
        # User clicks the window X -> emitted here -> we tear everything down.
        self._explore_dialog.cancelled.connect(self._on_explore_cancelled_by_user)

        # Build the worker. Parenting to self gives the thread a Qt owner so
        # it lives at least as long as this dialog does, even if the user
        # closes the main window mid-fetch.
        self._explore_worker = SiblingsFetchWorker(igsn, parent=self)
        self._explore_worker.finished.connect(self._on_explore_fetch_done)
        self._explore_worker.error.connect(self._on_explore_fetch_error)

        # 30s nag timer. singleShot=True means it fires once; if the user
        # clicks Keep Waiting we manually restart it for another interval.
        self._explore_nag_timer = QTimer(self)
        self._explore_nag_timer.setSingleShot(True)
        self._explore_nag_timer.setInterval(self._EXPLORE_NAG_INTERVAL_MS)
        self._explore_nag_timer.timeout.connect(self._on_explore_nag_fired)

        # Kick it all off.
        self._explore_worker.start()
        self._explore_nag_timer.start()
        self._explore_dialog.show()

    def _on_explore_fetch_done(self, data: dict) -> None:
        """Worker success path: cache the data and show the hierarchy."""
        igsn = self._pending_explore_igsn
        self._teardown_explore_fetch()

        if igsn is None:
            # Shouldn't happen — teardown clears this, but if we got a late
            # signal after a prior teardown, drop it quietly.
            return

        # Prime the explorer widget's cache so its internal _fetch_sample_data
        # hits the cache instead of re-fetching. This is how we avoid having
        # to refactor SampleHierarchyWidget to take an already-fetched dict.
        self.explorer_widget.sibling_data[igsn] = data
        self._show_hierarchy_for(igsn)

    def _on_explore_fetch_error(self, msg: str) -> None:
        """Worker error path: tear down and show the error to the user."""
        self._teardown_explore_fetch()
        QMessageBox.critical(
            self, "Search Error",
            f"Failed to fetch data from SESAR:\n\n{msg}"
        )
        # Leave explore_button unchecked (it was un-toggled during teardown)
        # so the user can fix the IGSN and try again.

    def _on_explore_cancelled_by_user(self) -> None:
        """
        User clicked the window X on the SearchingDialog.

        We tear down the worker (marks it cancelled so late signals are
        suppressed) and leave the explorer pane hidden. No error popup —
        user-initiated cancels are silent.
        """
        # Avoid re-entering teardown if this fires while we're already
        # tearing down (e.g. the error path just closed the dialog).
        if self._explore_dialog is None:
            return
        self._teardown_explore_fetch()

    def _on_explore_nag_fired(self) -> None:
        """
        The 30s nag timer elapsed with no result yet. Show a non-modal
        prompt that lets the user either keep waiting (reset the timer)
        or cancel the search.

        This prompt is parented to the main ImportFromSesar dialog, NOT to
        the SearchingDialog, because the SearchingDialog is modal and a
        modal-over-modal stack can get weird with focus and close handling.
        By parenting to self the nag sits alongside (on top of) the
        SearchingDialog in the window stack.
        """
        if self._explore_dialog is None:
            # Teardown already happened — nothing to nag about. Defensive.
            return

        prompt = QMessageBox(self)
        prompt.setWindowTitle("Taking longer than expected")
        prompt.setIcon(QMessageBox.Icon.Question)
        prompt.setText(
            "The SESAR search is taking longer than expected."
        )
        prompt.setInformativeText(
            "This may be a problem with SESAR's servers on their end.\n\n"
            "Keep waiting, or cancel the search?"
        )
        keep_btn   = prompt.addButton("Keep Waiting", QMessageBox.ButtonRole.AcceptRole)
        cancel_btn = prompt.addButton("Cancel",       QMessageBox.ButtonRole.RejectRole)
        prompt.setDefaultButton(keep_btn)
        prompt.exec()

        # If the user made the nag appear but then the search happened to
        # complete while they were reading the prompt, the worker's
        # finished/error slot already ran teardown and cleared the dialog.
        # Check again before acting on the user's click.
        if self._explore_dialog is None:
            return

        if prompt.clickedButton() is cancel_btn:
            self._teardown_explore_fetch()
        else:
            # Keep Waiting — reset the nag timer for another full interval.
            # The worker's own hard timeout (see SiblingsFetchWorker._HARD_
            # TIMEOUT_SECONDS) still applies as the ultimate backstop.
            if self._explore_nag_timer is not None:
                self._explore_nag_timer.start()

    def _teardown_explore_fetch(self) -> None:
        """
        Common cleanup for all four exit paths (success, error, user X,
        nag-cancel). Idempotent — safe to call even if some state is
        already None.
        """
        # Stop and release the nag timer.
        if self._explore_nag_timer is not None:
            self._explore_nag_timer.stop()
            self._explore_nag_timer.deleteLater()
            self._explore_nag_timer = None

        # Mark the worker cancelled. If it's still running (e.g. user clicked
        # X before the network returned), _cancelled suppresses late signals
        # so they don't re-trigger this teardown. We don't wait() or
        # terminate() — the thread will clean itself up when requests.get
        # returns or hits its hard timeout.
        if self._explore_worker is not None:
            self._explore_worker.cancel()
            # Disconnect to be doubly safe — even if the flag check in
            # run() somehow misses, disconnected signals go nowhere.
            try:
                self._explore_worker.finished.disconnect()
                self._explore_worker.error.disconnect()
            except TypeError:
                # Already disconnected or never connected — safe to ignore.
                pass
            self._explore_worker = None

        # Close and release the loading dialog. Disconnect its cancelled
        # signal first so close()->closeEvent() doesn't re-enter this
        # teardown via _on_explore_cancelled_by_user.
        if self._explore_dialog is not None:
            try:
                self._explore_dialog.cancelled.disconnect()
            except TypeError:
                pass
            self._explore_dialog.close()
            self._explore_dialog.deleteLater()
            self._explore_dialog = None

        self._pending_explore_igsn = None

        # Re-enable the Explore button and un-check it so the user is back
        # to the "not exploring" visual state. The explorer pane stays
        # hidden; it'll only be shown on a successful fetch (via
        # _show_hierarchy_for, called before teardown in the success path).
        self.explore_button.setEnabled(True)
        self.explore_button.setChecked(False)

    def _show_hierarchy_for(self, igsn: str) -> None:
        """
        Reveal the SampleHierarchyWidget pane and populate it for `igsn`.
        Assumes the IGSN's raw data is already in the widget's cache —
        either because we just primed it from a successful fetch, or
        because a previous successful fetch cached it during this session.
        """
        self.explorer_widget.setVisible(True)
        self.explore_button.setChecked(True)
        self.explorer_widget.load_siblings(igsn)
        # Expand the dialog so the explorer has room
        if self.height() < 800:
            self.resize(self.width(), 850)
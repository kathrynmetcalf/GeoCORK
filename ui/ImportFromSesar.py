"""
ImportFromSesar.py
------------------
Entry-point dialog for the IGSN-based import flow. Opened from ImportWizard.

User flow:
    1. User types an IGSN.
    2. User clicks "Explore Hierarchy" (or presses Enter in the IGSN field)
       — the dialog expands to reveal the SampleHierarchyWidget below.
    3. SampleHierarchyWidget fetches the IGSN and its siblings from the SESAR
       API, then lazy-loads children on expand. The user checks the samples
       they want to import.
    4. "Import Selected into GeoCORK" on SampleHierarchyWidget hands the
       checked raw SESAR dicts to SesarImportWindow, which runs the
       transform → preview → import pipeline without ever saving to disk.

SampleHierarchyWidget features:
    - Per-item checkboxes; Select All / Clear All buttons
    - Selected-count label with color warning thresholds (orange at 10, red at 20)
    - Batch import into GeoCORK, or per-item "Download IGSN Data" from the
      right-click context menu (saves one JSON file per IGSN)
    - Right-click menu also has Check / Uncheck actions

Networking:
    SampleHierarchyWidget uses synchronous requests.get() internally with an
    in-memory cache. Acceptable because the explorer is separate from the
    core import pipeline, and most expansions hit the cache.
"""

import sys
import json
import logging
import time
import requests
from pathlib import Path
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QMessageBox,
                             QWidget, QSplitter, QTreeWidget, QTreeWidgetItem,
                             QMenu, QApplication)
from PyQt6.QtGui import QAction

# ---------------------------------------------------------------------------
# Path bootstrap — ensure GeoCORK root is importable.
# ---------------------------------------------------------------------------
_UI_DIR       = Path(__file__).resolve().parent
_GEOCORK_ROOT = _UI_DIR.parent
if str(_GEOCORK_ROOT) not in sys.path:
    sys.path.insert(0, str(_GEOCORK_ROOT))

from ui.ImportFromSesarBuildWindow import SesarImportWindow, LoadingDialog

# SESAR-specific logger. get_sesar_logger() returns the currently-active
# session logger (set up by ImportWizard.open_import_sesar); SesarTimer is a
# context manager that logs start/end/duration of a named operation.
from Sesar_Import.sesar_logger import get_sesar_logger, SesarTimer, log_sesar_event


# ===========================================================================
# Background worker
# ===========================================================================

class SiblingsFetchWorker(QThread):
    """
    Runs a single SESAR API fetch off the main thread so the UI can show a
    loading popup instead of freezing. Used by ImportFromSesar's Explore
    Hierarchy flow — i.e. the first (cold-cache) lookup for a given IGSN.

    Subsequent lazy-expand and per-IGSN save calls inside SampleHierarchyWidget
    still use the widget's own synchronous _fetch_sample_data() path, because
    those usually hit the in-memory cache and don't warrant the worker overhead.
    """

    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)

    _URL = "https://app.geosamples.org/sample/igsn"

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
                # self._URL,
                # params={"igsn": self._igsn},
                f"{self._URL}/{self._igsn}",
                headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                
                timeout=self._HARD_TIMEOUT_SECONDS,
                allow_redirects=True,
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
# Loading dialog
# ===========================================================================

class SearchingDialog(QDialog):
    """
    Modal loading popup shown while SiblingsFetchWorker is running.

    Design choices:
      - No Cancel button. The user can dismiss it via the window X or Esc.
      - Matches the visual style of GeoCORK's existing LoadingDialog (bold
        title label + message label, no progress bar animation).
      - Emits a single `cancelled` signal when the user dismisses it, so the
        owner can tear down the worker + timer without this class needing
        to know about them directly.
    """

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
# Hierarchy explorer widget
# ===========================================================================

class CheckableTreeWidgetItem(QTreeWidgetItem):
    """
    QTreeWidgetItem subclass with a checkbox enabled by default.
    Used by SampleHierarchyWidget to let users select IGSNs for import.
    """

    def __init__(self, text):
        super().__init__()
        self.setText(0, text)
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.setCheckState(0, Qt.CheckState.Unchecked)


class SampleHierarchyWidget(QWidget):
    """Widget for exploring IGSN parent/sibling/child relationships."""

    _URL = "https://app.geosamples.org/sample/igsn"

    def __init__(self, parent=None, on_cancelled_callback=None):
        super().__init__(parent)
        self.current_igsn = None
        self.sibling_data = {}  # in-memory cache: igsn -> response dict
        # Forwarded from ImportFromSesar so that Back in PreviewWindow
        # re-shows the ImportFromSesar dialog correctly.
        self._on_cancelled_callback = on_cancelled_callback
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Label showing which IGSN is currently displayed
        self.current_label = QLabel("No sample selected")
        layout.addWidget(self.current_label)

        button_layout = QHBoxLayout()

        # Primary batch action: import all checked IGSNs into GeoCORK.
        # The disk-save path is still available via right-click context menu.
        self.download_selected_button = QPushButton("Import Selected into GeoCORK")
        self.download_selected_button.clicked.connect(self._import_selected_to_geocork)
        self.download_selected_button.setEnabled(False)
        button_layout.addWidget(self.download_selected_button)

        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self._select_all)
        button_layout.addWidget(self.select_all_button)

        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.clicked.connect(self._clear_all)
        button_layout.addWidget(self.clear_all_button)

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

        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Checkbox helpers
    # ------------------------------------------------------------------
    
    def _get_checked_igsns(self):
        """Return a list of all checked IGSN strings from the tree."""
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
        """Enable import button and update selected count when items are checked."""
        checked = self._get_checked_igsns()
        count = len(checked)
        self.download_selected_button.setEnabled(count > 0)
        self.selected_count_label.setText(f"Selected: {count}")

        # Color warning thresholds for rate-limit awareness.
        # Orange at 10+ selected, red at 20+ selected.
        if count >= 20:
            self.selected_count_label.setStyleSheet("color: red")
        elif count >= 10:
            self.selected_count_label.setStyleSheet("color: orange")
        else:
            self.selected_count_label.setStyleSheet("")
    
    def _select_all(self):
        """Check all IGSN items in the tree."""
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
        """Uncheck all IGSN items in the tree."""
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

    # ------------------------------------------------------------------
    # Duplicate-IGSN check against the currently-open GeoCORK database.
    # ------------------------------------------------------------------
    def _find_existing_igsns_in_db(self, igsns):
        """
        Query the currently-open GeoCORK database for any IGSNs in `igsns`
        that are already present in the Samples table.

        We use QSqlDatabase.database() (the default connection) rather than
        requiring the caller to pass one — this is the same pattern
        Database_manager.py uses throughout. It returns the connection that
        GeoCORKMain opened for the current DB, which is what we want: the
        user is about to import into that same DB.

        Args:
            igsns: list of IGSN strings to check.

        Returns:
            (existing_set, error_message)
              existing_set    — set of IGSN strings that were found.
                                Empty set on clean "no duplicates" result.
              error_message   — None on success, or a short human-readable
                                error string if the query couldn't run
                                (DB not open, query failed, etc.). Caller
                                should fail hard on any non-None error —
                                if we can't verify, we shouldn't import.
        """
        if not igsns:
            return set(), None

        db = QSqlDatabase.database()
        if not db.isValid() or not db.isOpen():
            return set(), "The GeoCORK database is not currently open."

        # Build a parameterized IN-clause. Using placeholders instead of
        # string interpolation is important both for SQL safety and because
        # IGSNs can contain characters like '/' that don't need escaping
        # but look messy in logs. Qt's QSqlQuery with positional '?'
        # placeholders handles this cleanly.
        placeholders = ",".join(["?"] * len(igsns))
        sql = f"SELECT SampleIGSN FROM Samples WHERE SampleIGSN IN ({placeholders})"

        query = QSqlQuery(db)
        if not query.prepare(sql):
            return set(), f"Could not prepare duplicate-check query: {query.lastError().text()}"

        for igsn in igsns:
            query.addBindValue(igsn)

        if not query.exec():
            return set(), f"Duplicate-check query failed: {query.lastError().text()}"

        # Collect results. The SELECT returns one row per matching IGSN;
        # put them in a set so membership testing is O(1) for the caller.
        existing = set()
        while query.next():
            value = query.value(0)
            if value is not None:
                existing.add(str(value))

        return existing, None

    def _import_selected_to_geocork(self):
        """
        Fetch all checked IGSNs (using the in-memory cache where possible),
        then pass the complete list of raw dicts to SesarImportWindow so
        they go through the normal transform → preview → import pipeline.
        Each IGSN becomes one independent sample in GeoCORK.
        """
        checked_igsns = self._get_checked_igsns()
        if not checked_igsns:
            get_sesar_logger().info(
                "Batch import clicked but no IGSNs are checked — aborting."
            )
            QMessageBox.warning(self, "No Selection",
                                "No IGSNs are checked for import.")
            return

        total_checked = len(checked_igsns)

        # Log the full list of IGSNs the user checked — before any filtering,
        # because "what did the user ask for" is a different question from
        # "what ended up getting imported."
        get_sesar_logger().info(
            f"Batch import requested [count={total_checked}]\n"
            + "\n".join(f"  - {igsn}" for igsn in checked_igsns)
        )

        # ----------------------------------------------------------------
        # Decision 1: Run the duplicate-IGSN check against the GeoCORK DB
        # BEFORE the confirm dialog, so the confirm dialog can show which
        # ones will be skipped.
        # ----------------------------------------------------------------
        existing_set, query_error = self._find_existing_igsns_in_db(checked_igsns)

        # Decision 3 (Q3 fail-hard): if the query couldn't run, refuse to
        # proceed. We can't verify uniqueness, and blind-importing could
        # create inconsistent rows. Better a clear error now than a subtle
        # data issue later.
        if query_error is not None:
            get_sesar_logger().error(
                f"Duplicate-IGSN pre-check failed — aborting import. "
                f"Reason: {query_error}"
            )
            QMessageBox.critical(
                self, "Database Error",
                f"Could not check for duplicate IGSNs:\n\n{query_error}\n\n"
                f"Import has been cancelled."
            )
            return

        # Partition the user's selection into two ordered lists. Ordered so
        # the confirm dialog shows them in the same order the user saw them
        # in the hierarchy tree, not in set-iteration order.
        to_import = [i for i in checked_igsns if i not in existing_set]
        to_skip   = [i for i in checked_igsns if i in existing_set]

        # Log the partition result — companion to the "requested" line above.
        get_sesar_logger().info(
            f"Duplicate check complete "
            f"[requested={total_checked}, to_import={len(to_import)}, "
            f"already_in_db={len(to_skip)}]"
        )
        if to_skip:
            get_sesar_logger().info(
                "Skipping (already in database):\n"
                + "\n".join(f"  - {igsn}" for igsn in to_skip)
            )

        # ----------------------------------------------------------------
        # Decision 4: ALL selected IGSNs are duplicates → info dialog only,
        # no confirm step, no import.
        # ----------------------------------------------------------------
        if not to_import:
            info = QMessageBox(self)
            info.setWindowTitle("Nothing to Import")
            info.setIcon(QMessageBox.Icon.Information)
            info.setText(
                f"All {total_checked} selected IGSN(s) are already in the database."
            )
            info.setInformativeText(
                "Already present:\n\n" + "\n".join(f"    {i}" for i in to_skip)
            )
            info.setStandardButtons(QMessageBox.StandardButton.Ok)
            info.exec()
            get_sesar_logger().info(
                "All selected IGSNs were duplicates — nothing imported."
            )
            return

        # ----------------------------------------------------------------
        # Decision 5: Confirm dialog shows both the to-import list and the
        # skipped list (if any). Button text is still Yes/No.
        # ----------------------------------------------------------------
        to_import_count = len(to_import)

        # Build the informative-text body. Truncate long lists at 10 entries
        # each to keep the dialog readable.
        def _format_list(items, max_shown=10):
            if len(items) <= max_shown:
                return "\n".join(f"    {i}" for i in items)
            shown = "\n".join(f"    {i}" for i in items[:max_shown])
            return shown + f"\n    …and {len(items) - max_shown} more"

        detail_parts = [
            "The following IGSNs will be imported:",
            _format_list(to_import),
        ]
        if to_skip:
            detail_parts.append("")  # blank line separator
            detail_parts.append("Skipped (already in database):")
            detail_parts.append(_format_list(to_skip))
        detail = "\n".join(detail_parts)

        confirm = QMessageBox(self)
        confirm.setWindowTitle("Confirm Batch Import")
        confirm.setIcon(QMessageBox.Icon.Question)
        confirm.setText(f"Import {to_import_count} IGSN(s) into GeoCORK?")
        confirm.setInformativeText(detail)
        confirm.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        confirm.setDefaultButton(QMessageBox.StandardButton.No)
        if confirm.exec() != QMessageBox.StandardButton.Yes:
            get_sesar_logger().info(
                "User cancelled at the batch-import confirmation dialog"
            )
            return

        # Show a progress dialog immediately so the user has visual feedback
        # during the synchronous download loop. LoadingDialog.set_message()
        # calls processEvents() internally, so the label repaints after each
        # IGSN without blocking the event loop.
        download_dlg = LoadingDialog(
            "Downloading",
            f"Downloading 1 of {to_import_count} IGSNs…",
            self,
        )

        raw_data_list = []
        failed = []
        cached_count = 0
        fetched_count = 0

        with SesarTimer("Batch pre-fetch for import", igsn_count=to_import_count):
            for idx, igsn in enumerate(to_import, start=1):
                download_dlg.set_message(
                    f"Downloading {idx} of {to_import_count} IGSNs…\n"
                    f"Current: {igsn}"
                )
                was_cached = igsn in self.sibling_data
                data = self._fetch_sample_data(igsn)
                if data:
                    raw_data_list.append(data)
                    if was_cached:
                        cached_count += 1
                        log_sesar_event(
                            "Batch pre-fetch: cache hit",
                            level=logging.DEBUG, igsn=igsn,
                        )
                    else:
                        fetched_count += 1
                        log_sesar_event(
                            "Batch pre-fetch: network fetch OK",
                            level=logging.DEBUG, igsn=igsn,
                        )
                else:
                    failed.append(igsn)
                    log_sesar_event(
                        "Batch pre-fetch: FAILED",
                        level=logging.DEBUG, igsn=igsn,
                    )

        # INFO-level summary — the single line most users will care about
        # when skimming the log.
        get_sesar_logger().info(
            f"Batch pre-fetch summary "
            f"[total={to_import_count}, cached={cached_count}, "
            f"fetched={fetched_count}, failed={len(failed)}]"
        )
        if failed:
            get_sesar_logger().warning(
                f"Failed IGSNs ({len(failed)}):\n"
                + "\n".join(f"  - {igsn}" for igsn in failed)
            )

        if failed:
            # Close the download dialog before showing the warning popup
            # so the two don't stack on screen.
            download_dlg.close()
            QMessageBox.warning(
                self, "Fetch Errors",
                f"Could not retrieve data for {len(failed)} IGSN(s):\n\n"
                + "\n".join(failed)
                + "\n\nThe rest will still be previewed."
            )

        if not raw_data_list:
            get_sesar_logger().error(
                "Batch import aborted — no IGSN fetches succeeded"
            )
            download_dlg.close()
            QMessageBox.critical(self, "No Data",
                                 "No data could be fetched for the selected IGSNs.")
            return

        get_sesar_logger().info(
            f"Handing {len(raw_data_list)} sample(s) to SesarImportWindow "
            f"for transform+preview+import"
        )

        # Pass the already-visible download dialog to SesarImportWindow so it
        # can reuse it for the transform phase — the user sees a single
        # seamless dialog that transitions from "Downloading…" to
        # "Transforming SESAR data…" without any gap.
        build_win = SesarImportWindow(
            raw_data_list=raw_data_list,
            parent=self.parent(),
            on_cancelled=self._on_cancelled_callback,
            loading_dlg=download_dlg,
        )

    # ------------------------------------------------------------------
    # Network helpers
    # ------------------------------------------------------------------

    def _fetch_sample_data(self, igsn):
        """Return cached data for *igsn*, fetching from SESAR if not yet cached."""
        if igsn in self.sibling_data:
            return self.sibling_data[igsn]

        try:
            response = requests.get(
                # self._URL,
                # params={"igsn": igsn},
                f"{self._URL}/{igsn}",
                headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                
                timeout=60,
                allow_redirects=True,
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

        menu.addSeparator()
        check_action = QAction("Check this item", self)
        check_action.triggered.connect(lambda: item.setCheckState(0, Qt.CheckState.Checked))
        menu.addAction(check_action)
        
        uncheck_action = QAction("Uncheck this item", self)
        uncheck_action.triggered.connect(lambda: item.setCheckState(0, Qt.CheckState.Unchecked))
        menu.addAction(uncheck_action)
        
        menu.exec(self.tree.viewport().mapToGlobal(position))

    # ------------------------------------------------------------------
    # Tree population / lazy loading
    # ------------------------------------------------------------------

    def _load_children_into_tree(self, parent_item, igsn):
        """Fetch children for *igsn* and populate *parent_item* in the tree."""
        data = self._fetch_sample_data(igsn)
        if not data:
            return

        children_info = data.get("sample", {}).get("children", {})
        children_data = children_info.get("samples", {}).get("sample", [])
        if not isinstance(children_data, list):
            children_data = [children_data] if children_data else []

        children = [
            {"ItemID": c["igsn"], "ParentID": igsn, "ParentRow": i}
            for i, c in enumerate(children_data)
            if isinstance(c, dict) and "igsn" in c
        ]

        parent_item.takeChildren()  # remove the placeholder dummy child

        if not children:
            no_child_item = QTreeWidgetItem(parent_item)
            no_child_item.setText(0, "No children found")
        else:
            for child in children:
                child_item = CheckableTreeWidgetItem(child["ItemID"])
                parent_item.addChild(child_item)
                child_item.setData(0, Qt.ItemDataRole.UserRole, child)
                # Dummy child so the expand arrow is shown; replaced on expansion
                child_item.addChild(QTreeWidgetItem())

    def _on_item_expanded(self, item):
        """Load real children when the user expands a tree node for the first time."""
        if item.childCount() > 0 and item.child(0).text(0) == "":
            self._load_children_into_tree(item, item.text(0))

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def load_siblings(self, igsn):
        """Populate the tree with *igsn* and its siblings."""
        self.current_igsn = igsn
        self.current_label.setText(f"Current Sample: {igsn}")
        self.tree.clear()
        self.selected_count_label.setText("Selected: 0")
        self.download_selected_button.setEnabled(False)

        data = self._fetch_sample_data(igsn)
        if not data:
            return

        parent_igsn  = data.get("sample", {}).get("parent_igsn", None)
        sibling_info = data.get("sample", {}).get("siblings", {})
        sibling_data = sibling_info.get("samples", {}).get("sample", [])
        if not isinstance(sibling_data, list):
            sibling_data = [sibling_data] if sibling_data else []

        # Build the full row list: current sample first, then its siblings
        rows = [{"ItemID": igsn, "ParentID": parent_igsn, "ParentRow": None}]
        for index, sibling in enumerate(sibling_data):
            if isinstance(sibling, dict) and "igsn" in sibling:
                rows.append({
                    "ItemID":    sibling["igsn"],
                    "ParentID":  parent_igsn,
                    "ParentRow": index,
                })

        for row in rows:
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

        # First log entry of the SESAR import session. The logger itself is
        # already set up by ImportWizard.open_import_sesar (which ran just
        # before this constructor was called), so get_sesar_logger() returns
        # the live session logger here.
        get_sesar_logger().info("ImportFromSesar dialog opened")

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
        log_sesar_event(
            "User pressed Enter on IGSN input",
            level=logging.DEBUG,
            igsn=self.igsn_input.text().strip() or "<empty>",
            explore_already_open=self.explore_button.isChecked(),
        )
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

        # Stash a start timestamp so the matching done/error handler can
        # compute elapsed time. perf_counter is monotonic and the right
        # clock for short real-world durations. Stored on self rather than
        # closed over because the fetch is asynchronous — the handler runs
        # on a different stack frame in response to a Qt signal.
        self._explore_fetch_started_at = time.perf_counter()

        get_sesar_logger().info(
            f"Explore-Hierarchy fetch starting [igsn={igsn}]"
        )

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
        # Compute elapsed from the timestamp stashed by _start_explore_fetch.
        # Using getattr with a default handles the (unlikely) case where a
        # late signal arrives after teardown has cleared the attribute.
        elapsed_ms = (time.perf_counter()
                      - getattr(self, "_explore_fetch_started_at", 0)) * 1000
        get_sesar_logger().info(
            f"Explore-Hierarchy fetch succeeded "
            f"[igsn={igsn}, elapsed_ms={elapsed_ms:.1f}]"
        )

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
        igsn = self._pending_explore_igsn
        elapsed_ms = (time.perf_counter()
                      - getattr(self, "_explore_fetch_started_at", 0)) * 1000
        get_sesar_logger().error(
            f"Explore-Hierarchy fetch FAILED "
            f"[igsn={igsn}, elapsed_ms={elapsed_ms:.1f}] — {msg}"
        )
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

        igsn = self._pending_explore_igsn
        elapsed_ms = (time.perf_counter()
                      - getattr(self, "_explore_fetch_started_at", 0)) * 1000
        get_sesar_logger().info(
            f"Explore-Hierarchy fetch CANCELLED by user "
            f"[igsn={igsn}, elapsed_ms={elapsed_ms:.1f}]"
        )
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

        igsn = self._pending_explore_igsn
        get_sesar_logger().info(
            f"30-second nag prompt shown [igsn={igsn}]"
        )

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
            get_sesar_logger().info(
                f"User cancelled fetch via nag prompt [igsn={igsn}]"
            )
            self._teardown_explore_fetch()
        else:
            # Keep Waiting — reset the nag timer for another full interval.
            # The worker's own hard timeout (see SiblingsFetchWorker._HARD_
            # TIMEOUT_SECONDS) still applies as the ultimate backstop.
            get_sesar_logger().info(
                f"User chose Keep Waiting — resetting 30s nag timer [igsn={igsn}]"
            )
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
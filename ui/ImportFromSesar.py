"""
ImportFromSesar.py
------------------
Entry-point dialog for importing SESAR samples into GeoCORK. Opened from
ImportWizard.open_import_sesar().

Uses the SESAR REST API (see Sesar_Import/sesar_api_client.py):
    GET samples/?q=...          search (public, or your own samples with a JWT)
    GET samples/{igsn}/         fetch full detail when the IGSN is known

User flow:
    1. Type a search (IGSN fragment or sample name) and press Enter / Search,
       optionally narrowing by scope, object type, or country.
       — or — type a full IGSN and click "Fetch IGSN" to go straight to it.
    2. Results appear in a paged table. Check the samples to import; checks
       persist across pages.
    3. "Import Selected into GeoCORK" skips IGSNs already in the open
       database, fetches full detail for the rest in a background thread,
       then hands the raw dicts to SesarImportWindow
       (transform → preview → import).

    "Send GeoCORK Samples to SESAR…" opens SesarExportWindow for the reverse
    direction (PATCH existing IGSNs / register new ones).

Replaces the old "Explore Hierarchy" tree: the new API has no siblings /
children data (only a flat `parent_sample`), which is shown as a column.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QDesktopServices, QGuiApplication
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import (QAbstractItemView, QComboBox, QDialog, QFileDialog,
                             QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMenu,
                             QMessageBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)

# ---------------------------------------------------------------------------
# Path bootstrap — ensure GeoCORK root is importable.
# ---------------------------------------------------------------------------
_UI_DIR       = Path(__file__).resolve().parent
_GEOCORK_ROOT = _UI_DIR.parent
if str(_GEOCORK_ROOT) not in sys.path:
    sys.path.insert(0, str(_GEOCORK_ROOT))

from ui.ImportFromSesarBuildWindow import SesarImportWindow, LoadingDialog
from Sesar_Import import sesar_api_client as api
from Sesar_Import.sesar_logger import get_sesar_logger, log_sesar_event


# ===========================================================================
# Background workers
# ===========================================================================

class ApiCallWorker(QThread):
    """
    Runs one SesarApiClient call off the UI thread.

    `succeeded` carries the call's return value; `failed` carries the
    SesarApiError (or any exception) so the slot can show `.details()`.
    `cancel()` suppresses late signals if the dialog moved on.
    """
    succeeded = pyqtSignal(object)
    failed    = pyqtSignal(object)

    def __init__(self, fn, *args, parent=None, **kwargs):
        super().__init__(parent)
        self._fn, self._args, self._kwargs = fn, args, kwargs
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            result = self._fn(*self._args, **self._kwargs)
        except Exception as exc:  # SesarApiError subclasses included
            if not self._cancelled:
                self.failed.emit(exc)
            return
        if not self._cancelled:
            self.succeeded.emit(result)


class DetailFetchWorker(QThread):
    """
    Fetches full sample detail (GET samples/{igsn}/) for a list of IGSNs.

    Emits `progress(index, total, igsn)` before each fetch and
    `done(results, failures)` at the end, where results is a list of
    (igsn, detail_dict) and failures a list of (igsn, message).
    Already-cached IGSNs are passed in and skipped.
    """
    progress = pyqtSignal(int, int, str)
    done     = pyqtSignal(list, list)

    def __init__(self, client: api.SesarApiClient, igsns: List[str],
                 cache: Dict[str, dict], parent=None):
        super().__init__(parent)
        self._client = client
        self._igsns = list(igsns)
        self._cache = dict(cache)

    def run(self):
        results, failures = [], []
        total = len(self._igsns)
        for idx, igsn in enumerate(self._igsns, start=1):
            self.progress.emit(idx, total, igsn)
            if igsn in self._cache:
                results.append((igsn, self._cache[igsn]))
                log_sesar_event("Detail fetch: cache hit", level=logging.DEBUG, igsn=igsn)
                continue
            try:
                results.append((igsn, self._client.get_sample(igsn)))
                log_sesar_event("Detail fetch: OK", level=logging.DEBUG, igsn=igsn)
            except api.SesarApiError as exc:
                failures.append((igsn, exc.message))
                log_sesar_event(f"Detail fetch FAILED — {exc.message}",
                                level=logging.WARNING, igsn=igsn)
            except Exception as exc:
                failures.append((igsn, str(exc)))
                log_sesar_event(f"Detail fetch FAILED — {exc}",
                                level=logging.WARNING, igsn=igsn)
        self.done.emit(results, failures)


# ===========================================================================
# Search widget
# ===========================================================================

_SCOPES = [
    ("Public samples",            "public"),
    ("My samples (incl. drafts)", "personal"),
    ("Shared with me",            "shared"),
    ("Mine + shared",             "personal_and_shared"),
]

# (header, extractor) for the results table. Column 0 holds the checkbox.
_RESULT_COLUMNS = [
    ("IGSN",         lambda s: s.get("igsn")),
    ("Name",         lambda s: s.get("name")),
    ("Object type",  lambda s: s.get("object_type")),
    ("Material",     lambda s: s.get("general_material_type") or s.get("sample_material")),
    ("Country",      lambda s: s.get("country")),
    ("Locality",     lambda s: s.get("locality") or s.get("primary_location_name")),
    ("Parent IGSN",  lambda s: s.get("parent_sample")),
    ("Draft",        lambda s: "Yes" if str(s.get("is_draft")).lower() == "true" else ""),
]


def _cell_text(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, dict):
        return str(value.get("label") or value.get("name") or "")
    if isinstance(value, list):
        return "; ".join(_cell_text(v) for v in value)
    return str(value)


class SampleSearchWidget(QWidget):
    """Search SESAR, pick samples, import them into GeoCORK."""

    def __init__(self, parent=None, on_cancelled_callback=None):
        super().__init__(parent)
        self._on_cancelled_callback = on_cancelled_callback
        self._checked: Dict[str, dict] = {}        # igsn -> summary row (persists across pages)
        self.detail_cache: Dict[str, dict] = {}    # igsn -> full detail dict
        self._rows: List[dict] = []                # current page
        self._page = 1
        self._last_query: Dict[str, Any] = {}
        self._last_page: Optional[api.SearchPage] = None
        self._worker: Optional[QThread] = None
        self._populating = False
        self._build_ui()
        self.refresh_auth_state()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        layout = QVBoxLayout(self)

        row1 = QHBoxLayout()
        self.query_edit = QLineEdit()
        self.query_edit.setPlaceholderText(
            "Search IGSN or sample name — or paste a full IGSN, e.g. 10.58052/IENWUC821")
        self.query_edit.returnPressed.connect(self._on_search_clicked)
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self._on_search_clicked)
        self.fetch_btn = QPushButton("Fetch IGSN")
        self.fetch_btn.setToolTip("Fetch one sample directly by its IGSN (GET samples/{igsn}/)")
        self.fetch_btn.clicked.connect(self._on_fetch_igsn_clicked)
        row1.addWidget(QLabel("Search:"))
        row1.addWidget(self.query_edit, 1)
        row1.addWidget(self.search_btn)
        row1.addWidget(self.fetch_btn)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.scope_combo = QComboBox()
        for label, value in _SCOPES:
            self.scope_combo.addItem(label, value)
        self.object_type_edit = QLineEdit()
        self.object_type_edit.setPlaceholderText("e.g. Core, Individual sample")
        self.country_edit = QLineEdit()
        self.country_edit.setPlaceholderText("ISO codes, e.g. US,CA")
        self.country_edit.setMaximumWidth(140)
        self.page_size_combo = QComboBox()
        for n in (25, 50, 100, 250, 500):
            self.page_size_combo.addItem(str(n), n)
        row2.addWidget(QLabel("Scope:"))
        row2.addWidget(self.scope_combo)
        row2.addWidget(QLabel("Object type:"))
        row2.addWidget(self.object_type_edit, 1)
        row2.addWidget(QLabel("Country:"))
        row2.addWidget(self.country_edit)
        row2.addWidget(QLabel("Per page:"))
        row2.addWidget(self.page_size_combo)
        layout.addLayout(row2)

        self.table = QTableWidget(0, len(_RESULT_COLUMNS))
        self.table.setHorizontalHeaderLabels([h for h, _ in _RESULT_COLUMNS])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.table, 1)

        nav = QHBoxLayout()
        self.status_label = QLabel("Enter a search to begin.")
        self.prev_btn = QPushButton("◀ Prev")
        self.prev_btn.clicked.connect(lambda: self._run_search(self._page - 1))
        self.page_label = QLabel("")
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.clicked.connect(lambda: self._run_search(self._page + 1))
        nav.addWidget(self.status_label, 1)
        nav.addWidget(self.prev_btn)
        nav.addWidget(self.page_label)
        nav.addWidget(self.next_btn)
        layout.addLayout(nav)

        actions = QHBoxLayout()
        self.import_btn = QPushButton("Import Selected into GeoCORK")
        self.import_btn.clicked.connect(self._import_selected_to_geocork)
        self.select_page_btn = QPushButton("Select Page")
        self.select_page_btn.clicked.connect(lambda: self._set_page_checked(True))
        self.clear_btn = QPushButton("Clear Selection")
        self.clear_btn.clicked.connect(self._clear_all)
        self.selected_count_label = QLabel("Selected: 0")
        actions.addWidget(self.import_btn)
        actions.addWidget(self.select_page_btn)
        actions.addWidget(self.clear_btn)
        actions.addStretch()
        actions.addWidget(self.selected_count_label)
        layout.addLayout(actions)

        self._update_nav(None)
        self._update_selected_count()

    # ------------------------------------------------------------- helpers
    @staticmethod
    def _client() -> api.SesarApiClient:
        # Built per action so Settings changes (environment, tokens) apply
        # immediately without reopening the dialog.
        return api.SesarApiClient.from_settings()

    def refresh_auth_state(self):
        """Disable scopes that need a JWT when none is configured."""
        try:
            has_token = self._client().has_credentials()
        except Exception:
            has_token = False
        model = self.scope_combo.model()
        for i in range(1, self.scope_combo.count()):
            item = model.item(i)
            item.setEnabled(has_token)
            item.setToolTip("" if has_token else
                            "Requires a SESAR JWT — add tokens in Settings → SESAR")
        if not has_token:
            self.scope_combo.setCurrentIndex(0)

    def _set_busy(self, busy: bool, message: str = ""):
        for w in (self.search_btn, self.fetch_btn, self.import_btn,
                  self.prev_btn, self.next_btn, self.query_edit):
            w.setEnabled(not busy)
        if message:
            self.status_label.setText(message)
        if not busy:
            self._update_nav(None)
            self._update_selected_count()

    def _start_worker(self, worker: QThread):
        if self._worker is not None and hasattr(self._worker, "cancel"):
            self._worker.cancel()
        self._worker = worker
        worker.finished.connect(worker.deleteLater)
        worker.start()

    # -------------------------------------------------------------- search
    def _on_search_clicked(self):
        self._last_query = {
            "q": self.query_edit.text().strip() or None,
            "object_type": self.object_type_edit.text().strip() or None,
            "country": self.country_edit.text().strip().upper() or None,
            "scope": self.scope_combo.currentData(),
            "page_size": self.page_size_combo.currentData(),
        }
        # "public" is the API default without a token; only send scope when
        # the user picked something else (with a token the default is personal).
        if self._last_query["scope"] == "public" and not self._client().has_credentials():
            self._last_query["scope"] = None
        self._run_search(1)

    def _run_search(self, page: int):
        if page < 1 or not self._last_query:
            return
        q = dict(self._last_query, page=page)
        get_sesar_logger().info(f"SESAR search requested {q}")
        self._set_busy(True, "Searching SESAR…")
        worker = ApiCallWorker(self._client().search, parent=self, **q)
        worker.succeeded.connect(self._on_search_done)
        worker.failed.connect(self._on_api_failed)
        self._start_worker(worker)

    def _on_search_done(self, page: api.SearchPage):
        self._set_busy(False)
        query_text = self._last_query.get("q") or ""
        if not page.items and api.has_doi_prefix(api.normalize_igsn(query_text)):
            # A full IGSN that search didn't match (e.g. a draft) — try direct fetch.
            self._on_fetch_igsn_clicked()
            return
        self._page = page.page
        self._show_rows(page.items)
        self._update_nav(page)
        self.status_label.setText(f"{page.count} sample(s) found" if page.count
                                  else "No samples matched.")

    def _on_fetch_igsn_clicked(self):
        igsn = api.normalize_igsn(self.query_edit.text())
        if not igsn:
            QMessageBox.warning(self, "Missing IGSN", "Please enter an IGSN.")
            return
        self._set_busy(True, f"Fetching {igsn}…")
        worker = ApiCallWorker(self._client().get_sample, igsn, parent=self)
        worker.succeeded.connect(self._on_fetch_done)
        worker.failed.connect(self._on_api_failed)
        self._start_worker(worker)

    def _on_fetch_done(self, sample: dict):
        self._set_busy(False)
        igsn = sample.get("igsn")
        if igsn:
            self.detail_cache[igsn] = sample
        self._page = 1
        self._last_query = {}
        self._last_page = None
        self._show_rows([sample])
        self._update_nav(None)
        self.status_label.setText(f"Fetched {igsn or 'sample'}.")

    def _on_api_failed(self, exc: Exception):
        self._set_busy(False, "Request failed.")
        get_sesar_logger().error(f"SESAR request failed: {exc}")
        detail = exc.details() if isinstance(exc, api.SesarApiError) else str(exc)
        QMessageBox.critical(self, "SESAR Error", detail)

    # ------------------------------------------------------------- table
    def _show_rows(self, rows: List[dict]):
        self._rows = rows
        self._populating = True
        self.table.setRowCount(len(rows))
        for r, sample in enumerate(rows):
            igsn = sample.get("igsn") or ""
            for c, (_, extract) in enumerate(_RESULT_COLUMNS):
                item = QTableWidgetItem(_cell_text(extract(sample)))
                if c == 0:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    item.setCheckState(Qt.CheckState.Checked if igsn in self._checked
                                       else Qt.CheckState.Unchecked)
                    item.setData(Qt.ItemDataRole.UserRole, igsn)
                self.table.setItem(r, c, item)
        self._populating = False
        self.table.resizeColumnsToContents()
        self._update_selected_count()

    def _on_item_changed(self, item: QTableWidgetItem):
        if self._populating or item.column() != 0:
            return
        igsn = item.data(Qt.ItemDataRole.UserRole)
        if not igsn:
            return
        if item.checkState() == Qt.CheckState.Checked:
            self._checked[igsn] = self._rows[item.row()]
        else:
            self._checked.pop(igsn, None)
        self._update_selected_count()

    def _set_page_checked(self, checked: bool):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for r in range(self.table.rowCount()):
            self.table.item(r, 0).setCheckState(state)

    def _clear_all(self):
        self._checked.clear()
        self._set_page_checked(False)
        self._update_selected_count()

    def _update_selected_count(self):
        count = len(self._checked)
        self.selected_count_label.setText(f"Selected: {count}")
        self.import_btn.setEnabled(count > 0)
        # Rate-limit awareness: orange at 10+, red at 20+.
        self.selected_count_label.setStyleSheet(
            "color: red" if count >= 20 else "color: orange" if count >= 10 else "")

    def _update_nav(self, page: Optional[api.SearchPage]):
        if page is not None:
            self._last_page = page
        page = self._last_page if self._last_query else None
        if page is None:
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.page_label.setText("")
            return
        self.prev_btn.setEnabled(page.has_previous)
        self.next_btn.setEnabled(page.has_next)
        self.page_label.setText(f"Page {page.page} of {page.total_pages}")

    # -------------------------------------------------------- context menu
    def _show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if item is None:
            return
        row = item.row()
        igsn = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not igsn:
            return
        menu = QMenu(self)
        act_save = QAction("Save Sample JSON…", self)
        act_save.triggered.connect(lambda: self._save_sample_json(igsn))
        act_copy = QAction("Copy IGSN", self)
        act_copy.triggered.connect(lambda: QGuiApplication.clipboard().setText(igsn))
        act_open = QAction("Open Landing Page", self)
        act_open.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl(api.LANDING_PAGE_URL.format(igsn=igsn))))
        act_parent = QAction("Fetch Parent Sample", self)
        parent_igsn = self._rows[row].get("parent_sample") if row < len(self._rows) else None
        act_parent.setEnabled(bool(parent_igsn))
        act_parent.triggered.connect(lambda: self._fetch_specific(parent_igsn))
        for a in (act_save, act_copy, act_open):
            menu.addAction(a)
        menu.addSeparator()
        menu.addAction(act_parent)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _fetch_specific(self, igsn: Optional[str]):
        if igsn:
            self.query_edit.setText(str(igsn))
            self._on_fetch_igsn_clicked()

    def _save_sample_json(self, igsn: str):
        try:
            data = self.detail_cache.get(igsn) or self._client().get_sample(igsn)
        except api.SesarApiError as exc:
            QMessageBox.warning(self, "Download Failed", exc.details())
            return
        self.detail_cache[igsn] = data
        default = f"sesar_{igsn.replace('/', '_')}.json"
        path, _ = QFileDialog.getSaveFileName(self, "Save SESAR JSON", default,
                                              "JSON files (*.json)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as exc:
            QMessageBox.critical(self, "Save Failed", f"Could not save file: {exc}")

    # ---------------------------------------------- duplicate check (DB)
    def _find_existing_igsns_in_db(self, igsns):
        """
        Return (existing_set, error_message) for IGSNs already in Samples.

        Compares case-insensitively and also matches when one side stores
        the IGSN without its DOI prefix (older imports) — Samples.SampleIGSN
        is UNIQUE COLLATE NOCASE.
        """
        if not igsns:
            return set(), None
        db = QSqlDatabase.database()
        if not db.isValid() or not db.isOpen():
            return set(), "The GeoCORK database is not currently open."

        candidates = {}
        for igsn in igsns:
            candidates[igsn.upper()] = igsn
            candidates[api.bare_igsn(igsn).upper()] = igsn
        keys = list(candidates)
        placeholders = ",".join(["?"] * len(keys))
        query = QSqlQuery(db)
        if not query.prepare(
                f"SELECT SampleIGSN FROM Samples WHERE upper(SampleIGSN) IN ({placeholders})"):
            return set(), f"Could not prepare duplicate-check query: {query.lastError().text()}"
        for k in keys:
            query.addBindValue(k)
        if not query.exec():
            return set(), f"Duplicate-check query failed: {query.lastError().text()}"
        existing = set()
        while query.next():
            value = query.value(0)
            if value is not None:
                existing.add(candidates[str(value).upper()])
        return existing, None

    # ------------------------------------------------------------ import
    def _import_selected_to_geocork(self):
        checked_igsns = list(self._checked)
        if not checked_igsns:
            QMessageBox.warning(self, "No Selection", "No IGSNs are checked for import.")
            return
        total_checked = len(checked_igsns)
        get_sesar_logger().info(
            f"Batch import requested [count={total_checked}]\n"
            + "\n".join(f"  - {igsn}" for igsn in checked_igsns))

        existing_set, query_error = self._find_existing_igsns_in_db(checked_igsns)
        if query_error is not None:
            get_sesar_logger().error(f"Duplicate-IGSN pre-check failed — aborting. {query_error}")
            QMessageBox.critical(self, "Database Error",
                                 f"Could not check for duplicate IGSNs:\n\n{query_error}\n\n"
                                 "Import has been cancelled.")
            return

        to_import = [i for i in checked_igsns if i not in existing_set]
        to_skip = [i for i in checked_igsns if i in existing_set]
        get_sesar_logger().info(
            f"Duplicate check complete [requested={total_checked}, "
            f"to_import={len(to_import)}, already_in_db={len(to_skip)}]")

        if not to_import:
            info = QMessageBox(self)
            info.setWindowTitle("Nothing to Import")
            info.setIcon(QMessageBox.Icon.Information)
            info.setText(f"All {total_checked} selected IGSN(s) are already in the database.")
            info.setInformativeText("Already present:\n\n" + "\n".join(f"    {i}" for i in to_skip))
            info.exec()
            return

        def _fmt(items, max_shown=10):
            shown = "\n".join(f"    {i}" for i in items[:max_shown])
            return shown + (f"\n    …and {len(items) - max_shown} more"
                            if len(items) > max_shown else "")

        detail = "The following IGSNs will be imported:\n" + _fmt(to_import)
        if to_skip:
            detail += "\n\nSkipped (already in database):\n" + _fmt(to_skip)
        confirm = QMessageBox(self)
        confirm.setWindowTitle("Confirm Batch Import")
        confirm.setIcon(QMessageBox.Icon.Question)
        confirm.setText(f"Import {len(to_import)} IGSN(s) into GeoCORK?")
        confirm.setInformativeText(detail)
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm.setDefaultButton(QMessageBox.StandardButton.No)
        if confirm.exec() != QMessageBox.StandardButton.Yes:
            get_sesar_logger().info("User cancelled at the batch-import confirmation dialog")
            return

        self._download_dlg = LoadingDialog("Downloading",
                                           f"Fetching 1 of {len(to_import)} samples…", self)
        self._set_busy(True, "Fetching sample details…")
        self._fetch_started = time.perf_counter()
        worker = DetailFetchWorker(self._client(), to_import, self.detail_cache, parent=self)
        worker.progress.connect(
            lambda i, n, igsn: self._download_dlg.set_message(
                f"Fetching {i} of {n} samples…\nCurrent: {igsn}"))
        worker.done.connect(self._on_details_fetched)
        self._start_worker(worker)

    def _on_details_fetched(self, results: list, failures: list):
        self._set_busy(False)
        for igsn, data in results:
            self.detail_cache[igsn] = data
        get_sesar_logger().info(
            f"Batch detail fetch summary [ok={len(results)}, failed={len(failures)}, "
            f"elapsed={time.perf_counter() - self._fetch_started:.2f}s]")

        if failures:
            self._download_dlg.close()
            QMessageBox.warning(
                self, "Fetch Errors",
                f"Could not retrieve {len(failures)} sample(s):\n\n"
                + "\n".join(f"{i}: {m}" for i, m in failures[:15])
                + ("\n…" if len(failures) > 15 else "")
                + ("\n\nThe rest will still be previewed." if results else ""))
        if not results:
            self._download_dlg.close()
            return

        raw_data_list = [data for _, data in results]
        get_sesar_logger().info(
            f"Handing {len(raw_data_list)} sample(s) to SesarImportWindow")
        dlg = self._download_dlg if self._download_dlg.isVisible() else None
        # Keep a reference so the coordinator outlives this slot regardless
        # of Qt parent ownership.
        self._import_window = SesarImportWindow(
            raw_data_list=raw_data_list,
            parent=self.window(),
            on_cancelled=self._on_cancelled_callback,
            loading_dlg=dlg,
        )


# ===========================================================================
# Main dialog
# ===========================================================================

class ImportFromSesar(QDialog):
    """Entry-point dialog for the SESAR import flow (opened by ImportWizard)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        get_sesar_logger().info("ImportFromSesar dialog opened")
        self.setWindowTitle("Import from SESAR")
        self.setMinimumSize(900, 600)
        self.setModal(True)

        root = QVBoxLayout(self)
        title = QLabel("<b>Import Sample Data from SESAR</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        self.env_label = QLabel()
        self.env_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.env_label)

        self.search_widget = SampleSearchWidget(self, on_cancelled_callback=self._on_preview_cancelled)
        root.addWidget(self.search_widget, 1)

        bottom = QHBoxLayout()
        self.export_btn = QPushButton("Send GeoCORK Samples to SESAR…")
        self.export_btn.setToolTip("Update existing IGSNs or register new samples from this database")
        self.export_btn.clicked.connect(self._open_export)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        bottom.addWidget(self.export_btn)
        bottom.addStretch()
        bottom.addWidget(self.close_button)
        root.addLayout(bottom)

        self._update_env_label()

    # Backwards-compat alias for callers that referenced the old widget name.
    @property
    def explorer_widget(self):
        return self.search_widget

    def _update_env_label(self):
        try:
            client = api.SesarApiClient.from_settings()
            env = client.environment
            auth = "token configured" if client.has_credentials() else "no token (public data only)"
        except Exception:
            env, auth = api.DEFAULT_ENVIRONMENT, "settings unavailable"
        colour = "#b36b00" if env == "sandbox" else "#2e7d32"
        self.env_label.setText(
            f"<span style='color:{colour}'>SESAR {env}</span> — {auth} "
            f"<span style='color:gray'>(change in Settings → SESAR)</span>")

    def _on_preview_cancelled(self):
        """Called by SesarImportWindow when the user pressed Back."""
        self.show()
        self.raise_()
        self.activateWindow()

    def _open_export(self):
        from ui.SesarExportWindow import SesarExportWindow
        SesarExportWindow(parent=self).exec()
        self._update_env_label()
        self.search_widget.refresh_auth_state()
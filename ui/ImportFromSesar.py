# ImportFromSesar.py
# Handles importing sample data from SESAR using IGSN numbers.
# Fetches JSON from the SESAR API and hands it directly to SesarImportWindow
# (ImportFromSesarBuildWindow.py) so the user can preview and import without
# ever saving a file to disk.
#
# MERGE NOTES (partner branch):
#   - SampleHierarchyWidget (new): explores parent/sibling/child IGSN
#     relationships via a lazy-loading QTreeWidget + tabular text display.
#     Context-menu "Download IGSN Data" saves a JSON file to disk.
#   - "Explore Hierarchy" button added to ImportFromSesar to show/hide the
#     widget in a QSplitter below the existing fetch area.
#   - Our FetchWorker / _on_fetch_clicked / _on_load_clicked architecture is
#     fully preserved. The partner's synchronous fetch_and_save() is NOT
#     brought back — data flows through FetchWorker → SesarImportWindow.
#   - SampleHierarchyWidget uses its own synchronous requests.get() internally
#     (with an in-memory cache) — acceptable for an explorer that isn't part of
#     the core import pipeline.

# added checkboxes next to each igsn so users can select multiple at once
# added select all and clear all buttons to make bulk selection easier
# added download selected button with a confirmation popup that shows how many files
# added a counter that shows how many are selected
# right click menu now has checkand uncheck options
# batch download shows progress and tells you which ones failed at the end
# each igsn downloads as a separate json file named sesar_[igsn].json

import sys
import json
import requests
from pathlib import Path
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QTextEdit, QMessageBox,
                             QWidget, QSplitter, QTreeWidget, QTreeWidgetItem,
                             QMenu, QApplication)
from PyQt6.QtGui import QTextCursor, QAction

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
# Background worker — fetches SESAR JSON for a given IGSN off the main thread.
# Used by ImportFromSesar (the main dialog) so the UI never freezes during
# the core fetch→preview→import flow.
# ===========================================================================

class FetchWorker(QThread):
    """Moves requests.get() off the main thread so the UI stays responsive."""
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)

    _URL = "https://app.geosamples.org/webservices/display.php"

    def __init__(self, igsn: str, parent=None):
        super().__init__(parent)
        self._igsn = igsn.strip()

    def run(self):
        try:
            params  = {"igsn": self._igsn}
            headers = {"Accept": "application/json"}
            response = requests.get(self._URL, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            self.finished.emit(data)
        except requests.exceptions.ConnectionError:
            self.error.emit(
                "Could not connect to the SESAR API.\n\n"
                "Please check your internet connection and try again."
            )
        except requests.exceptions.Timeout:
            self.error.emit(
                "The SESAR API request timed out (15 s).\n\n"
                "The server may be busy — please try again shortly."
            )
        except requests.exceptions.HTTPError as e:
            self.error.emit(f"SESAR API error: {e}")
        except Exception as e:
            self.error.emit(f"Unexpected error while fetching IGSN:\n\n{e}")


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


class SampleHierarchyWidget(QWidget):
    """Widget for exploring IGSN parent/sibling/child relationships."""

    _URL = "https://app.geosamples.org/webservices/display.php"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_igsn = None
        self.sibling_data = {}  # in-memory cache: igsn -> response dict
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Label showing which IGSN is currently displayed
        self.current_label = QLabel("No sample selected")
        layout.addWidget(self.current_label)

        #button layout for download controls
        button_layout = QHBoxLayout()
        
        #download selected button
        self.download_selected_button = QPushButton("Download Selected IGSNs")
        self.download_selected_button.clicked.connect(self._download_selected)
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
    
    def _download_selected(self):
        """show confirmation dialog then download all selected IGSNs"""
        checked_igsns = self._get_checked_igsns()
        if not checked_igsns:
            QMessageBox.warning(self, "No Selection", "No IGSNs selected for download")
            return
        
        #confirmation dialog
        confirm_dialog = QMessageBox(self)
        confirm_dialog.setWindowTitle("Confirm Download")
        confirm_dialog.setIcon(QMessageBox.Icon.Question)
        confirm_dialog.setText(f"You are about to download {len(checked_igsns)} IGSN(s)")
        
        if len(checked_igsns) <= 10:
            igsn_list = "\n".join(checked_igsns)
            confirm_dialog.setInformativeText(f"The following IGSNs will be downloaded:\n\n{igsn_list}")
        else:
            igsn_list = "\n".join(checked_igsns[:10])
            confirm_dialog.setInformativeText(f"The following IGSNs will be downloaded (showing first 10 of {len(checked_igsns)}):\n\n{igsn_list}\n\n...and {len(checked_igsns) - 10} more")
        
        confirm_dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm_dialog.setDefaultButton(QMessageBox.StandardButton.No)
        
        if confirm_dialog.exec() == QMessageBox.StandardButton.Yes:
            self._perform_download(checked_igsns)
    
    def _perform_download(self, checked_igsns):
        """download all selected IGSNs with progress indication"""
        success_count = 0
        fail_count = 0
        failed_igsns = []
        
        #progress dialog
        progress = QMessageBox(self)
        progress.setWindowTitle("Downloading")
        progress.setText(f"Downloading 0 of {len(checked_igsns)} IGSNs...")
        progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress.setIcon(QMessageBox.Icon.Information)
        progress.show()
        
        for i, igsn in enumerate(checked_igsns):
            progress.setText(f"Downloading {i+1} of {len(checked_igsns)} IGSNs...\nCurrent: {igsn}")
            QApplication.processEvents()
            
            if self._save_sample_data(igsn, show_message=False):
                success_count += 1
            else:
                fail_count += 1
                failed_igsns.append(igsn)
        
        progress.accept()
        
        #show results
        result_msg = f"Download Complete!\n\nSuccessfully downloaded: {success_count}\nFailed: {fail_count}"
        if failed_igsns and len(failed_igsns) <= 10:
            result_msg += f"\n\nFailed IGSNs:\n" + "\n".join(failed_igsns)
        elif failed_igsns:
            result_msg += f"\n\nFailed IGSNs (showing first 10 of {len(failed_igsns)}):\n" + "\n".join(failed_igsns[:10])
        
        QMessageBox.information(self, "Download Results", result_msg)

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
      1. User types an IGSN and clicks "Fetch and Preview".
      2. FetchWorker downloads the JSON from SESAR in a background thread.
      3. Results are shown in the text area for review.
      4. "Load into GeoCORK" becomes available — clicking it opens
         SesarImportWindow with the raw dict pre-loaded, skipping file-browse.
      5. Optionally, "Explore Hierarchy" reveals a SampleHierarchyWidget below
         the fetch area so the user can browse parent/sibling/child IGSNs.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import from SESAR (IGSN)")
        self.setMinimumSize(600, 500)
        self.setModal(True)

        self._raw_data:     dict | None         = None
        self._fetch_worker: FetchWorker | None  = None

        # ------------------------------------------------------------------
        # Root layout contains a vertical splitter so the hierarchy explorer
        # can expand below the fetch area without disturbing it.
        # ------------------------------------------------------------------
        root_layout = QVBoxLayout()

        splitter = QSplitter(Qt.Orientation.Vertical)

        # ---- Top pane: fetch / preview area --------------------------------
        fetch_widget = QWidget()
        fetch_layout = QVBoxLayout()
        fetch_widget.setLayout(fetch_layout)

        # Title
        title_label = QLabel("Import Sample Data from SESAR")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fetch_layout.addWidget(title_label)

        # IGSN input row
        igsn_layout = QHBoxLayout()
        igsn_label  = QLabel("IGSN:")
        self.igsn_input = QLineEdit()
        self.igsn_input.setPlaceholderText("e.g., 10.58052/IENWUC821")
        self.igsn_input.returnPressed.connect(self._on_fetch_clicked)
        igsn_layout.addWidget(igsn_label)
        igsn_layout.addWidget(self.igsn_input)
        fetch_layout.addLayout(igsn_layout)

        # Button row
        button_layout = QHBoxLayout()

        self.fetch_button = QPushButton("Fetch and Preview")
        self.fetch_button.clicked.connect(self._on_fetch_clicked)
        button_layout.addWidget(self.fetch_button)

        # Disabled until a successful fetch
        self.load_button = QPushButton("Load into GeoCORK")
        self.load_button.setEnabled(False)
        self.load_button.clicked.connect(self._on_load_clicked)
        button_layout.addWidget(self.load_button)

        # Shows/hides the SampleHierarchyWidget pane below
        self.explore_button = QPushButton("Explore Hierarchy")
        self.explore_button.setCheckable(True)
        self.explore_button.clicked.connect(self._on_explore_toggled)
        button_layout.addWidget(self.explore_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)

        fetch_layout.addLayout(button_layout)

        # Results text area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Results will appear here...")
        fetch_layout.addWidget(self.results_text)

        splitter.addWidget(fetch_widget)

        # ---- Bottom pane: hierarchy explorer (hidden by default) -----------
        self.explorer_widget = SampleHierarchyWidget()
        self.explorer_widget.setVisible(False)
        splitter.addWidget(self.explorer_widget)

        root_layout.addWidget(splitter)
        self.setLayout(root_layout)

    # ------------------------------------------------------------------
    # Fetch / load slots  (our existing pipeline — unchanged)
    # ------------------------------------------------------------------

    def _on_fetch_clicked(self):
        igsn = self.igsn_input.text().strip()
        if not igsn:
            QMessageBox.warning(self, "Missing IGSN", "Please enter an IGSN.")
            return

        self._raw_data = None
        self.load_button.setEnabled(False)
        self.fetch_button.setEnabled(False)
        self.results_text.clear()
        self.results_text.append(f"Fetching data for IGSN: {igsn}...")

        self._fetch_worker = FetchWorker(igsn, parent=self)
        self._fetch_worker.finished.connect(self._on_fetch_done)
        self._fetch_worker.error.connect(self._on_fetch_error)
        self._fetch_worker.start()

    def _on_fetch_done(self, data: dict):
        """Store raw dict, enable Load button, and display a summary."""
        self._raw_data = data
        self.fetch_button.setEnabled(True)

        igsn = self.igsn_input.text().strip()
        self.results_text.append(f"\u2713 Successfully fetched data for: {igsn}")
        self.results_text.append("\n--- Sample Information ---")

        # Display key fields; supports both SESAR v1 ('sample') and legacy ('data') shapes.
        sample = data.get("sample") or data.get("data") or {}

        field_map = [
            ("igsn",                  "IGSN"),
            ("name",                  "Sample Name"),
            ("sample_primary_name",   "Sample Name"),
            ("sample_type",           "Sample Type"),
            ("material",              "Material"),
            ("sample_description",    "Description"),
            ("description",           "Description"),
            ("latitude",              "Latitude"),
            ("sample_latitude",       "Latitude"),
            ("longitude",             "Longitude"),
            ("sample_longitude",      "Longitude"),
            ("collection_start_date", "Collection Date"),
        ]
        seen_labels = set()
        for key, label in field_map:
            if label in seen_labels:
                continue
            val = sample.get(key)
            if val:
                self.results_text.append(f"{label}: {val}")
                seen_labels.add(label)

        self.results_text.append("\n--- Raw JSON ---")
        self.results_text.append(json.dumps(data, indent=2))

        self.load_button.setEnabled(True)
        self.results_text.append(
            "\n\u2192 Click 'Load into GeoCORK' to transform and preview this sample."
        )

    def _on_fetch_error(self, msg: str):
        self.fetch_button.setEnabled(True)
        self.results_text.append(f"\u2717 Error: {msg}")
        QMessageBox.critical(self, "Fetch Error", f"Failed to fetch data:\n\n{msg}")

    def _on_load_clicked(self):
        """Open SesarImportWindow with the pre-fetched raw dict."""
        if self._raw_data is None:
            return

        # SesarImportWindow is never shown in API mode — it is a pure
        # coordinator object. We hide ImportFromSesar first, then pass
        # a callback so SesarImportWindow can re-show us on Back.
        self.hide()

        build_win = SesarImportWindow(
            raw_data=self._raw_data,
            parent=self.parent(),
            on_cancelled=self._on_preview_cancelled,
        )
        # build_win is never shown — it runs the transform internally
        # and calls PreviewWindow.exec() on the main thread via its worker.

    def _on_preview_cancelled(self):
        """Called by SesarImportWindow when the user pressed Back."""
        self.show()

    # ------------------------------------------------------------------
    # Explore Hierarchy slot  (partner's feature — integrated here)
    # ------------------------------------------------------------------

    def _on_explore_toggled(self, checked: bool):
        """Show or hide the SampleHierarchyWidget pane."""
        self.explorer_widget.setVisible(checked)

        if checked:
            igsn = self.igsn_input.text().strip()
            if not igsn:
                QMessageBox.warning(
                    self, "Missing IGSN",
                    "Please enter an IGSN first, then click Explore Hierarchy."
                )
                self.explore_button.setChecked(False)
                self.explorer_widget.setVisible(False)
                return
            self.explorer_widget.load_siblings(igsn)
            # Expand the dialog so the explorer has room
            if self.height() < 800:
                self.resize(self.width(), 850)
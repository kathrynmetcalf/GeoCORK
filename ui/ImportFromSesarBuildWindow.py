"""
ImportFromSesarBuildWindow.py
-----------------------------
PyQt6 UI for importing SESAR sample data into the currently-open GeoCORK database.

Workflow:
    1. ImportFromSesar.py fetches raw SESAR JSON from the API using an IGSN.
    2. SesarImportWindow receives the raw dict (raw_data=) and opens.
    3. "Load Preview" transforms the data in a background thread and shows
       a staging table for review.
    4. "Import →" runs import_staging_inplace() in a background thread,
       writing directly into the already-open GeoCORK database.
    5. Success/failure message shown; window closes on success.

Naming conventions (UserInterfaceNamingConventions.md):
    Static objects  → static_<n>_<Type>_<Description>
    Dynamic objects → <type>_<n>_<Description>
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Path bootstrap - ensure GeoCORK root is on sys.path so that
# `from Sesar_Import.x import y` resolves correctly regardless of
# where this script is launched from.
# ---------------------------------------------------------------------------
_UI_DIR       = Path(__file__).resolve().parent   # GeoCORK/ui/
_GEOCORK_ROOT = _UI_DIR.parent                    # GeoCORK/

if str(_GEOCORK_ROOT) not in sys.path:
    sys.path.insert(0, str(_GEOCORK_ROOT))

# ---------------------------------------------------------------------------
# Pipeline imports
# ---------------------------------------------------------------------------
from Sesar_Import.json_staging_transformer import transform_sesar_to_geocork_staging_format, build_raw_sesar_table
from Sesar_Import.geocork_importer import import_staging_inplace

# ---------------------------------------------------------------------------
# PyQt6
# ---------------------------------------------------------------------------
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QSizePolicy, QFrame, QSplitter,
)



# ===========================================================================
# Helpers
# ===========================================================================

def _val(x: Any) -> str:
    """Return a display-safe string for a value that may be None / empty."""
    if x is None or x == "" or x == [] or x == {}:
        return "-"
    return str(x)


def _join_names(items: list, name_key: str) -> str:
    """Flatten a list of dicts to a comma-separated string of one field."""
    names = [str(d[name_key]) for d in items if name_key in d and d[name_key]]
    return ", ".join(names) if names else "-"


def _build_preview_rows(staging: Dict[str, Any]) -> list[tuple[str, str]]:
    """
    Extract human-readable (label, value) pairs from a staging dict for
    display in the preview table. One row per field of interest.
    """
    rows: list[tuple[str, str]] = []

    samples = staging.get("Samples", [])
    primary = next((s for s in samples if s.get("_DescriptionInstance", 1) == 1), {})

    rows.append(("Sample Name", _val(primary.get("SampleName"))))
    rows.append(("IGSN",        _val(primary.get("SampleIGSN"))))

    gps_list = staging.get("GPSLocations", [])
    if gps_list:
        g = gps_list[0]
        rows.append(("Latitude",    _val(g.get("GPSLatDeg"))))
        rows.append(("Longitude",   _val(g.get("GPSLonDeg"))))
        rows.append(("Elevation",   _val(g.get("GPSElev"))))
        utm_zone = g.get("GPSUTMZone")
        if utm_zone:
            rows.append(("UTM Zone",     _val(utm_zone)))
            rows.append(("UTM Easting",  _val(g.get("GPSUTME"))))
            rows.append(("UTM Northing", _val(g.get("GPSUTMN"))))
    else:
        rows.append(("Latitude",  "-"))
        rows.append(("Longitude", "-"))
        rows.append(("Elevation", "-"))

    if _val(primary.get("HeightDepth")) != "-":
        rows.append(("Depth (min)", _val(primary.get("HeightDepth"))))
        rows.append(("Depth (max)", _val(primary.get("HeightDepthError"))))

    rows.append(("Rock Types",
                 _join_names(staging.get("RockTypes", []), "RockTypeName")))
    rows.append(("Regions",
                 _join_names(staging.get("Regions", []), "RegionName")))
    rows.append(("Sampling Methods",
                 _join_names(staging.get("SamplingMethods", []), "SamplingMethodName")))
    rows.append(("Sample Contexts",
                 _join_names(staging.get("SampleContexts", []), "SampleContextName")))
    rows.append(("Ages",
                 _join_names(staging.get("Ages", []), "AgeName")))
    rows.append(("Stratigraphic Units",
                 _join_names(staging.get("Units", []), "UnitName")))

    refs = staging.get("References", [])
    ref_titles = [
        str(r.get("ReferenceCitation") or r.get("ReferenceTitle") or "")
        for r in refs if r
    ]
    rows.append(("References", ", ".join(filter(None, ref_titles)) or "-"))

    desc = primary.get("SampleDescription") or ""
    if len(desc) > 300:
        desc = desc[:297] + "..."
    rows.append(("Description", _val(desc) if desc else "-"))

    return rows



# ===========================================================================
# Background worker threads
# ===========================================================================

class TransformWorker(QThread):
    """
    Runs the SESAR → staging transform off the main thread.

    Accepts either:
      - json_path (str): path to a local SESAR JSON file, OR
      - raw_data  (dict): a pre-loaded raw SESAR dict (from the IGSN API flow).

    Exactly one of the two must be provided; raw_data takes priority.
    """
    finished = pyqtSignal(dict)     # fires when done, carries result
    error    = pyqtSignal(str)      # fires on failure, carries message

    def __init__(                   # this runs on the background thread
        self,
        json_path: Optional[str] = None,
        raw_data:  Optional[dict] = None,
    ):
        super().__init__()
        self.json_path = json_path
        self.raw_data  = raw_data

    def run(self):
        try:
            if self.raw_data is not None:       
                raw = self.raw_data         # came from API
            elif self.json_path is not None:
                raw = json.loads(Path(self.json_path).read_text(encoding="utf-8"))                   # read from file
            else:
                raise ValueError("TransformWorker: neither json_path nor raw_data was provided.")
            staging = transform_sesar_to_geocork_staging_format(raw)
            self.finished.emit(staging)                                                              # success --> send result to UI
        except Exception as exc:
            self.error.emit(str(exc))                                                                # failure --> send error to UI




# ===========================================================================
# Loading dialog
# Matches the style of GeoCORK's LoadingDialogManager.
# ===========================================================================

class LoadingDialog(QDialog):
    """Simple modal loading indicator shown during background operations."""

    def __init__(self, title: str, message: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )
        self.setMinimumWidth(260)

        # static_root_Layout_Loading
        static_root_Layout_Loading = QVBoxLayout(self)
        static_root_Layout_Loading.setContentsMargins(24, 18, 24, 18)
        static_root_Layout_Loading.setSpacing(8)

        # static_title_Label_LoadingTitle
        static_title_Label_LoadingTitle = QLabel(title)
        title_font = QFont()
        title_font.setBold(True)
        static_title_Label_LoadingTitle.setFont(title_font)
        static_title_Label_LoadingTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        static_root_Layout_Loading.addWidget(static_title_Label_LoadingTitle)

        # static_message_Label_LoadingMessage
        self.static_message_Label_LoadingMessage = QLabel(message)
        self.static_message_Label_LoadingMessage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.static_message_Label_LoadingMessage.setWordWrap(True)
        static_root_Layout_Loading.addWidget(self.static_message_Label_LoadingMessage)

        self.setModal(True)
        self.show()
        QApplication.processEvents()

    def set_message(self, message: str) -> None:
        self.static_message_Label_LoadingMessage.setText(message)
        self.adjustSize()
        QApplication.processEvents()


# ===========================================================================
# Preview window
# ===========================================================================

class PreviewWindow(QDialog):
    """
    Side-by-side preview of raw SESAR JSON (left) and transformed GeoCORK
    staging data (right). Provides Back and Import action buttons.

    Both tables use a wide column layout: field names as column headers,
    one row per IGSN. This is intentional — when multi-IGSN import is
    added, each IGSN will appear as its own row in both tables.
    """

    import_requested = pyqtSignal(dict)

    def __init__(self, staging: dict, raw_data: Optional[dict] = None,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.staging  = staging
        self.raw_data = raw_data
        self.setWindowTitle("Preview - SESAR Sample Data")
        self.setMinimumSize(900, 400)
        # Size to ~60 % of the primary screen, centred.
        screen_geo = QApplication.primaryScreen().availableGeometry()
        w = int(screen_geo.width()  * 0.60)
        h = int(screen_geo.height() * 0.60)
        self.resize(w, h)
        self.move(
            screen_geo.center().x() - w // 2,
            screen_geo.center().y() - h // 2,
        )

        # static_root_Layout_Preview
        static_root_Layout_Preview = QVBoxLayout(self)
        static_root_Layout_Preview.setContentsMargins(6, 6, 6, 6)
        static_root_Layout_Preview.setSpacing(4)

        # static_header_Label_SampleInfo
        igsn = (staging.get("Samples") or [{}])[0].get("SampleIGSN") or "Unknown"
        name = (staging.get("Samples") or [{}])[0].get("SampleName") or "Unknown"
        static_header_Label_SampleInfo = QLabel(
            f"<b>Sample:</b> {name} &nbsp;|&nbsp; <b>IGSN:</b> {igsn}"
        )
        static_header_Label_SampleInfo.setStyleSheet("font-size: 12px; padding: 1px 0;")
        static_root_Layout_Preview.addWidget(static_header_Label_SampleInfo)

        # static_divider_Frame_Separator
        static_divider_Frame_Separator = QFrame()
        static_divider_Frame_Separator.setFrameShape(QFrame.Shape.HLine)
        static_divider_Frame_Separator.setFrameShadow(QFrame.Shadow.Sunken)
        static_root_Layout_Preview.addWidget(static_divider_Frame_Separator)

        # static_splitter_Splitter_Tables - resizable left/right panes
        static_splitter_Splitter_Tables = QSplitter(Qt.Orientation.Horizontal)
        static_splitter_Splitter_Tables.setChildrenCollapsible(False)

        # ── Left pane: raw SESAR JSON ──────────────────────────────────────
        # Wide column layout: field names as column headers, one row per IGSN.
        # Ready for multi-IGSN: each future IGSN will add another row.
        raw_pairs = build_raw_sesar_table(raw_data) if raw_data else []
        raw_col_count = len(raw_pairs)

        static_left_Layout_RawPane = QVBoxLayout()
        static_left_Layout_RawPane.setContentsMargins(0, 0, 4, 0)
        static_left_Layout_RawPane.setSpacing(4)

        static_rawLabel_Label_PaneTitle = QLabel("Raw SESAR JSON")
        raw_label_font = QFont()
        raw_label_font.setBold(True)
        static_rawLabel_Label_PaneTitle.setFont(raw_label_font)
        static_left_Layout_RawPane.addWidget(static_rawLabel_Label_PaneTitle)

        # static_raw_TableWidget_RawData
        # Columns = field names, rows = one per IGSN (multi-IGSN ready).
        self.static_raw_TableWidget_RawData = QTableWidget(1, raw_col_count)
        self.static_raw_TableWidget_RawData.setObjectName("static_raw_TableWidget_RawData")
        self.static_raw_TableWidget_RawData.setHorizontalHeaderLabels(
            [pair[0] for pair in raw_pairs]
        )
        self.static_raw_TableWidget_RawData.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.static_raw_TableWidget_RawData.verticalHeader().setVisible(False)
        self.static_raw_TableWidget_RawData.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.static_raw_TableWidget_RawData.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.static_raw_TableWidget_RawData.setAlternatingRowColors(True)
        self.static_raw_TableWidget_RawData.setWordWrap(False)

        for col_idx, (_, value) in enumerate(raw_pairs):
            self.static_raw_TableWidget_RawData.setItem(0, col_idx, QTableWidgetItem(value))

        self.static_raw_TableWidget_RawData.resizeRowsToContents()
        static_left_Layout_RawPane.addWidget(self.static_raw_TableWidget_RawData)

        static_left_Widget_RawPane = QFrame()
        static_left_Widget_RawPane.setLayout(static_left_Layout_RawPane)
        static_splitter_Splitter_Tables.addWidget(static_left_Widget_RawPane)

        # ── Right pane: GeoCORK staging ────────────────────────────────────
        # Wide column layout: field names as column headers, one row per IGSN.
        # Ready for multi-IGSN: each future IGSN will add another row.
        preview_rows = _build_preview_rows(staging)
        staging_col_count = len(preview_rows)

        static_right_Layout_StagingPane = QVBoxLayout()
        static_right_Layout_StagingPane.setContentsMargins(4, 0, 0, 0)
        static_right_Layout_StagingPane.setSpacing(4)

        static_stagingLabel_Label_PaneTitle = QLabel("GeoCORK Staging")
        staging_label_font = QFont()
        staging_label_font.setBold(True)
        static_stagingLabel_Label_PaneTitle.setFont(staging_label_font)
        static_right_Layout_StagingPane.addWidget(static_stagingLabel_Label_PaneTitle)

        # static_preview_TableWidget_StagingData
        # Columns = field names, rows = one per IGSN (multi-IGSN ready).
        self.static_preview_TableWidget_StagingData = QTableWidget(1, staging_col_count)
        self.static_preview_TableWidget_StagingData.setObjectName(
            "static_preview_TableWidget_StagingData"
        )
        self.static_preview_TableWidget_StagingData.setHorizontalHeaderLabels(
            [label for label, _ in preview_rows]
        )
        self.static_preview_TableWidget_StagingData.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.static_preview_TableWidget_StagingData.verticalHeader().setVisible(False)
        self.static_preview_TableWidget_StagingData.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.static_preview_TableWidget_StagingData.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.static_preview_TableWidget_StagingData.setAlternatingRowColors(True)
        self.static_preview_TableWidget_StagingData.setWordWrap(False)

        for col_idx, (_, value) in enumerate(preview_rows):
            self.static_preview_TableWidget_StagingData.setItem(
                0, col_idx, QTableWidgetItem(value)
            )

        self.static_preview_TableWidget_StagingData.resizeRowsToContents()
        static_right_Layout_StagingPane.addWidget(self.static_preview_TableWidget_StagingData)

        static_right_Widget_StagingPane = QFrame()
        static_right_Widget_StagingPane.setLayout(static_right_Layout_StagingPane)
        static_splitter_Splitter_Tables.addWidget(static_right_Widget_StagingPane)

        # Give both panes equal initial width
        static_splitter_Splitter_Tables.setSizes([700, 700])
        # stretch=1 so the splitter (and the tables inside it) expands to fill
        # all remaining vertical space — the button row below gets stretch=0.
        static_root_Layout_Preview.addWidget(static_splitter_Splitter_Tables, stretch=1)

        # static_btnRow_Layout_Actions
        static_btnRow_Layout_Actions = QHBoxLayout()
        static_btnRow_Layout_Actions.addStretch()

        # btn_back_Action
        self.btn_back_Action = QPushButton("← Back")
        self.btn_back_Action.setObjectName("btn_back_Action")
        self.btn_back_Action.setFixedWidth(100)
        self.btn_back_Action.clicked.connect(self.reject)
        static_btnRow_Layout_Actions.addWidget(self.btn_back_Action)

        # btn_import_Action
        self.btn_import_Action = QPushButton("Import →")
        self.btn_import_Action.setObjectName("btn_import_Action")
        self.btn_import_Action.setFixedWidth(110)
        self.btn_import_Action.setDefault(True)
        self.btn_import_Action.clicked.connect(self._on_import_clicked)
        static_btnRow_Layout_Actions.addWidget(self.btn_import_Action)

        static_root_Layout_Preview.addLayout(static_btnRow_Layout_Actions)

    def _on_import_clicked(self) -> None:
        self.btn_import_Action.setEnabled(False)
        self.btn_back_Action.setEnabled(False)
        self.import_requested.emit(self.staging)


# ===========================================================================
# Main window
# ===========================================================================

class SesarImportWindow(QDialog):
    """
    Main entry-point window for the SESAR importer.

    Two launch modes:
      1. Standalone / file-browse: SesarImportWindow()
         User browses for a local SESAR JSON file and a GeoCORK .db.
      2. IGSN API mode: SesarImportWindow(raw_data=<dict>, parent=<widget>)
         raw_data is a pre-fetched SESAR JSON dict passed in from ImportFromSesar.
         The JSON file-browse row is hidden; the user only needs to pick a .db.
    """

    def __init__(
        self,
        raw_data:     Optional[dict]    = None,
        parent:       Optional[QWidget] = None,
        on_cancelled: Optional[object]  = None,   # callable, API mode only
    ):
        super().__init__(parent)
        self.setWindowTitle("SESAR → GeoCORK Importer")
        self.setMinimumWidth(560)
        self.resize(600, 230)

        # Only set modal in file-browse mode where this window is actually shown.
        if raw_data is None:
            self.setModal(True)

        self._raw_data:         Optional[dict]            = raw_data
        self._on_cancelled                                = on_cancelled
        self._staging:          Optional[dict]            = None
        self._json_path:        Optional[str]             = None

        if raw_data is not None:
            from PyQt6.QtSql import QSqlDatabase
            self._db_path: Optional[str] = QSqlDatabase.database().databaseName() or None
        else:
            self._db_path: Optional[str] = None
        self._transform_worker: Optional[TransformWorker] = None
        self._loading_dlg:      Optional[LoadingDialog]   = None
        self._preview_win:      Optional[PreviewWindow]   = None

        if self._raw_data is not None:
            # API mode: never show self — just run the transform.
            # PreviewWindow will be shown via exec() from _on_transform_done.
            self._start_transform()
        else:
            self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        # static_root_Layout_Main
        static_root_Layout_Main = QVBoxLayout(self)
        static_root_Layout_Main.setContentsMargins(20, 20, 20, 16)
        static_root_Layout_Main.setSpacing(12)

        # static_title_Label_AppTitle
        static_title_Label_AppTitle = QLabel("SESAR Sample Importer")
        title_font = QFont()
        title_font.setBold(True)
        static_title_Label_AppTitle.setFont(title_font)
        static_root_Layout_Main.addWidget(static_title_Label_AppTitle)

        # static_subtitle_Label_AppSubtitle
        if self._raw_data is not None:
            subtitle_text = "Review the fetched SESAR sample, select a GeoCORK database, then preview before importing."
        else:
            subtitle_text = "Select a SESAR JSON file and a GeoCORK database, then preview before importing."
        static_subtitle_Label_AppSubtitle = QLabel(subtitle_text)
        static_subtitle_Label_AppSubtitle.setWordWrap(True)
        static_root_Layout_Main.addWidget(static_subtitle_Label_AppSubtitle)

        # static_btnRow_Layout_LoadAction
        static_root_Layout_Main.addStretch()
        static_btnRow_Layout_LoadAction = QHBoxLayout()
        static_btnRow_Layout_LoadAction.addStretch()

        # btn_loadPreview_Action
        self.btn_loadPreview_Action = QPushButton("Load Preview")
        self.btn_loadPreview_Action.setObjectName("btn_loadPreview_Action")
        self.btn_loadPreview_Action.setFixedWidth(130)
        self.btn_loadPreview_Action.clicked.connect(self._on_load_preview)
        # Set initial enabled state: in API mode both data sources are
        # already resolved so the button can be enabled immediately.
        self._update_load_btn()

        static_btnRow_Layout_LoadAction.addWidget(self.btn_loadPreview_Action)
        static_root_Layout_Main.addLayout(static_btnRow_Layout_LoadAction)

    def _update_load_btn(self) -> None:
        if self._raw_data is not None:
            # API mode: both data sources are resolved at init time -
            # enable Load Preview immediately (no user input needed).
            self.btn_loadPreview_Action.setEnabled(bool(self._db_path))
        else:
            # File-browse mode: both paths must be set by the user first.
            self.btn_loadPreview_Action.setEnabled(
                bool(self._json_path) and bool(self._db_path)
            )

    # ------------------------------------------------------------------
    def _start_transform(self) -> None:
        """Kick off the TransformWorker. Called automatically in API mode,
        or via btn_loadPreview_Action in file-browse mode."""
        # In API mode self is intentionally hidden — parent the LoadingDialog
        # to our own parent so it doesn't drag SesarImportWindow into view.
        loading_parent = self.parent() if self._raw_data is not None else self
        self._loading_dlg = LoadingDialog("Loading", "Transforming SESAR data…", loading_parent)

        self._transform_worker = TransformWorker(
            json_path=self._json_path,
            raw_data=self._raw_data,
        )
        self._transform_worker.finished.connect(self._on_transform_done)
        self._transform_worker.error.connect(self._on_transform_error)
        self._transform_worker.start()

    def _on_load_preview(self) -> None:
        """Button handler for file-browse mode - disables the button then delegates."""
        self.btn_loadPreview_Action.setEnabled(False)
        self._start_transform()

    def _on_transform_done(self, staging: dict) -> None:
        self._staging = staging
        if self._loading_dlg:
            self._loading_dlg.set_message("Building preview…")

        self._preview_win = PreviewWindow(staging, raw_data=self._raw_data, parent=self.parent())
        self._preview_win.import_requested.connect(self._on_import_requested)

        if self._loading_dlg:
            self._loading_dlg.close()
            self._loading_dlg = None

        if self._raw_data is None:
            self.btn_loadPreview_Action.setEnabled(True)

        # Always use exec() — this blocks until the user clicks Back or Import.
        # No nesting issue here because SesarImportWindow itself is never shown
        # in API mode, so exec() on PreviewWindow runs cleanly.
        self._preview_win.exec()

        # After exec() returns: if Back was pressed, call the cancellation
        # callback so ImportFromSesar can re-show itself.
        if self._raw_data is not None:
            if self._preview_win.result() != QDialog.DialogCode.Accepted:
                if self._on_cancelled:
                    self._on_cancelled()

    def _on_preview_finished(self, result: int) -> None:
        """No longer used — kept as a no-op for safety."""
        pass

    def _on_transform_error(self, msg: str) -> None:
        if self._loading_dlg:
            self._loading_dlg.close()
            self._loading_dlg = None
        if self._raw_data is None:
            self.btn_loadPreview_Action.setEnabled(True)
        QMessageBox.critical(
            self, "Transform Error",
            f"Failed to process SESAR JSON:\n\n{msg}"
        )

    # ------------------------------------------------------------------
    def _on_import_requested(self, staging: dict) -> None:
        # import_staging_inplace() uses QSqlQuery on the Qt default connection,
        # which must be called from the main thread - NOT a QThread worker.
        # We show a loading dialog for visual feedback and call processEvents()
        # so it renders, then run the import synchronously on the main thread.
        if self._loading_dlg:
            self._loading_dlg.close()

        self._loading_dlg = LoadingDialog(
            "Importing", "Importing into GeoCORK…", self
        )

        try:
            import_staging_inplace(staging, self._db_path)
            self._on_import_done(self._db_path)
        except Exception as exc:
            self._on_import_error(str(exc))

    def _on_import_done(self, out_db: str) -> None:
        if self._loading_dlg:
            self._loading_dlg.close()
            self._loading_dlg = None

        if self._raw_data is not None:
            msg = (f"✓ Import successful!\n\n"
                   f"Sample(s) added to: {Path(out_db).name}")
        else:
            msg = (f"✓ Import successful!\n\n"
                   f"Output database:\n{Path(out_db).name}")
        QMessageBox.information(self, "Import Complete", msg)

        # Accept PreviewWindow — this ends exec() with Accepted result,
        # so _on_transform_done will NOT call the on_cancelled callback.
        if self._preview_win:
            self._preview_win.accept()
            self._preview_win = None

    def _on_import_error(self, msg: str) -> None:
        if self._loading_dlg:
            self._loading_dlg.close()
            self._loading_dlg = None
        if self._preview_win:
            self._preview_win.btn_import_Action.setEnabled(True)
            self._preview_win.btn_back_Action.setEnabled(True)

        QMessageBox.critical(
            self, "Import Error",
            f"Import failed - database was not modified.\n\n{msg}"
        )
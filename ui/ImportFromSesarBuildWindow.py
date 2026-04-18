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
from Sesar_Import.json_staging_transformer import (
    transform_sesar_to_geocork_staging_format,
    transform_multiple_sesar_samples,
    build_raw_sesar_table,
)
from Sesar_Import.geocork_importer import import_staging_inplace

# ---------------------------------------------------------------------------
# PyQt6
# ---------------------------------------------------------------------------
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QBrush
from PyQt6.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QSizePolicy, QFrame, QSplitter, QWidget,
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


# ---------------------------------------------------------------------------
# Edit-mode configuration for the staging preview
# ---------------------------------------------------------------------------

# Columns whose values must not be edited by the user, regardless of whether
# they're single-value or not. These are either unique identifiers (changing
# them would break referential integrity) or auto-computed codes (the
# transformer derives them from other fields; a manual edit would be out of
# sync with the rest of the sample).
_LOCKED_COLUMNS: set = {
    "SampleIGSN",        # unique sample identifier
    "GPSFormatID",       # computed from which of the lat/lon/UTM fields are present
}

# Columns whose names end with these suffixes are also locked — FK ID columns
# and parent-row index columns that the importer populates at write time.
_LOCKED_COLUMN_SUFFIXES: tuple = ("ID", "ParentRow")

# Visual styling for locked vs. edited cells.
# Locked:  subtly greyed text so the user sees they can't edit.
# Edited:  bold text + a pale yellow background tint so changes stand out.
_LOCKED_TEXT_COLOR  = QColor(140, 140, 140)   # medium grey
_EDITED_BG_COLOR    = QColor(255, 249, 196)   # pale yellow ("highlighter")
_DEFAULT_BG_BRUSH   = QBrush()                # default/reset brush
_DEFAULT_FG_COLOR   = QColor(0, 0, 0)         # standard black


def _is_column_locked(col_name: str) -> bool:
    """True if a column should never be editable (identifiers, computed codes)."""
    if col_name in _LOCKED_COLUMNS:
        return True
    return any(col_name.endswith(suffix) for suffix in _LOCKED_COLUMN_SUFFIXES)


# ---------------------------------------------------------------------------
# Original preview helpers follow
# ---------------------------------------------------------------------------

# Upper bound on any single cell's rendered text. Long free-form fields like
# SampleDescription commonly exceed this; they are truncated with an ellipsis
# so one oversized cell doesn't blow out the whole row height.
_STAGING_CELL_MAX_CHARS = 500

# Separator used to join values from multiple bridge-linked rows into one cell.
# Example: a sample with 3 Regions gets RegionName = "Nevada | Humboldt co. | mine coordinate system".
# Using " | " (with spaces) instead of ", " avoids collision with commas that
# may appear inside individual field values (e.g. addresses, citations).
_STAGING_MULTIROW_JOIN = " | "

# Preferred left-to-right column order for well-known fields. Any field
# collected from the staging dict that isn't in this list gets appended to the
# right in alphabetical order, so nothing is ever hidden if the transformer
# grows new fields — but the common stuff stays in a predictable place.
_STAGING_PREFERRED_COLUMN_ORDER: list[str] = [
    # Sample identity
    "SampleName", "SampleIGSN", "SampleType",
    # Description instances (the transformer emits multiple instances per sample)
    "SampleDescription", "SampleDescription [2]", "SampleDescription [3]",
    "SampleDescription [4]",
    # GPS / location
    "GPSLatDeg", "GPSLonDeg", "GPSElev", "GPSElevUnit",
    "GPSUTMZone", "GPSUTME", "GPSUTMN",
    "GPSFormatID",
    # Depth (core samples)
    "HeightDepth", "HeightDepthError", "HeightDepthUnit",
    # Bridge-linked content (names first, descriptions right next to them so
    # RegionDescription / locality_description sits immediately next to RegionName)
    "RegionName", "RegionDescription", "_ParentRegionName",
    "RockTypeName", "RockTypeDescription",
    "SamplingMethodName", "SamplingMethodDescription",
    "SampleContextName", "SampleContextDescription",
    "AgeName", "AgeDescription", "AgeMin", "AgeMax", "AgeUnit",
    "UnitName", "UnitDescription",
    # References live at the far right — usually long strings
    "ReferenceCitation", "ReferenceTitle", "ReferenceDOI", "ReferenceURL",
]

# Internal plumbing: top-level staging keys we never show in the preview.
# - Keys starting with "_" are transformer-internal staging helpers.
# - Samples_X bridge tables carry ID-pair plumbing, not content.
# - Columns is a GeoCORK-internal UI layout table, not sample data.
_STAGING_SKIP_TABLES: set = {
    "Columns",
}

# Per-row field names we never show (noise columns).
# - Keys starting with "_" are flagged at the field level and skipped generically.
# - ID-style FK fields are None until import resolves them; they're plumbing.
_STAGING_SKIP_FIELDS_WHEN_NONE: set = {
    "SampleID", "AliquotID", "SpotID", "UPbAnalysisID",
    "RegionID", "ParentRegionID", "RegionParentRow",
    "RockTypeID", "ParentRockTypeID", "RockTypeParentRow",
    "SamplingMethodID", "ParentSamplingMethodID", "SamplingMethodParentRow",
    "SampleContextID", "ParentSampleContextID", "SampleContextParentRow",
    "UnitID", "ParentUnitID", "UnitParentRow",
    "AgeID", "ReferenceID", "ColumnID",
    "GPSLocationID",
}


def _truncate(text: str) -> str:
    """Clip overlong cell text with an ellipsis so rows stay readable."""
    if len(text) > _STAGING_CELL_MAX_CHARS:
        return text[:_STAGING_CELL_MAX_CHARS - 3] + "..."
    return text


def _is_internal_field(key: str) -> bool:
    """Transformer-internal keys start with an underscore (e.g. _SampleNaturalKey)."""
    return key.startswith("_")


def _should_show_field(key: str, value: Any) -> bool:
    """
    Decide whether a (key, value) pair is worth surfacing in the preview.

    Hides:
      - Internal plumbing fields (underscore-prefixed)
      - Empty values (None / "" / [] / {})
      - Pre-import FK IDs that are None
    """
    if _is_internal_field(key):
        return False
    if value is None or value == "" or value == [] or value == {}:
        if key in _STAGING_SKIP_FIELDS_WHEN_NONE:
            return False
        return False
    return True


def _merge_row_values(existing: str, new_val: str) -> str:
    """
    Combine a new cell value into an existing cell using the multi-row join
    separator. Used when multiple bridge-linked rows contribute to the same
    column (e.g. 3 Regions -> RegionName = "a | b | c").
    """
    return f"{existing}{_STAGING_MULTIROW_JOIN}{new_val}" if existing else new_val


def _collect_fields_into_row(
    out_row: dict[str, str],
    source_row: dict[str, Any],
    sources: Optional[dict] = None,
) -> None:
    """
    Fold every non-empty, non-internal field from `source_row` into `out_row`,
    joining against any existing value with the multi-row separator so multiple
    bridge-linked rows (e.g. several Regions for one sample) stack visibly.

    If `sources` is provided, record (source_row, field_name) per output key
    on the first contribution — this lets callers later trace an edited cell
    back to the exact staging dict location to mutate. When a second source
    contributes to the same key (making the cell multi-value), the mapping is
    removed so the caller knows the cell cannot be unambiguously reverse-mapped.
    """
    for key, val in source_row.items():
        if not _should_show_field(key, val):
            continue
        cell = _truncate(str(val))
        if key in out_row:
            out_row[key] = _merge_row_values(out_row[key], cell)
            # A second contributor makes this cell ambiguous — drop the map entry
            # so the UI treats it as read-only.
            if sources is not None:
                sources.pop(key, None)
        else:
            out_row[key] = cell
            if sources is not None:
                sources[key] = (source_row, key)


def _order_columns(discovered: set[str]) -> list[str]:
    """
    Return a column ordering that puts well-known fields in a curated position
    and appends any other discovered fields in alphabetical order at the end.
    Ensures new transformer outputs never get silently hidden.
    """
    ordered = [c for c in _STAGING_PREFERRED_COLUMN_ORDER if c in discovered]
    extras = sorted(discovered - set(ordered))
    return ordered + extras


def _build_staging_table(
    staging: Dict[str, Any],
) -> tuple:
    """
    Build the GeoCORK staging data in wide-column format for the right pane.

    Columns are discovered dynamically from whatever fields the staging dict
    actually contains — no hand-curated allow-list. This means fields like
    RegionDescription (which carries SESAR's locality_description), AgeDescription,
    and any future transformer additions appear automatically without needing
    to touch this file.

    One row per unique primary IGSN (matching the left pane's layout). Bridge
    tables (Samples_X) contribute to their linked primary sample's row by
    joining multiple linked-row values with " | " per column.

    Returns
    -------
    col_headers : list[str]
        Ordered column names — curated order for common fields, then
        alphabetical for anything else discovered.
    row_dicts : list[dict]
        One dict per primary IGSN, keyed by col_headers values. Cells missing
        from a given sample are filled with "-" by the UI code (not here)
        so the table stays rectangular.
    cell_map : dict[(row_idx, col_idx) -> (source_row, field_name, original_value)]
        Reverse-mapping for editable cells. `source_row` is a live reference
        to the dict inside the staging dict that the UI should mutate when the
        cell is edited; `field_name` is the key to write to; `original_value`
        is the string the cell held at build time (used for edit-detection
        styling). Only single-value cells appear here — multi-value/joined
        cells are deliberately omitted so the UI locks them.
    """
    # ─── Step 1: identify one primary sample row per unique natural key ───
    # Primary = _DescriptionInstance == 1 (the "base" sample row; instances
    # 2/3/4 carry auxiliary descriptions that we'll fold in next to it).
    samples = staging.get("Samples", [])
    seen_nks: list[str] = []
    primary_by_nk: dict[str, Any] = {}
    instances_by_nk: dict[str, list[dict]] = {}
    for s in samples:
        nk = s.get("SampleIGSN") or s.get("SampleName") or ""
        if not nk:
            continue
        instances_by_nk.setdefault(nk, []).append(s)
        if s.get("_DescriptionInstance", 1) == 1 and nk not in primary_by_nk:
            primary_by_nk[nk] = s
            seen_nks.append(nk)

    # ─── Step 2: GPS lookup keyed by _gps_key for per-sample attachment ───
    gps_by_key: dict[str, Any] = {
        g.get("_gps_key", ""): g
        for g in staging.get("GPSLocations", [])
    }

    # ─── Step 3: pre-group bridge tables by sample natural key ───
    # Every Samples_X bridge row has _SampleNaturalKey pointing to its sample,
    # and the parent table rows can be matched by name. We group the parent
    # rows (not the bridge rows) per sample, because the parent rows hold the
    # actual content fields like RegionName, RegionDescription, etc.
    def _parent_rows_for_sample(
        bridge_key: str, parent_key: str,
        name_field_in_bridge: str, name_field_in_parent: str,
        nk: str,
    ) -> list[dict]:
        """Return the parent-table rows linked to sample `nk` via `bridge_key`."""
        bridges = staging.get(bridge_key, [])
        parents = staging.get(parent_key, [])
        linked_names = {
            b.get(name_field_in_bridge)
            for b in bridges
            if b.get("_SampleNaturalKey") == nk and b.get(name_field_in_bridge)
        }
        return [p for p in parents if p.get(name_field_in_parent) in linked_names]

    # ─── Step 4: assemble one flat row dict per primary sample ───
    # Alongside each row we build a per-row "sources" dict mapping column-name
    # -> (source_row_ref, field_name). These start out as column-name-keyed
    # (since col_idx isn't known yet) and get re-keyed by col_idx at the end.
    row_dicts: list[dict[str, str]] = []
    per_row_sources: list = []

    for nk in seen_nks:
        row: dict[str, str] = {}
        sources: dict = {}

        # Primary sample row (SampleName, SampleIGSN, SampleDescription, HeightDepth, etc.)
        _collect_fields_into_row(row, primary_by_nk[nk], sources)

        # Additional description instances (2, 3, 4) — the transformer emits
        # these as separate Sample rows that share the same IGSN but with
        # _DescriptionInstance = 2/3/4. We fold them in under a suffixed key
        # so all descriptions for one sample live in one preview row.
        # Note: the synthetic column label ("SampleDescription [N]") maps back
        # to the instance row's REAL field ("SampleDescription") — that's what
        # gets recorded in `sources` so edits write back correctly.
        for inst in instances_by_nk.get(nk, []):
            inst_num = inst.get("_DescriptionInstance")
            if inst_num in (None, 1):
                continue
            desc = inst.get("SampleDescription")
            if desc:
                label = f"SampleDescription [{inst_num}]"
                row[label] = _truncate(str(desc))
                sources[label] = (inst, "SampleDescription")

        # GPS (single row per sample, looked up by _SampleGPSKey)
        gps_key = primary_by_nk[nk].get("_SampleGPSKey")
        if gps_key and gps_key in gps_by_key:
            _collect_fields_into_row(row, gps_by_key[gps_key], sources)

        # Bridge-linked tables — each contributes one or more parent rows.
        # We iterate every linked parent row and fold its fields into the
        # sample's row; multiple linked rows get joined by " | " per column.
        # When that joining happens, _collect_fields_into_row drops the
        # source mapping so the cell becomes read-only in the UI.
        for bridge_key, parent_key, bridge_name, parent_name in [
            ("Samples_Regions",         "Regions",
             "_RegionName",             "RegionName"),
            ("Samples_RockTypes",       "RockTypes",
             "_RockTypeName",           "RockTypeName"),
            ("Samples_SamplingMethods", "SamplingMethods",
             "_SamplingMethodName",     "SamplingMethodName"),
            ("Samples_SampleContexts",  "SampleContexts",
             "_SampleContextName",      "SampleContextName"),
            ("Samples_Units",           "Units",
             "_UnitName",               "UnitName"),
        ]:
            for parent_row in _parent_rows_for_sample(
                bridge_key, parent_key, bridge_name, parent_name, nk
            ):
                _collect_fields_into_row(row, parent_row, sources)

        # Ages — not per-sample in the current staging schema; fold in every
        # Age row globally (matches the prior preview behavior).
        for age_row in staging.get("Ages", []):
            _collect_fields_into_row(row, age_row, sources)

        # References — stored in a staging helper table; fold every non-internal
        # field of every reference row. Content fields are prefixed with "_" in
        # the staging format to mark them as staging-only; we strip the prefix
        # for display, but remember the ORIGINAL key in the source mapping so
        # edits write back to the correct dict field.
        for ref_row in staging.get("_Samples_References_staging", []):
            if ref_row.get("_SampleNaturalKey") not in (nk, None):
                continue
            for key, val in ref_row.items():
                if key == "_SampleNaturalKey":
                    continue
                display_key = key.lstrip("_") if _is_internal_field(key) else key
                if val is None or val == "" or val == [] or val == {}:
                    continue
                cell = _truncate(str(val))
                if display_key in row:
                    row[display_key] = _merge_row_values(row[display_key], cell)
                    sources.pop(display_key, None)  # now multi-source, lock it
                else:
                    row[display_key] = cell
                    sources[display_key] = (ref_row, key)  # map to REAL key

        row_dicts.append(row)
        per_row_sources.append(sources)

    # ─── Step 5: discover the union of all columns, then order them ───
    discovered: set[str] = set()
    for r in row_dicts:
        discovered.update(r.keys())
    col_headers = _order_columns(discovered)

    # ─── Step 6: convert per-row column-keyed sources to (row_idx, col_idx) cell_map ───
    # The widget code indexes cells by (row, col) integer pairs, so we re-key
    # once we know the final column ordering. We also attach the original cell
    # value here so the UI can detect edits without a separate lookup.
    col_idx_by_name = {name: i for i, name in enumerate(col_headers)}
    cell_map: dict = {}
    for row_idx, (row_dict, sources) in enumerate(zip(row_dicts, per_row_sources)):
        for col_name, (src_row, field) in sources.items():
            col_idx = col_idx_by_name[col_name]
            original = row_dict[col_name]
            cell_map[(row_idx, col_idx)] = (src_row, field, original)

    return col_headers, row_dicts, cell_map



# ===========================================================================
# Background worker threads
# ===========================================================================

class TransformWorker(QThread):
    """
    Runs the SESAR → staging transform off the main thread.

    Accepts one of three input modes (checked in priority order):
      - raw_data_list (list[dict]): multiple pre-fetched SESAR dicts
            → calls transform_multiple_sesar_samples (batch mode)
      - raw_data (dict): a single pre-fetched SESAR dict (API mode)
            → calls transform_sesar_to_geocork_staging_format
      - json_path (str): path to a local SESAR JSON file (file-browse mode)
            → reads the file then calls transform_sesar_to_geocork_staging_format
    """
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)

    def __init__(
        self,
        json_path:     Optional[str]  = None,
        raw_data:      Optional[dict] = None,
        raw_data_list: Optional[list] = None,
    ):
        super().__init__()
        self.json_path     = json_path
        self.raw_data      = raw_data
        self.raw_data_list = raw_data_list

    def run(self):
        try:
            if self.raw_data_list is not None:
                staging = transform_multiple_sesar_samples(self.raw_data_list)
            elif self.raw_data is not None:
                staging = transform_sesar_to_geocork_staging_format(self.raw_data)
            elif self.json_path is not None:
                raw = json.loads(Path(self.json_path).read_text(encoding="utf-8"))
                staging = transform_sesar_to_geocork_staging_format(raw)
            else:
                raise ValueError(
                    "TransformWorker: none of json_path, raw_data, or "
                    "raw_data_list was provided.")
            self.finished.emit(staging)
        except Exception as exc:
            self.error.emit(str(exc))




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

    Left table  - raw SESAR fields: one row per IGSN, columns = field names.
    Right table - GeoCORK staging:  one row per IGSN, columns = GeoCORK field names.
                  Both panes share the same wide-column layout so they are
                  visually consistent and ready for future per-cell editing.
    """

    import_requested = pyqtSignal(dict)

    def __init__(self, staging: dict, raw_data: Optional[dict] = None,
                 raw_data_list: Optional[list] = None,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.staging       = staging
        self.raw_data      = raw_data
        self.raw_data_list = raw_data_list
        self.setWindowTitle("Preview - SESAR Sample Data")
        self.setMinimumSize(1100, 520)
        self.resize(1400, 620)

        # static_root_Layout_Preview
        static_root_Layout_Preview = QVBoxLayout(self)
        static_root_Layout_Preview.setContentsMargins(16, 16, 16, 12)
        static_root_Layout_Preview.setSpacing(10)

        # ── Header label ─────────────────────────────────────────────────
        # Count unique IGSNs (instance-1 rows only, to avoid duplicates
        # from description instances 2/3/4).
        samples_list = staging.get("Samples") or [{}]
        unique_igsns = {
            s.get("SampleIGSN") or s.get("SampleName")
            for s in samples_list
            if s.get("_DescriptionInstance", 1) == 1
        }
        sample_count = len(unique_igsns)

        if sample_count <= 1:
            igsn = samples_list[0].get("SampleIGSN") or "Unknown"
            name = samples_list[0].get("SampleName") or "Unknown"
            header_text = f"<b>Sample:</b> {name} &nbsp;|&nbsp; <b>IGSN:</b> {igsn}"
        else:
            igsn_preview = ", ".join(list(unique_igsns)[:5])
            if sample_count > 5:
                igsn_preview += f", … (+{sample_count - 5} more)"
            header_text = (
                f"<b>{sample_count} samples queued for import</b>"
                f"&nbsp;|&nbsp; {igsn_preview}"
            )

        static_header_Label_SampleInfo = QLabel(header_text)
        static_header_Label_SampleInfo.setStyleSheet("font-size: 12px; padding: 2px 0;")
        static_header_Label_SampleInfo.setWordWrap(True)
        static_root_Layout_Preview.addWidget(static_header_Label_SampleInfo)

        # static_divider_Frame_Separator
        static_divider_Frame_Separator = QFrame()
        static_divider_Frame_Separator.setFrameShape(QFrame.Shape.HLine)
        static_divider_Frame_Separator.setFrameShadow(QFrame.Shadow.Sunken)
        static_root_Layout_Preview.addWidget(static_divider_Frame_Separator)

        # static_splitter_Splitter_Tables
        static_splitter_Splitter_Tables = QSplitter(Qt.Orientation.Horizontal)
        static_splitter_Splitter_Tables.setChildrenCollapsible(False)

        # ── Left pane: raw SESAR JSON ─────────────────────────────────────
        # One row per IGSN, columns = union of all field names.
        static_left_Layout_RawPane = QVBoxLayout()
        static_left_Layout_RawPane.setContentsMargins(0, 0, 4, 0)
        static_left_Layout_RawPane.setSpacing(4)

        static_rawLabel_Label_PaneTitle = QLabel("Raw SESAR JSON")
        raw_label_font = QFont()
        raw_label_font.setBold(True)
        static_rawLabel_Label_PaneTitle.setFont(raw_label_font)
        static_left_Layout_RawPane.addWidget(static_rawLabel_Label_PaneTitle)

        # Determine which raw dicts to display.
        raw_list = self.raw_data_list if self.raw_data_list else (
            [self.raw_data] if self.raw_data else []
        )

        # Build union of all field names (preserving first-seen order).
        all_row_pairs: list = []
        col_order: list = []
        col_set: set = set()
        for rd in raw_list:
            pairs = build_raw_sesar_table(rd)
            all_row_pairs.append(pairs)
            for field, _ in pairs:
                if field not in col_set:
                    col_order.append(field)
                    col_set.add(field)

        row_dicts = [
            {field: val for field, val in row_pairs}
            for row_pairs in all_row_pairs
        ]

        self.static_raw_TableWidget_RawData = QTableWidget(len(row_dicts), len(col_order))
        self.static_raw_TableWidget_RawData.setObjectName("static_raw_TableWidget_RawData")
        self.static_raw_TableWidget_RawData.setHorizontalHeaderLabels(col_order)
        self.static_raw_TableWidget_RawData.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.static_raw_TableWidget_RawData.verticalHeader().setVisible(False)
        self.static_raw_TableWidget_RawData.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.static_raw_TableWidget_RawData.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectColumns
        )
        self.static_raw_TableWidget_RawData.setAlternatingRowColors(True)
        self.static_raw_TableWidget_RawData.setWordWrap(True)

        for row_idx, row_dict in enumerate(row_dicts):
            for col_idx, col_name in enumerate(col_order):
                cell = row_dict.get(col_name, "-")
                item = QTableWidgetItem(cell)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
                )
                self.static_raw_TableWidget_RawData.setItem(
                    row_idx, col_idx, item
                )

        self.static_raw_TableWidget_RawData.resizeRowsToContents()
        static_left_Layout_RawPane.addWidget(self.static_raw_TableWidget_RawData)

        static_left_Widget_RawPane = QFrame()
        static_left_Widget_RawPane.setLayout(static_left_Layout_RawPane)
        static_splitter_Splitter_Tables.addWidget(static_left_Widget_RawPane)

        # ── Right pane: GeoCORK staging ────────────────────────────────────
        # Wide-column layout: fields as column headers, one row per IGSN.
        # Mirrors the left pane so both tables are visually consistent and
        # the layout is ready for future per-cell editing.
        static_right_Layout_StagingPane = QVBoxLayout()
        static_right_Layout_StagingPane.setContentsMargins(4, 0, 0, 0)
        static_right_Layout_StagingPane.setSpacing(4)

        static_stagingLabel_Label_PaneTitle = QLabel("GeoCORK Staging")
        staging_label_font = QFont()
        staging_label_font.setBold(True)
        static_stagingLabel_Label_PaneTitle.setFont(staging_label_font)
        static_right_Layout_StagingPane.addWidget(static_stagingLabel_Label_PaneTitle)

        # Build the wide-column staging data: dynamic columns, one row per IGSN.
        # cell_map holds (source_row_ref, field_name, original_value) for every
        # editable cell so that edits in the UI can be written back to the
        # correct underlying staging dict location.
        staging_col_headers, staging_row_dicts, staging_cell_map = \
            _build_staging_table(staging)

        # Stash on self so the edit handler can consult them later.
        self._staging_cell_map = staging_cell_map
        self._staging_col_headers = staging_col_headers

        self.static_preview_TableWidget_StagingData = QTableWidget(
            len(staging_row_dicts), len(staging_col_headers)
        )
        self.static_preview_TableWidget_StagingData.setObjectName(
            "static_preview_TableWidget_StagingData"
        )
        self.static_preview_TableWidget_StagingData.setHorizontalHeaderLabels(
            staging_col_headers
        )
        self.static_preview_TableWidget_StagingData.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.static_preview_TableWidget_StagingData.verticalHeader().setVisible(False)
        # Editable cells: double-click or start typing to edit. Non-editable
        # cells ignore these triggers because their ItemIsEditable flag is off.
        self.static_preview_TableWidget_StagingData.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked
            | QTableWidget.EditTrigger.AnyKeyPressed
        )
        # SelectItems (not SelectColumns) — editing one cell shouldn't select
        # the whole column.
        self.static_preview_TableWidget_StagingData.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectItems
        )
        self.static_preview_TableWidget_StagingData.setAlternatingRowColors(True)
        self.static_preview_TableWidget_StagingData.setWordWrap(True)

        # Columns likely to contain long free-form text. They're fixed-width
        # so word wrap kicks in rather than these columns expanding to fit
        # the longest paragraph. Any column name from this set gets capped;
        # other columns stay ResizeToContents.
        _LONG_TEXT_COLUMNS = {
            "SampleDescription",
            "SampleDescription [2]",
            "SampleDescription [3]",
            "SampleDescription [4]",
            "RegionDescription",
            "RockTypeDescription",
            "SamplingMethodDescription",
            "SampleContextDescription",
            "AgeDescription",
            "UnitDescription",
            "ReferenceCitation",
            "ReferenceTitle",
        }
        long_col_indices = [
            i for i, name in enumerate(staging_col_headers)
            if name in _LONG_TEXT_COLUMNS
        ]

        # Populate cells. For each cell, decide editability:
        #   - Editable iff: (row, col) is in cell_map AND the column isn't
        #     locked by _is_column_locked() AND the cell value isn't "-"
        #     (i.e. a missing-field placeholder).
        # Read-only cells get muted grey text so the user sees at a glance
        # which cells they can vs. can't edit.
        # We also stash the cell's original string on the item via UserRole,
        # so the change handler can distinguish "back to original" from
        # "genuinely edited" for the edit-marker styling.
        #
        # NOTE: itemChanged is connected AFTER the loop so that this initial
        # population doesn't fire N*M spurious change events.
        for row_idx, row_dict in enumerate(staging_row_dicts):
            for col_idx, col_name in enumerate(staging_col_headers):
                cell = row_dict.get(col_name, "-")
                item = QTableWidgetItem(cell)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
                )
                # Stash the original for later edit-detection.
                item.setData(Qt.ItemDataRole.UserRole, cell)

                is_reverse_mappable = (row_idx, col_idx) in staging_cell_map
                is_locked_col = _is_column_locked(col_name)
                is_placeholder = (cell == "-")
                editable = is_reverse_mappable and not is_locked_col and not is_placeholder

                flags = item.flags()
                if editable:
                    flags |= Qt.ItemFlag.ItemIsEditable
                else:
                    flags &= ~Qt.ItemFlag.ItemIsEditable
                    # Muted text color so the user can visually tell read-only
                    # cells apart from editable ones.
                    item.setForeground(QBrush(_LOCKED_TEXT_COLOR))
                item.setFlags(flags)

                self.static_preview_TableWidget_StagingData.setItem(
                    row_idx, col_idx, item
                )

        header = self.static_preview_TableWidget_StagingData.horizontalHeader()
        for col_idx in long_col_indices:
            header.setSectionResizeMode(col_idx, QHeaderView.ResizeMode.Fixed)
            self.static_preview_TableWidget_StagingData.setColumnWidth(col_idx, 260)

        # Connect the change handler AFTER population so the initial setItem()
        # calls above don't each trigger a fake "edit".
        self.static_preview_TableWidget_StagingData.itemChanged.connect(
            self._on_cell_changed
        )

        self.static_preview_TableWidget_StagingData.resizeRowsToContents()
        static_right_Layout_StagingPane.addWidget(
            self.static_preview_TableWidget_StagingData
        )

        static_right_Widget_StagingPane = QFrame()
        static_right_Widget_StagingPane.setLayout(static_right_Layout_StagingPane)
        static_splitter_Splitter_Tables.addWidget(static_right_Widget_StagingPane)

        # Give both panes equal initial width
        static_splitter_Splitter_Tables.setSizes([700, 700])
        static_root_Layout_Preview.addWidget(static_splitter_Splitter_Tables)

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

    # ------------------------------------------------------------------
    def _on_cell_changed(self, item: QTableWidgetItem) -> None:
        """
        Write user edits from the staging preview back into self.staging.

        The cell map tells us which staging-dict row and field each cell
        originated from; mutating that dict here makes the edit visible to
        _on_import_clicked automatically (self.staging is emitted unchanged —
        the mutation is in place on the dicts it references).

        Blanking a cell removes the field from the source dict entirely
        (so the importer writes NULL / skips it); any other edit writes the
        new string back verbatim.

        Visual styling: edited cells get bold + a pale yellow background so
        users can see their changes at a glance. Reverting a cell back to
        its original value removes that styling.
        """
        key = (item.row(), item.column())
        mapping = self._staging_cell_map.get(key)
        if mapping is None:
            # Shouldn't happen for editable cells, but guard defensively —
            # e.g. in case Qt fires itemChanged for a cell we never registered.
            return

        source_row, field_name, original_value = mapping
        new_text = item.text()

        # ─── Mutate the underlying staging dict ───
        if new_text == "" or new_text is None:
            # Blank cell → remove the field entirely so the importer treats
            # it as unset. Guard against KeyError in case the field was
            # already removed on a previous edit-then-reclear cycle.
            source_row.pop(field_name, None)
        else:
            source_row[field_name] = new_text

        # ─── Apply edit-marker styling ───
        # Setting font/background fires itemChanged again, so block the signal
        # for the duration of the restyle to avoid infinite recursion.
        table = self.static_preview_TableWidget_StagingData
        was_blocked = table.blockSignals(True)
        try:
            font = item.font()
            if new_text != original_value:
                # Edited: bold text + pale yellow background
                font.setBold(True)
                item.setFont(font)
                item.setBackground(QBrush(_EDITED_BG_COLOR))
            else:
                # Reverted to original: reset to default styling
                font.setBold(False)
                item.setFont(font)
                item.setBackground(_DEFAULT_BG_BRUSH)
        finally:
            table.blockSignals(was_blocked)


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
        raw_data:      Optional[dict]   = None,
        raw_data_list: Optional[list]   = None,
        on_cancelled:  Optional[object] = None,
        parent:        Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("SESAR → GeoCORK Importer")
        self.setMinimumWidth(560)
        self.resize(600, 230)
        self.setModal(True)

        self._raw_data:         Optional[dict]            = raw_data
        self._raw_data_list:    Optional[list]            = raw_data_list
        self._on_cancelled      = on_cancelled
        self._staging:          Optional[dict]            = None
        self._json_path:        Optional[str]             = None

        if raw_data is not None or raw_data_list is not None:
            from PyQt6.QtSql import QSqlDatabase
            self._db_path: Optional[str] = QSqlDatabase.database().databaseName() or None
        else:
            self._db_path: Optional[str] = None
        self._transform_worker: Optional[TransformWorker] = None
        self._loading_dlg:      Optional[LoadingDialog]   = None
        self._preview_win:      Optional[PreviewWindow]   = None

        if self._raw_data is not None or self._raw_data_list is not None:
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
        if self._raw_data is not None or self._raw_data_list is not None:
            self.btn_loadPreview_Action.setEnabled(bool(self._db_path))
        else:
            self.btn_loadPreview_Action.setEnabled(
                bool(self._json_path) and bool(self._db_path)
            )

    # ------------------------------------------------------------------
    def _start_transform(self) -> None:
        self._loading_dlg = LoadingDialog("Loading", "Transforming SESAR data…", self)
        self._transform_worker = TransformWorker(
            json_path=self._json_path,
            raw_data=self._raw_data,
            raw_data_list=self._raw_data_list,
        )
        self._transform_worker.finished.connect(self._on_transform_done)
        self._transform_worker.error.connect(self._on_transform_error)
        self._transform_worker.start()

    def _on_load_preview(self) -> None:
        self.btn_loadPreview_Action.setEnabled(False)
        self._start_transform()

    def _on_transform_done(self, staging: dict) -> None:
        self._staging = staging
        if self._loading_dlg:
            self._loading_dlg.set_message("Building preview…")

        self._preview_win = PreviewWindow(
            staging,
            raw_data=self._raw_data,
            raw_data_list=self._raw_data_list,
            parent=self,
        )
        self._preview_win.import_requested.connect(self._on_import_requested)

        # Wire Back button to on_cancelled so ImportFromSesar re-shows itself.
        if self._on_cancelled is not None:
            self._preview_win.rejected.connect(self._on_cancelled)

        if self._loading_dlg:
            self._loading_dlg.close()
            self._loading_dlg = None

        if self._raw_data is None and self._raw_data_list is None:
            self.btn_loadPreview_Action.setEnabled(True)

        self._preview_win.exec()

    def _on_transform_error(self, msg: str) -> None:
        if self._loading_dlg:
            self._loading_dlg.close()
            self._loading_dlg = None
        if self._raw_data is None and self._raw_data_list is None:
            self.btn_loadPreview_Action.setEnabled(True)
        QMessageBox.critical(
            self, "Transform Error",
            f"Failed to process SESAR JSON:\n\n{msg}"
        )

    # ------------------------------------------------------------------
    def _on_import_requested(self, staging: dict) -> None:
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
        if self._preview_win:
            self._preview_win.accept()
            self._preview_win = None

        if self._raw_data is not None or self._raw_data_list is not None:
            msg = (f"✓ Import successful!\n\n"
                   f"Sample(s) added to: {Path(out_db).name}")
        else:
            msg = (f"✓ Import successful!\n\n"
                   f"Output database:\n{Path(out_db).name}")
        QMessageBox.information(self, "Import Complete", msg)
        self.accept()

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
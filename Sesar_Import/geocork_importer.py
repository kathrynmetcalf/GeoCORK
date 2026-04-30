"""
geocork_importer.py
-------------------
Imports a GeoCORK staging JSON (produced by json_staging_transformer.py)
directly into the already-open GeoCORK database.

Entry point:

  import_staging_inplace(staging, db_path)
      Writes into the currently-open GeoCORK database using the Qt
      QSqlDatabase / QSqlQuery layer so that GeoCORK's savepoint system
      (Savepoint_manager.py) covers every write.

ParentRow rule:
    ParentRow is a SIBLING POSITION INDEX — the sequential order of a node
    among all nodes sharing the same ParentID (NULL or a real ID).
    It starts at 0 for the first child of any parent and increments by 1
    for each additional sibling.

    When inserting a new node:
        1. Query MAX(ParentRow) WHERE ParentID matches (NULL or specific ID)
        2. new ParentRow = MAX + 1, or 0 if no siblings exist yet
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from Sesar_Import.sesar_logger import get_sesar_logger


def is_filled(x: Any) -> bool:
    """Return False for values that are None, empty string, empty list, or empty dict."""
    return x not in (None, "", [], {})


# Helpers — QSqlQuery layer (used by import_staging_inplace only)
# ---------------------------------------------------------------------------

def _q_resolve_unit_id(value: Any, unit_table: str,
                        abbrev_col: str, id_col: str) -> Optional[int]:
    """Qt-layer equivalent of resolve_unit_id."""
    from PyQt6.QtSql import QSqlQuery
    if not is_filled(value):
        return None
    val = str(value).strip()
    q = QSqlQuery()
    q.prepare(f"SELECT {id_col} FROM {unit_table} WHERE lower({abbrev_col}) = lower(?)")
    q.addBindValue(val)
    q.exec()
    if q.next():
        return q.value(0)
    # Fallback: full name column
    name_col = id_col.replace("ID", "Name")
    q2 = QSqlQuery()
    q2.prepare(f"SELECT {id_col} FROM {unit_table} WHERE lower({name_col}) = lower(?)")
    q2.addBindValue(val)
    q2.exec()
    if q2.next():
        return q2.value(0)
    get_sesar_logger().warning(f"[SESAR import] Unit {value!r} not found in {unit_table}")
    return None


def _q_next_sibling_parent_row(table: str, id_col: str, parent_id_col: str,
                                parent_row_col: str, parent_id: Optional[int]) -> int:
    """Qt-layer equivalent of next_sibling_parent_row."""
    from PyQt6.QtSql import QSqlQuery
    q = QSqlQuery()
    if parent_id is None:
        q.prepare(
            f"SELECT MAX({parent_row_col}) FROM {table} WHERE {parent_id_col} IS NULL")
    else:
        q.prepare(
            f"SELECT MAX({parent_row_col}) FROM {table} WHERE {parent_id_col} = ?")
        q.addBindValue(parent_id)
    q.exec()
    # MAX() on an empty table returns SQL NULL; the Qt SQLite driver may
    # surface this as Python None, empty string "", or 0 depending on the
    # driver version. Treat any non-integer-castable value as "no rows yet".
    raw = q.value(0) if q.next() else None
    try:
        max_row = int(raw)
    except (TypeError, ValueError):
        max_row = -1
    return max_row + 1


def _q_insert_tree_row(
    table: str,
    id_col: str,
    parent_id_col: str,
    parent_row_col: str,
    name_col: str,
    name: str,
    parent_id: Optional[int],
    extra_cols: Optional[Dict[str, Any]] = None,
    name_cache: Optional[Dict[str, int]] = None,
) -> int:
    """Qt-layer equivalent of insert_tree_row."""
    from PyQt6.QtSql import QSqlQuery
    if name_cache is not None and name in name_cache:
        return name_cache[name]

    # Check for existing row
    q = QSqlQuery()
    q.prepare(f"SELECT {id_col} FROM {table} WHERE {name_col} = ? COLLATE NOCASE")
    q.addBindValue(name)
    q.exec()
    if q.next():
        row_id = q.value(0)
        if name_cache is not None:
            name_cache[name] = row_id
        return row_id

    parent_row = _q_next_sibling_parent_row(
        table, id_col, parent_id_col, parent_row_col, parent_id)

    cols = [name_col, parent_id_col, parent_row_col]
    vals: List[Any] = [name, parent_id, parent_row]
    if extra_cols:
        for k, v in extra_cols.items():
            if is_filled(v):
                cols.append(k)
                vals.append(v)

    placeholders = ", ".join(["?"] * len(vals))
    ins = QSqlQuery()
    ins.prepare(
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})")
    for v in vals:
        ins.addBindValue(v)
    if not ins.exec():
        raise RuntimeError(
            f"Insert into {table} failed: {ins.lastError().text()}")
    row_id = ins.lastInsertId()
    if name_cache is not None:
        name_cache[name] = row_id
    return row_id


def _q_insert_bridge(table: str, col_a: str, col_b: str,
                      id_a: int, id_b: int) -> None:
    """Qt-layer equivalent of insert_bridge."""
    from PyQt6.QtSql import QSqlQuery
    q = QSqlQuery()
    q.prepare(f"INSERT INTO {table} ({col_a}, {col_b}) VALUES (?, ?)")
    q.addBindValue(id_a)
    q.addBindValue(id_b)
    if not q.exec():
        err = q.lastError().text()
        if "UNIQUE" in err or "PRIMARY KEY" in err:
            return
        raise RuntimeError(f"Insert bridge into {table} failed: {err}")

# ---------------------------------------------------------------------------
# Inplace importer — writes into the already-open GeoCORK database
# Uses QSqlQuery throughout so GeoCORK's savepoint system covers every write.
# Called from ImportWorker (ImportFromSesarBuildWindow.py) when importing via
# the SESAR UI into the currently-open database.
# ---------------------------------------------------------------------------

def import_staging_inplace(staging: dict, db_path: str) -> None:
    """
    Import a staging dict directly into the already-open GeoCORK database.

    Uses the Qt QSqlDatabase default connection (QSqlDatabase.database()) so
    that savepoints created by Savepoint_manager cover every insert and the
    whole operation can be rolled back atomically if anything goes wrong.

    Savepoint strategy (mirrors ImportWizard pattern):
      - Outer savepoint 'sesar_import' wraps the entire operation.
      - Inner savepoint 'sesar_import_upb_chain' wraps the Aliquot/Spot/
        UPbAnalysis stub inserts specifically, since a failure there would
        leave samples stranded and invisible in the UI.
      - On any exception, rolls back the outermost savepoint so the DB is
        left exactly as it was before the import started.
      - On success, releases 'sesar_import' to commit permanently.

    Parameters
    ----------
    staging : dict
        The staging dict produced by json_staging_transformer.py.
    db_path : str
        Path to the open .db file (used only for logging; writes go through
        the Qt default connection, not a new sqlite3 connection).
    """
    from PyQt6.QtSql import QSqlQuery
    from Functions.Savepoint_manager import (
        create_savepoint, release_savepoint, rollback_savepoint)

    log = get_sesar_logger()
    log.info(f"[SESAR import] Starting inplace import into {db_path}")

    # ------------------------------------------------------------------
    # Outer savepoint — wraps the entire SESAR import operation.
    # If anything fails, ROLLBACK TO SAVEPOINT sesar_import restores the
    # DB to its exact pre-import state.
    # ------------------------------------------------------------------
    if not create_savepoint("sesar_import"):
        raise RuntimeError(
            "Could not create savepoint 'sesar_import' — import aborted.")

    try:
        # ---------------------------------------------------------------
        # 1. GPS Locations
        # ---------------------------------------------------------------
        gps_key_to_id: Dict[str, int] = {}

        for gps in staging.get("GPSLocations", []):
            elev_unit_id = _q_resolve_unit_id(
                gps.get("_GPSElevUnitAbbrev"),
                "DistanceUnits", "DistanceUnitAbbreviation", "DistanceUnitID")
            q = QSqlQuery()
            q.prepare("""
                INSERT INTO GPSLocations
                    (GPSLocationConverted, GPSLatDeg, GPSLatMin, GPSLatSec,
                     GPSLatDirectionID, GPSLonDeg, GPSLonMin, GPSLonSec,
                     GPSLonDirectionID, GPSUTMZone, GPSUTMN, GPSUTME,
                     GPSFormatID, GPSElev, GPSElevError, GPSElevUnitID)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """)
            for v in (
                gps.get("GPSLocationConverted"),
                gps.get("GPSLatDeg"),   gps.get("GPSLatMin"),   gps.get("GPSLatSec"),
                gps.get("GPSLatDirectionID"),
                gps.get("GPSLonDeg"),   gps.get("GPSLonMin"),   gps.get("GPSLonSec"),
                gps.get("GPSLonDirectionID"),
                gps.get("GPSUTMZone"),  gps.get("GPSUTMN"),     gps.get("GPSUTME"),
                gps.get("GPSFormatID"),
                gps.get("GPSElev"),     gps.get("GPSElevError"), elev_unit_id,
            ):
                q.addBindValue(v)
            if not q.exec():
                raise RuntimeError(f"GPS insert failed: {q.lastError().text()}")
            gps_key_to_id[gps["_gps_key"]] = q.lastInsertId()
            log.info(f"  [GPS] id={q.lastInsertId()}  lat={gps.get('GPSLatDeg')}")

        # ---------------------------------------------------------------
        # 2. Columns (core samples only)
        # ---------------------------------------------------------------
        column_name_to_id: Dict[str, int] = {}

        for col in staging.get("Columns", []):
            unit_id = _q_resolve_unit_id(
                col.get("_ColumnHeightDepthUnitAbbrev"),
                "DistanceUnits", "DistanceUnitAbbreviation", "DistanceUnitID")
            base_gps_id = gps_key_to_id.get(col.get("_ColumnBaseGPSKey"))
            q = QSqlQuery()
            q.prepare("""
                INSERT INTO Columns
                    (ColumnName, ColumnTotalHeightDepth, ColumnTotalHeightDepthUnitID,
                     ColumnBaseGPSID, ColumnDescription)
                VALUES (?,?,?,?,?)
            """)
            for v in (col["ColumnName"], col.get("ColumnTotalHeightDepth"),
                      unit_id, base_gps_id, col.get("ColumnDescription")):
                q.addBindValue(v)
            if not q.exec():
                raise RuntimeError(f"Column insert failed: {q.lastError().text()}")
            column_name_to_id[col["ColumnName"]] = q.lastInsertId()
            log.info(f"  [Column] id={q.lastInsertId()}  name={col['ColumnName']!r}")

        # ---------------------------------------------------------------
        # 3. Samples
        #
        # One Samples row per IGSN. SampleDescription is synthesized here
        # from the _SampleDescriptionFields staging list rather than being
        # read directly off the row — this way the preview window's
        # per-cell edits (which mutate individual field entries) are the
        # single source of truth for description content.
        # ---------------------------------------------------------------
        sample_nk_to_id: Dict[str, int] = {}

        # Pre-group the per-field description entries by natural key so we
        # can assemble each sample's SampleDescription in one lookup rather
        # than filtering the full list for every sample. In batch mode this
        # list can get long (N samples × up to 22 fields each).
        sd_fields_by_nk: Dict[str, List[Dict[str, Any]]] = {}
        for entry in staging.get("_SampleDescriptionFields", []):
            nk = entry.get("_SampleNaturalKey")
            if nk is None:
                continue
            sd_fields_by_nk.setdefault(nk, []).append(entry)

        def _synthesize_sample_description(nk: str) -> Optional[str]:
            """
            Rebuild the concatenated SampleDescription TEXT for one sample.

            Matches the format produced by the old sd1+sd2+sd3+sd4 code:
              - Each field becomes one line formatted "Label: Value"
              - Fields are ordered by (Group, Order) so sd1 comes before sd2
                before sd3 before sd4, and within each group the order is
                the same as the field-definition list in the transformer.
              - A blank line separates consecutive groups (reproduces the
                "\\n\\n" that the old instance-2/3/4 UPDATE branch appended).
              - Empty/blank Value entries are dropped (implements the Q5
                "clear to drop" behavior from the UI).
              - Returns None if no field has a non-empty value, so the row
                stores SQL NULL rather than an empty string.
            """
            entries = sd_fields_by_nk.get(nk, [])
            # Sort by (group, order) so output is deterministic regardless of
            # how the transformer or preview happened to order the list.
            entries = sorted(
                entries,
                key=lambda e: (e.get("Group", 0), e.get("Order", 0))
            )
            lines: List[str] = []
            prev_group: Optional[int] = None
            for e in entries:
                val = e.get("Value")
                if not is_filled(val):
                    continue
                label = e.get("Label") or ""
                group = e.get("Group")
                # Blank line between groups so sd1/sd2/sd3/sd4 are visually
                # separated in the DB string, same as the old output.
                if prev_group is not None and group != prev_group:
                    lines.append("")
                lines.append(f"{label}: {val}")
                prev_group = group
            if not lines:
                return None
            return "\n".join(lines)

        for s in staging.get("Samples", []):
            nk = s.get("SampleIGSN") or s.get("SampleName")

            # Guard against a repeat natural key (shouldn't happen in the
            # new one-row-per-IGSN world, but cheap insurance against any
            # future regression in the transformer).
            if nk in sample_nk_to_id:
                log.warning(
                    f"  [Sample] duplicate natural key {nk!r} — skipping "
                    f"(already inserted as SampleID={sample_nk_to_id[nk]})")
                continue

            gps_id  = gps_key_to_id.get(s.get("_SampleGPSKey"))
            col_id  = column_name_to_id.get(s.get("_ColumnName"))
            unit_id = _q_resolve_unit_id(
                s.get("_HeightDepthUnitAbbrev"),
                "DistanceUnits", "DistanceUnitAbbreviation", "DistanceUnitID")
            # Synthesize the final description TEXT from the field list. The
            # SampleDescription value on the Samples row itself is ignored
            # here on purpose — the field list is authoritative.
            desc = _synthesize_sample_description(nk)

            q = QSqlQuery()
            q.prepare("""
                INSERT INTO Samples
                    (SampleName, SampleIGSN, SampleGPSLocationID, SampleColumnID,
                     HeightDepth, HeightDepthError, HeightDepthUnitID, SampleDescription)
                VALUES (?,?,?,?,?,?,?,?)
            """)
            for v in (s.get("SampleName"), s.get("SampleIGSN"),
                      gps_id, col_id,
                      s.get("HeightDepth"), s.get("HeightDepthError"),
                      unit_id, desc):
                q.addBindValue(v)
            if not q.exec():
                raise RuntimeError(f"Sample insert failed: {q.lastError().text()}")
            sample_id = q.lastInsertId()
            sample_nk_to_id[nk] = sample_id
            log.info(f"  [Sample] id={sample_id}  name={s.get('SampleName')!r}")

        # ---------------------------------------------------------------
        # 3b. Stub Aliquot -> Spot -> UPbAnalysis chain
        #
        # Inner savepoint: if this step fails the samples were already
        # inserted, so roll back to 'sesar_import' (outer) rather than
        # 'sesar_import_upb_chain' (inner) to undo everything cleanly.
        # ---------------------------------------------------------------
        if not create_savepoint("sesar_import_upb_chain"):
            raise RuntimeError(
                "Could not create savepoint 'sesar_import_upb_chain' — import aborted.")

        try:
            for nk, sample_id in sample_nk_to_id.items():
                # Fetch the sample name for use as stub row label
                q = QSqlQuery()
                q.prepare("SELECT SampleName FROM Samples WHERE SampleID = ?")
                q.addBindValue(sample_id)
                q.exec()
                sample_name = q.value(0) if q.next() else str(nk)

                # Stub Aliquot
                q = QSqlQuery()
                q.prepare(
                    "INSERT INTO Aliquots "
                    "(AliquotName, ParentAliquotID, AliquotParentRow, SampleID) "
                    "VALUES (?, NULL, 0, ?)")
                q.addBindValue(sample_name)
                q.addBindValue(sample_id)
                if not q.exec():
                    raise RuntimeError(
                        f"Stub Aliquot insert failed: {q.lastError().text()}")
                aliquot_id = q.lastInsertId()

                # Stub Spot
                q = QSqlQuery()
                q.prepare("INSERT INTO Spots (SpotName, AliquotID) VALUES (?, ?)")
                q.addBindValue(sample_name)
                q.addBindValue(aliquot_id)
                if not q.exec():
                    raise RuntimeError(
                        f"Stub Spot insert failed: {q.lastError().text()}")
                spot_id = q.lastInsertId()

                # Stub UPbAnalysis
                q = QSqlQuery()
                q.prepare(
                    "INSERT INTO UPbAnalyses (UPbAnalysisName, SpotID, Rejected) "
                    "VALUES (?, ?, 0)")
                q.addBindValue(sample_name)
                q.addBindValue(spot_id)
                if not q.exec():
                    raise RuntimeError(
                        f"Stub UPbAnalysis insert failed: {q.lastError().text()}")
                log.info(
                    f"  [Stub chain] SampleID={sample_id}  "
                    f"AliquotID={aliquot_id}  SpotID={spot_id}")

            release_savepoint("sesar_import_upb_chain")

        except Exception:
            # Inner failure — roll back only the stub chain inserts.
            # The outer rollback in the except below will then undo the samples too.
            rollback_savepoint("sesar_import_upb_chain")
            raise

        # ---------------------------------------------------------------
        # 4. Regions tree
        # ---------------------------------------------------------------
        region_cache: Dict[str, int] = {}

        for reg in staging.get("Regions", []):
            parent_id = region_cache.get(reg["_ParentRegionName"]) \
                        if reg.get("_ParentRegionName") else None
            reg_id = _q_insert_tree_row(
                "Regions", "RegionID", "ParentRegionID", "RegionParentRow",
                "RegionName", reg["RegionName"], parent_id,
                extra_cols={"RegionDescription": reg.get("RegionDescription")},
                name_cache=region_cache)
            log.info(f"  [Region] id={reg_id}  name={reg['RegionName']!r}")

        for bridge in staging.get("Samples_Regions", []):
            sid = sample_nk_to_id.get(bridge["_SampleNaturalKey"])
            rid = region_cache.get(bridge["_RegionName"])
            if sid and rid:
                _q_insert_bridge("Samples_Regions", "SampleID", "RegionID", sid, rid)

        # ---------------------------------------------------------------
        # 5. SamplingMethods tree
        # ---------------------------------------------------------------
        method_cache: Dict[str, int] = {}

        for method in staging.get("SamplingMethods", []):
            parent_id = method_cache.get(method["_ParentSamplingMethodName"]) \
                        if method.get("_ParentSamplingMethodName") else None
            m_id = _q_insert_tree_row(
                "SamplingMethods", "SamplingMethodID", "ParentSamplingMethodID",
                "SamplingMethodParentRow", "SamplingMethodName",
                method["SamplingMethodName"], parent_id,
                extra_cols={"SamplingMethodDescription": method.get("SamplingMethodDescription")},
                name_cache=method_cache)
            log.info(f"  [SamplingMethod] id={m_id}  name={method['SamplingMethodName']!r}")

        for bridge in staging.get("Samples_SamplingMethods", []):
            sid = sample_nk_to_id.get(bridge["_SampleNaturalKey"])
            mid = method_cache.get(bridge["_SamplingMethodName"])
            if sid and mid:
                _q_insert_bridge("Samples_SamplingMethods",
                                 "SampleID", "SamplingMethodID", sid, mid)

        # ---------------------------------------------------------------
        # 6. RockTypes tree
        # ---------------------------------------------------------------
        rocktype_cache: Dict[str, int] = {}

        for rt in staging.get("RockTypes", []):
            parent_id = rocktype_cache.get(rt["_ParentRockTypeName"]) \
                        if rt.get("_ParentRockTypeName") else None
            rt_id = _q_insert_tree_row(
                "RockTypes", "RockTypeID", "ParentRockTypeID", "RockTypeParentRow",
                "RockTypeName", rt["RockTypeName"], parent_id,
                extra_cols={"RockTypeDescription": rt.get("RockTypeDescription")},
                name_cache=rocktype_cache)
            log.info(f"  [RockType] id={rt_id}  name={rt['RockTypeName']!r}")

        for bridge in staging.get("Samples_RockTypes", []):
            sid  = sample_nk_to_id.get(bridge["_SampleNaturalKey"])
            rtid = rocktype_cache.get(bridge["_RockTypeName"])
            if sid and rtid:
                _q_insert_bridge("Samples_RockTypes",
                                 "SampleID", "RockTypeID", sid, rtid)

        # ---------------------------------------------------------------
        # 7. SampleContexts tree
        # ---------------------------------------------------------------
        ctx_cache: Dict[str, int] = {}

        for ctx in staging.get("SampleContexts", []):
            ctx_id = _q_insert_tree_row(
                "SampleContexts", "SampleContextID", "ParentSampleContextID",
                "SampleContextParentRow", "SampleContextName",
                ctx["SampleContextName"], None,
                extra_cols={"SampleContextDescription": ctx.get("SampleContextDescription")},
                name_cache=ctx_cache)
            log.info(f"  [SampleContext] id={ctx_id}  name={ctx['SampleContextName']!r}")

        for bridge in staging.get("Samples_SampleContexts", []):
            sid   = sample_nk_to_id.get(bridge["_SampleNaturalKey"])
            ctxid = ctx_cache.get(bridge["_SampleContextName"])
            if sid and ctxid:
                _q_insert_bridge("Samples_SampleContexts",
                                 "SampleID", "SampleContextID", sid, ctxid)

        # ---------------------------------------------------------------
        # 8. Ages tree
        # ---------------------------------------------------------------
        age_cache: Dict[str, int] = {}

        for age in staging.get("Ages", []):
            age_id = _q_insert_tree_row(
                "Ages", "AgeID", "ParentAgeID", "AgeParentRow", "AgeName",
                age["AgeName"], None,
                extra_cols={"OldestAge": age.get("OldestAge"),
                            "YoungestAge": age.get("YoungestAge")},
                name_cache=age_cache)
            log.info(f"  [Age] id={age_id}  name={age['AgeName']!r}")

        # ---------------------------------------------------------------
        # 9. Units tree
        # ---------------------------------------------------------------
        unit_cache: Dict[str, int] = {}

        for unit in staging.get("Units", []):
            u_id = _q_insert_tree_row(
                "Units", "UnitID", "ParentUnitID", "UnitParentRow", "UnitName",
                unit["UnitName"], None,
                name_cache=unit_cache)
            log.info(f"  [Unit] id={u_id}  name={unit['UnitName']!r}")

        for bridge in staging.get("Samples_Units", []):
            sid = sample_nk_to_id.get(bridge["_SampleNaturalKey"])
            uid = unit_cache.get(bridge["_UnitName"])
            if sid and uid:
                _q_insert_bridge("Samples_Units", "SampleID", "UnitID", sid, uid)

        # ---------------------------------------------------------------
        # 10. References
        # ---------------------------------------------------------------
        ref_key_to_id: Dict[str, int] = {}

        for ref in staging.get("References", []):
            dedup_key = ref.get("DOI") or ref.get("Title") or \
                        (ref.get("ReferenceDescription") or "")[:80]

            # Check for existing reference to avoid duplicates
            q = QSqlQuery()
            if ref.get("DOI"):
                q.prepare('SELECT ReferenceID FROM "References" WHERE DOI = ?')
                q.addBindValue(ref["DOI"])
            elif ref.get("Title"):
                q.prepare('SELECT ReferenceID FROM "References" WHERE Title = ?')
                q.addBindValue(ref["Title"])
            else:
                q.prepare('SELECT ReferenceID FROM "References" '
                          'WHERE ReferenceDescription = ?')
                q.addBindValue(ref.get("ReferenceDescription"))
            q.exec()

            if q.next():
                ref_id = q.value(0)
            else:
                ins = QSqlQuery()
                ins.prepare("""
                    INSERT INTO "References"
                        (Authors, Year, Title, Source, DOI, ReferenceDescription)
                    VALUES (?,?,?,?,?,?)
                """)
                for v in (ref.get("Authors"), ref.get("Year"), ref.get("Title"),
                          ref.get("Source"), ref.get("DOI"),
                          ref.get("ReferenceDescription")):
                    ins.addBindValue(v)
                if not ins.exec():
                    raise RuntimeError(
                        f"Reference insert failed: {ins.lastError().text()}")
                ref_id = ins.lastInsertId()
            ref_key_to_id[dedup_key] = ref_id
            log.info(f"  [Reference] id={ref_id}  DOI={ref.get('DOI')!r}")

        # ---------------------------------------------------------------
        # 11. SampleAges + bridges
        # ---------------------------------------------------------------
        sa_index_to_id: Dict[int, int] = {}

        for i, sa in enumerate(staging.get("SampleAges", [])):
            oldest_age_id   = age_cache.get(sa.get("_OldestAgeName"))
            youngest_age_id = age_cache.get(sa.get("_YoungestAgeName"))
            q = QSqlQuery()
            q.prepare("""
                INSERT INTO SampleAges
                    (DirectAge, DirectAgeError, DirectAgeErrorFormatID,
                     OldestDirectAge, YoungestDirectAge, DirectAgeUnitID,
                     OldestAgeID, YoungestAgeID, SampleAgeDescription)
                VALUES (?,?,?,?,?,?,?,?,?)
            """)
            for v in (
                sa.get("DirectAge"), sa.get("DirectAgeError"),
                sa.get("DirectAgeErrorFormatID"),
                sa.get("OldestDirectAge"), sa.get("YoungestDirectAge"),
                sa.get("DirectAgeUnitID"),
                oldest_age_id, youngest_age_id, sa.get("SampleAgeDescription"),
            ):
                q.addBindValue(v)
            if not q.exec():
                raise RuntimeError(f"SampleAge insert failed: {q.lastError().text()}")
            sa_index_to_id[i] = q.lastInsertId()
            log.info(f"  [SampleAge] id={q.lastInsertId()}")

        for bridge in staging.get("Samples_SampleAges", []):
            sid  = sample_nk_to_id.get(bridge["_SampleNaturalKey"])
            said = sa_index_to_id.get(bridge.get("_SampleAgeIndex", 0))
            if sid and said:
                _q_insert_bridge("Samples_SampleAges",
                                 "SampleID", "SampleAgeID", sid, said)

        # ---------------------------------------------------------------
        # Success — release the outer savepoint to permanently commit
        # ---------------------------------------------------------------
        release_savepoint("sesar_import")
        log.info(
            f"[SESAR import] Complete — "
            f"{len(sample_nk_to_id)} sample(s), "
            f"{len(gps_key_to_id)} GPS location(s), "
            f"{len(region_cache)} region(s), "
            f"{len(rocktype_cache)} rock type(s), "
            f"{len(method_cache)} sampling method(s), "
            f"{len(ctx_cache)} sample context(s)."
        )

    except Exception as exc:
        # Roll back every insert made since 'sesar_import' was created,
        # leaving the DB in its exact pre-import state.
        rollback_savepoint("sesar_import")
        log.error(f"[SESAR import] FAILED — rolled back to savepoint. Error: {exc}")
        raise
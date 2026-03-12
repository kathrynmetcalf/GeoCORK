"""
geocork_importer.py
-------------------
Imports a GeoCORK staging JSON (produced by json-staging-transformer.py)
into a GeoCORK SQLite database.

Usage:
    python geocork_importer.py <staging_json> <geocork_db>

(separate note) ParentRow rule:
    ParentRow is a SIBLING POSITION INDEX - the sequential order of a node
    among all nodes sharing the same ParentID (NULL or a real ID).
    It starts at 0 for the first child of any parent and increments by 1
    for each additional sibling.

    When inserting a new node:
        1. Query MAX(ParentRow) WHERE ParentID matches (NULL or specific ID)
        2. new ParentRow = MAX + 1, or 0 if no siblings exist yet
"""

import json
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_filled(x: Any) -> bool:
    return x not in (None, "", [], {})


def resolve_unit_id(cur: sqlite3.Cursor, value: Any,
                    unit_table: str, abbrev_col: str, id_col: str) -> Optional[int]:
    """
    Look up a unit ID by abbreviation first, then by full name as fallback.
    SESAR uses full words (e.g. 'meters') while GeoCORK stores abbreviations ('m').
    """
    if not is_filled(value):
        return None
    val = str(value).strip()
    cur.execute(
        f"SELECT {id_col} FROM {unit_table} WHERE lower({abbrev_col}) = lower(?)", (val,))
    row = cur.fetchone()
    if row:
        return row[0]
    # Fallback: match against full name column
    name_col = id_col.replace("ID", "Name")
    cur.execute(
        f"SELECT {id_col} FROM {unit_table} WHERE lower({name_col}) = lower(?)", (val,))
    row = cur.fetchone()
    if not row:
        print(f"  [WARN] Unit {value!r} not found in {unit_table}")
    return row[0] if row else None


def next_sibling_parent_row(cur: sqlite3.Cursor, table: str,
                             id_col: str, parent_id_col: str, parent_row_col: str,
                             parent_id: Optional[int]) -> int:
    """
    Returns the next available ParentRow for a new sibling under parent_id.
    ParentRow is a sequential sibling index (0, 1, 2, ...) among nodes
    sharing the same ParentID - confirmed from real GeoCORK DB inspection.
    """
    if parent_id is None:
        cur.execute(
            f"SELECT MAX({parent_row_col}) FROM {table} WHERE {parent_id_col} IS NULL")
    else:
        cur.execute(
            f"SELECT MAX({parent_row_col}) FROM {table} WHERE {parent_id_col} = ?",
            (parent_id,))
    row = cur.fetchone()
    max_row = row[0] if row and row[0] is not None else -1
    return max_row + 1


def insert_tree_row(
    cur: sqlite3.Cursor,
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
    """
    Insert a tree-table row (or return existing ID if name already present).
    ParentRow is assigned as the next sibling index under parent_id.
    """
    if name_cache is not None and name in name_cache:
        return name_cache[name]

    # Reuse existing row if the name already exists
    cur.execute(
        f"SELECT {id_col} FROM {table} WHERE {name_col} = ? COLLATE NOCASE", (name,))
    existing = cur.fetchone()
    if existing:
        row_id = existing[0]
        if name_cache is not None:
            name_cache[name] = row_id
        return row_id

    # Calculate the correct ParentRow = next sibling index under this parent
    parent_row = next_sibling_parent_row(
        cur, table, id_col, parent_id_col, parent_row_col, parent_id)

    # Build INSERT
    cols = [name_col, parent_id_col, parent_row_col]
    vals: List[Any] = [name, parent_id, parent_row]
    if extra_cols:
        for k, v in extra_cols.items():
            if is_filled(v):
                cols.append(k)
                vals.append(v)

    placeholders = ", ".join(["?"] * len(vals))
    cur.execute(
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})", vals)
    row_id = cur.lastrowid

    if name_cache is not None:
        name_cache[name] = row_id
    return row_id


def insert_bridge(cur: sqlite3.Cursor, table: str,
                  col_a: str, col_b: str, id_a: int, id_b: int) -> None:
    """Insert into a bridge/junction table, silently skipping duplicates."""
    try:
        cur.execute(
            f"INSERT INTO {table} ({col_a}, {col_b}) VALUES (?, ?)", (id_a, id_b))
    except sqlite3.IntegrityError as e:
        if "UNIQUE" in str(e) or "PRIMARY KEY" in str(e):
            pass
        else:
            raise


# ---------------------------------------------------------------------------
# Main importer
# ---------------------------------------------------------------------------

def import_staging(staging_path: str, db_path: str) -> str:
    staging = json.loads(Path(staging_path).read_text(encoding="utf-8"))

    # Always work on a copy - never touch the original
    out_db = str(Path(db_path).with_stem(Path(db_path).stem + "_imported"))
    shutil.copy2(db_path, out_db)
    print(f"Working on copy: {out_db}")

    conn = sqlite3.connect(out_db)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    try:
        conn.execute("BEGIN")

        # -------------------------------------------------------------------
        # 1. GPS Locations
        # -------------------------------------------------------------------
        gps_key_to_id: Dict[str, int] = {}

        for gps in staging.get("GPSLocations", []):
            elev_unit_id = resolve_unit_id(
                cur, gps.get("_GPSElevUnitAbbrev"),
                "DistanceUnits", "DistanceUnitAbbreviation", "DistanceUnitID")
            cur.execute("""
                INSERT INTO GPSLocations
                    (GPSLocationConverted, GPSLatDeg, GPSLatMin, GPSLatSec,
                     GPSLatDirectionID, GPSLonDeg, GPSLonMin, GPSLonSec,
                     GPSLonDirectionID, GPSUTMZone, GPSUTMN, GPSUTME,
                     GPSFormatID, GPSElev, GPSElevError, GPSElevUnitID)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                gps.get("GPSLocationConverted"),
                gps.get("GPSLatDeg"),   gps.get("GPSLatMin"),   gps.get("GPSLatSec"),
                gps.get("GPSLatDirectionID"),
                gps.get("GPSLonDeg"),   gps.get("GPSLonMin"),   gps.get("GPSLonSec"),
                gps.get("GPSLonDirectionID"),
                gps.get("GPSUTMZone"),  gps.get("GPSUTMN"),     gps.get("GPSUTME"),
                gps.get("GPSFormatID"),
                gps.get("GPSElev"),     gps.get("GPSElevError"), elev_unit_id,
            ))
            gps_key_to_id[gps["_gps_key"]] = cur.lastrowid
            print(f"  [GPS] id={cur.lastrowid}  lat={gps.get('GPSLatDeg')}  "
                  f"lon={gps.get('GPSLonDeg')}  elev={gps.get('GPSElev')}")

        # -------------------------------------------------------------------
        # 2. Columns (core samples only)
        # -------------------------------------------------------------------
        column_name_to_id: Dict[str, int] = {}

        for col in staging.get("Columns", []):
            unit_id = resolve_unit_id(
                cur, col.get("_ColumnHeightDepthUnitAbbrev"),
                "DistanceUnits", "DistanceUnitAbbreviation", "DistanceUnitID")
            base_gps_id = gps_key_to_id.get(col.get("_ColumnBaseGPSKey"))
            cur.execute("""
                INSERT INTO Columns
                    (ColumnName, ColumnTotalHeightDepth, ColumnTotalHeightDepthUnitID,
                     ColumnBaseGPSID, ColumnDescription)
                VALUES (?,?,?,?,?)
            """, (
                col["ColumnName"], col.get("ColumnTotalHeightDepth"),
                unit_id, base_gps_id, col.get("ColumnDescription"),
            ))
            column_name_to_id[col["ColumnName"]] = cur.lastrowid
            print(f"  [Column] id={cur.lastrowid}  name={col['ColumnName']!r}")

        # -------------------------------------------------------------------
        # 3. Samples
        #    Instance 1  -> INSERT the primary row
        #    Instances 2+ -> APPEND their SampleDescription text to that row
        # -------------------------------------------------------------------
        sample_nk_to_id: Dict[str, int] = {}

        sample_rows = sorted(
            staging.get("Samples", []),
            key=lambda r: r.get("_DescriptionInstance", 1))

        for s in sample_rows:
            instance = s.get("_DescriptionInstance", 1)
            nk       = s.get("SampleIGSN") or s.get("SampleName")
            desc     = s.get("SampleDescription")

            if instance == 1 or nk not in sample_nk_to_id:
                gps_id  = gps_key_to_id.get(s.get("_SampleGPSKey"))
                col_id  = column_name_to_id.get(s.get("_ColumnName"))
                unit_id = resolve_unit_id(
                    cur, s.get("_HeightDepthUnitAbbrev"),
                    "DistanceUnits", "DistanceUnitAbbreviation", "DistanceUnitID")
                cur.execute("""
                    INSERT INTO Samples
                        (SampleName, SampleIGSN, SampleGPSLocationID, SampleColumnID,
                         HeightDepth, HeightDepthError, HeightDepthUnitID, SampleDescription)
                    VALUES (?,?,?,?,?,?,?,?)
                """, (
                    s.get("SampleName"), s.get("SampleIGSN"),
                    gps_id, col_id,
                    s.get("HeightDepth"), s.get("HeightDepthError"), unit_id,
                    desc,
                ))
                sample_id = cur.lastrowid
                sample_nk_to_id[nk] = sample_id
                print(f"  [Sample] id={sample_id}  name={s.get('SampleName')!r}  "
                      f"instance={instance}")

            else:
                # Append subsequent description instances to the existing row
                sample_id = sample_nk_to_id[nk]
                if is_filled(desc):
                    cur.execute("""
                        UPDATE Samples
                        SET SampleDescription = CASE
                            WHEN SampleDescription IS NULL OR SampleDescription = ''
                            THEN ?
                            ELSE SampleDescription || char(10) || char(10) || ?
                        END
                        WHERE SampleID = ?
                    """, (desc, desc, sample_id))
                    print(f"  [Sample] Appended instance {instance} to SampleID={sample_id}")


        # -------------------------------------------------------------------
        # 3b. Stub Aliquot -> Spot -> UPbAnalysis chain (required for SampleView)
        #
        # GeoCORK's SampleView query is a WITH RECURSIVE CTE:
        #   LimitedSamplesAliquots:        Samples INNER JOIN Aliquots
        #   LimitedSpotsUPbAnalysesGrains: Spots   INNER JOIN UPbAnalyses
        #                                          INNER JOIN LimitedSamplesAliquots
        # A sample with no Aliquot->Spot->UPbAnalysis chain returns zero rows
        # and is invisible in the UI even though it exists in Samples.
        # We insert one stub row at each level using the sample name as placeholder.
        # -------------------------------------------------------------------
        for nk, sample_id in sample_nk_to_id.items():
            sample_name = cur.execute(
                "SELECT SampleName FROM Samples WHERE SampleID=?", (sample_id,)
            ).fetchone()[0]

            # Stub Aliquot: ParentAliquotID=NULL, AliquotParentRow=0
            cur.execute(
                "INSERT INTO Aliquots (AliquotName, ParentAliquotID, AliquotParentRow, SampleID)"
                " VALUES (?, NULL, 0, ?)",
                (sample_name, sample_id))
            aliquot_id = cur.lastrowid

            # Stub Spot
            cur.execute(
                "INSERT INTO Spots (SpotName, AliquotID) VALUES (?, ?)",
                (sample_name, aliquot_id))
            spot_id = cur.lastrowid

            # Stub UPbAnalysis: only UPbAnalysisName and SpotID are NOT NULL
            cur.execute(
                "INSERT INTO UPbAnalyses (UPbAnalysisName, SpotID, Rejected) VALUES (?, ?, 0)",
                (sample_name, spot_id))
            upb_id = cur.lastrowid

            print(f"  [Stub chain] SampleID={sample_id}  AliquotID={aliquot_id}"
                  f"  SpotID={spot_id}  UPbAnalysisID={upb_id}")

        # -------------------------------------------------------------------
        # 4. Regions tree
        # -------------------------------------------------------------------
        region_cache: Dict[str, int] = {}

        for reg in staging.get("Regions", []):
            parent_id = region_cache.get(reg["_ParentRegionName"]) \
                        if reg.get("_ParentRegionName") else None
            reg_id = insert_tree_row(
                cur, "Regions", "RegionID", "ParentRegionID", "RegionParentRow",
                "RegionName", reg["RegionName"], parent_id,
                extra_cols={"RegionDescription": reg.get("RegionDescription")},
                name_cache=region_cache)
            print(f"  [Region] id={reg_id}  name={reg['RegionName']!r}  "
                  f"parent={reg.get('_ParentRegionName')!r}")

        for bridge in staging.get("Samples_Regions", []):
            sid = sample_nk_to_id.get(bridge["_SampleNaturalKey"])
            rid = region_cache.get(bridge["_RegionName"])
            if sid and rid:
                insert_bridge(cur, "Samples_Regions", "SampleID", "RegionID", sid, rid)

        # -------------------------------------------------------------------
        # 5. SamplingMethods tree
        # -------------------------------------------------------------------
        method_cache: Dict[str, int] = {}

        for method in staging.get("SamplingMethods", []):
            parent_id = method_cache.get(method["_ParentSamplingMethodName"]) \
                        if method.get("_ParentSamplingMethodName") else None
            m_id = insert_tree_row(
                cur, "SamplingMethods", "SamplingMethodID", "ParentSamplingMethodID",
                "SamplingMethodParentRow", "SamplingMethodName",
                method["SamplingMethodName"], parent_id,
                extra_cols={"SamplingMethodDescription": method.get("SamplingMethodDescription")},
                name_cache=method_cache)
            print(f"  [SamplingMethod] id={m_id}  name={method['SamplingMethodName']!r}  "
                  f"parent={method.get('_ParentSamplingMethodName')!r}")

        for bridge in staging.get("Samples_SamplingMethods", []):
            sid = sample_nk_to_id.get(bridge["_SampleNaturalKey"])
            mid = method_cache.get(bridge["_SamplingMethodName"])
            if sid and mid:
                insert_bridge(cur, "Samples_SamplingMethods",
                              "SampleID", "SamplingMethodID", sid, mid)

        # -------------------------------------------------------------------
        # 6. RockTypes tree
        # -------------------------------------------------------------------
        rocktype_cache: Dict[str, int] = {}

        for rt in staging.get("RockTypes", []):
            parent_id = rocktype_cache.get(rt["_ParentRockTypeName"]) \
                        if rt.get("_ParentRockTypeName") else None
            rt_id = insert_tree_row(
                cur, "RockTypes", "RockTypeID", "ParentRockTypeID", "RockTypeParentRow",
                "RockTypeName", rt["RockTypeName"], parent_id,
                extra_cols={"RockTypeDescription": rt.get("RockTypeDescription")},
                name_cache=rocktype_cache)
            print(f"  [RockType] id={rt_id}  name={rt['RockTypeName']!r}  "
                  f"parent={rt.get('_ParentRockTypeName')!r}")

        for bridge in staging.get("Samples_RockTypes", []):
            sid  = sample_nk_to_id.get(bridge["_SampleNaturalKey"])
            rtid = rocktype_cache.get(bridge["_RockTypeName"])
            if sid and rtid:
                insert_bridge(cur, "Samples_RockTypes",
                              "SampleID", "RockTypeID", sid, rtid)

        # -------------------------------------------------------------------
        # 7. SampleContexts tree
        # -------------------------------------------------------------------
        ctx_cache: Dict[str, int] = {}

        for ctx in staging.get("SampleContexts", []):
            ctx_id = insert_tree_row(
                cur, "SampleContexts", "SampleContextID", "ParentSampleContextID",
                "SampleContextParentRow", "SampleContextName",
                ctx["SampleContextName"], None,
                extra_cols={"SampleContextDescription": ctx.get("SampleContextDescription")},
                name_cache=ctx_cache)
            print(f"  [SampleContext] id={ctx_id}  name={ctx['SampleContextName']!r}  "
                  f"instance={ctx.get('_ContextInstance')}")

        for bridge in staging.get("Samples_SampleContexts", []):
            sid   = sample_nk_to_id.get(bridge["_SampleNaturalKey"])
            ctxid = ctx_cache.get(bridge["_SampleContextName"])
            if sid and ctxid:
                insert_bridge(cur, "Samples_SampleContexts",
                              "SampleID", "SampleContextID", sid, ctxid)

        # -------------------------------------------------------------------
        # 8. Ages tree
        # -------------------------------------------------------------------
        age_cache: Dict[str, int] = {}

        for age in staging.get("Ages", []):
            age_id = insert_tree_row(
                cur, "Ages", "AgeID", "ParentAgeID", "AgeParentRow", "AgeName",
                age["AgeName"], None,
                extra_cols={"OldestAge": age.get("OldestAge"),
                            "YoungestAge": age.get("YoungestAge")},
                name_cache=age_cache)
            print(f"  [Age] id={age_id}  name={age['AgeName']!r}")

        # -------------------------------------------------------------------
        # 9. Units tree
        # -------------------------------------------------------------------
        unit_cache: Dict[str, int] = {}

        for unit in staging.get("Units", []):
            u_id = insert_tree_row(
                cur, "Units", "UnitID", "ParentUnitID", "UnitParentRow", "UnitName",
                unit["UnitName"], None,
                name_cache=unit_cache)
            print(f"  [Unit] id={u_id}  name={unit['UnitName']!r}")

        for bridge in staging.get("Samples_Units", []):
            sid = sample_nk_to_id.get(bridge["_SampleNaturalKey"])
            uid = unit_cache.get(bridge["_UnitName"])
            if sid and uid:
                insert_bridge(cur, "Samples_Units", "SampleID", "UnitID", sid, uid)

        # -------------------------------------------------------------------
        # 10. References
        # -------------------------------------------------------------------
        ref_key_to_id: Dict[str, int] = {}

        for ref in staging.get("References", []):
            dedup_key = ref.get("DOI") or ref.get("Title") or \
                        (ref.get("ReferenceDescription") or "")[:80]
            if ref.get("DOI"):
                cur.execute('SELECT ReferenceID FROM "References" WHERE DOI = ?',
                            (ref["DOI"],))
            elif ref.get("Title"):
                cur.execute('SELECT ReferenceID FROM "References" WHERE Title = ?',
                            (ref["Title"],))
            else:
                cur.execute('SELECT ReferenceID FROM "References" '
                            'WHERE ReferenceDescription = ?',
                            (ref.get("ReferenceDescription"),))
            existing = cur.fetchone()
            if existing:
                ref_id = existing[0]
            else:
                cur.execute("""
                    INSERT INTO "References"
                        (Authors, Year, Title, Source, DOI, ReferenceDescription)
                    VALUES (?,?,?,?,?,?)
                """, (ref.get("Authors"), ref.get("Year"), ref.get("Title"),
                      ref.get("Source"), ref.get("DOI"),
                      ref.get("ReferenceDescription")))
                ref_id = cur.lastrowid
            ref_key_to_id[dedup_key] = ref_id
            print(f"  [Reference] id={ref_id}  DOI={ref.get('DOI')!r}")

        # -------------------------------------------------------------------
        # 11. SampleAges + bridges
        # -------------------------------------------------------------------
        sa_index_to_id: Dict[int, int] = {}

        for i, sa in enumerate(staging.get("SampleAges", [])):
            oldest_age_id   = age_cache.get(sa.get("_OldestAgeName"))
            youngest_age_id = age_cache.get(sa.get("_YoungestAgeName"))
            cur.execute("""
                INSERT INTO SampleAges
                    (DirectAge, DirectAgeError, DirectAgeErrorFormatID,
                     OldestDirectAge, YoungestDirectAge, DirectAgeUnitID,
                     OldestAgeID, YoungestAgeID, SampleAgeDescription)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                sa.get("DirectAge"), sa.get("DirectAgeError"),
                sa.get("DirectAgeErrorFormatID"),
                sa.get("OldestDirectAge"), sa.get("YoungestDirectAge"),
                sa.get("DirectAgeUnitID"),
                oldest_age_id, youngest_age_id, sa.get("SampleAgeDescription"),
            ))
            sa_index_to_id[i] = cur.lastrowid
            print(f"  [SampleAge] id={cur.lastrowid}")

        for bridge in staging.get("Samples_SampleAges", []):
            sid  = sample_nk_to_id.get(bridge["_SampleNaturalKey"])
            said = sa_index_to_id.get(bridge.get("_SampleAgeIndex", 0))
            if sid and said:
                insert_bridge(cur, "Samples_SampleAges",
                              "SampleID", "SampleAgeID", sid, said)

        # -------------------------------------------------------------------
        # Commit
        # -------------------------------------------------------------------
        conn.execute("COMMIT")
        print(f"\n✓ Import complete → {out_db}")
        print(f"  Samples        : {len(sample_nk_to_id)}")
        print(f"  GPS            : {len(gps_key_to_id)}")
        print(f"  Regions        : {len(region_cache)}")
        print(f"  RockTypes      : {len(rocktype_cache)}")
        print(f"  SamplingMethods: {len(method_cache)}")
        print(f"  SampleContexts : {len(ctx_cache)}")

    except Exception as e:
        conn.execute("ROLLBACK")
        print(f"\n✗ Import FAILED - rolled back.\n  Error: {e}")
        import traceback; traceback.print_exc()
        raise
    finally:
        conn.close()

    return out_db


# ---------------------------------------------------------------------------
# Verification - compare ParentRow pattern against reference DB
# ---------------------------------------------------------------------------

def verify_import(db_path: str, igsn: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    print(f"\n{'='*60}")
    print(f"Verification - IGSN: {igsn}")
    print(f"{'='*60}")

    cur.execute("SELECT * FROM Samples WHERE SampleIGSN = ?", (igsn,))
    samples = cur.fetchall()
    if not samples:
        print("  ✗ Sample NOT found!")
        return

    for s in samples:
        print(f"\n  [Sample] id={s['SampleID']}  name={s['SampleName']!r}")
        print(f"    IGSN: {s['SampleIGSN']}")

        if s["SampleGPSLocationID"]:
            cur.execute("SELECT GPSLatDeg, GPSLonDeg, GPSElev FROM GPSLocations "
                        "WHERE GPSLocationID=?", (s["SampleGPSLocationID"],))
            g = cur.fetchone()
            if g:
                print(f"    [GPS] lat={g[0]}  lon={g[1]}  elev={g[2]}")

        cur.execute("""SELECT r.RegionName, r.ParentRegionID, r.RegionParentRow
                       FROM Samples_Regions sr JOIN Regions r ON sr.RegionID=r.RegionID
                       WHERE sr.SampleID=?""", (s["SampleID"],))
        for r in cur.fetchall():
            print(f"    [Region] {r[0]!r}  parentID={r[1]}  parentRow={r[2]}")

        cur.execute("""SELECT rt.RockTypeName, rt.ParentRockTypeID, rt.RockTypeParentRow
                       FROM Samples_RockTypes srt JOIN RockTypes rt ON srt.RockTypeID=rt.RockTypeID
                       WHERE srt.SampleID=?""", (s["SampleID"],))
        for rt in cur.fetchall():
            print(f"    [RockType] {rt[0]!r}  parentID={rt[1]}  parentRow={rt[2]}")

        cur.execute("""SELECT sm.SamplingMethodName, sm.SamplingMethodParentRow
                       FROM Samples_SamplingMethods ssm
                       JOIN SamplingMethods sm ON ssm.SamplingMethodID=sm.SamplingMethodID
                       WHERE ssm.SampleID=?""", (s["SampleID"],))
        for sm in cur.fetchall():
            print(f"    [SamplingMethod] {sm[0]!r}  parentRow={sm[1]}")

        cur.execute("""SELECT sc.SampleContextName, sc.SampleContextParentRow
                       FROM Samples_SampleContexts ssc
                       JOIN SampleContexts sc ON ssc.SampleContextID=sc.SampleContextID
                       WHERE ssc.SampleID=?""", (s["SampleID"],))
        for sc in cur.fetchall():
            print(f"    [SampleContext] {sc[0]!r}  parentRow={sc[1]}")

    # Show all tree table ParentRow patterns for inspection
    print("\n  Tree ParentRow patterns (should be sibling indices 0,1,2...):")
    for tbl, col in [("Regions","RegionParentRow"), ("RockTypes","RockTypeParentRow"),
                     ("SamplingMethods","SamplingMethodParentRow"),
                     ("SampleContexts","SampleContextParentRow")]:
        cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tbl,))
        if not cur.fetchone():
            continue
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        n = cur.fetchone()[0]
        if n:
            cur.execute(f"SELECT {col} FROM {tbl} ORDER BY {col}")
            rows = [r[0] for r in cur.fetchall()]
            print(f"    {tbl}: {rows}")

    conn.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

STAGING_JSON = Path("geocork_staging_with_bridges.json")  # output from json-staging-transformer.py
GEOCORK_DB   = Path("geocork_test.db")               # blank GeoCORK database to import into

if __name__ == "__main__":
    out_db = import_staging(str(STAGING_JSON), str(GEOCORK_DB))

    staging = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
    igsn = staging["Samples"][0].get("SampleIGSN") or staging["Samples"][0].get("SampleName")
    verify_import(out_db, igsn)
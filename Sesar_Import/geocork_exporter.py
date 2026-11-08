"""
geocork_exporter.py
-------------------
GeoCORK → SESAR: builds SESAR API payloads from samples in the open GeoCORK
database. The reverse of json_staging_transformer.py + geocork_importer.py.

Pieces
    list_geocork_samples(text)      rows for the export window's sample picker
    load_sample_record(sample_id)   one sample + related rows (QSqlQuery)
    build_export_fields(record)     [ExportField] — candidate SESAR fields
    apply_remote(fields, remote)    mark which fields differ from SESAR
    build_payload(fields)           dict for PATCH / POST from checked fields
    write_back_igsn(sample_id, igsn)  store a newly minted IGSN (savepointed)

Field confidence
    Fields with a direct GeoCORK column (name, coordinates, elevation, depth,
    ages, geologic unit, description) are "direct" and are pre-checked when
    they differ from SESAR. Fields reconstructed from GeoCORK's tree tables
    (Regions → country/province/…, RockTypes → material_types,
    SamplingMethods → sampling_method) are "derived": the import encoded them
    heuristically and SESAR validates some against vocabularies, so they are
    shown but left UNchecked by default for the user to opt in.

Mapping mirrors the importer so a round-trip is stable:
    Samples.HeightDepth / HeightDepthError  <-> depth_min / depth_max
    GPSElev ± GPSElevError                  <-> elevation / elevation_end
    Regions chain Country>Province>"X co.">City>Locality>"type: name"
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from Sesar_Import.sesar_logger import get_sesar_logger


# ===========================================================================
# Field metadata
# ===========================================================================

NUMERIC_FIELDS = frozenset({"latitude", "longitude", "elevation", "elevation_end",
                            "depth_min", "depth_max", "numeric_age_min", "numeric_age_max"})
LIST_FIELDS = frozenset({"material_types", "other_names"})

# Display order in the export preview.
FIELD_ORDER = [
    "name", "object_type", "sesar_code", "sample_description", "purpose",
    "size", "size_unit", "other_names",
    "latitude", "longitude", "elevation", "elevation_end", "elevation_unit",
    "depth_min", "depth_max", "depth_scale",
    "country", "province", "county", "city", "locality", "locality_description",
    "location_description", "primary_location_type", "primary_location_name",
    "material_types", "sampling_method", "sampling_method_detail",
    "geologic_age_verbatim", "numeric_age_min", "numeric_age_max",
    "numeric_age_unit", "age_description", "geologic_unit",
]

FIELD_LABELS = {
    "name": "Sample name", "object_type": "Object type", "sesar_code": "SESAR code",
    "sample_description": "Description", "purpose": "Purpose", "size": "Size",
    "size_unit": "Size unit", "other_names": "Other names",
    "latitude": "Latitude", "longitude": "Longitude", "elevation": "Elevation",
    "elevation_end": "Elevation (end)", "elevation_unit": "Elevation unit",
    "depth_min": "Depth min", "depth_max": "Depth max", "depth_scale": "Depth scale",
    "country": "Country", "province": "State/Province", "county": "County",
    "city": "City", "locality": "Locality", "locality_description": "Locality description",
    "location_description": "Location description",
    "primary_location_type": "Physiographic feature type",
    "primary_location_name": "Physiographic feature name",
    "material_types": "Material types", "sampling_method": "Sampling method",
    "sampling_method_detail": "Sampling method detail",
    "geologic_age_verbatim": "Geologic age", "numeric_age_min": "Numeric age min",
    "numeric_age_max": "Numeric age max", "numeric_age_unit": "Numeric age unit",
    "age_description": "Age description", "geologic_unit": "Geologic unit",
}

# SESAR ElevationUnitEnum
_ELEVATION_UNITS = {"m": "meters", "km": "kilometers", "ft": "feet", "mi": "miles"}
# Other GeoCORK DistanceUnits converted to meters before sending.
_TO_METERS = {"cm": 0.01, "mm": 0.001, "µm": 1e-6, "um": 1e-6, "yd": 0.9144, "in": 0.0254}

# SESAR NumericAgeUnitEnum, keyed by lower-case GeoCORK AgeUnits abbreviation.
_AGE_UNITS = {
    "yr": "years (yr)", "y": "years (yr)", "a": "years (yr)", "years": "years (yr)",
    "ka": "thousand years (Ka)", "kyr": "thousand years (Ka)", "ky": "thousand years (Ka)",
    "ma": "million years (Ma)", "myr": "million years (Ma)", "my": "million years (Ma)",
    "ga": "billion years (Ga)", "gyr": "billion years (Ga)", "gy": "billion years (Ga)",
    "bp": "Before Present, 1950 (BP)", "ad": "Anno Domini (AD)",
    "ce": "Common Era (CE)", "bce": "Before Common Era (BCE)",
}

_CONTINENTS = {"africa", "antarctica", "asia", "europe", "north america",
               "south america", "oceania", "australia"}

# Lines of a SampleDescription synthesized by geocork_importer from SESAR
# fields ("Label: value"). Used to pull structured values back out.
_SD_MARKERS = ("SESAR object type:", "SESAR sample_type:")
_SD_LINE_RE = re.compile(r"^([^:\n]{1,40}):\s?(.*)$")


@dataclass
class ExportField:
    key: str
    value: Any                       # python value to send (float, str, list)
    direct: bool = True              # False = derived/heuristic -> unchecked by default
    note: str = ""
    remote: Any = None               # value currently on SESAR (PATCH only)
    remote_known: bool = False
    send: bool = True                # initial checkbox state

    @property
    def label(self) -> str:
        return FIELD_LABELS.get(self.key, self.key)


@dataclass
class SampleRecord:
    sample_id: int
    name: str
    igsn: Optional[str]
    columns: Dict[str, Any] = field(default_factory=dict)       # Samples + GPS + units
    trees: Dict[str, List[Tuple[str, Optional[str], Optional[str]]]] = field(default_factory=dict)
    age: Dict[str, Any] = field(default_factory=dict)


# ===========================================================================
# Value helpers
# ===========================================================================

def _filled(v: Any) -> bool:
    return v not in (None, "", [], {})


def _f(v: Any) -> Optional[float]:
    try:
        if v in (None, ""):
            return None
        x = float(v)
        return None if math.isnan(x) else x
    except (TypeError, ValueError):
        return None


def to_display(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return "; ".join(to_display(x) for x in v)
    if isinstance(v, dict):
        return str(v.get("label") or v.get("name") or v)
    if isinstance(v, float):
        return f"{v:.10g}"
    return str(v)


def parse_edited(key: str, text: str) -> Any:
    """Convert a user-edited preview cell back to the type SESAR expects."""
    text = (text or "").strip()
    if not text:
        return None
    if key in NUMERIC_FIELDS:
        val = _f(text)
        if val is None:
            raise ValueError(f"{FIELD_LABELS.get(key, key)} must be a number (got {text!r}).")
        return val
    if key in LIST_FIELDS:
        return [p.strip() for p in text.split(";") if p.strip()]
    return text


def values_equal(key: str, local: Any, remote: Any) -> bool:
    """Compare a GeoCORK value with SESAR's, tolerant of type/format noise."""
    if not _filled(local) and not _filled(remote):
        return True
    if key in NUMERIC_FIELDS:
        a, b = _f(local), _f(remote)
        if a is None or b is None:
            return a is None and b is None
        return math.isclose(a, b, rel_tol=1e-7, abs_tol=1e-6)
    if key in LIST_FIELDS:
        def norm(v):
            if isinstance(v, str):
                v = re.split(r"[;,]", v)
            return sorted({to_display(x).strip().casefold() for x in (v or []) if to_display(x).strip()})
        return norm(local) == norm(remote)
    return to_display(local).strip().casefold() == to_display(remote).strip().casefold()


# ===========================================================================
# Database access (QSqlQuery — must run on the GUI thread's connection)
# ===========================================================================

def _rows(sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
    from PyQt6.QtSql import QSqlQuery
    q = QSqlQuery()
    if not q.prepare(sql):
        raise RuntimeError(f"Could not prepare query: {q.lastError().text()}\n{sql}")
    for p in params:
        q.addBindValue(p)
    if not q.exec():
        raise RuntimeError(f"Query failed: {q.lastError().text()}\n{sql}")
    rec = q.record()
    names = [rec.fieldName(i) for i in range(rec.count())]
    out = []
    while q.next():
        # PyQt returns '' for SQL NULL via value(); use isNull() so NULL stays
        # None (otherwise re-binding it, e.g. coalesce(?, ...), silently breaks).
        out.append({n: (None if q.isNull(i) else q.value(i)) for i, n in enumerate(names)})
    return out


def list_geocork_samples(filter_text: str = "", limit: int = 2000) -> List[Dict[str, Any]]:
    """SampleID / SampleName / SampleIGSN for the picker, filtered by name or IGSN."""
    like = f"%{filter_text.strip()}%"
    return _rows(
        "SELECT SampleID, SampleName, SampleIGSN FROM Samples "
        "WHERE SampleName LIKE ? OR ifnull(SampleIGSN, '') LIKE ? "
        "ORDER BY SampleName COLLATE NOCASE LIMIT ?",
        (like, like, limit))


# (key, bridge table, tree table, id col, parent col, name col, description col)
_TREE_TABLES = [
    ("Regions", "Samples_Regions", "Regions", "RegionID", "ParentRegionID",
     "RegionName", "RegionDescription"),
    ("RockTypes", "Samples_RockTypes", "RockTypes", "RockTypeID", "ParentRockTypeID",
     "RockTypeName", "RockTypeDescription"),
    ("SamplingMethods", "Samples_SamplingMethods", "SamplingMethods", "SamplingMethodID",
     "ParentSamplingMethodID", "SamplingMethodName", "SamplingMethodDescription"),
    ("Units", "Samples_Units", "Units", "UnitID", "ParentUnitID", "UnitName", "UnitDescription"),
]


def load_sample_record(sample_id: int) -> SampleRecord:
    rows = _rows(
        """SELECT s.SampleID, s.SampleName, s.SampleIGSN, s.HeightDepth, s.HeightDepthError,
                  s.SampleDescription, s.DefaultSampleAgeID,
                  du.DistanceUnitName AS DepthUnitName,
                  du.DistanceUnitAbbreviation AS DepthUnitAbbrev,
                  g.GPSLatDeg, g.GPSLatMin, g.GPSLatSec, g.GPSLatDirectionID,
                  g.GPSLonDeg, g.GPSLonMin, g.GPSLonSec, g.GPSLonDirectionID,
                  g.GPSUTMZone, g.GPSUTME, g.GPSUTMN, g.GPSElev, g.GPSElevError,
                  eu.DistanceUnitAbbreviation AS ElevUnitAbbrev
           FROM Samples s
           LEFT JOIN GPSLocations g  ON g.GPSLocationID = s.SampleGPSLocationID
           LEFT JOIN DistanceUnits du ON du.DistanceUnitID = s.HeightDepthUnitID
           LEFT JOIN DistanceUnits eu ON eu.DistanceUnitID = g.GPSElevUnitID
           WHERE s.SampleID = ?""", (sample_id,))
    if not rows:
        raise LookupError(f"SampleID {sample_id} not found")
    cols = rows[0]
    rec = SampleRecord(sample_id=sample_id, name=cols["SampleName"],
                       igsn=(cols["SampleIGSN"] or None), columns=cols)

    for key, bridge, table, id_col, parent_col, name_col, desc_col in _TREE_TABLES:
        try:
            linked = _rows(
                f"SELECT t.{id_col} AS id, t.{name_col} AS name, t.{desc_col} AS descr, "
                f"p.{name_col} AS parent FROM {bridge} b "
                f"JOIN {table} t ON t.{id_col} = b.{id_col} "
                f"LEFT JOIN {table} p ON p.{id_col} = t.{parent_col} "
                f"WHERE b.SampleID = ?", (sample_id,))
        except RuntimeError as exc:
            get_sesar_logger().warning(f"[SESAR export] {key} lookup failed: {exc}")
            linked = []
        rec.trees[key] = [(r["name"], r["parent"], r["descr"]) for r in linked]

    try:
        ages = _rows(
            """SELECT sa.YoungestDirectAge, sa.OldestDirectAge, sa.DirectAge,
                      sa.SampleAgeDescription, au.AgeUnitAbbreviation AS AgeUnitAbbrev,
                      ya.AgeName AS YoungestAgeName, oa.AgeName AS OldestAgeName
               FROM SampleAges sa
               LEFT JOIN AgeUnits au ON au.AgeUnitID = sa.DirectAgeUnitID
               LEFT JOIN Ages ya ON ya.AgeID = sa.YoungestAgeID
               LEFT JOIN Ages oa ON oa.AgeID = sa.OldestAgeID
               WHERE sa.SampleAgeID = coalesce(?, (SELECT SampleAgeID FROM Samples_SampleAges
                                                   WHERE SampleID = ? ORDER BY SampleAgeID LIMIT 1))""",
            (cols.get("DefaultSampleAgeID"), sample_id))
        rec.age = ages[0] if ages else {}
    except RuntimeError as exc:
        get_sesar_logger().warning(f"[SESAR export] age lookup failed: {exc}")
    return rec


def write_back_igsn(sample_id: int, igsn: str) -> None:
    """Store a newly minted IGSN on the GeoCORK sample, under a savepoint."""
    from PyQt6.QtSql import QSqlQuery
    from Functions.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint
    if not create_savepoint("sesar_igsn_writeback"):
        raise RuntimeError("Could not create savepoint for IGSN write-back.")
    try:
        q = QSqlQuery()
        q.prepare("UPDATE Samples SET SampleIGSN = ? WHERE SampleID = ?")
        q.addBindValue(igsn)
        q.addBindValue(sample_id)
        if not q.exec():
            raise RuntimeError(q.lastError().text())
        release_savepoint("sesar_igsn_writeback")
        get_sesar_logger().info(f"[SESAR export] Wrote IGSN {igsn} to SampleID={sample_id}")
    except Exception:
        rollback_savepoint("sesar_igsn_writeback")
        raise


# ===========================================================================
# Conversions
# ===========================================================================

def decimal_degrees(c: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    """Signed decimal degrees from any stored GPSFormat (DD/DDM/DMS ± or NSEW, or UTM)."""

    def deg(d, m, s, direction_id):
        d = _f(d)
        if d is None:
            return None
        value = abs(d) + (_f(m) or 0) / 60 + (_f(s) or 0) / 3600
        negative = math.copysign(1, d) < 0
        if direction_id not in (None, ""):
            try:
                from Functions import SQLUtils
                abbrev = SQLUtils.direction_units[int(direction_id) - 1][1]
                negative = negative or abbrev in ("S", "W")
            except Exception:
                negative = negative or int(direction_id) in (2, 4)  # S / W per DirectionUnits order
        return -value if negative else value

    lat = deg(c.get("GPSLatDeg"), c.get("GPSLatMin"), c.get("GPSLatSec"), c.get("GPSLatDirectionID"))
    lon = deg(c.get("GPSLonDeg"), c.get("GPSLonMin"), c.get("GPSLonSec"), c.get("GPSLonDirectionID"))
    if (lat is None or lon is None) and c.get("GPSUTMZone") and \
            _f(c.get("GPSUTME")) is not None and _f(c.get("GPSUTMN")) is not None:
        try:
            from Functions.GPS_conversions import convert_utm_to_dd
            r = convert_utm_to_dd(str(c["GPSUTMZone"]), float(c["GPSUTME"]), float(c["GPSUTMN"]))
            if isinstance(r, tuple) and r[0] not in ("", None):
                lat, lon = float(r[0][0]), float(r[1][0])
        except Exception as exc:
            get_sesar_logger().warning(f"[SESAR export] UTM conversion failed: {exc}")
    return (round(lat, 6) if lat is not None else None,
            round(lon, 6) if lon is not None else None)


def _distance_to_sesar(value: Optional[float], abbrev: Optional[str]) -> Tuple[Optional[float], Optional[str], str]:
    """(value, ElevationUnitEnum, note) — converts units SESAR doesn't accept to meters."""
    if value is None:
        return None, None, ""
    a = (abbrev or "").strip()
    if a.lower() in _ELEVATION_UNITS:
        return value, _ELEVATION_UNITS[a.lower()], ""
    if a in _TO_METERS or a.lower() in _TO_METERS:
        factor = _TO_METERS.get(a, _TO_METERS.get(a.lower()))
        return value * factor, "meters", f"converted from {a} to meters"
    if not a:
        return value, None, "no unit in GeoCORK"
    return value, None, f"unit {a!r} has no SESAR equivalent"


def parse_synthesized_description(text: Optional[str]) -> Tuple[Optional[str], Dict[str, str]]:
    """
    If SampleDescription was synthesized by the SESAR importer
    ("SESAR object type: …\\nDescription: …\\nPurpose: …"), return
    (description_only, {label: value}). Otherwise (text, {}).

    Prevents an Update from overwriting SESAR's sample_description with the
    whole labelled blob GeoCORK built from SESAR's own fields.
    """
    if not text:
        return None, {}
    if not any(m in text for m in _SD_MARKERS):
        return text, {}
    parsed: Dict[str, str] = {}
    current = None
    for line in text.splitlines():
        m = _SD_LINE_RE.match(line)
        if m and m.group(1).strip() in _KNOWN_SD_LABELS:
            current = m.group(1).strip()
            parsed[current] = m.group(2)
        elif current and line.strip():
            parsed[current] += "\n" + line   # continuation of a multi-line value
        elif not line.strip():
            current = None
    return parsed.get("Description"), parsed


# Must match labels in json_staging_transformer._SD_FIELD_DEFS
_KNOWN_SD_LABELS = {
    "SESAR object type", "SESAR sample_type", "Description", "Other names", "Comment",
    "Classification comment", "Purpose", "Size", "Size unit", "Parent IGSN",
    "External sample ID", "Owner", "Original registrant name", "Current registrant name",
    "Collector/Chief Scientist", "Collector address", "Collection date", "Collection time",
    "Collection date (end)", "Collection time (end)", "Collection date precision",
    "Location method", "Current archive", "Current archive contact",
    "Original archive contact", "Original archive", "Is archived", "Storage location",
}


def _tree_chain(entries: List[Tuple[str, Optional[str], Optional[str]]]) -> List[str]:
    """
    Longest root→leaf chain among a sample's linked tree nodes. The importer
    links a sample to every node of its chain, so we can rebuild it from
    (name, parent) pairs.
    """
    names = {n for n, _, _ in entries}
    children: Dict[Optional[str], List[str]] = {}
    for n, p, _ in entries:
        children.setdefault(p if p in names else None, []).append(n)

    best: List[str] = []

    def walk(node: str, path: List[str]):
        nonlocal best
        path = path + [node]
        kids = children.get(node, [])
        if not kids and len(path) > len(best):
            best = path
        for k in kids:
            if k not in path:
                walk(k, path)

    for root in children.get(None, []):
        walk(root, [])
    return best


def _region_fields(entries) -> Dict[str, str]:
    """Reverse the importer's Regions encoding (heuristic → 'derived')."""
    out: Dict[str, str] = {}
    chain = _tree_chain(entries)
    chain_set = set(chain)
    # Standalone single-node roots that aren't part of the chain were
    # location_description in the importer.
    standalone = [n for n, p, _ in entries if n not in chain_set and not p]
    if standalone:
        out["location_description"] = standalone[0]

    geo: List[str] = []
    for name in chain:
        if ": " in name and "primary_location_type" not in out:
            t, nm = name.split(": ", 1)
            out["primary_location_type"], out["primary_location_name"] = t.strip(), nm.strip()
        elif name.lower().endswith(" co."):
            out["county"] = name[:-4].strip()
            geo.append("<county>")
        elif name.lower() in _CONTINENTS and not geo:
            continue
        else:
            geo.append(name)
    descs = {n: d for n, _, d in entries if d}

    if "<county>" in geo:
        i = geo.index("<county>")
        before, after = geo[:i], geo[i + 1:]
        if before:
            out["country"] = before[0]
        if len(before) > 1:
            out["province"] = before[1]
        if after:
            out["city"] = after[0]
        if len(after) > 1:
            out["locality"] = after[-1]
    else:
        if geo:
            out["country"] = geo[0]
        if len(geo) > 1:
            out["province"] = geo[1]
        if len(geo) > 2:
            out["locality"] = geo[-1]
        if len(geo) > 3:
            out["city"] = geo[2]
    if out.get("locality") and descs.get(out["locality"]):
        out["locality_description"] = descs[out["locality"]]
    return out


# ===========================================================================
# Payload building
# ===========================================================================

def build_export_fields(rec: SampleRecord, sesar_code: str = "",
                        default_object_type: str = "",
                        for_register: Optional[bool] = None) -> List[ExportField]:
    """Candidate SESAR fields for one GeoCORK sample (unchecked/derived marked)."""
    register = (not rec.igsn) if for_register is None else for_register
    c = rec.columns
    fields: Dict[str, ExportField] = {}

    def add(key, value, direct=True, note=""):
        if _filled(value):
            fields[key] = ExportField(key, value, direct=direct, note=note, send=direct)

    add("name", rec.name)

    desc, parsed = parse_synthesized_description(c.get("SampleDescription"))
    add("sample_description", desc,
        note="extracted from GeoCORK's SESAR-imported description" if parsed else "")
    if parsed:
        add("purpose", parsed.get("Purpose"))
        add("size", parsed.get("Size"))
        add("size_unit", parsed.get("Size unit"))
        if parsed.get("Other names"):
            add("other_names", [x.strip() for x in parsed["Other names"].split(";") if x.strip()],
                direct=False, note="replaces SESAR's whole list")

    if register:
        add("object_type", parsed.get("SESAR object type") or parsed.get("SESAR sample_type")
            or default_object_type, note="SESAR vocabulary leaf label — required")
        add("sesar_code", sesar_code, note="required to publish")

    lat, lon = decimal_degrees(c)
    add("latitude", lat)
    add("longitude", lon)

    elev, err = _f(c.get("GPSElev")), _f(c.get("GPSElevError"))
    if elev is not None:
        if err:
            # Importer stored average ± half-range; send the range back.
            lo, unit, note = _distance_to_sesar(elev - err, c.get("ElevUnitAbbrev"))
            hi, _, _ = _distance_to_sesar(elev + err, c.get("ElevUnitAbbrev"))
            add("elevation", lo, note=note or "GeoCORK elevation − error")
            add("elevation_end", hi, note=note or "GeoCORK elevation + error")
        else:
            val, unit, note = _distance_to_sesar(elev, c.get("ElevUnitAbbrev"))
            add("elevation", val, note=note)
        add("elevation_unit", unit)

    add("depth_min", _f(c.get("HeightDepth")))
    add("depth_max", _f(c.get("HeightDepthError")),
        note="GeoCORK HeightDepthError holds SESAR depth_max (importer mapping)")
    if _filled(c.get("HeightDepth")) or _filled(c.get("HeightDepthError")):
        add("depth_scale", (c.get("DepthUnitName") or "").lower() or None)

    for key, value in _region_fields(rec.trees.get("Regions", [])).items():
        add(key, value, direct=False, note="derived from GeoCORK Regions")

    rock_chain = _tree_chain(rec.trees.get("RockTypes", []))
    if rock_chain:
        add("material_types", [rock_chain[-1]], direct=False,
            note="deepest RockType (may be the informal field name) — must match a SESAR "
                 "material-type label; replaces SESAR's list")

    methods = rec.trees.get("SamplingMethods", [])
    method_chain = _tree_chain(methods)
    if method_chain:
        add("sampling_method", method_chain[-1], direct=False,
            note="must match SESAR sampling-method vocabulary")
        leaf_desc = next((d for n, _, d in methods if n == method_chain[-1] and d), None)
        add("sampling_method_detail", leaf_desc)

    units = _tree_chain(rec.trees.get("Units", []))
    if units:
        add("geologic_unit", units[-1])

    a = rec.age or {}
    age_name = a.get("YoungestAgeName") or a.get("OldestAgeName")
    if a.get("YoungestAgeName") and a.get("OldestAgeName") and \
            a["YoungestAgeName"] != a["OldestAgeName"]:
        age_name = f"{a['OldestAgeName']} – {a['YoungestAgeName']}"
    add("geologic_age_verbatim", age_name)
    add("numeric_age_min", _f(a.get("YoungestDirectAge")))
    add("numeric_age_max", _f(a.get("OldestDirectAge")))
    if _filled(a.get("YoungestDirectAge")) or _filled(a.get("OldestDirectAge")):
        unit = _AGE_UNITS.get(str(a.get("AgeUnitAbbrev") or "").strip().lower())
        if unit:
            add("numeric_age_unit", unit)
        elif a.get("AgeUnitAbbrev"):
            for k in ("numeric_age_min", "numeric_age_max"):
                if k in fields:
                    fields[k].note = f"GeoCORK age unit {a['AgeUnitAbbrev']!r} has no SESAR equivalent"
    add("age_description", a.get("SampleAgeDescription"))

    return sorted(fields.values(),
                  key=lambda f: FIELD_ORDER.index(f.key) if f.key in FIELD_ORDER else 999)


def apply_remote(fields: List[ExportField], remote: Dict[str, Any]) -> List[ExportField]:
    """
    PATCH preparation: record SESAR's current values and keep only meaningful
    changes checked. Unchanged fields stay visible (unchecked) for context.
    Fields SESAR can't take via PATCH are dropped.
    """
    out = []
    for f in fields:
        if f.key == "sesar_code":
            continue  # cannot be changed by PATCH
        f.remote = remote.get(f.key)
        f.remote_known = True
        changed = not values_equal(f.key, f.value, f.remote)
        f.send = f.direct and changed
        if not changed:
            f.note = (f.note + "; " if f.note else "") + "same as SESAR"
        out.append(f)
    return out


def build_payload(fields: List[ExportField], register: bool,
                  is_draft: bool = False) -> Dict[str, Any]:
    """Dict of checked fields for POST/PATCH."""
    payload = {f.key: f.value for f in fields if f.send and _filled(f.value)}
    if register:
        payload["is_draft"] = bool(is_draft)
    return payload


def register_problems(payload: Dict[str, Any]) -> List[str]:
    """Client-side check of the documented publish requirements."""
    need = ["name", "object_type"]
    if not payload.get("is_draft"):
        need += ["latitude", "longitude", "sesar_code"]
    return [FIELD_LABELS.get(k, k) for k in need if not _filled(payload.get(k))]

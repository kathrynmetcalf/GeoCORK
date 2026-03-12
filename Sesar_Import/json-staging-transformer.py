import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure the GeoCORK project root is on the path so that sibling packages
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Functions.GPS_conversions import convert_utm_to_dd

# update path for directory
IN_PATH = Path("sesar_file.json")
OUT_PATH = Path("geocork_staging_with_bridges.json")


# -------------------------
# Helpers
# -------------------------
def safe_float(x: Any) -> Optional[float]:
    try:
        if x in ("", None, [], {}):
            return None
        return float(x)
    except Exception:
        return None


def safe_int(x: Any) -> Optional[int]:
    try:
        if x in ("", None, [], {}):
            return None
        return int(x)
    except Exception:
        return None


def is_filled(x: Any) -> bool:
    return x not in (None, "", [], {})


def append_kv(lines: List[str], label: str, value: Any) -> None:
    if is_filled(value):
        lines.append(f"{label}: {value}")


# -------------------------
# SampleDescription builders - 4 separate instances per diagram
#
# Instance 1: SampleDescription (the base SESAR description field itself)
#   + Other names, Comment, Classification Comment, Purpose
#   + Size / Size unit (only if NOT a core sample)
#
# Instance 2: Original Registrant Name (new instance)
#   + Current Registrant Name
#
# Instance 3: Collector/Chief Scientist (new instance)
#   + Collector/Chief Scientist Address
#   + Collection date, Collection time
#   + Collection date (end), Collection time (end)
#   + Collection date precision
#
# Instance 4: Current archive (new instance)
#   + Current archive contact
#   + Original archive contact
#   + Original archive
#   + IsArchived
# -------------------------

def build_sample_description_1(s: Dict[str, Any], is_core: bool) -> Optional[str]:
    """Instance 1: base description + metadata fields."""
    lines: List[str] = []
    append_kv(lines, "SESAR sample_type", s.get("sample_type"))
    append_kv(lines, "Description", s.get("description"))
    append_kv(lines, "Other names", s.get("other_names") or s.get("sample_other_names"))
    append_kv(lines, "Comment", s.get("comment"))
    append_kv(lines, "Classification comment", s.get("classification_comment"))
    append_kv(lines, "Purpose", s.get("purpose"))
    # Size/Size unit only here if NOT a core (cores go to Columns)
    if not is_core:
        append_kv(lines, "Size", s.get("size"))
        append_kv(lines, "Size unit", s.get("size_unit"))
    return "\n".join(lines).strip() or None


def build_sample_description_2(s: Dict[str, Any]) -> Optional[str]:
    """Instance 2: registrant names."""
    lines: List[str] = []
    append_kv(lines, "Original registrant name", s.get("original_registrant_name"))
    append_kv(lines, "Current registrant name", s.get("current_registrant_name"))
    return "\n".join(lines).strip() or None


def build_sample_description_3(s: Dict[str, Any]) -> Optional[str]:
    """Instance 3: collector and collection event info."""
    lines: List[str] = []
    append_kv(lines, "Collector/Chief Scientist", s.get("collector"))
    append_kv(lines, "Collector address", s.get("collector_chief_scientist_address"))
    append_kv(lines, "Collection date", s.get("collection_start_date"))
    append_kv(lines, "Collection time", s.get("collection_time"))
    append_kv(lines, "Collection date (end)", s.get("collection_end_date"))
    append_kv(lines, "Collection time (end)", s.get("collection_time_end"))
    append_kv(lines, "Collection date precision", s.get("collection_date_precision"))
    return "\n".join(lines).strip() or None


def build_sample_description_4(s: Dict[str, Any]) -> Optional[str]:
    """Instance 4: archive info."""
    lines: List[str] = []
    append_kv(lines, "Current archive", s.get("current_archive"))
    append_kv(lines, "Current archive contact", s.get("current_archive_contact"))
    append_kv(lines, "Original archive contact", s.get("original_archive_contact"))
    append_kv(lines, "Original archive", s.get("original_archive"))
    append_kv(lines, "Is archived", s.get("is_archived"))
    return "\n".join(lines).strip() or None


# -------------------------
# ReferenceDescription builder
# Per diagram:
#   URL (non-DOI) -> prepend to ReferenceDescription
#   Related URL Type -> filter -> append to ReferenceDescription
#   Related URL Description -> append to ReferenceDescription
#   Related URL 1-5, Related URL Type 1-5 -> append to ReferenceDescription
# -------------------------
def build_reference_description(url_entry: Dict[str, Any], is_doi: bool) -> str:
    lines: List[str] = []
    url_val = url_entry.get("url", "")
    url_type = url_entry.get("url_type", "")
    url_desc = url_entry.get("description", "")

    # Non-DOI URL prepended per diagram filter path
    if is_filled(url_val) and not is_doi:
        lines.append(f"URL: {url_val}")
    if is_filled(url_type):
        lines.append(f"URL type: {url_type}")
    if is_filled(url_desc):
        lines.append(f"URL description: {url_desc}")

    # Related URL fields 1-5 (all appended)
    for i in range(1, 6):
        suffix = f"_{i}"
        append_kv(lines, f"Related URL {i}", url_entry.get(f"related_url{suffix}"))
        append_kv(lines, f"Related URL type {i}", url_entry.get(f"related_url_type{suffix}"))

    return "\n".join(lines).strip()


# -------------------------
# GPS format resolver
# -------------------------
def determine_gps_format_id(gps_row: Dict[str, Any]) -> Optional[int]:
    """
    1: LatDeg + LonDeg
    2: LatDeg+LatDir + LonDeg+LonDir
    3: LatDeg+LatMin + LonDeg+LonMin
    4: LatDeg+LatMin+LatDir + LonDeg+LonMin+LonDir
    5: LatDeg+LatMin+LatSec + LonDeg+LonMin+LonSec
    6: LatDeg+LatMin+LatSec+LatDir + LonDeg+LonMin+LonSec+LonDir
    7: UTMZone + UTME + UTMN
    """
    if is_filled(gps_row.get("GPSUTMZone")) and is_filled(gps_row.get("GPSUTME")) and is_filled(gps_row.get("GPSUTMN")):
        return 7
    lat_sec = is_filled(gps_row.get("GPSLatSec"))
    lon_sec = is_filled(gps_row.get("GPSLonSec"))
    lat_min = is_filled(gps_row.get("GPSLatMin"))
    lon_min = is_filled(gps_row.get("GPSLonMin"))
    lat_dir = is_filled(gps_row.get("GPSLatDirectionID"))
    lon_dir = is_filled(gps_row.get("GPSLonDirectionID"))
    lat_deg = is_filled(gps_row.get("GPSLatDeg"))
    lon_deg = is_filled(gps_row.get("GPSLonDeg"))
    if lat_deg and lon_deg and lat_min and lon_min and lat_sec and lon_sec:
        return 6 if (lat_dir and lon_dir) else 5
    if lat_deg and lon_deg and lat_min and lon_min:
        return 4 if (lat_dir and lon_dir) else 3
    if lat_deg and lon_deg:
        return 2 if (lat_dir and lon_dir) else 1
    return None


# -------------------------
# Classification tree flattener
# Diagram: Classification + Field name -> RockType tree
# -------------------------
def flatten_classification_tree(
    node: Any,
    parent_name: Optional[str] = None,
    results: Optional[List[Tuple[str, Optional[str]]]] = None,
) -> List[Tuple[str, Optional[str]]]:
    if results is None:
        results = []
    if isinstance(node, dict):
        for key, value in node.items():
            results.append((key, parent_name))
            flatten_classification_tree(value, parent_name=key, results=results)
    elif isinstance(node, list):
        for item in node:
            flatten_classification_tree(item, parent_name=parent_name, results=results)
    elif isinstance(node, str) and is_filled(node):
        results.append((node, parent_name))
    return results


# -------------------------
# Sampling method hierarchy splitter
# SESAR uses '>' for parent > child (e.g. "Grab>ROV")
# -------------------------
def split_sampling_method_hierarchy(method_str: str) -> List[str]:
    if not is_filled(method_str):
        return []
    return [part.strip() for part in method_str.split(">") if part.strip()]


# =========================================================
# Main Transformer
# =========================================================
def transform_sesar_to_geocork_staging_format_b(data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    s = data.get("sample", {})
    sample_type = (s.get("sample_type") or "").lower()
    is_core = "core" in sample_type
    sample_nk = s.get("igsn") or s.get("name")

    # =========================================================
    # GPSLocations
    # Diagram: Latitude, Latitude (end), Longitude, Longitude (end),
    #          Northing (m), Easting (m), Zone,
    #          Elevation start, Elevation end, Elevation unit
    # =========================================================
    lat = safe_float(s.get("latitude"))
    lon = safe_float(s.get("longitude"))
    northing = safe_float(s.get("northing"))
    easting = safe_float(s.get("easting"))
    utm_zone = s.get("zone")
    elev_start = safe_float(s.get("elevation"))
    elev_end = safe_float(s.get("elevation_end"))
    elev_unit_abbrev = s.get("elevation_unit")

    # Elevation logic:
    # If both elevation (start) and elevation (end) are present:
    #   GPSElev      = average(elev_start, elev_end)
    #   GPSElevError = |elev_start - GPSElev|  (half the range)
    # If only elevation (start) is present:
    #   GPSElev      = elev_start
    #   GPSElevError = None
    if elev_start is not None and elev_end is not None:
        elev = (elev_start + elev_end) / 2.0
        elev_error = abs(elev_start - elev)
    else:
        elev = elev_start
        elev_error = None

    gps_rows: List[Dict[str, Any]] = []
    gps_key = None

    if lat is not None or lon is not None or (northing is not None and easting is not None):
        # If only UTM is provided, convert to DD so GeoCORK has lat/lon populated
        if (lat is None or lon is None) and (northing is not None and easting is not None and utm_zone):
            dd_lat, dd_lon = convert_utm_to_dd(utm_zone, easting, northing)
            if dd_lat and dd_lat != '' and dd_lon and dd_lon != '':
                lat = dd_lat[0]
                lon = dd_lon[0]

        gps_row = {
            "GPSLocationID": None,
            "GPSLocationConverted": None,
            # GPSLocationDisplay is AS-generated; not staged.
            "GPSLatDeg": lat,
            "GPSLatMin": None,
            "GPSLatSec": None,
            "GPSLatDirectionID": None,
            "GPSLonDeg": lon,
            "GPSLonMin": None,
            "GPSLonSec": None,
            "GPSLonDirectionID": None,
            "GPSUTMZone": utm_zone if is_filled(utm_zone) else None,
            "GPSUTMN": northing,
            "GPSUTME": easting,
            "GPSFormatID": None,  # set below
            "GPSElev": elev,
            "GPSElevError": elev_error,
            "GPSElevUnitID": None,   # resolved later using _GPSElevUnitAbbrev
            "_gps_key": f"{lat}|{lon}|{northing}|{easting}",
            "_GPSElevUnitAbbrev": elev_unit_abbrev if is_filled(elev_unit_abbrev) else None,
        }
        gps_row["GPSFormatID"] = determine_gps_format_id(gps_row)
        gps_rows.append(gps_row)
        gps_key = gps_row["_gps_key"]

    # =========================================================
    # Samples
    # Diagram:
    #   name            -> SampleName
    #   igsn            -> SampleIGSN
    #   depth_min       -> HeightDepth        (Depth in Core min)
    #   depth_max       -> HeightDepthError   (Depth in Core max)
    #   depth_scale     -> HeightDepthUnitID
    #   (many fields)   -> SampleDescription
    # =========================================================
    depth_min = safe_float(s.get("depth_min"))
    depth_max = safe_float(s.get("depth_max"))
    depth_unit_abbrev = s.get("depth_scale")

    # Build the 4 SampleDescription instance strings up front
    sd1 = build_sample_description_1(s, is_core)
    sd2 = build_sample_description_2(s)
    sd3 = build_sample_description_3(s)
    sd4 = build_sample_description_4(s)

    # Base sample row - SampleDescription instance 1 (the primary record)
    base_sample: Dict[str, Any] = {
        "SampleID": None,
        "SampleName": s.get("name"),
        "SampleIGSN": s.get("igsn"),
        "SampleGPSLocationID": None,    # resolved later using _SampleGPSKey
        "SampleColumnID": None,         # resolved later if is_core
        "HeightDepth": depth_min,       # Depth in Core (min) per diagram
        "HeightDepthError": depth_max,  # Depth in Core (max) per diagram
        "HeightDepthUnitID": None,      # resolved later using _HeightDepthUnitAbbrev
        "DefaultSampleAgeID": None,     # resolved later from SampleAges
        "SampleDescription": sd1,
        "_SampleGPSKey": gps_key,
        "_HeightDepthUnitAbbrev": depth_unit_abbrev,
        "_DescriptionInstance": 1,
    }

    samples_rows: List[Dict[str, Any]] = [base_sample]

    # Instance 2: registrant names - new SampleDescription row linked to same sample
    if sd2 is not None:
        samples_rows.append({
            "SampleID": None,
            "SampleName": s.get("name"),
            "SampleIGSN": s.get("igsn"),
            "SampleGPSLocationID": None,
            "SampleColumnID": None,
            "HeightDepth": None,
            "HeightDepthError": None,
            "HeightDepthUnitID": None,
            "DefaultSampleAgeID": None,
            "SampleDescription": sd2,
            "_SampleGPSKey": gps_key,
            "_HeightDepthUnitAbbrev": None,
            "_DescriptionInstance": 2,
        })

    # Instance 3: collector + collection event info
    if sd3 is not None:
        samples_rows.append({
            "SampleID": None,
            "SampleName": s.get("name"),
            "SampleIGSN": s.get("igsn"),
            "SampleGPSLocationID": None,
            "SampleColumnID": None,
            "HeightDepth": None,
            "HeightDepthError": None,
            "HeightDepthUnitID": None,
            "DefaultSampleAgeID": None,
            "SampleDescription": sd3,
            "_SampleGPSKey": gps_key,
            "_HeightDepthUnitAbbrev": None,
            "_DescriptionInstance": 3,
        })

    # Instance 4: archive info
    if sd4 is not None:
        samples_rows.append({
            "SampleID": None,
            "SampleName": s.get("name"),
            "SampleIGSN": s.get("igsn"),
            "SampleGPSLocationID": None,
            "SampleColumnID": None,
            "HeightDepth": None,
            "HeightDepthError": None,
            "HeightDepthUnitID": None,
            "DefaultSampleAgeID": None,
            "SampleDescription": sd4,
            "_SampleGPSKey": gps_key,
            "_HeightDepthUnitAbbrev": None,
            "_DescriptionInstance": 4,
        })

    # =========================================================
    # Aliquots
    # Diagram: Sub-object type -> Aliquot
    # =========================================================
    aliquots_rows: List[Dict[str, Any]] = []
    sub_object_type = s.get("sub_object_type")
    if is_filled(sub_object_type):
        aliquots_rows.append({
            "AliquotID": None,
            "ParentAliquotID": None,
            "AliquotParentRow": None,
            "AliquotName": sub_object_type,
            "SampleID": None,
            "_SampleNaturalKey": sample_nk,
        })

    # =========================================================
    # Regions (TREE) + Samples_Regions bridge
    # Nesting order (largest area -> smallest):
    #
    #   Country
    #     └─ State/Province
    #          └─ County  (stored as "<value> co." to avoid ambiguity, e.g. "LA co.")
    #               └─ City
    #                    └─ Primary physiographic feature  (combined: "<type>: <name>")
    #                         └─ Location description      (appended to phys RegionDescription)
    #                              └─ Locality             (child of phys root or city if no phys)
    #                                   └─ Locality Description (RegionDescription)
    #                                       └─ Phys Feature
    #   LocationDescription (ex. SoCal Batholith)
    # =========================================================
    regions_rows: List[Dict[str, Any]] = []
    samples_regions_rows: List[Dict[str, Any]] = []
    seen_regions: set = set()

    def add_region(name: str, parent: Optional[str], description: Optional[str]) -> None:
        if name not in seen_regions:
            seen_regions.add(name)
            regions_rows.append({
                "RegionID": None,
                "ParentRegionID": None,
                "RegionParentRow": None,
                "RegionName": name,
                "RegionDescription": description,
                "_ParentRegionName": parent,
            })
            samples_regions_rows.append({
                "SampleID": None,
                "RegionID": None,
                "_SampleNaturalKey": sample_nk,
                "_RegionName": name,
            })

    # Physiographic + Geographic blocks.
    # Nesting order (largest -> smallest):
    #   Country -> State/Province -> County -> City
    #   -> Primary physiographic feature
    #   -> Location description  (own RegionName instance)
    #   -> Locality
    #
    # primary_location_type and primary_location_name are combined into a
    # single RegionName: "<type>: <name>" (or just "<type>" if name absent).
    primary_loc_type = s.get("primary_location_type")
    primary_loc_name = s.get("primary_location_name")
    location_desc = s.get("location_description")
    locality = s.get("locality")
    locality_desc = s.get("locality_description")

    # Build combined physiographic region name
    if is_filled(primary_loc_type) and is_filled(primary_loc_name):
        phys_region_name = f"{primary_loc_type}: {primary_loc_name}"
    elif is_filled(primary_loc_type):
        phys_region_name = primary_loc_type
    else:
        phys_region_name = None

    # Geographic block: Country > State/Province > County > City (largest to smallest)
    prev_geo: Optional[str] = None
    for field in ["country", "province", "county", "city"]:
        val = s.get(field)
        if is_filled(val):
            # Append "co." suffix to county values to distinguish from city names
            if field == "county":
                val = f"{val} co."
            add_region(val, prev_geo, None)
            prev_geo = val

    # location_description is a standalone root region - no parent, nothing nested under it
    if is_filled(location_desc):
        add_region(location_desc, None, None)

    # Locality sits under the geographic chain; phys feature is the deepest leaf
    locality_root: Optional[str] = None
    if is_filled(locality):
        add_region(locality, prev_geo, locality_desc if is_filled(locality_desc) else None)
        locality_root = locality

    # Physiographic feature (primary_location_type + primary_location_name combined)
    # is the last/deepest item in the chain - nested under locality if present, else city/geo
    if phys_region_name is not None:
        add_region(phys_region_name, locality_root or prev_geo, None)

    # =========================================================
    # SamplingMethods (TREE) + Samples_SamplingMethods bridge
    # Diagram: Collection method -> SamplingMethodName (with '>' hierarchy)
    #          Collection method description -> SamplingMethodDescription
    # =========================================================
    sampling_methods_rows: List[Dict[str, Any]] = []
    samples_sampling_methods_rows: List[Dict[str, Any]] = []

    method_str = s.get("collection_method")
    method_parts = split_sampling_method_hierarchy(method_str) if is_filled(method_str) else []
    method_descr = s.get("collection_method_descr")

    if method_parts:
        prev_method: Optional[str] = None
        for i, part_name in enumerate(method_parts):
            is_leaf = (i == len(method_parts) - 1)
            sampling_methods_rows.append({
                "SamplingMethodID": None,
                "ParentSamplingMethodID": None,
                "SamplingMethodParentRow": None,
                "SamplingMethodName": part_name,
                "SamplingMethodDescription": method_descr if is_leaf else None,
                "_ParentSamplingMethodName": prev_method,
            })
            prev_method = part_name
        samples_sampling_methods_rows.append({
            "SampleID": None,
            "SamplingMethodID": None,
            "_SampleNaturalKey": sample_nk,
            "_SamplingMethodName": method_parts[-1],
        })

    # =========================================================
    # RockTypes (TREE) + Samples_RockTypes bridge
    # Diagram: Classification (nested dict) -> RockType tree (parent/child)
    #          Field name (informal classification) -> RockType (new instance, leaf)
    # =========================================================
    rocktypes_rows: List[Dict[str, Any]] = []
    samples_rocktypes_rows: List[Dict[str, Any]] = []

    classification = s.get("classification")
    field_name = s.get("field_name")

    rock_type_pairs: List[Tuple[str, Optional[str]]] = []
    if is_filled(classification) and isinstance(classification, dict):
        rock_type_pairs = flatten_classification_tree(classification)

    # If description uses '>' notation it encodes a classification sub-hierarchy
    # (e.g. "Metamorphic>Foliated>Schistose>Schist"). Parse it and append any
    # nodes not already in the tree as children of the current deepest node.
    description_val = s.get("description") or ""
    if ">" in description_val:
        desc_parts = [p.strip() for p in description_val.split(">") if p.strip()]
        existing_names = {name for name, _ in rock_type_pairs}
        prev_desc: Optional[str] = rock_type_pairs[-1][0] if rock_type_pairs else None
        for part in desc_parts:
            if part not in existing_names:
                rock_type_pairs.append((part, prev_desc))
                existing_names.add(part)
            prev_desc = part

    # field_name appended as leaf under deepest classification node
    if is_filled(field_name):
        deepest_parent = rock_type_pairs[-1][0] if rock_type_pairs else None
        rock_type_pairs.append((field_name, deepest_parent))

    seen_rt: set = set()
    leaf_rt_name: Optional[str] = None
    for rt_name, rt_parent in rock_type_pairs:
        if rt_name not in seen_rt:
            seen_rt.add(rt_name)
            rocktypes_rows.append({
                "RockTypeID": None,
                "ParentRockTypeID": None,
                "RockTypeParentRow": None,
                "RockTypeName": rt_name,
                "RockTypeDescription": None,
                "_ParentRockTypeName": rt_parent,
            })
            leaf_rt_name = rt_name

    if is_filled(leaf_rt_name):
        samples_rocktypes_rows.append({
            "SampleID": None,
            "RockTypeID": None,
            "_SampleNaturalKey": sample_nk,
            "_RockTypeName": leaf_rt_name,
        })

    # =========================================================
    # SampleContexts (TREE) + Samples_SampleContexts bridge
    # Diagram - 3 separate instances:
    #
    # Instance 1: Material -> SampleContext
    #
    # Instance 2 (new instance): VerticalDatum -> SampleContext
    #
    # Instance 3 (new instance): Field program/cruise -> SampleContext (root of hierarchy)
    #   Platform type        -> Append to SampleContextDescription (instance 3)
    #   Platform name        -> Append to SampleContextDescription (instance 3)
    #   Platform description -> Append to SampleContextDescription (instance 3)
    #   Launch type          -> Append to SampleContextDescription (instance 3)
    #   Launch platform name -> Append to SampleContextDescription (instance 3)
    #   Launch ID            -> Append to SampleContextDescription (instance 3)
    # =========================================================
    sample_contexts_rows: List[Dict[str, Any]] = []
    samples_sample_contexts_rows: List[Dict[str, Any]] = []

    def add_sample_context(name: str, description: Optional[str], instance: int) -> None:
        sample_contexts_rows.append({
            "SampleContextID": None,
            "ParentSampleContextID": None,
            "SampleContextParentRow": None,
            "SampleContextName": name,
            "SampleContextDescription": description,
            "_ContextInstance": instance,
        })
        samples_sample_contexts_rows.append({
            "SampleID": None,
            "SampleContextID": None,
            "_SampleNaturalKey": sample_nk,
            "_SampleContextName": name,
            "_ContextInstance": instance,
        })

    # Instance 1: Material
    material = s.get("material")
    if is_filled(material):
        add_sample_context(material, None, 1)

    # Instance 2: VerticalDatum
    vertical_datum = s.get("vertical_datum")
    if is_filled(vertical_datum):
        add_sample_context(vertical_datum, None, 2)

    # Instance 3: Field program/cruise as root; all platform/launch fields
    # appended into the SampleContextDescription of this instance
    cruise = s.get("cruise_field_prgrm") or s.get("field_program")
    if is_filled(cruise):
        ctx3_desc_parts: List[str] = []
        append_kv(ctx3_desc_parts, "Platform type", s.get("platform_type"))
        append_kv(ctx3_desc_parts, "Platform name", s.get("platform_name"))
        append_kv(ctx3_desc_parts, "Platform description", s.get("platform_description"))
        append_kv(ctx3_desc_parts, "Launch type", s.get("launch_type_name"))
        append_kv(ctx3_desc_parts, "Launch platform name", s.get("launch_platform_name"))
        append_kv(ctx3_desc_parts, "Launch ID", s.get("launch_id"))
        ctx3_desc = "\n".join(ctx3_desc_parts) or None
        add_sample_context(cruise, ctx3_desc, 3)

    # =========================================================
    # References + staging bridge
    # Diagram:
    #   URL -> filter: DOI -> DOI column; else prepend to ReferenceDescription
    #   Related URL Type -> filter -> append to ReferenceDescription
    #   Related URL Description -> append to ReferenceDescription
    #   Related URL 1-5, Related URL Type 1-5 -> append to ReferenceDescription
    # =========================================================
    references_rows: List[Dict[str, Any]] = []
    samples_references_rows: List[Dict[str, Any]] = []

    raw_urls = s.get("external_urls")
    url_entries: List[Dict[str, Any]] = []
    if isinstance(raw_urls, dict):
        inner = raw_urls.get("external_url")
        if isinstance(inner, list):
            url_entries = inner
        elif isinstance(inner, dict):
            url_entries = [inner]
    elif isinstance(raw_urls, list):
        url_entries = raw_urls

    for url_entry in url_entries:
        if not isinstance(url_entry, dict):
            continue
        url_val = url_entry.get("url", "")
        url_type = url_entry.get("url_type", "")
        url_desc = url_entry.get("description", "")
        is_doi = "doi" in str(url_type).lower() or "doi" in str(url_val).lower()

        ref_row = {
            "ReferenceID": None,
            "Authors": None,
            "Year": None,
            "Title": url_desc if is_filled(url_desc) else None,
            "Source": None,
            "DOI": url_val if is_doi else None,
            "ReferenceDescription": build_reference_description(url_entry, is_doi) or None,
        }
        if any(is_filled(v) for k, v in ref_row.items() if k != "ReferenceID"):
            references_rows.append(ref_row)
            samples_references_rows.append({
                "SampleID": None,
                "ReferenceID": None,
                "_SampleNaturalKey": sample_nk,
                "_ReferenceDOI": ref_row["DOI"],
                "_ReferenceTitle": ref_row["Title"],
            })

    # =========================================================
    # SampleAges + Samples_SampleAges bridge
    # Diagram: Age (min) -> YoungestAge, Age (max) -> OldestAge
    # =========================================================
    sample_ages_rows: List[Dict[str, Any]] = []
    samples_sample_ages_rows: List[Dict[str, Any]] = []

    age_min = safe_float(s.get("age_min"))
    age_max = safe_float(s.get("age_max"))

    if age_min is not None or age_max is not None:
        sample_ages_rows.append({
            "SampleAgeID": None,
            "DirectAge": None,
            "DirectAgeError": None,
            "DirectAgeErrorFormatID": None,
            "OldestDirectAge": age_max,
            "YoungestDirectAge": age_min,
            "DirectAgeUnitID": None,
            "OldestAgeID": None,   # resolved via _OldestAgeName
            "YoungestAgeID": None, # resolved via _YoungestAgeName
            "SampleAgeDescription": None,
        })
        samples_sample_ages_rows.append({
            "SampleID": None,
            "SampleAgeID": None,
            "_SampleNaturalKey": sample_nk,
            "_SampleAgeIndex": 0,
        })

    # =========================================================
    # Ages (tree lookup seed)
    # Diagram: Geological age -> AgeName
    # =========================================================
    ages_rows: List[Dict[str, Any]] = []
    geological_age_str = s.get("geological_age")
    if is_filled(geological_age_str):
        ages_rows.append({
            "AgeID": None,
            "ParentAgeID": None,
            "AgeParentRow": None,
            "AgeName": geological_age_str,
            "OldestAge": age_max,
            "YoungestAge": age_min,
        })
        for sa in sample_ages_rows:
            sa["_OldestAgeName"] = geological_age_str
            sa["_YoungestAgeName"] = geological_age_str

    # =========================================================
    # Units (tree)
    # Diagram: Geological Unit -> UnitName
    # =========================================================
    units_rows: List[Dict[str, Any]] = []
    samples_units_rows: List[Dict[str, Any]] = []

    geological_unit = s.get("geological_unit")
    if is_filled(geological_unit):
        units_rows.append({
            "UnitID": None,
            "ParentUnitID": None,
            "UnitParentRow": None,
            "UnitName": geological_unit,
            "UnitDescription": None,
        })
        samples_units_rows.append({
            "SampleID": None,
            "UnitID": None,
            "_SampleNaturalKey": sample_nk,
            "_UnitName": geological_unit,
        })

    # =========================================================
    # Columns (IF/ELSE path per diagram)
    # Diagram: Size / Size Unit -> IF core: put in Columns (ColumnName)
    #                              IF NOT core: append to SampleDescription (done above)
    # =========================================================
    columns_rows: List[Dict[str, Any]] = []
    size_val = s.get("size")
    size_unit_val = s.get("size_unit")

    if is_core and is_filled(size_val):
        columns_rows.append({
            "ColumnID": None,
            "ColumnName": str(size_val),
            "ColumnTotalHeightDepth": depth_max,
            "ColumnTotalHeightDepthUnitID": None,  # resolved later using _ColumnHeightDepthUnitAbbrev
            "ColumnBaseGPSID": None,               # resolved later using _ColumnBaseGPSKey
            "ColumnDescription": f"Size unit: {size_unit_val}" if is_filled(size_unit_val) else None,
            "_ColumnHeightDepthUnitAbbrev": depth_unit_abbrev,
            "_ColumnBaseGPSKey": gps_key,
        })
        samples_rows[0]["_ColumnName"] = str(size_val)

    # =========================================================
    # SESAR Drop - intentionally not mapped per diagram:
    #   release_date, navigation_type
    # =========================================================

    # =========================================================
    # Output
    # =========================================================
    return {
        "GPSLocations": gps_rows,
        "Samples": samples_rows,
        "Aliquots": aliquots_rows,

        "Regions": regions_rows,
        "Samples_Regions": samples_regions_rows,

        "SamplingMethods": sampling_methods_rows,
        "Samples_SamplingMethods": samples_sampling_methods_rows,

        "RockTypes": rocktypes_rows,
        "Samples_RockTypes": samples_rocktypes_rows,

        "SampleContexts": sample_contexts_rows,
        "Samples_SampleContexts": samples_sample_contexts_rows,

        "References": references_rows,
        "_Samples_References_staging": samples_references_rows,  # staging helper; not a real GeoCORK table

        "SampleAges": sample_ages_rows,
        "Samples_SampleAges": samples_sample_ages_rows,
        "SampleAges_References": [],

        "Ages": ages_rows,

        "Units": units_rows,
        "Samples_Units": samples_units_rows,

        "Columns": columns_rows,
    }


def main():
    data = json.loads(IN_PATH.read_text(encoding="utf-8"))
    out = transform_sesar_to_geocork_staging_format_b(data)
    OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote GeoCORK staging JSON to: {OUT_PATH}")


if __name__ == "__main__":
    main()
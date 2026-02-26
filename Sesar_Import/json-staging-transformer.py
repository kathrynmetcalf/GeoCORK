import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# update path for directiory
IN_PATH = Path("sesar_sample.json")
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


def is_filled(x: Any) -> bool:
    return x not in (None, "", [], {})


def append_kv(lines: List[str], label: str, value: Any) -> None:
    if is_filled(value):
        lines.append(f"{label}: {value}")

# -------------------------
# Appending SESAR for sampleDescription
# -------------------------
def build_sample_description(s: Dict[str, Any]) -> str:
    lines: List[str] = []
    append_kv(lines, "SESAR sample_type", s.get("sample_type"))
    append_kv(lines, "Other names", s.get("other_names"))
    append_kv(lines, "Description", s.get("description"))
    append_kv(lines, "Purpose", s.get("purpose"))
    append_kv(lines, "Classification", s.get("classification"))
    append_kv(lines, "Classification comment", s.get("classification_comment"))
    append_kv(lines, "Collector", s.get("collector"))
    append_kv(lines, "Collector detail", s.get("collector_detail"))
    append_kv(lines, "Collection start date", s.get("collection_start_date"))
    append_kv(lines, "Collection end date", s.get("collection_end_date"))
    append_kv(lines, "Current archive", s.get("current_archive"))
    append_kv(lines, "Current archive contact", s.get("current_archive_contact"))
    append_kv(lines, "Primary location type", s.get("primary_location_type"))
    append_kv(lines, "Primary location name", s.get("primary_location_name"))
    append_kv(lines, "Locality", s.get("locality"))
    append_kv(lines, "Locality description", s.get("locality_description"))
    append_kv(lines, "Parent IGSN", s.get("parent_igsn"))
    return "\n".join(lines).strip()


# -------------------------
# GPS format resolver
# -------------------------
def determine_gps_format_id(gps_row: Dict[str, Any]) -> Optional[int]:
    """
    Chooses GPSFormatID based on which GPS fields are filled, matching the schema's display cases:

    1: LatDeg + LonDeg
    2: LatDeg + LatDirection + LonDeg + LonDirection
    3: LatDeg+LatMin + LonDeg+LonMin
    4: LatDeg+LatMin+LatDirection + LonDeg+LonMin+LonDirection
    5: LatDeg+LatMin+LatSec + LonDeg+LonMin+LonSec
    6: LatDeg+LatMin+LatSec+LatDirection + LonDeg+LonMin+LonSec+LonDirection
    7: UTMZone + UTME + UTMN

    This aligns with the CASE statement in GeoCORKSchema.GPSLocations.
    """
    # UTM case
    if is_filled(gps_row.get("GPSUTMZone")) and is_filled(gps_row.get("GPSUTME")) and is_filled(gps_row.get("GPSUTMN")):
        return 7

    # DMS / DM / D cases
    lat_sec = is_filled(gps_row.get("GPSLatSec"))
    lon_sec = is_filled(gps_row.get("GPSLonSec"))
    lat_min = is_filled(gps_row.get("GPSLatMin"))
    lon_min = is_filled(gps_row.get("GPSLonMin"))
    lat_dir = is_filled(gps_row.get("GPSLatDirectionID"))
    lon_dir = is_filled(gps_row.get("GPSLonDirectionID"))
    lat_deg = is_filled(gps_row.get("GPSLatDeg"))
    lon_deg = is_filled(gps_row.get("GPSLonDeg"))

    # Prefer the "most specific" format available
    if lat_deg and lon_deg and lat_min and lon_min and lat_sec and lon_sec:
        return 6 if (lat_dir and lon_dir) else 5

    if lat_deg and lon_deg and lat_min and lon_min:
        return 4 if (lat_dir and lon_dir) else 3

    if lat_deg and lon_deg:
        return 2 if (lat_dir and lon_dir) else 1

    return None


# -------------------------
# Transformer
# -------------------------
def transform_sesar_to_geocork_staging_format_b(data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    s = data.get("sample", {})

    # ---- GPSLocations (GeoCORK columns) ----
    lat = safe_float(s.get("latitude"))
    lon = safe_float(s.get("longitude"))

    gps_rows: List[Dict[str, Any]] = []
    gps_key = None  # helper key to link sample -> gps in staging without real IDs

    if lat is not None or lon is not None:
        gps_row = {
            "GPSLocationID": None,
            "GPSLocationConverted": None,
            # Display is AS-generated in GeoCORK; we don't stage it.
            "GPSLatDeg": lat,
            "GPSLatMin": None,
            "GPSLatSec": None,
            "GPSLatDirectionID": None,
            "GPSLonDeg": lon,
            "GPSLonMin": None,
            "GPSLonSec": None,
            "GPSLonDirectionID": None,
            "GPSUTMZone": None,
            "GPSUTMN": None,
            "GPSUTME": None,
            "GPSFormatID": None,  # set below
            "GPSElev": None,
            "GPSElevError": None,
            "GPSElevUnitID": None,
            # helper
            "_gps_key": f"{lat}|{lon}",
        }
        gps_row["GPSFormatID"] = determine_gps_format_id(gps_row)  # should be 1 here for initial sample (LatDeg and LonDeg used)
        gps_rows.append(gps_row)
        gps_key = gps_row["_gps_key"]

    # ---- Samples (GeoCORK columns) ----
    # Samples table columns are defined here.
    depth = safe_float(s.get("depth_max"))
    depth_unit_abbrev = s.get("depth_scale")  # e.g. "cm" (will later be resolved to DistanceUnitID)

    samples_rows: List[Dict[str, Any]] = [{
        "SampleID": None,
        "SampleName": s.get("name"),
        "SampleIGSN": s.get("igsn"),
        "SampleGPSLocationID": None,      # resolved later using _SampleGPSKey
        "SampleColumnID": None,           # not staging Columns yet
        "HeightDepth": depth,
        "HeightDepthError": None,
        "HeightDepthUnitID": None,        # resolved later using _HeightDepthUnitAbbrev
        "DefaultSampleAgeID": None,       # for later stage of SampleAges, resolve this
        "SampleDescription": build_sample_description(s),

        # helpers (not DB columns): used by the importer to resolve IDs
        "_SampleGPSKey": gps_key,
        "_HeightDepthUnitAbbrev": depth_unit_abbrev,
    }]

    # use SampleIGSN as the natural key for bridge staging
    sample_nk = s.get("igsn") or s.get("name")

    # ---- Regions tree rows + bridge rows ----
    # Regions is a TREE with a bridge table Samples_Regions.
    regions_rows: List[Dict[str, Any]] = []
    samples_regions_rows: List[Dict[str, Any]] = []

    # Simple path list (add true parent/child structure later)
    # order is country -> specific location name
    region_names = [
        s.get("country"),
        s.get("province"),
        s.get("city"),
        s.get("primary_location_type"),
        s.get("primary_location_name"),
    ]
    seen = set()
    for rn in region_names:
        if is_filled(rn) and rn not in seen:
            seen.add(rn)
            regions_rows.append({
                "RegionID": None,
                "ParentRegionID": None,
                "RegionParentRow": None,
                "RegionName": rn,
                "RegionDescription": None,
            })
            # Bridge table expects SampleID + RegionID.
            samples_regions_rows.append({
                "SampleID": None,
                "RegionID": None,
                # helpers for later resolution
                "_SampleNaturalKey": sample_nk,
                "_RegionName": rn,
            })

    # ---- SamplingMethods tree rows + bridge rows ----
    # SamplingMethods is a TREE with bridge Samples_SamplingMethods
    sampling_methods_rows: List[Dict[str, Any]] = []
    samples_sampling_methods_rows: List[Dict[str, Any]] = []

    if is_filled(s.get("collection_method")) or is_filled(s.get("collection_method_descr")):
        sm_name = s.get("collection_method") or "Unknown sampling method"
        sampling_methods_rows.append({
            "SamplingMethodID": None,
            "ParentSamplingMethodID": None,
            "SamplingMethodParentRow": None,
            "SamplingMethodName": sm_name,
            "SamplingMethodDescription": s.get("collection_method_descr"),
        })
        # Bridge table expects SampleID + SamplingMethodID
        samples_sampling_methods_rows.append({
            "SampleID": None,
            "SamplingMethodID": None,
            "_SampleNaturalKey": sample_nk,
            "_SamplingMethodName": sm_name,
        })

    # ---- RockTypes tree rows + bridge rows ----
    # RockTypes is a TREE with bridge Samples_RockTypes
    rocktypes_rows: List[Dict[str, Any]] = []
    samples_rocktypes_rows: List[Dict[str, Any]] = []

    # "classification/material" mapped to RockTypeName.
    if is_filled(s.get("material")):
        rt_name = s.get("material")
        rocktypes_rows.append({
            "RockTypeID": None,
            "ParentRockTypeID": None,
            "RockTypeParentRow": None,
            "RockTypeName": rt_name,
            "RockTypeDescription": None,
        })
        # Bridge table expects SampleID + RockTypeID.
        samples_rocktypes_rows.append({
            "SampleID": None,
            "RockTypeID": None,
            "_SampleNaturalKey": sample_nk,
            "_RockTypeName": rt_name,
        })

    # ---- Output  ----
    # NOTE: Many-to-many tables in schema are real tables, so staging them is valid.
    staging = {
        "GPSLocations": gps_rows,
        "Samples": samples_rows,

        "Regions": regions_rows,
        "Samples_Regions": samples_regions_rows,

        "SamplingMethods": sampling_methods_rows,
        "Samples_SamplingMethods": samples_sampling_methods_rows,

        "RockTypes": rocktypes_rows,
        "Samples_RockTypes": samples_rocktypes_rows,

        # Not staged yet (add later):
        "SampleAges": [],
        "Samples_SampleAges": [],
        "References": [],
        "SampleAges_References": [],
    }
    return staging


def main():
    data = json.loads(IN_PATH.read_text(encoding="utf-8"))
    out = transform_sesar_to_geocork_staging_format_b(data)
    OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote GeoCORK staging JSON to: {OUT_PATH}")


if __name__ == "__main__":
    main()
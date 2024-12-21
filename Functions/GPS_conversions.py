import math
import pyproj
import PyQt6
from PyQt6 import QtSql as QtS

def convert_dd_to_ddm(ddlat: list, ddlon: list):
    if len(ddlat) != 1 or len(ddlon) != 1:
        return "Invalid input"
    lat_deg = int(ddlat[0])
    lon_deg = int(ddlon[0])
    lat_min = (abs(ddlat[0]) - abs(lat_deg)) * 60
    lon_min = (abs(ddlon[0]) - abs(lon_deg)) * 60
    return [lat_deg, lat_min], [lon_deg, lon_min]

def convert_ddm_to_dd(ddmlat: list, ddmlon: list):
    if len(ddmlat) != 2 or len(ddmlon) != 2:
        return "Invalid input"
    if ddmlat[0] >= 0:
        lat_deg = ddmlat[0] + ddmlat[1] / 60
    else:
        lat_deg = ddmlat[0] - ddmlat[1] / 60
    if ddmlon[0] >= 0:
        lon_deg = ddmlon[0] + ddmlon[1] / 60
    else:
        lon_deg = ddmlon[0] - ddmlon[1] / 60
    return [lat_deg], [lon_deg]

def convert_dd_to_dms(ddlat: list, ddlon: list):
    if len(ddlat) != 1 or len(ddlon) != 1:
        return "Invalid input"
    lat_deg = int(ddlat)
    lon_deg = int(ddlon)
    lat_dm = (abs(ddlat) - abs(lat_deg)) * 60
    lon_dm = (abs(ddlon) - abs(lon_deg)) * 60
    lat_min = int(lat_dm)
    lon_min = int(lon_dm)
    lat_sec = (lat_dm - lat_min) * 60
    lon_sec = (lon_dm - lon_min) * 60
    return [lat_deg, lat_min, lat_sec], [lon_deg, lon_min, lon_sec]

def convert_dms_to_dd(dmslat: list, dmslon: list):
    if len(dmslat) != 3 or len(dmslon) != 3:
        return "Invalid input"
    if dmslat[0] >= 0:
        lat_deg = dmslat[0] + dmslat[1] / 60 + dmslat[2] / 3600
    else:
        lat_deg = dmslat[0] - dmslat[1] / 60 - dmslat[2] / 3600
    if dmslon[0] >= 0:
        lon_deg = dmslon[0] + dmslon[1] / 60 + dmslon[2] / 3600
    else:
        lon_deg = dmslon[0] - dmslon[1] / 60 - dmslon[2] / 3600
    return [lat_deg], [lon_deg]

def convert_ddm_to_dms(ddmlat: list, ddmlon: list):
    """
    Convert degrees, decimal minutes (DDM) to degrees, minutes, seconds (DMS)
    @param ddmlat: [degrees, decimal_minutes]
    @param ddmlon: [degrees, decimal_minutes]
    @return: List of latitude and longitude values in the order [degrees, minutes, seconds] or "Invalid input"
    """
    if len(ddmlat) != 2 or len(ddmlon) != 2:
        return "Invalid input"
    lat_deg = ddmlat[0]
    lon_deg = ddmlon[0]
    lat_min = int(ddmlat[1])
    lon_min = int(ddmlon[1])
    lat_sec = (ddmlat[1] - lat_min) * 60
    lon_sec = (ddmlon[1] - lon_min) * 60
    return [lat_deg, lat_min, lat_sec], [lon_deg, lon_min, lon_sec]

def convert_dms_to_ddm(dmslat: list, dmslon: list):
    """
    Convert degrees, minutes, seconds (DMS) to degrees, decimal minutes (DDM)
    @param dmslat: [degrees, minutes, seconds]
    @param dmslon: [degrees, minutes, seconds]
    @return: List of latitude and longitude values in the order [degrees, decimal_minutes] or "Invalid input"
    """
    if len(dmslat) != 3 or len(dmslon) != 3:
        return "Invalid input"
    lat_deg = dmslat[0]
    lon_deg = dmslon[0]
    lat_min = dmslat[1] + dmslat[2] / 60
    lon_min = dmslon[1] + dmslon[2] / 60
    return [lat_deg, lat_min], [lon_deg, lon_min]

def convert_sign_to_direction(lat: list, lon: list):
    """
    Convert DD, DDM, or DMS values with a sign to the same format with a direction
    @param lat: list of latitude values in the order [degrees, minutes, seconds]
    @param lon: list of longitude values in the order [degrees, minutes, seconds]
    @return: list each of latitude and longitude values in the order [degrees, minutes, seconds, direction_abbreviation] or "Invalid input"
    """
    lat_deg = abs(lat[0])
    lon_deg = abs(lon[0])
    lat_dir = 'N' if lat[0] >= 0 else 'S'
    lon_dir = 'E' if lon[0] >= 0 else 'W'
    if len(lat) == 1:
        return [lat_deg, lat_dir], [lon_deg, lon_dir]
    elif len(lat) == 2:
        return [lat_deg, lat[1], lat_dir], [lon_deg, lon[1], lon_dir]
    elif len(lat) == 3:
        return [lat_deg, lat[1], lat[2], lat_dir], [lon_deg, lon[1], lon[2], lon_dir]
    else:
        return "Invalid input"


def convert_direction_to_sign(lat: list, lon: list):
    """
    Convert DD, DDM, or DMS values with direction to the same format with a sign
    @param lat: list of latitude values in the order [degrees, minutes, seconds, direction_unit_id], skip any values not present
    @param lon: list of longitude values in the order [degrees, minutes, seconds, direction_unit_id], skip any values not present
    @return: list each of latitude and longitude values in the order [degrees, minutes, seconds] as appropriate or "Invalid input"
    """
    if len(lat) == 2:
        direction_index = 1
    elif len(lat) == 3:
        direction_index = 2
    elif len(lat) == 4:
        direction_index = 3
    else:
        return "Invalid input"
    direction_model = QtS.QSqlTableModel()
    direction_model.setTable('DirectionUnits')
    direction_model.select()
    direction_model.setFilter(f'DirectionUnitID = "{lat[direction_index]}"')
    lat_dir = direction_model.record(0).value('DirectionUnitAbbreviation')
    direction_model.setFilter(f'DirectionUnitID = "{lon[direction_index]}"')
    lon_dir = direction_model.record(0).value('DirectionUnitAbbreviation')
    if lat_dir == 'N':
        lat_deg = lat[0]
    else:
        lat_deg = -lat[0]
    if lon_dir == 'E':
        lon_deg = lon[0]
    else:
        lon_deg = -lon[0]
    if len(lat) == 2:
        return [lat_deg], [lon_deg]
    elif len(lat) == 3:
        return [lat_deg, lat[1]], [lon_deg, lon[1]]
    elif len(lat) == 4:
        return [lat_deg, lat[1], lat[2]], [lon_deg, lon[1], lon[2]]

def convert_dd_to_utm(ddlat, ddlon):
    """
    Convert latitude and longitude in decimal degrees to UTM coordinates using WGS84 datum
    @param ddlat: latitude in decimal degrees as real number
    @param ddlon: longitude in decimal degrees as real number
    @return: UTMN, UTME, zone with N or S, or "Invalid input"
    """
    if len(ddlat) != 1 or len(ddlon) != 1:
        return "Invalid input"
    lat_deg = ddlat[0]
    lon_deg = ddlon[0]
    if lon_deg < -180 or lon_deg >= 180:
        return f"Invalid longitude: {lon_deg}"
    if lat_deg < 56 or lat_deg >= -80:
        zone = math.floor((ddlon[0] + 180)/6) + 1
    elif 72 <= lat_deg < 84:
        if 0 <= lon_deg < 9:
            zone = 31
        elif 9 <= lon_deg < 21:
            zone = 33
        elif 21 <= lon_deg < 33:
            zone = 35
        elif 33 <= lon_deg < 42:
            zone = 37
    elif 56 <= lat_deg < 64 and 3 <= lon_deg < 12:
        zone = 32
    else:
        return f"Invalid latitude: {lat_deg}"
    if lat_deg < 0:
        south = True
        zone_txt = f"{zone}S"
    else:
        south = False
        zone_txt = f"{zone}N"

    proj_utm = pyproj.Proj(proj="utm", zone=zone, datum="WGS84", south=south)
    UTMN, UTME = proj_utm(lat_deg, lon_deg)
    return UTMN, UTME, zone_txt

def convert_utm_to_dd(zone_txt, UTME, UTMN):
    """
    Convert UTM coordinates to latitude and longitude in decimal degrees using WGS84 datum
    @param zone_txt: UTM zone as string with N or S to indicate hemisphere, e.g. "10N", assumes N if no direction given
    @param UTME: UTM easting as real number
    @param UTMN: UTM northing as real number
    @return: decimal degree latitude and longitude as real numbers or "Invalid input"
    """
    # remove any spaces in the zone text
    zone_txt = zone_txt.replace(" ", "")
    if zone_txt[-1] == 'S':
        south = True
        zone = int(zone_txt[:-1])
    elif zone_txt[-1] == 'N':
        south = False
        zone = int(zone_txt[:-1])
    else:
        south = False
        zone = int(zone_txt)
    proj_utm = pyproj.Proj(proj="utm", zone=zone, datum="WGS84", south=south)
    lat, lon = proj_utm(UTME, UTMN, inverse=True)
    return [lat], [lon]
from PyQt6 import QtSql

import logger_setup
import util.Text_manipulations as TxM
from Functions.Settings_manager import SettingsManager

settings = SettingsManager().settings


def display_age(string: str) -> str:
    """
    Displays and converts an age to a rounded value if desired.
    :param string: Age string in the format 'DirectAge±DirectAgeError (DirectAgeUnitID),
    OldestDirectAge-YoungestDirectAge (DirectAgeUnitID), OldestRelativeAge-YoungestRelativeAge'
    :return: Age formatted to the current rounding setting.
    """
    # split string on commas
    from util.database.database_helper import get_name_from_id
    if ',' not in string:
        return ''
    else:
        age_elements = string.split(', ')
        # element 0 is the direct age with error, element 1 is the direct age range, and element 2 is the relative age range
        # for 0, retrieve the number in parentheses, the direct age unit ID which is the same for 0 and 1
        age_ids = age_elements[2].split('-')
        if age_ids[0] != '':
            old_age_id = int(age_ids[0])
            old_age_name = get_name_from_id('Ages', old_age_id)
        else:
            old_age_name = ''
        if age_ids[1] != '':
            young_age_id = int(age_ids[1])
            young_age_name = get_name_from_id('Ages', young_age_id)
        else:
            young_age_name = ''
        if ' (' in age_elements[0]:
            # age unit is in the display, so replace ids with abbreviations
            age_unit_id = int(age_elements[0].split(' (')[1].split(')')[0])
            if age_unit_id is not None:
                age_unit_abbreviation = get_name_from_id('AgeUnits', age_unit_id)
            else:
                age_unit_abbreviation = ''
            # in age_elements[0] and age_elements[1], replace the direct age unit ID with the unit abbreviation
            age_elements[0] = age_elements[0].replace(f'({age_unit_id})', f'({age_unit_abbreviation})')
            age_elements[1] = age_elements[1].replace(f'({age_unit_id})', f'({age_unit_abbreviation})')
        # age_elements[0] is in the format 'DirectAge±DirectAgeError (DirectAgeUnitID)' or 'DirectAge±DirectAgeError'
        # age_elements[1] is in the format 'OldestDirectAge-YoungestDirectAge (DirectAgeUnitID)' or 'OldestDirectAge-YoungestDirectAge'
        # replace the float values with the rounded values unless the value is an integer
        age = age_elements[0].split('±')[0]
        rounded_age = return_rounded(age)
        age_error = age_elements[0].split('±')[1].split(' ')[0]
        rounded_error = return_rounded(age_error)
        old_age = age_elements[1].split('-')[0]
        rounded_old_age = return_rounded(old_age)
        young_age = age_elements[1].split('-')[1]
        rounded_young_age = return_rounded(young_age)
        age_elements[0] = age_elements[0].replace(f'{age}±{age_error}', f'{rounded_age}±{rounded_error}')
        age_elements[1] = age_elements[1].replace(f'{old_age}-{young_age}', f'{rounded_old_age}-{rounded_young_age}')
        age_elements[2] = f'{old_age_name}-{young_age_name}'
        return ', '.join(age_elements)


def display_gps(string: str):
    lat_dir = ''
    lon_dir = ''
    if '"' in string or '\'\'' in string:
        # DMS format, (lat_deg°lat_min'lat_sec" lat_dir, lon_deg°lon_min'lon_sec" lon_dir) or (lat_deg°lat_min'lat_sec", lon_deg°lon_min'lon_sec")
        if '"' in string:
            second_delimiter = '"'
        elif '\'\'' in string:
            second_delimiter = '\'\''
        lat_string = string.split(', ')[0]
        lon_string = string.split(', ')[1]
        lat_sec = lat_string.split('°')[1].split(second_delimiter)[0].split('\'')[1]
        lon_sec = lon_string.split('°')[1].split(second_delimiter)[0].split('\'')[1]
        rounded_lat_sec = return_rounded(lat_sec)
        rounded_lon_sec = return_rounded(lon_sec)
        string = string.replace(f'{lat_sec}{second_delimiter}', f'{rounded_lat_sec}{second_delimiter}')
        string = string.replace(f'{lon_sec}{second_delimiter}', f'{rounded_lon_sec}{second_delimiter}')
        if not lat_dir and not lon_dir:
            try:
                lat_dir = lat_string.split(f'{second_delimiter} ')[1]
                lon_dir = lon_string.split(f'{second_delimiter} ')[1]
            except IndexError:
                pass
    if "'" in string:
        # DM format, (lat_deg°lat_min' lat_dir, lon_deg°lon_min' lon_dir) or (lat_deg°lat_min', lon_deg°lon_min')
        lat_string = string.split(', ')[0]
        lon_string = string.split(', ')[1]
        lat_min = lat_string.split('°')[1].split('\'')[0]
        lon_min = lon_string.split('°')[1].split('\'')[0]
        rounded_lat_min = return_rounded(lat_min)
        rounded_lon_min = return_rounded(lon_min)
        string = string.replace(f'{lat_min}\'', f'{rounded_lat_min}\'')
        string = string.replace(f'{lon_min}\'', f'{rounded_lon_min}\'')
        if not lat_dir and not lon_dir:
            try:
                lat_dir = lat_string.split('\' ')[1]
                lon_dir = lon_string.split('\' ')[1]
            except IndexError:
                pass
    if '°' in string:
        # D format, (lat_deg° lat_dir, lon_deg° lon_dir)
        lat_deg = string.split('°')[0]
        lon_deg = string.split(', ')[1].split('°')[0]
        rounded_lat_deg = return_rounded(lat_deg)
        rounded_lon_deg = return_rounded(lon_deg)
        string = string.replace(f'{lat_deg}°', f'{rounded_lat_deg}°')
        string = string.replace(f'{lon_deg}°', f'{rounded_lon_deg}°')
        if not lat_dir and not lon_dir:
            try:
                lat_dir = string.split('° ')[1].split(', ')[0]
                lon_dir = string.split('° ')[2]
            except IndexError:
                lat_dir = ''
                lon_dir = ''
        try:
            lat_dir_id = int(lat_dir)
            query = QtSql.QSqlQuery()
            if query.exec(f'SELECT DirectionUnitAbbreviation FROM DirectionUnits WHERE DirectionUnitID={lat_dir_id}'):
                query.next()
                lat_dir_abbreviation = query.value(0)
                lat_string = string.split(', ')[0][:-1] + lat_dir_abbreviation
                string = string.replace(string.split(', ')[0], lat_string)
            lon_dir_id = int(lon_dir)
            if query.exec(f'SELECT DirectionUnitAbbreviation FROM DirectionUnits WHERE DirectionUnitID={lon_dir_id}'):
                query.next()
                lon_dir_abbreviation = query.value(0)
                lon_string = string.split(', ')[1][:-1] + lon_dir_abbreviation
                string = string.replace(string.split(', ')[1], lon_string)
        except:
            # If there is no direction or it is not an ID, there is nothing to do
            pass
    elif ',' in string:
        # UTM format, (UTMZone, UTMEasting, UTMNorthing)
        utm_easting = string.split(',')[1]
        utm_e_m = utm_easting.split('m')[0]
        utm_northing = string.split(',')[2]
        utm_n_m = utm_northing.split('m')[0]
        rounded_northing = return_rounded(utm_n_m)
        rounded_easting = return_rounded(utm_e_m)
        string = string.replace(utm_n_m, f'{rounded_northing}')
        string = string.replace(utm_e_m, f'{rounded_easting}')
    else:
        # No GPS given, return ''
        string = ''
    return string


def display_value_with_error(string: str):
    if string == '± ()':
        return ''
    if '±' in string:
        # value with error, value±error (unit) or value±error
        value = string.split('±')[0]
        rounded_value = return_rounded(value)
        error = string.split('±')[1].split(' ')[0]
        rounded_error = return_rounded(error)
        string = string.replace(f'{value}±{error}', f'{rounded_value}±{rounded_error}')
    return string


def return_rounded(value: str | float | int):
    round_values = settings.value('round_values')
    if round_values == 'false':
        return value
    decimal_places = settings.value('decimals_to_show')
    if isinstance(value, str):
        if value == '':
            return value
        elif '.' in value:
            try:
                float(value)  # value is float, not text
                if value.split('.')[1] != '0':
                    # if the decimal places exceed the limit, return a rounded value, prevents 1.1 from becoming 1.100000
                    if len(value.split('.')[1]) > decimal_places:
                        rounded_value = str(round(float(value), decimal_places))
                    else:
                        rounded_value = value
                else:  # value is an integer
                    rounded_value = int(float(value))
            except ValueError:
                rounded_value = value
        else:
            try:
                int(value)  # value is integer, not text
                rounded_value = int(value)
            except ValueError:
                rounded_value = value
    elif isinstance(value, float):
        if value - int(value) != 0:
            rounded_value = f'{value:.{decimal_places}f}'
        else:
            rounded_value = int(value)
    else:
        rounded_value = value
    return rounded_value


def return_number(value: str | float | int):
    """
    Convert a string to a number, if possible. If not, return it as is.
    :param value: String, float, or integer to convert to the best number format
    :return: Value as a number or the original string if it was not a number
    """
    if isinstance(value, str):
        if value == '':
            return value
        try:
            return_value = int(value)
        except ValueError:
            try:
                return_value = float(value)
            except ValueError:
                return_value = value
        return return_value
    elif isinstance(value, float):
        try:
            return_value = int(value)
        except ValueError:
            return_value = value
        return return_value
    elif isinstance(value, int):
        return value
    else:
        logger_setup.get_logger().info(f"Invalid value type: {type(value)}. Expected str, float, or int.")
        return value


def get_readable_header(header: str):
    """
    For a given header/col name it will convert to a user readable header format by removing spaces, abbreviations, and
    adding units from the settings where appropriate. This method MUST work for all viewable columns and tables.
    :param header: header to convert
    :return: converted header
    """
    header = TxM.remove_spaces(header)
    if 'ID' in header or 'Abbreviation' in header:
        if 'Elev' in header:
            header = 'Elevation Unit'
        elif 'AgeUnit' in header:
            header = 'Age Unit'
        elif 'RatioErrorFormat' in header:
            header = 'Ratio Error Format'
        elif 'AgeErrorFormat' in header:
            header = 'Age Error Format'
        elif 'Height' in header:
            header = 'Height/Depth Unit'
        elif 'GPSFormat' in header:
            header = 'GPS Format'
        elif 'SpotSize' in header:
            header = 'Spot Size Unit'
        elif 'ConcordanceFormat' in header:
            header = 'Concordance Format'
    if 'GPSLocationConverted' in header:
        header = 'Converted GPS Location'
    elif 'GPSLocationDisplay' in header:
        header = 'GPS Location'
    elif 'SampleElevationCalculated' in header:
        header = f'Calculated Sample Elevation ({settings.value('elevation_unit_abbreviation')})'
    elif 'SampleElevation' in header:
        header = f'Sample Elevation'
    elif 'ColumnElevationCalculated' in header:
        header = f'Calculated Column Elevation ({settings.value('elevation_unit_abbreviation')})'
    elif 'ColumnElevation' in header:
        header = f'Column Elevation'
    elif 'GPSElev' in header:
        header += f' ({settings.value("elevation_unit_abbreviation")})'
    elif 'TotalHeightDepthCalculated' in header:
        header = f'Calculated Total Height/Depth ({settings.value('heightdepth_unit_abbreviation')})'
    elif 'TotalHeightDepth' in header:
        header = f'Total Height/Depth'
    elif 'HeightDepthCalculated' in header or 'CalculatedHeightDepth' in header:
        header = f'Calculated Height/Depth ({settings.value('heightdepth_unit_abbreviation')})'
    elif 'HeightDepth' in header:
        header = header.replace('HeightDepth', 'Height/Depth')
    elif 'AgeError' in header and 'Calculated' in header:
        header += f' ({settings.value("age_error_format_abbreviation")})'
    elif 'CalculatedSpotSize' in header:
        header = f'Calculated Spot Size ({settings.value('spotsize_unit_abbreviation')})'
    elif 'CalculatedConcordance_206Pb/238Uv207Pb/206Pb' in header:
        header = f'Calculated Concordance 206Pb/238Uv207Pb/206Pb ({settings.value('concordance_format_abbreviation')})'
    elif 'CalculatedConcordance_206Pb/238Uv207Pb/235U' in header:
        header = f'Calculated Concordance 206Pb/238Uv207Pb/235U ({settings.value('concordance_format_abbreviation')})'
    elif ('Age' in header and 'Calculated' in header
          and not any(
                s in header for s in ['Name', 'Description', 'Reference', 'Unit', 'Format', 'Created', 'Modified'])):
        header += f' ({settings.value("age_unit_abbreviation")})'
    elif 'Error' in header and 'Calculated' in header:
        if 'Corr/Rho' in header:
            header += f' ({settings.value("ratio_error_format_abbreviation")})'
        else:
            header = header.replace('Error', f' Error ({settings.value("ratio_error_format_abbreviation")})')
    if 'Name' in header and header not in ('SampleName', 'Sample Name', 'AliquotName', 'Aliquot Name', 'SpotName',
                                           'Spot Name', 'GrainName', 'Grain Name', 'UPbAnalysisName',
                                           'U-Pb Analysis Name'):
        header = header.replace('Name', '')
        if header.endswith('y'):
            header = header[:-1] + 'ies'
        elif header.endswith('is'):
            header = header[:-2] + 'es'
        else:
            header += 's'
    if 'Display' in header:
        header = header.replace('Display', '')
    if 'Calculated' in header:
        header = header.replace('Calculated', 'Converted ')
    if 'ppm' in header:
        header = header.replace('ppm', '(ppm)')
    if 'cps' in header:
        header = header.replace('cps', '(cps)')
    if '"' in header:
        header = header.replace('"', '')
    header = TxM.add_spaces_camel(header)
    if 'U Pb' in header:
        header = header.replace('U Pb', 'U-Pb')
    if ' Pb/' in header:
        header = header.replace(' Pb/', 'Pb/')
    if '8 U' in header:
        header = header.replace('8 U', '8U')
    if '5 U' in header:
        header = header.replace('5 U', '5U')
    if '2 Th' in header:
        header = header.replace('2 Th', '2Th')
    if ' Pb' in header:
        header = header.replace(' Pb', 'Pb')
    if ' U ' in header:
        header = header.replace(' U ', 'U ')
    if '(' in header and ' (' not in header:
        header = header.replace('(', ' (')
    return header

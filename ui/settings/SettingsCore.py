"""
Shared Settings helpers: setting keys, defaults, color/theme functions and ColorButton.
Moved verbatim from ui/Settings.py; ui/Settings.py re-exports everything so existing imports keep working.
"""

from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (QFont, QColor, QPalette, QBrush)
from PyQt6.QtSql import QSqlQueryModel, QSqlQuery
from PyQt6.QtWidgets import QColorDialog

import logger_setup
import Functions.SQLUtils as SQLUtils
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings

# ----------------------------------------------------------------------------------------------------------------------
# Color settings
# ----------------------------------------------------------------------------------------------------------------------
COLOR_MODES = ['light', 'dark']
"""Color modes that each have their own set of color settings."""

COLOR_THEME_MODES = ['System', 'Light', 'Dark']
"""Options for the 'color_theme_mode' setting. 'System' follows the operating system light/dark preference."""

THEME_COLOR_ROLES = {
    'text': 'Main text',
    'fill': 'Fill (background)',
}
"""Application theme color roles -> display label. Setting key format: theme_{mode}_{role}_color"""

IMPORTER_COLOR_ROLES = {
    'mapped': 'Mapped column header',
    'loaded_mapping': 'Loaded mapping header',
    'autofilled': 'Auto-filled cell',
    'conflict': 'Conflict / error cell',
    'existing': 'Existing record cell',
    'disabled_text': 'Disabled row text',
    'text': 'Cell text',
}
"""Import Wizard color roles -> display label. Setting key format: importer_{mode}_{role}_color"""

DEFAULT_THEME_COLORS = {
    'light': {'text': '#000000', 'fill': '#f0f0f0'},
    'dark': {'text': '#e6e6e6', 'fill': '#2b2b2b'},
}
"""Default application theme colors for each mode."""

DEFAULT_IMPORTER_COLORS = {
    # Light mode values match the colors currently hard-coded in ImportWizard.py
    'light': {'mapped': '#c0ffb8', 'loaded_mapping': '#b8cfff', 'autofilled': '#d4b8ff', 'conflict': '#ffb8b8',
              'existing': '#fffab8', 'disabled_text': '#a0a0a0', 'text': '#000000'},
    # Dark mode values are darker, saturated versions so light text stays readable
    'dark': {'mapped': '#2f5d2a', 'loaded_mapping': '#2c4373', 'autofilled': '#4e3a78', 'conflict': '#7a2e2e',
             'existing': '#6e6526', 'disabled_text': '#7a7a7a', 'text': '#e6e6e6'},
}
"""Default Import Wizard colors for each mode."""

SHOW_PER_PAGE_VALUES = ['10', '25', '50', '100', '250', '500', '1000']

def theme_color_key(mode: str, role: str) -> str:
    """Setting key for an application theme color, e.g. theme_dark_text_color"""
    return f'theme_{mode}_{role}_color'


def importer_color_key(mode: str, role: str) -> str:
    """Setting key for an Import Wizard color, e.g. importer_light_conflict_color"""
    return f'importer_{mode}_{role}_color'


THEME_COLOR_KEYS = [theme_color_key(mode, role) for mode in COLOR_MODES for role in THEME_COLOR_ROLES]
IMPORTER_COLOR_KEYS = [importer_color_key(mode, role) for mode in COLOR_MODES for role in IMPORTER_COLOR_ROLES]
COLOR_SETTING_KEYS = ['color_theme_mode', 'custom_theme_colors'] + THEME_COLOR_KEYS + IMPORTER_COLOR_KEYS
"""All color related setting keys"""

settings_list = [
    'default_settings', 'age_unit_id', 'age_unit_abbreviation', 'elevation_unit_id', 'elevation_unit_abbreviation',
    'gps_format_id',
    'gps_format_abbreviation', 'heightdepth_unit_id', 'heightdepth_unit_abbreviation', 'spotsize_unit_id',
    'spotsize_unit_abbreviation', 'age_error_format_id', 'age_error_format_abbreviation', 'ratio_error_format_id',
    'ratio_error_format_abbreviation', 'concordance_format_id', 'concordance_format_abbreviation', 'reference_format',
    'geochem_error_format_id', 'geochem_error_format_abbreviation',
    'decimals_to_show', 'sample_view_columns', 'sample_view_freeze', 'sample_edit_columns', 'sample_edit_freeze',
    'aliquot_view_columns', 'aliquot_view_freeze', 'aliquot_edit_columns', 'aliquot_edit_freeze',
    'grain_view_columns', 'grain_view_freeze', 'grain_edit_columns', 'grain_edit_freeze',
    'spot_view_columns', 'spot_view_freeze', 'spot_edit_columns', 'spot_edit_freeze',
    'upb_analysis_view_columns', 'upb_analysis_view_freeze', 'upb_analysis_edit_columns', 'upb_analysis_edit_freeze',
    'geochem_analysis_view_columns', 'geochem_analysis_view_freeze', 'geochem_analysis_edit_columns', 'geochem_analysis_edit_freeze',
    'column_view_columns', 'column_view_freeze', 'column_edit_columns', 'column_edit_freeze', 'reference_view_columns',
    'reference_view_freeze', 'checkable_combobox_height_scalar', 'geochem_values_edit_columns',
    'checkable_combobox_width_scalar', 'font_family', 'font_size', 'table_font_size', 'debug_level', 'show_per_page',
    'autofill_best_age', 'young_fill_best_age', 'old_fill_best_age', 'best_age_cutoff', 'geocork_version',
    'current_db_path', 'display_tooltips', 'show_items_missing_data', 'display_analyses'] + COLOR_SETTING_KEYS
"""List of all setting keys used by GeoCORK. This list is used to check for missing settings and to reset settings to default values."""

# True when apply_color_palette() has set a custom palette on the QApplication
_custom_palette_applied = False
# Guards against re-entry when changing the color scheme hint emits colorSchemeChanged
_applying_palette = False


def _apply_color_scheme_hint():
    """
    Requests the Qt color scheme matching the 'color_theme_mode' setting (Qt 6.8+). On older Qt versions this does
    nothing and the custom palette (if enabled) is the only change.
    """
    hints = QtW.QApplication.styleHints()
    if not hasattr(hints, 'setColorScheme'):
        return
    mode = settings.value('color_theme_mode', 'System')
    if mode == 'Light':
        hints.setColorScheme(Qt.ColorScheme.Light)
    elif mode == 'Dark':
        hints.setColorScheme(Qt.ColorScheme.Dark)
    elif hasattr(hints, 'unsetColorScheme'):
        hints.unsetColorScheme()
    else:
        hints.setColorScheme(Qt.ColorScheme.Unknown)


def is_dark_mode() -> bool:
    """
    Returns True if GeoCORK should currently use the dark mode colors. An explicit 'Light'/'Dark' setting wins,
    otherwise the operating system preference is used.
    :rtype: bool
    """
    mode = settings.value('color_theme_mode', 'System')
    if mode == 'Dark':
        return True
    if mode == 'Light':
        return False
    try:
        scheme = QtW.QApplication.styleHints().colorScheme()
        if scheme == Qt.ColorScheme.Dark:
            return True
        if scheme == Qt.ColorScheme.Light:
            return False
    except AttributeError:
        # Qt < 6.5 has no colorScheme()
        pass
    # Fall back to the lightness of the style's standard palette (not app.palette(), which may be our custom one)
    style = QtW.QApplication.style()
    if style is None:
        return False
    return style.standardPalette().color(QPalette.ColorRole.Window).lightness() < 128


def active_color_mode() -> str:
    """Returns 'dark' or 'light' depending on is_dark_mode()"""
    return 'dark' if is_dark_mode() else 'light'


def _setting_color(key: str, fallback: str) -> QColor:
    """Returns the QColor stored in key, or fallback if the stored value is missing/invalid."""
    color = QColor(str(settings.value(key, fallback)))
    if not color.isValid():
        logger_setup.get_logger().warning(f'Invalid color stored for {key}, using {fallback}')
        color = QColor(fallback)
    return color


def get_theme_color(role: str, dark: bool = None) -> QColor:
    """
    Returns the application theme color for the given role ('text' or 'fill').
    :param str role: key of THEME_COLOR_ROLES
    :param bool dark: force dark (True) or light (False) colors, None uses the active mode
    """
    mode = active_color_mode() if dark is None else ('dark' if dark else 'light')
    return _setting_color(theme_color_key(mode, role), DEFAULT_THEME_COLORS[mode][role])


def get_importer_color(role: str, dark: bool = None) -> QColor:
    """
    Returns the Import Wizard color for the given role.
    :param str role: key of IMPORTER_COLOR_ROLES, e.g. 'conflict'
    :param bool dark: force dark (True) or light (False) colors, None uses the active mode
    """
    mode = active_color_mode() if dark is None else ('dark' if dark else 'light')
    return _setting_color(importer_color_key(mode, role), DEFAULT_IMPORTER_COLORS[mode][role])


def get_importer_brushes(dark: bool = None) -> dict:
    """
    Returns {role: QBrush} for every Import Wizard color role in the active (or forced) mode. Intended to replace the
    hard-coded brushes in ImportWizard.__init__.
    :param bool dark: force dark (True) or light (False) colors, None uses the active mode
    """
    return {role: QBrush(get_importer_color(role, dark)) for role in IMPORTER_COLOR_ROLES}


def _blend(color_a: QColor, color_b: QColor, ratio: float = 0.5) -> QColor:
    """Linear blend of two colors, ratio 0 -> color_a, 1 -> color_b"""
    return QColor(round(color_a.red() + (color_b.red() - color_a.red()) * ratio),
                  round(color_a.green() + (color_b.green() - color_a.green()) * ratio),
                  round(color_a.blue() + (color_b.blue() - color_a.blue()) * ratio))


def build_theme_palette(text: QColor, fill: QColor) -> QPalette:
    """
    Builds a QPalette from a main text color and a fill color. Bevel colors (light, mid, dark, shadow) are derived
    by Qt from the fill, input/table backgrounds are a slight shift of the fill, highlight colors are kept from the
    style's standard palette.
    """
    standard = QtW.QApplication.style().standardPalette()
    palette = QPalette(fill, fill)
    dark = fill.lightness() < 128
    base = fill.lighter(115) if dark else fill.lighter(106)
    alternate_base = base.lighter(112) if dark else base.darker(104)
    disabled_text = _blend(text, fill, 0.5)

    for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
        palette.setColor(group, QPalette.ColorRole.WindowText, text)
        palette.setColor(group, QPalette.ColorRole.Text, text)
        palette.setColor(group, QPalette.ColorRole.ButtonText, text)
        palette.setColor(group, QPalette.ColorRole.ToolTipText, text)
        palette.setColor(group, QPalette.ColorRole.PlaceholderText, disabled_text)
        palette.setColor(group, QPalette.ColorRole.Window, fill)
        palette.setColor(group, QPalette.ColorRole.Button, fill)
        palette.setColor(group, QPalette.ColorRole.ToolTipBase, fill)
        palette.setColor(group, QPalette.ColorRole.Base, base)
        palette.setColor(group, QPalette.ColorRole.AlternateBase, alternate_base)
        palette.setColor(group, QPalette.ColorRole.Highlight, standard.color(group, QPalette.ColorRole.Highlight))
        palette.setColor(group, QPalette.ColorRole.HighlightedText,
                         standard.color(group, QPalette.ColorRole.HighlightedText))
        palette.setColor(group, QPalette.ColorRole.Link, standard.color(group, QPalette.ColorRole.Link))

    group = QPalette.ColorGroup.Disabled
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText,
                 QPalette.ColorRole.PlaceholderText):
        palette.setColor(group, role, disabled_text)
    palette.setColor(group, QPalette.ColorRole.Window, fill)
    palette.setColor(group, QPalette.ColorRole.Button, fill)
    palette.setColor(group, QPalette.ColorRole.Base, fill)
    return palette


def apply_color_palette():
    """
    Applies the color settings to the active QApplication: sets the light/dark color scheme hint and, if
    'custom_theme_colors' is enabled, a palette built from the active mode's text and fill colors.
    """
    global _custom_palette_applied, _applying_palette
    app = QtW.QApplication.instance()
    if app is None or _applying_palette:
        return
    _applying_palette = True
    try:
        _apply_color_scheme_hint()
        if settings.value('custom_theme_colors') == 'true':
            mode = active_color_mode()
            logger_setup.get_logger().debug(f'Applying custom {mode} mode theme colors')
            app.setPalette(build_theme_palette(get_theme_color('text'), get_theme_color('fill')))
            _custom_palette_applied = True
        elif _custom_palette_applied:
            # Custom colors were turned off, go back to the style's palette
            app.setPalette(app.style().standardPalette())
            _custom_palette_applied = False
    finally:
        _applying_palette = False


def update_stylesheet():
    """
    Updates the stylesheet of the application based on the current settings.
    """
    # Apply the stylesheet to the active QApplication object
    app = QtW.QApplication.instance()
    set_font = QFont(settings.value('font_family'), int(settings.value('font_size')))
    app.setFont(set_font)
    # setting the font size and family, by setting to lower class QAbstractItemView
    # subclasses QTableView, QTreeView, QListView and created ones in Widget_classes.py are still affected
    app.setStyleSheet(f'''
        QAbstractItemView {{
            font-size: {settings.value('table_font_size')}pt;
        }}
        ''')
    apply_color_palette()


def populate_app_defaults():
    """
    Populate the application with default settings. This is called when the application starts up.
    """
    app = QtW.QApplication.instance()
    settings.setValue('default_font_family', app.font().family())
    settings.setValue('default_font_size', app.font().pointSize())
    settings.setValue('default_table_font_size', app.font().pointSize())

    # Re-apply colors when the operating system switches between light and dark mode (Qt 6.5+)
    hints = QtW.QApplication.styleHints()
    if hasattr(hints, 'colorSchemeChanged'):
        hints.colorSchemeChanged.connect(lambda *_: apply_color_palette())

    # If other settings have been set, update the font and stylesheet
    if settings.value('default_settings') == 'false':
        update_stylesheet()


def default_settings():
    """
    Sets the default settings for the application. Every setting has a default variant with the prefix 'default_'.
    """
    # set the default settings values
    # Unit and Format settings
    default_dict = {'default_geocork_version': 'v1.1.0',
                    'default_age_unit_id': 2,
                    'default_age_unit_abbreviation': 'Ma',
                    'default_elevation_unit_id': 2,
                    'default_elevation_unit_abbreviation': 'm',
                    'default_gps_format_id': 1,
                    'default_gps_format_abbreviation': 'DD +/-',
                    'default_heightdepth_unit_id': 2,
                    'default_heightdepth_unit_abbreviation': 'm',
                    'default_spotsize_unit_id': 5,
                    'default_spotsize_unit_abbreviation': 'µm',
                    'default_age_error_format_id': 1,
                    'default_age_error_format_abbreviation': '1σ abs',
                    'default_ratio_error_format_id': 3,
                    'default_ratio_error_format_abbreviation': '1σ %',
                    'default_concordance_format_id': 2,
                    'default_concordance_format_abbreviation': 'Con%',
                    'default_reference_format': '''(ifnull(Authors, "") || ", " || ifnull(Year, "") || ", " || ifnull(Source, ""))''',
                    'default_geochem_error_format_id': 1,
                    'default_geochem_error_format_abbreviation': '1σ abs',
                    'default_round_values': 'false',
                    'default_decimals_to_show': 4,
                    'default_db_file': '',
                    'default_checkable_combobox_height_scalar': 1.0,
                    'default_checkable_combobox_width_scalar': 1.0,
                    'default_debug_level': 'INFO',
                    'default_show_per_page': 100,
                    'default_autofill_best_age': 'true',
                    'default_young_fill_best_age': '"206Pb/238UAge"',
                    'default_old_fill_best_age': '"207Pb/206PbAge"',
                    'default_best_age_cutoff': 1000,
                    'default_display_tooltips': 'true',
                    'default_show_items_missing_data': 'true',
                    'default_display_analyses': ['UPbAnalyses', 'GeoChemicalAnalyses'],
                    'default_color_theme_mode': 'System',
                    'default_custom_theme_colors': 'false'}
    for mode in COLOR_MODES:
        for role in THEME_COLOR_ROLES:
            default_dict[f'default_{theme_color_key(mode, role)}'] = DEFAULT_THEME_COLORS[mode][role]
        for role in IMPORTER_COLOR_ROLES:
            default_dict[f'default_{importer_color_key(mode, role)}'] = DEFAULT_IMPORTER_COLORS[mode][role]
    for default_key, default_value in default_dict.items():
        custom_key = default_key.split('default_')[1]
        if not settings.contains(default_key) or (settings.contains(default_key) and settings.value(default_key) != default_value):
            settings.setValue(default_key, default_value)
            settings.setValue(custom_key, default_value)
        if not settings.contains(custom_key):
            settings.setValue(custom_key, default_value)

    default_sample_view_columns = []
    sample_view_columns = SQLUtils.view_attributes_dict['SampleView']
    for column in sample_view_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_sample_view_columns.append(column_name)
    # Column display settings
    if (not settings.contains('default_sample_view_columns') or
            (settings.contains('default_sample_view_columns') and
            set(settings.value('default_sample_view_columns')) != set(default_sample_view_columns))):
        settings.setValue('default_sample_view_columns', default_sample_view_columns)
        settings.setValue('sample_view_columns', default_sample_view_columns)

    default_sample_edit_columns = []
    sample_edit_columns = SQLUtils.view_attributes_dict['SampleEditView']
    for column in sample_edit_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_sample_edit_columns.append(column_name)
    if (not settings.contains('default_sample_edit_columns') or
            (settings.contains('default_sample_edit_columns') and
            set(settings.value('default_sample_edit_columns')) != set(default_sample_edit_columns))):
        settings.setValue('default_sample_edit_columns', default_sample_edit_columns)
        settings.setValue('sample_edit_columns', default_sample_edit_columns)

    default_aliquot_view_columns = []
    aliquot_view_columns = SQLUtils.view_attributes_dict['AliquotView']
    for column in aliquot_view_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_aliquot_view_columns.append(column_name)
    if (not settings.contains('default_aliquot_view_columns') or
            (settings.contains('default_aliquot_view_columns') and
            set(settings.value('default_aliquot_view_columns')) != set(default_aliquot_view_columns))):
        settings.setValue('default_aliquot_view_columns', default_aliquot_view_columns)
        settings.setValue('aliquot_view_columns', default_aliquot_view_columns)

    default_aliquot_edit_columns = []
    aliquot_edit_columns = SQLUtils.view_attributes_dict['AliquotEditView']
    for column in aliquot_edit_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_aliquot_edit_columns.append(column_name)
    if (not settings.contains('default_aliquot_edit_columns') or
            (settings.contains('default_aliquot_edit_columns') and
            set(settings.value('default_aliquot_edit_columns')) != set(default_aliquot_edit_columns))):
        settings.setValue('default_aliquot_edit_columns', default_aliquot_edit_columns)
        settings.setValue('aliquot_edit_columns', default_aliquot_edit_columns)

    default_grain_view_columns = []
    grain_view_columns = SQLUtils.view_attributes_dict['GrainView']
    for column in grain_view_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_grain_view_columns.append(column_name)
    if (not settings.contains('default_grain_view_columns') or
            (settings.contains('default_grain_view_columns') and
             set(settings.value('default_grain_view_columns')) != set(default_grain_view_columns))):
        settings.setValue('default_grain_view_columns', default_grain_view_columns)

    default_grain_edit_columns = []
    grain_edit_columns = SQLUtils.view_attributes_dict['GrainEditView']
    for column in grain_edit_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_grain_edit_columns.append(column_name)
    if (not settings.contains('default_grain_edit_columns') or
            (settings.contains('default_grain_edit_columns') and
            set(settings.value('default_grain_edit_columns')) != set(default_grain_edit_columns))):
        settings.setValue('default_grain_edit_columns', default_grain_edit_columns)
        settings.setValue('grain_edit_columns', default_grain_edit_columns)

    default_spot_view_columns = []
    spot_view_columns = SQLUtils.view_attributes_dict['SpotView']
    for column in spot_view_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_spot_view_columns.append(column_name)
    if (not settings.contains('default_spot_view_columns') or
            (settings.contains('default_spot_view_columns') and
            set(settings.value('default_spot_view_columns')) != set(default_spot_view_columns))):
        settings.setValue('default_spot_view_columns', default_spot_view_columns)

    default_spot_edit_columns = []
    spot_edit_columns = SQLUtils.view_attributes_dict['SpotEditView']
    for column in spot_edit_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_spot_edit_columns.append(column_name)
    if (not settings.contains('default_spot_edit_columns') or
            (settings.contains('default_spot_edit_columns') and
            set(settings.value('default_spot_edit_columns')) != set(default_spot_edit_columns))):
        settings.setValue('default_spot_edit_columns', default_spot_edit_columns)
        settings.setValue('spot_edit_columns', default_spot_edit_columns)

    default_upb_analysis_view_columns = []
    upb_analysis_view_columns = SQLUtils.view_attributes_dict['UPbView']
    for column in upb_analysis_view_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_upb_analysis_view_columns.append(column_name)
    if (not settings.contains('default_upb_analysis_view_columns') or
            (settings.contains('default_upb_analysis_view_columns') and
            set(settings.value('default_upb_analysis_view_columns')) != set(default_upb_analysis_view_columns))):
        settings.setValue('default_upb_analysis_view_columns', default_upb_analysis_view_columns)
        settings.setValue('upb_analysis_view_columns', default_upb_analysis_view_columns)

    default_upb_analysis_edit_columns = []
    upb_analysis_edit_columns = SQLUtils.view_attributes_dict['UPbEditView']
    for column in upb_analysis_edit_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_upb_analysis_edit_columns.append(column_name)
    if (not settings.contains('default_upb_analysis_edit_columns') or
            (settings.contains('default_upb_analysis_edit_columns') and
            set('default_upb_analysis_edit_columns') == set(default_upb_analysis_edit_columns))):
        settings.setValue('default_upb_analysis_edit_columns', default_upb_analysis_edit_columns)
        settings.setValue('upb_analysis_edit_columns', default_upb_analysis_edit_columns)

    default_geochem_analysis_view_columns = []
    geochem_analysis_view_columns = SQLUtils.view_attributes_dict['GeoChemView']
    for column in geochem_analysis_view_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        if 'Created' in column:
            # Retrieve all analyte abbreviations from the database and include columns for value, error, and unit
            query = QSqlQuery()
            if not query.exec(f'SELECT GeoChemAnalyteAbbreviation FROM GeoChemicalAnalytes') and 'Driver' not in query.lastError().text():
                logger_setup.get_logger().critical(f'Error fetching geochemical analytes for settings')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                continue
            if 'Driver' not in query.lastError().text():
                while query.next():
                    default_geochem_analysis_view_columns.append(query.value('GeoChemAnalyteAbbreviation'))
        default_geochem_analysis_view_columns.append(column_name)
    if (not settings.contains('default_geochem_analysis_view_columns') or
            (settings.contains('default_geochem_analysis_view_columns') and
             set(settings.value('default_geochem_analysis_view_columns')) != set(default_geochem_analysis_view_columns))):
        settings.setValue('default_geochem_analysis_view_columns', default_geochem_analysis_view_columns)
        settings.setValue('geochem_analysis_view_columns', default_geochem_analysis_view_columns)

    default_geochem_analysis_edit_columns = []
    geochem_analysis_edit_columns = SQLUtils.view_attributes_dict['GeoChemEditView']
    for column in geochem_analysis_edit_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        if 'Created' in column:
            # Retrieve all analyte abbreviations from the database and include columns for value, error, and unit
            query = QSqlQuery()
            if not query.exec(f'SELECT GeoChemAnalyteAbbreviation FROM GeoChemicalAnalytes') and 'Driver' not in query.lastError().text():
                logger_setup.get_logger().critical(f'Error fetching geochemical analytes for settings')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                continue
            analyte_abbreviations = []
            if 'Driver' not in query.lastError().text():
                while query.next():
                    analyte_abbreviations.append(query.value('GeoChemAnalyteAbbreviation'))
                for abbreviation in analyte_abbreviations:
                    default_geochem_analysis_edit_columns.append(f'{abbreviation}Value')
                    default_geochem_analysis_edit_columns.append(f'{abbreviation}Error')
                    default_geochem_analysis_edit_columns.append(f'{abbreviation}Unit')
                    default_geochem_analysis_edit_columns.append(f'{abbreviation}ErrorFormat')
        default_geochem_analysis_edit_columns.append(column_name)
    if (not settings.contains('default_geochem_analysis_edit_columns') or
            (settings.contains('default_geochem_analysis_edit_columns') and
             set('default_geochem_analysis_edit_columns') != set(default_geochem_analysis_edit_columns))):
        settings.setValue('default_geochem_analysis_edit_columns', default_geochem_analysis_edit_columns)
        settings.setValue('geochem_analysis_edit_columns', default_geochem_analysis_edit_columns)

    default_column_view_columns = []
    column_view_columns = SQLUtils.view_attributes_dict['ColumnView']
    for column in column_view_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_column_view_columns.append(column_name)
    if (not settings.contains('default_column_view_columns') or
            (settings.contains('default_column_view_columns') and
            set(settings.value('default_column_view_columns')) != set(default_column_view_columns))):
        settings.setValue('default_column_view_columns', default_column_view_columns)
        settings.setValue('column_view_columns', default_column_view_columns)

    default_column_edit_columns = []
    column_edit_columns = SQLUtils.view_attributes_dict['ColumnEditView']
    for column in column_edit_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_column_edit_columns.append(column_name)
    if (not settings.contains('default_column_edit_columns') or
            (settings.contains('default_column_edit_columns') and
            set(settings.value('default_column_edit_columns')) != set(default_column_edit_columns))):
        settings.setValue('default_column_edit_columns', default_column_edit_columns)
        settings.setValue('column_edit_columns', default_column_edit_columns)

    default_reference_view_columns = []
    reference_view_columns = SQLUtils.view_attributes_dict['ReferenceView']
    for column in reference_view_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_reference_view_columns.append(column_name)
    if (not settings.contains('default_reference_view_columns') or
            (settings.contains('default_reference_view_columns') and
            set(settings.value('default_reference_view_columns')) != set(default_reference_view_columns))):
        settings.setValue('default_reference_view_columns', default_reference_view_columns)
        settings.setValue('reference_view_columns', default_reference_view_columns)

def reset_to_default_settings():
    """
    Reset the settings to utilize default_settings.
    """
    if settings.value('default_settings') == 'true':
        for setting in settings_list:
            if setting == 'default_settings':
                pass
            else:
                # Set the value of setting to default_setting, e.g. sets 'decimals_to_show' to 'default_decimals_to_show'
                # effectively resetting the setting to default, the rest of the app uses 'decimals_to_show'
                settings.setValue(setting, settings.value(f'default_{setting}'))

        # Apply the stylesheet to the active QApplication object
        update_stylesheet()


def check_missing_settings():
    """
    Check if any of the settings are missing, if so, set them to the default
    """
    for setting in settings_list:
        if settings.value(setting) is None:
            settings.setValue(setting, settings.value(f'default_{setting}'))

def update_column_settings() -> bool:
    """
    Check the current column settings against the default settings. If a column does not exist in the default settings,
    remove it. This is a column name from an older version that is no longer in use.
    :return:
    """
    from Functions import SQLUtils
    column_settings_dict = SQLUtils.view_setting_dict.copy()
    for view, column_settings in column_settings_dict.items():
        # remove any duplicates
        current_columns = list(dict.fromkeys(settings.value(column_settings)))
        default_columns = settings.value(f'default_{column_settings}')
        for column in current_columns:
            # Remove any columns that are not in the default list
            if column not in default_columns:
                try:
                    # Some columns had 'Name' appended from previous versions
                    if f'{column}Name' in default_columns:
                        index = current_columns.index(column)
                        current_columns[index] = f'{column}Name'
                    else:
                        current_columns.remove(column)
                except Exception as e:
                    logger_setup.get_logger().debug(f'Remove column error: {e}')
                    return False
        settings.setValue(column_settings, current_columns)
    return True

def update_setting(key: str, value: str):
    """
    Sets the given setting key to the given value. Sets default_settings to false if it is true, since default settings
    are no longer being utilized.
    :param str key: setting key
    :param value: setting value to set
    """
    settings.setValue(key, value)
    if settings.value('default_settings') == 'true':
        settings.setValue('default_settings', 'false')


def update_abbreviation(id_key: str) -> bool:
    """
    Update the abbreviation for the given id_key in the settings.
    :param str id_key: the id_key to update the setting to
    :return: True for success, False for failure
    :rtype: bool
    """
    # Update the abbreviations in the settings file
    model = QSqlQueryModel()
    if id_key == 'age_unit_id':
        model.setQuery(f"SELECT AgeUnitAbbreviation FROM AgeUnits WHERE AgeUnitID = {settings.value(id_key)}")
    # if id_key == 'analytical_unit_id':
    #     model.setQuery(f"SELECT AgeUnitAbbreviation FROM AgeUnits WHERE AgeUnitID = {settings.value(id_key)}")
    elif id_key == 'elevation_unit_id':
        model.setQuery(
            f"SELECT DistanceUnitAbbreviation FROM DistanceUnits WHERE DistanceUnitID = {settings.value(id_key)}")
    elif id_key == 'gps_format_id':
        model.setQuery(f"SELECT GPSFormatAbbreviation FROM GPSFormats WHERE GPSFormatID = {settings.value(id_key)}")
    elif id_key == 'heightdepth_unit_id':
        model.setQuery(
            f"SELECT DistanceUnitAbbreviation FROM DistanceUnits WHERE DistanceUnitID = {settings.value(id_key)}")
    elif id_key == 'spotsize_unit_id':
        model.setQuery(
            f"SELECT DistanceUnitAbbreviation FROM DistanceUnits WHERE DistanceUnitID = {settings.value(id_key)}")
    elif id_key == 'age_error_format_id':
        model.setQuery(
            f"SELECT ErrorFormatAbbreviation FROM ErrorFormats WHERE ErrorFormatID = {settings.value(id_key)}")
    elif id_key == 'ratio_error_format_id':
        model.setQuery(
            f"SELECT ErrorFormatAbbreviation FROM ErrorFormats WHERE ErrorFormatID = {settings.value(id_key)}")
    elif id_key == 'concordance_format_id':
        model.setQuery(
            f"SELECT ConcordanceFormatAbbreviation FROM ConcordanceFormats WHERE ConcordanceFormatID = {settings.value(id_key)}")
    while model.canFetchMore():
        model.fetchMore()
    if model.rowCount() == 0:
        logger_setup.get_logger().critical(f"Error: No results found for {id_key}: {model.lastError().text()}")
        return False
    abbreviation_key = id_key.replace('_id', '_abbreviation')
    settings.setValue(abbreviation_key, model.record(0).value(0))
    return True


class ColorButton(QtW.QPushButton):
    """
    Push button that displays a color swatch with its hex code and opens a QColorDialog when clicked.
    """
    colorChanged = pyqtSignal(str)

    def __init__(self, color: str = '#000000', parent=None):
        super().__init__(parent)
        self._color = '#000000'
        self._text_color = None
        self.setMinimumSize(90, 25)
        self.setMaximumHeight(25)
        self.set_color(color)
        self.clicked.connect(self.pick_color)

    def color(self) -> str:
        """Returns the current color as a lowercase '#rrggbb' string"""
        return self._color

    def set_color(self, color: str):
        """Sets the swatch color, invalid colors are ignored"""
        qcolor = QColor(str(color))
        if not qcolor.isValid():
            logger_setup.get_logger().warning(f'Invalid color {color} for {self.objectName()}')
            return
        self._color = qcolor.name()
        self._refresh()

    def set_text_color(self, color: str = None):
        """
        Sets the color of the hex label drawn on the swatch, used to preview text over a fill color. None picks
        black or white for contrast.
        """
        self._text_color = QColor(str(color)).name() if color and QColor(str(color)).isValid() else None
        self._refresh()

    def _refresh(self):
        text_color = self._text_color or ('#000000' if QColor(self._color).lightness() > 127 else '#ffffff')
        self.setText(self._color.upper())
        self.setStyleSheet(f'QPushButton {{ background-color: {self._color}; color: {text_color}; '
                           f'border: 1px solid #808080; border-radius: 3px; }}')

    def pick_color(self):
        """Opens a color dialog and updates the swatch if a color is chosen"""
        qcolor = QColorDialog.getColor(QColor(self._color), self, 'Select Color')
        if qcolor.isValid() and qcolor.name() != self._color:
            self.set_color(qcolor.name())
            self.colorChanged.emit(self._color)

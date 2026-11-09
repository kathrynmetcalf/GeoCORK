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
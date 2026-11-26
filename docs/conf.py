"""
Sphinx configuration for the GeoCORK documentation.

Build locally from the repository root with::

    pip install -r docs/requirements.txt
    sphinx-build -b html docs docs/_build/html

Read the Docs uses the same file through ``.readthedocs.yaml`` at the repository root.
"""
import os
import re
import shutil
import sys
from pathlib import Path

# -- Paths -------------------------------------------------------------------
# GeoCORK uses absolute imports from the repository root (``from Functions import SQLUtils``,
# ``from util.database ...``), so the root must be importable.
DOCS_DIR = Path(__file__).resolve().parent
REPO_ROOT = DOCS_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

# -- Headless Qt -------------------------------------------------------------
# Many GeoCORK modules run Qt code at import time (``settings = SettingsManager().settings``,
# ``QStandardPaths.writableLocation(...)``), and geocork_logger.critical()/error() open a QMessageBox.
# A QApplication on the offscreen platform keeps autodoc imports from aborting the build.
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS', '--no-sandbox')
os.environ.setdefault('QTWEBENGINE_DISABLE_SANDBOX', '1')
try:
    from PyQt6 import QtCore, QtWidgets

    # Must be set before the QApplication exists for QtWebEngine (ui.SampleMap) to import cleanly
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    try:  # QtWebEngine has to be imported before the QApplication is created
        from PyQt6 import QtWebEngineWidgets  # noqa: F401
    except ImportError:
        pass
    # Separate organization so a docs build never touches a developer's real GeoCORK QSettings
    QtCore.QCoreApplication.setOrganizationName('GeoCORK-docs')
    _qt_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(['sphinx'])

    # A modal message box would hang an unattended build (nobody can click OK), so during the docs build the
    # static QMessageBox helpers return their default button immediately.
    def _no_block(*args, **kwargs):
        return kwargs.get('defaultButton', QtWidgets.QMessageBox.StandardButton.Ok)

    for _name in ('critical', 'warning', 'information', 'question', 'about'):
        setattr(QtWidgets.QMessageBox, _name, staticmethod(_no_block))
except ImportError:  # PyQt6 not installed: fall back to mocking it (see autodoc_mock_imports)
    _qt_app = None

# -- Project information -----------------------------------------------------
project = 'GeoCORK'
author = 'Kathryn Metcalf and Jarrod M. Burges'
copyright = '2026, GeoCORK developers'


def _geocork_version() -> str:
    """Read 'default_geocork_version' from ui/settings/SettingsCore.py so the docs never drift from the app."""
    settings_core = REPO_ROOT / 'ui' / 'settings' / 'SettingsCore.py'
    try:
        match = re.search(r"['\"]default_geocork_version['\"]\s*:\s*['\"]v?([^'\"]+)['\"]",
                          settings_core.read_text(encoding='utf-8'))
        if match:
            return match.group(1)
    except OSError:
        pass
    return os.environ.get('GEOCORK_VERSION', 'dev')


release = _geocork_version()
version = '.'.join(release.split('.')[:2])

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx_copybutton',
    'myst_parser',  # lets Markdown files (e.g. ui/UserInterfaceNamingConventions.md) be included
]

source_suffix = {'.rst': 'restructuredtext', '.md': 'markdown'}
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
root_doc = 'index'
language = 'en'

# -- autodoc / autosummary ---------------------------------------------------
autosummary_generate = True
autosummary_imported_members = False
autosummary_ignore_module_all = True

autodoc_default_options = {
    'members': True,
    'undoc-members': True,  # most Qt slots are undocumented; list them anyway
    'show-inheritance': True,
    'member-order': 'bysource',
    # Do NOT add 'inherited-members': it would pull in hundreds of QWidget/QObject methods per class
}
autodoc_typehints = 'description'
autodoc_typehints_format = 'short'
autodoc_class_signature = 'separated'
autodoc_preserve_defaults = True  # show `database=QSqlDatabase()` instead of an object repr
autoclass_content = 'both'  # class docstring + __init__ docstring

# Libraries that are heavy or not on PyPI are mocked. PyQt6 is installed for real (see docs/requirements.txt)
# because GeoCORK runs Qt code at import time; it is only mocked if it cannot be imported at all.
autodoc_mock_imports = ['detritalPy', 'pyrolite']
if _qt_app is None:
    autodoc_mock_imports.append('PyQt6')

todo_include_todos = True

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
}

# Keep the build readable: a missing cross-reference to a Qt class is expected, not an error
nitpicky = False
suppress_warnings = ['autosummary.import_cycle']

# -- HTML output (Furo) ------------------------------------------------------
html_theme = 'furo'
html_title = f'GeoCORK {release}'
html_static_path = ['_static']
html_baseurl = os.environ.get('READTHEDOCS_CANONICAL_URL', 'https://documentation.geocork.org/')

# Copy the app's light/dark logos from ui/ so there is one source for both the app and the docs
_logos = {}
for _key, _logo in (('light_logo', 'GeoCORKLogo_Lightmode.svg'), ('dark_logo', 'GeoCORKLogo_Darkmode.svg')):
    _src = REPO_ROOT / 'ui' / _logo
    if _src.exists():
        (DOCS_DIR / '_static').mkdir(exist_ok=True)
        shutil.copy2(_src, DOCS_DIR / '_static' / _logo)
        _logos[_key] = _logo

html_theme_options = {
    **_logos,
    'sidebar_hide_name': bool(_logos),  # show the text title only when there is no logo
    'navigation_with_keys': True,
    'source_repository': 'https://github.com/OWNER/GeoCORK/',  # TODO: set the real GitHub owner
    'source_branch': 'main',
    'source_directory': 'docs/',
}
html_favicon = None


# -- Docstring clean-up --------------------------------------------------------
_FIELD = re.compile(r'^\s*:(param|type|return|returns|rtype|raises|raise|var|ivar|cvar|vartype|meta)\b')


def _separate_field_lists(app, what, name, obj, options, lines):
    """
    GeoCORK docstrings usually put ``:param ...:`` directly under the summary with no blank line. reST then reads
    the fields as part of the summary paragraph, so they render as plain text. Insert the missing blank line.
    Empty ``:return:`` fields are dropped so they don't render as a blank "Returns" heading.
    """
    cleaned = []
    for line in lines:
        if re.fullmatch(r'\s*:returns?:\s*', line):
            continue
        if _FIELD.match(line) and cleaned and cleaned[-1].strip() and not _FIELD.match(cleaned[-1]) \
                and not cleaned[-1].startswith((' ', '\t')):
            cleaned.append('')
        cleaned.append(line)
    lines[:] = cleaned


def setup(app):
    app.connect('autodoc-process-docstring', _separate_field_lists)

import os
import sys

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QPainter, QPalette
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QDialog, QApplication, QHBoxLayout, QPushButton

import logger_setup
from Functions.Settings_manager import SettingsManager

settings = SettingsManager().settings

GITHUB_URL = 'https://github.com/kathrynmetcalf/GeoCORK'
HELP_URL = GITHUB_URL + '/wiki'  # Placeholder: point this at the real help site
ISSUES_URL = GITHUB_URL + '/issues'
CITATION_DOI = 'https://doi.org/10.5281/zenodo.15833658'
LOGO_HEIGHT = 70  # logical pixels


def _logo_pixmap(widget) -> QPixmap | None:
    """Render the light or dark GeoCORK logo to match the current palette."""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    palette = QApplication.palette()
    is_dark = (palette.color(QPalette.ColorRole.Window).lightness()
               < palette.color(QPalette.ColorRole.WindowText).lightness())
    svg_name = 'GeoCORKLogo_Darkmode.svg' if is_dark else 'GeoCORKLogo_Lightmode.svg'
    renderer = QSvgRenderer(os.path.join(base_path, svg_name))
    if not renderer.isValid():
        logger_setup.get_logger().debug(f'Could not load {svg_name} for the About dialog')
        return None

    dpr = widget.devicePixelRatioF()
    default_size = renderer.defaultSize()
    width = round(default_size.width() * LOGO_HEIGHT / default_size.height())
    pixmap = QPixmap(QSize(round(width * dpr), round(LOGO_HEIGHT * dpr)))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(dpr)
    return pixmap


class AboutDialog(QDialog):
    """About box shown from the Help menu. Identical in every window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('static_AboutDialog_Dialog_About')
        self.setWindowTitle('About GeoCORK')
        self.setModal(True)

        layout = QVBoxLayout(self)

        logo = QLabel()
        logo.setObjectName('static_AboutLogo_Label_Logo')
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = _logo_pixmap(self)
        if pixmap is not None:
            logo.setPixmap(pixmap)
        layout.addWidget(logo)

        title = QLabel(f'<p>Version {settings.value("default_geocork_version")}</p>')
        title.setObjectName('static_AboutTitle_Label_Title')
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        description = QLabel('A database application for managing geochemical and geochronological data. \n \n'
                             'Developed by Kathryn Metcalf and Jarrod M. Burges')
        description.setObjectName('static_AboutDescription_Label_Description')
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)

        links = QLabel(
            f'<a href="{GITHUB_URL}">GitHub repository</a><br>'
            f'<a href="{CITATION_DOI}">Cite GeoCORK (Zenodo DOI)</a><br>'
            f'<a href="{HELP_URL}">Help documentation</a>'
        )
        links.setObjectName('static_AboutLinks_Label_Links')
        links.setTextFormat(Qt.TextFormat.RichText)
        links.setOpenExternalLinks(True)
        links.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(links)

        close_button = QPushButton('Close')
        close_button.setObjectName('static_AboutClose_Button_Close')
        close_button.setDefault(True)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

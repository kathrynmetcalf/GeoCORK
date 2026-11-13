from PyQt6.QtCore import QEvent, QTimer, QObject, QUrl
from PyQt6.QtGui import QAction, QKeySequence, QDesktopServices
from PyQt6.QtWidgets import QMenuBar, QMenu, QMainWindow

import logger_setup
from ui.menus.AboutDialog import AboutDialog

GITHUB_URL = 'https://github.com/kathrynmetcalf/GeoCORK'
HELP_URL = GITHUB_URL + '/wiki'  # Placeholder: point this at the real help site
ISSUES_URL = GITHUB_URL + '/issues'
CITATION_DOI = 'https://doi.org/10.5281/zenodo.15833658'
LOGO_HEIGHT = 70  # logical pixels

def show_about(window=None):
    logger_setup.get_logger().info('Opening About dialog')
    AboutDialog(window).exec()

def open_help(topic: str | None = None):
    """Open the help site, optionally at a topic anchor."""
    url = f'{HELP_URL}#{topic}' if topic else HELP_URL
    logger_setup.get_logger().info(f'Opening help: {url}')
    QDesktopServices.openUrl(QUrl(url))

class StaticMenuGuard(QObject):
    """Keeps the static menus at the end of a menu bar when the window adds or removes actions."""

    def __init__(self, menu_bar: QMenuBar, menus: list[QMenu]):
        super().__init__(menu_bar)
        self.menu_bar = menu_bar
        self.menus = menus
        self._reorder_queued = False

    def eventFilter(self, watched, event):
        if watched is self.menu_bar and event.type() in (QEvent.Type.ActionAdded, QEvent.Type.ActionRemoved):
            if not self._reorder_queued:
                # Defer so the window finishes its batch of changes first, and so a reorder that
                # triggers its own events does not recurse.
                self._reorder_queued = True
                QTimer.singleShot(0, self.reorder)
        return False  # never consume the event

    def reorder(self):
        self._reorder_queued = False
        static_actions = [menu.menuAction() for menu in self.menus]
        bar_actions = self.menu_bar.actions()
        if bar_actions[-len(static_actions):] == static_actions:
            return  # already at the end; nothing to do, so no further events
        for action in static_actions:
            if action in bar_actions:
                self.menu_bar.removeAction(action)
            self.menu_bar.addAction(action)


def install_static_menus(window: QMainWindow) -> QMenu:
    """
    Add the static Help menu (Help Contents, Current Window Help, Report an Issue, About GeoCORK) to a window's
    menu bar. Calling it again on the same window returns the existing menu.
    """
    existing = getattr(window, 'static_help_menu', None)
    if existing is not None:
        return existing

    help_menu = QMenu('Help', window)
    help_menu.setObjectName('static_HelpMenu_Menu_Help')

    def make_action(text: str, object_name: str, slot, shortcut: QKeySequence | None = None) -> QAction:
        action = QAction(text, window)
        action.setObjectName(object_name)
        if shortcut is not None:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        help_menu.addAction(action)
        return action

    make_action('Help Contents', 'static_HelpContents_Action_Help',
                lambda _checked=False: open_help(),
                QKeySequence(QKeySequence.StandardKey.HelpContents))
    make_action('Current Window Help', 'static_CurrentWindowHelp_Action_Help',
                lambda _checked=False: open_help(getattr(window, 'help_topic', None)),
                QKeySequence('Shift+F1'))
    make_action('Report an Issue', 'static_ReportIssue_Action_Help',
                lambda _checked=False: QDesktopServices.openUrl(QUrl(ISSUES_URL)))
    help_menu.addSeparator()
    about_action = make_action('About GeoCORK', 'static_About_Action_Help',
                               lambda _checked=False: show_about(window))
    # macOS moves an AboutRole action into the application menu; other platforms keep it here.
    about_action.setMenuRole(QAction.MenuRole.AboutRole)

    menu_bar = window.menuBar()
    menu_bar.addMenu(help_menu)
    guard = StaticMenuGuard(menu_bar, [help_menu])
    menu_bar.installEventFilter(guard)

    # Keep Python references alive for the life of the window
    window.static_help_menu = help_menu
    window.static_menu_guard = guard
    logger_setup.get_logger().info(f'Installed static Help menu on {window.objectName() or type(window).__name__}')
    return help_menu
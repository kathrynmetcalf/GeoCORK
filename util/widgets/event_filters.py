from PyQt6.QtCore import QObject, QSettings, QEvent
from PyQt6.QtWidgets import QToolTip


class TooltipFilter(QObject):
    """
    Event filter to accept/reject ALL tooltips globally
    based on a user setting (stored in QSettings).
    """

    def __init__(self, settings: QSettings):
        super().__init__()
        self.settings = settings

    def eventFilter(self, obj, event):
        # Tooltip triggered by moving/hovering (QHelpEvent)
        # logger_setup.get_logger().debug(f'object: {obj.objectName()}, {obj}\nevent: {event}')
        if event.type() == QEvent.Type.ToolTip:
            allow = self.settings.value("display_tooltips", True, bool)
            if not allow:
                # Hide tooltip + stop event propagation
                QToolTip.hideText()
                return True
            return False  # allow tooltip normally

        if event.type() in (
            QEvent.Type.ToolTipChange,
            QEvent.Type.QueryWhatsThis
        ):
            allow = self.settings.value("display_tooltips", True, bool)
            if not allow:
                QToolTip.hideText()
                return True
            return False

        return super().eventFilter(obj, event)

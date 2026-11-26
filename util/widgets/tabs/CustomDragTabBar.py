from PyQt6 import QtCore, QtGui, QtWidgets


class CustomDragTabBar(QtWidgets.QTabBar):
    """
    A custom QTabBar that allows drag-and-drop reordering of tabs while keeping a set of permanent tabs static.

    Permanent tabs (i.e., 'Data Tables', 'Filters', 'Export') are expected to occupy the leading positions of the tab
    bar. They cannot be picked up and dragged (movable is switched off while a permanent tab is pressed) and
    cannot be displaced by other tabs (a dragged tab is clamped so it can never cross into the permanent area).
    All other tabs remain freely movable among themselves. correct_tab_order() is kept as a safety net and runs after
    every mouse release.
    """

    def __init__(self, permanent_tabs: list, parent=None):
        super().__init__(parent)
        self.permanent_tabs = permanent_tabs
        self._restore_movable = None
        """Movable state to restore on release after a permanent tab was pressed (None = nothing to restore)"""
        self._grab_offset = None
        """Distance from the dragged tab's leading edge to the mouse at press time (None = no movable drag active)"""

    def add_vertical_line(self):
        # self.setStyleSheet("""
        #     QTabBar::tab {padding: 10px;}
        #     QTabBar::tab:nth-child(3) {{border-right: 5px solid red;}}
        #     """)
        self.setStyleSheet("""
            QTabBar::tab {padding: 10px;}
            """)

    def update_permanent_tabs(self, names: list[str]) -> None:
        """
        Update the list of permanent tabs. This method is used to set or update the names of the tabs that should
        remain in a fixed position (permanent tabs) in the tab bar.
        :param names: list of names of the tabs that should be permanent, which will not be closable or movable
        :return:
        """
        self.permanent_tabs = names

    # ------------------------------------------------------------------ helpers
    def _is_horizontal(self) -> bool:
        return self.shape() in (QtWidgets.QTabBar.Shape.RoundedNorth, QtWidgets.QTabBar.Shape.RoundedSouth,
                                QtWidgets.QTabBar.Shape.TriangularNorth, QtWidgets.QTabBar.Shape.TriangularSouth)

    def _is_permanent(self, index: int) -> bool:
        return 0 <= index < self.count() and self.tabText(index) in self.permanent_tabs

    def _permanent_count(self) -> int:
        """Number of leading tabs that are permanent."""
        count = 0
        while count < self.count() and self._is_permanent(count):
            count += 1
        return count

    def _permanent_boundary(self):
        """Pixel coordinate (x for horizontal, y for vertical) where the permanent area ends, or None if empty."""
        count = self._permanent_count()
        if count == 0:
            return None
        rect = self.tabRect(count - 1)
        return rect.right() + 1 if self._is_horizontal() else rect.bottom() + 1

    # ------------------------------------------------------------------ events
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        If a permanent tab is pressed, disable moving for the duration of the press so it can still be selected but
        never dragged. If a normal tab is pressed, remember where it was grabbed so the drag can be clamped.
        """
        self._restore_movable = None
        self._grab_offset = None
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            index = self.tabAt(event.position().toPoint())
            if self._is_permanent(index):
                if self.isMovable():
                    self._restore_movable = True
                    self.setMovable(False)
            elif index >= 0 and self.isMovable():
                rect = self.tabRect(index)
                pos = event.position()
                self._grab_offset = pos.x() - rect.left() if self._is_horizontal() else pos.y() - rect.top()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        While a normal tab is being dragged, clamp the mouse position so the tab's leading edge can never pass the
        end of the permanent area. This stops other tabs from displacing the permanent tabs.
        """
        boundary = self._permanent_boundary()
        if (self._grab_offset is not None and boundary is not None
                and event.buttons() & QtCore.Qt.MouseButton.LeftButton):
            pos = event.position()
            minimum = boundary + self._grab_offset
            horizontal = self._is_horizontal()
            current = pos.x() if horizontal else pos.y()
            if current < minimum:
                delta = minimum - current
                shift = QtCore.QPointF(delta, 0) if horizontal else QtCore.QPointF(0, delta)
                event = QtGui.QMouseEvent(event.type(), pos + shift, event.globalPosition() + shift,
                                          event.button(), event.buttons(), event.modifiers())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Finish the press: restore the movable state if it was turned off for a permanent tab, then make sure the
        permanent tabs are still in their designated positions.
        """
        super().mouseReleaseEvent(event)
        if self._restore_movable is not None:
            self.setMovable(self._restore_movable)
            self._restore_movable = None
        self._grab_offset = None
        if self.permanent_tabs:
            self.correct_tab_order()

    def correct_tab_order(self) -> None:
        """
        Safety net: ensure each permanent tab sits at its designated index (its position in self.permanent_tabs).
        :return:
        """
        for target, name in enumerate(self.permanent_tabs):
            for index in range(self.count()):
                if self.tabText(index) == name:
                    if index != target and target < self.count():
                        self.moveTab(index, target)
                    break

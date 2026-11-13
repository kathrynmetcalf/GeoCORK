from PyQt6 import QtWidgets


class CustomDragTabBar(QtWidgets.QTabBar):
    """
    A custom QTabBar that allows for drag-and-drop reordering of tabs and maintains a list of permanent tabs.
    This class extends QTabBar to provide functionality for dragging tabs, reordering them, and ensuring that certain
    tabs remain in a fixed position (permanent tabs). It also provides methods to update the list of permanent tabs
    and to correct the order of tabs after a drag-and-drop operation. The mouseReleaseEvent is overridden to ensure
    that the permanent tabs are always in the correct order after a drag-and-drop operation.
    """
    def __init__(self, permanent_tabs: list, parent=None):
        super().__init__(parent)
        self.permanent_tabs = permanent_tabs

    def add_vertical_line(self):
        # self.setStyleSheet("""
        #     QTabBar::tab {padding: 10px;}
        #     QTabBar::tab:nth-child(3) {{border-right: 5px solid red;}}
        #     """)
        self.setStyleSheet("""
            QTabBar::tab {padding: 10px;}
            """)

    def update_permanent_tabs(self, names: list[str]):
        """
        Update the list of permanent tabs. This method is used to set or update the names of the tabs that should
        remain in a fixed position (permanent tabs) in the tab bar. It can be called to change the permanent tabs
        dynamically, for example, when the user changes the configuration of the application or when new tabs are added.
        :param names: list of names of the tabs that should be permanent, which will not be closable or movable
        :return:
        """
        self.permanent_tabs = names

    def mouseReleaseEvent(self, event):
        """
        Handle the mouse release event to ensure that permanent tabs are always in the correct order after a drag-and-drop operation.
        :param event:
        :return:
        """
        # Move the permanent tabs to the left side of the tab bar
        super().mouseReleaseEvent(event)
        if self.permanent_tabs:
            self.correct_tab_order()

    def correct_tab_order(self):
        """
        Correct the order of permanent tabs in the tab bar. This method checks the current order of tabs in the tab bar
        and ensures that the permanent tabs are in the correct positions. If a permanent tab is not in the correct position,
        it moves it to the correct position. This is useful after a drag-and-drop operation to ensure that the permanent
        tabs remain in their designated positions.
        :return:
        """
        for index in range(self.count()):
            if self.tabText(index) in self.permanent_tabs:
                for i in range(len(self.permanent_tabs)):
                    if self.tabText(index) == self.permanent_tabs[i]:
                        if index != i:
                            # Permanent tab is not in the correct position
                            self.moveTab(index, i)
                        else:  # Permanent tab is in the correct position
                            break
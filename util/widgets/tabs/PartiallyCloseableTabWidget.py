from PyQt6 import QtWidgets

# todo add vertical line between indexes 1-3 and others
class PartiallyCloseableTabWidget(QtWidgets.QTabWidget):
    """
    Custom QTabWidget that allows for some permanent tabs that cannot be closed or moved, but allows other tabs to be
    created, moved, and closed.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.permanent_tabs = []
        from util.widgets.tabs.CustomDragTabBar import CustomDragTabBar
        self.tabBar = CustomDragTabBar(self.permanent_tabs)
        self.setTabBar(self.tabBar)
        self.setTabsClosable(True)
        self.setMovable(True)

    def set_permanent_tabs(self, names: list[str]):
        """
        Set the list of permanent tabs that should not be closable or movable. This method updates the list of permanent
        tabs in the tab widget. Permanent tabs are those that should always remain in the tab bar and cannot be closed
        or moved by the user.
        :param names: list of names of the tabs that should be permanent, which will not be closable or movable
        :return:
        """
        self.permanent_tabs = names
        self.tabBar.update_permanent_tabs(self.permanent_tabs)
        self.update_close_buttons()

    def update_close_buttons(self):
        """
        Update the close buttons for the tabs in the tab widget. This method iterates through all tabs and sets the
        close buttons for each tab based on whether the tab is a permanent tab or not. Permanent tabs will not have
        close buttons, while other tabs will have close buttons that allow them to be closed by the user.
        :return:
        """
        for index in range(self.count()):
            if self.tabText(index) in self.permanent_tabs:
                self.tabBar.setTabButton(index, QtWidgets.QTabBar.ButtonPosition.LeftSide, None)
                self.tabBar.setTabButton(index, QtWidgets.QTabBar.ButtonPosition.RightSide, None)
        # self.setTabsClosable(True)
        # self.setMovable(True)

    def addTab(self, widget: QtWidgets.QWidget, name: str):
        """
        Add a new tab to the tab widget with the specified widget and name. If a tab with the same name already exists,
        it will set focus to that tab instead of creating a new one. This prevents duplicate tabs with the same name.
        :param widget: QWidget to be added as a tab
        :param name: Name of the tab to be added
        :return:
        """
        for index in range(self.count()):
            # Check all tabs to see if the name already exists, set focus to that tab if it does
            if self.tabText(index) == name:
                self.setCurrentIndex(index)
                return
        super().addTab(widget, name)
        # if self.count() >= 3:
        #     self.tabBar.add_vertical_line()
        self.update_close_buttons()
        self.setCurrentIndex(self.count() - 1)

    def insertTab(self, index: int, widget: QtWidgets.QWidget, name: str):
        """
        Insert a new tab at the specified index with the given widget and name. If a tab with the same name already
        exists, it will set focus to that tab instead of creating a new one. This prevents duplicate tabs with the same name.
        :param index: Position at which to insert the new tab
        :param widget: QWidget to be added as a tab
        :param name: Name of the tab to be added
        :return:
        """
        for i in range(self.count()):
            if self.tabText(i) == name:
                self.setCurrentIndex(i)
                return
        super().insertTab(index, widget, name)
        self.update_close_buttons()
        self.setCurrentIndex(index)

    def removeTab(self, index: int):
        """
        Remove the tab at the specified index. If the tab being removed is a permanent tab, it will not be removed.
        :param index: Position at which to remove the tab
        :return:
        """
        super().removeTab(index)
        self.update_close_buttons()
        if self.tabText(index) in self.permanent_tabs and self.tabText(index-1) in self.permanent_tabs:
            self.setCurrentIndex(index-1)
        elif self.tabText(index) in self.permanent_tabs:
            self.setCurrentIndex(index-1)
        elif self.tabText(index-1) in self.permanent_tabs:
            self.setCurrentIndex(index)
        else:
            self.setCurrentIndex(index)
        # if self.count() >= 3:
            # self.tabBar.add_vertical_line()
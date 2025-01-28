from PyQt6 import QtCore as QtC
from PyQt6 import QtWidgets as QtW


class FocusGroupBox(QtW.QGroupBox):
    focusLost = QtC.pyqtSignal()
    def __init__(self, parent=None):
        super(FocusGroupBox, self).__init__(parent)
        self.setFocusPolicy(QtC.Qt.FocusPolicy.NoFocus)
        self.installEventFilter(self)
        self.install_children_event_filter()
        self.focus_lost_timer = QtC.QTimer(self)
        self.focus_lost_timer.setSingleShot(True)
        self.focus_lost_timer.timeout.connect(self.check_focus_state)
        self.initial_values = []
        self.edited = False

    def connect_child_signals(self):
        self.initial_values = []
        for child in self.findChildren(QtW.QWidget):
            if isinstance(child, QtW.QLineEdit):
                try:
                    child.editingFinished.disconnect(self.set_edited)
                except TypeError:
                    pass
                self.initial_values.append([child, child.text()])
                child.editingFinished.connect(lambda ch=child: self.set_edited(ch))
            elif isinstance(child, QtW.QComboBox):
                try:
                    child.currentIndexChanged.disconnect(self.set_edited)
                except TypeError:
                    pass
                self.initial_values.append([child, child.currentIndex()])
                child.currentIndexChanged.connect(lambda ch=child: self.set_edited(ch))
            elif isinstance(child, QtW.QCheckBox):
                try:
                    child.stateChanged.disconnect(self.set_edited)
                except TypeError:
                    pass
                self.initial_values.append([child, child.isChecked()])
                child.stateChanged.connect(lambda ch=child: self.set_edited(ch))

    def disconnect_child_signals(self):
        for child in self.findChildren(QtW.QWidget):
            if isinstance(child, QtW.QLineEdit):
                try:
                    child.editingFinished.disconnect(self.set_edited)
                except TypeError:
                    pass
            elif isinstance(child, QtW.QComboBox):
                try:
                    child.currentIndexChanged.disconnect(self.set_edited)
                except TypeError:
                    pass
            elif isinstance(child, QtW.QCheckBox):
                try:
                    child.stateChanged.disconnect(self.set_edited)
                except TypeError:
                    pass

    def install_children_event_filter(self):
        for child in self.findChildren(QtW.QWidget):
            child.installEventFilter(self)

    def set_edited(self, child: QtW.QWidget):
        try: child.objectName()
        except AttributeError: return
        # print(f'{child.objectName()} called set_edited')
        initial_value = None
        for pair in self.initial_values:
            if pair[0] == child:
                initial_value = pair[1]
        if initial_value is None:
            return
        if isinstance(child, QtW.QLineEdit):
            if child.text() != initial_value:
                # print(f'{child.objectName()} was edited')
                self.edited = True
        elif isinstance(child, QtW.QComboBox):
            if child.currentIndex() != initial_value:
                self.edited = True
        elif isinstance(child, QtW.QCheckBox):
            if child.isChecked() != initial_value:
                self.edited = True

    def eventFilter(self, obj, event):
        if event.type() == QtC.QEvent.Type.FocusOut:
            self.focus_lost_timer.start(100)
        return super().eventFilter(obj, event)

    def check_focus_state(self, child=None):
        has_focus = self.any_child_has_focus()
        if not has_focus:
            # print(f'{self.objectName()} has lost focus')
            if self.edited:
                # print(f'{self.objectName()} was edited and needs to be updated')
                self.focusLost.emit()
                self.edited = False

    def any_child_has_focus(self):
        for child in self.findChildren(QtW.QWidget):
            if child.hasFocus():
                return True
        return False

class CustomDragTabBar(QtW.QTabBar):
    def __init__(self, permanent_tabs: list, parent=None):
        super().__init__(parent)
        self.permanent_tabs = permanent_tabs

    def update_permanent_tabs(self, names: list):
        self.permanent_tabs = names

    def mouseMoveEvent(self, event):
        index = self.tabAt(event.pos())
        if self.tabText(index) in self.permanent_tabs:
            return
        super().mouseMoveEvent(event)

class PartiallyCloseableTabWidget(QtW.QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.permanent_tabs = []
        self.tabBar = CustomDragTabBar(self.permanent_tabs)
        self.setTabBar(self.tabBar)
        self.setTabsClosable(True)
        self.setMovable(True)

    def set_permanent_tabs(self, names: list):
        # todo: try tracking by name instead of index
        self.permanent_tabs = names
        self.tabBar.update_permanent_tabs(self.permanent_tabs)
        self.update_close_buttons()

    def update_close_buttons(self):
        for index in range(self.count()):
            if self.tabText(index) in self.permanent_tabs:
                self.tabBar.setTabButton(index, QtW.QTabBar.ButtonPosition.LeftSide, None)
                self.tabBar.setTabButton(index, QtW.QTabBar.ButtonPosition.RightSide, None)
        # self.setTabsClosable(True)
        # self.setMovable(True)

    def addTab(self, widget, name):
        for index in range(self.count()):
            if self.tabText(index) == name:
                self.setCurrentIndex(index)
                return
        super().addTab(widget, name)
        self.update_close_buttons()
        self.setCurrentIndex(self.count() - 1)

    def insertTab(self, index, widget, name):
        for i in range(self.count()):
            if self.tabText(i) == name:
                self.setCurrentIndex(i)
                return
        super().insertTab(index, widget, name)
        self.update_close_buttons()
        self.setCurrentIndex(index)

    def removeTab(self, index):
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
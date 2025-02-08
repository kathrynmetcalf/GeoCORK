from PyQt6 import QtCore as QtC
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtGui as QtG
import Functions.Text_manipulations as TxM
from Functions.Settings_manager import settings
from Functions import SQLUtils as SQLUtils
from Functions import Tree_classes as TrC
import ui.EditTree as EditTree
import ui.AddTreeTags as AddTreeTags
import ui.New_reference as NewReference
import ui.EditTable as EditTable
import ui.AddTags as AddTags

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

    def add_vertical_line(self):
        # self.setStyleSheet("""
        #     QTabBar::tab {padding: 10px;}
        #     QTabBar::tab:nth-child(3) {{border-right: 5px solid red;}}
        #     """)
        self.setStyleSheet("""
            QTabBar::tab {padding: 10px;}
            """)

    def update_permanent_tabs(self, names: list):
        self.permanent_tabs = names

    def mouseReleaseEvent(self, event):
        # Move the permanent tabs to the left side of the tab bar
        super().mouseReleaseEvent(event)
        if self.permanent_tabs:
            self.correct_tab_order()

    def correct_tab_order(self):
        for index in range(self.count()):
            if self.tabText(index) in self.permanent_tabs:
                for i in range(len(self.permanent_tabs)):
                    if self.tabText(index) == self.permanent_tabs[i]:
                        if index != i:
                            # Permanent tab is not in the correct position
                            self.moveTab(index, i)
                        else:  # Permanent tab is in the correct position
                            break

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
            # Check all tabs to see if the name already exists, set focus to that tab if it does
            if self.tabText(index) == name:
                self.setCurrentIndex(index)
                return
        super().addTab(widget, name)
        # if self.count() >= 3:
        #     self.tabBar.add_vertical_line()
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
        # if self.count() >= 3:
            # self.tabBar.add_vertical_line()

class CompleterInputDialog(QtW.QDialog):
    def __init__(self, parent: QtW.QWidget, title: str, label: str, completer_list: list[str], editable: bool = False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setLayout(QtW.QVBoxLayout())
        self.layout().addWidget(QtW.QLabel(label))
        self.combo_box = QtW.QComboBox()
        self.combo_box.setEditable(editable)
        self.line_edit = self.combo_box.lineEdit()
        self.combo_box.addItems(completer_list)
        self.completer = QtW.QCompleter(completer_list)
        self.completer.setFilterMode(QtC.Qt.MatchFlag.MatchContains)
        self.completer.setCompletionMode(QtW.QCompleter.CompletionMode.PopupCompletion)
        self.line_edit.setCompleter(self.completer)
        self.layout().addWidget(self.combo_box)
        self.button_box = QtW.QDialogButtonBox(QtW.QDialogButtonBox.StandardButton.Ok | QtW.QDialogButtonBox.StandardButton.Cancel)
        self.layout().addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def get_input(self):
        return self.line_edit.text()

class ColumnListProxyModel(QtC.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def data(self, index: QtC.QModelIndex, role: int = ...):
        if role == QtC.Qt.ItemDataRole.DisplayRole:
            header = super().data(index, role)
            if 'ID' in header or 'Abbreviation' in header:
                if 'Elev' in header:
                    header = 'Elevation Unit'
                elif 'AgeUnit' in header:
                    header = 'Age Unit'
                elif 'RatioErrorFormat' in header:
                    header = 'Ratio Error Format'
                elif 'AgeErrorFormat' in header:
                    header = 'Age Error Format'
                elif 'Height' in header:
                    header = 'Height/Depth Unit'
                elif 'GPSFormat' in header:
                    header = 'GPS Format'
                elif 'SpotSize' in header:
                    header = 'Spot Size Unit'
                elif 'ConcordanceFormat' in header:
                    header = 'Concordance Format'
            if 'GPSLocationConverted' in header:
                header = 'GPS Location'
            elif 'SampleElevationCalculated' in header:
                header = f'Sample Elevation ({settings.value('elevation_unit_abbreviation')})'
            elif 'SampleElevation' in header:
                header = f'Sample Elevation'
            elif 'ColumnElevationCalculated' in header:
                header = f'Column Elevation ({settings.value('elevation_unit_abbreviation')})'
            elif 'ColumnElevation' in header:
                header = f'Column Elevation'
            elif 'TotalHeightDepthCalculated' in header:
                header = f'Total Height/Depth ({settings.value('heightdepth_unit_abbreviation')})'
            elif 'TotalHeightDepth' in header:
                header = f'Total Height/Depth'
            elif 'HeightDepthCalculated' in header:
                header = f'Height/Depth ({settings.value('heightdepth_unit_abbreviation')})'
            elif 'HeightDepth' in header:
                header = f'Height/Depth'
            elif 'AgeCalculated' in header:
                header = f'Age ({settings.value('age_unit_abbreviation')})'
            elif 'SpotSizeCalculated' in header:
                header = f'Spot Size ({settings.value('spotsize_unit_abbreviation')})'
            if 'Name' in header and (header != 'SampleName' and header != 'AliquotName' and header != 'SpotName'):
                header = header.replace('Name', '')
                if header.endswith('y'):
                    header = header[:-1] + 'ies'
                elif header.endswith('is'):
                    header = header[:-2] + 'es'
                else:
                    header += 's'
            if 'Display' in header:
                header = header.replace('Display', '')
            if 'Calculated' in header:
                header = header.replace('Calculated', '')
            if 'ppm' in header:
                header = header.replace('ppm', '(ppm)')
            if 'cps' in header:
                header = header.replace('cps', '(cps)')
            if '"' in header:
                header = header.replace('"', '')
            header = TxM.add_spaces_camel(header)
            if 'U Pb' in header:
                header = header.replace('U Pb', 'U-Pb')
            return header
        return super().data(index, role)

class ColumnItemModel(QtG.QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.permanent_header = ''

    def set_permanent_header(self, header: str):
        # Set the header that should always be checked, the name or display column
        self.permanent_header = header

    def data(self, index, role: int = ...):
        if role == QtC.Qt.ItemDataRole.CheckStateRole:
            if self.data(index, QtC.Qt.ItemDataRole.DisplayRole) == self.permanent_header:
                return QtC.Qt.CheckState.Checked
            else:
                return super().data(index, role)
        return super().data(index, role)

    def setData(self, index, value, role: int = ...):
        if role == QtC.Qt.ItemDataRole.CheckStateRole:
            if self.data(index, QtC.Qt.ItemDataRole.DisplayRole) == self.permanent_header and value == QtC.Qt.CheckState.Unchecked:
                return False
        return super().setData(index, value, role)

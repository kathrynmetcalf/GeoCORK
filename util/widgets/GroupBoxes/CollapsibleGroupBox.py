from PyQt6 import QtCore, QtWidgets


class CollapsibleGroupBox(QtWidgets.QWidget):
    """
    Group box that can be expanded or collapsed with a click on the button
    """

    def __init__(self, title='', parent=None):
        super().__init__(parent)
        self.isExpanded = True
        self.expand_button = QtWidgets.QToolButton(self)
        self.expand_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.expand_button.setArrowType(QtCore.Qt.ArrowType.DownArrow)
        self.expand_button.setCheckable(True)
        self.expand_button.setChecked(True)
        # self.expand_button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)
        self.header_label = QtWidgets.QLabel(title)
        self.header_label.setMaximumHeight(self.header_label.sizeHint().height())
        # self.header_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)
        # self.header_label.setStyleSheet("font-weight: bold;")
        self.expand_button.setMaximumSize(self.header_label.sizeHint().height(), self.header_label.sizeHint().height())

        self.header_layout = QtWidgets.QHBoxLayout()
        self.header_layout.addWidget(self.expand_button)
        self.header_layout.addWidget(self.header_label)
        self.header_layout.setContentsMargins(0, 0, 0, 0)

        self.header_widget = QtWidgets.QWidget(self)
        self.header_widget.setLayout(self.header_layout)
        # self.header_widget.setMaximumHeight(self.header_layout.contentsMargins().top())
        self.header_widget.mouseReleaseEvent = lambda e: self.expand_button.click()

        self.content_area = QtWidgets.QWidget(self)
        self.content_area.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Minimum)

        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addWidget(self.header_widget)
        self.main_layout.addWidget(self.content_area)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Minimum)

        self.expand_button.toggled.connect(self.onVisibilityChanged)

    def onVisibilityChanged(self, checked):
        self.isExpanded = checked
        if self.isExpanded:
            self.collapse_groupBox()
        else:
            self.expand_groupBox()

    def collapse_groupBox(self):
        if self.isExpanded:
            self.isExpanded = False
        self.content_area.setVisible(False)
        self.content_area.setMaximumHeight(0)
        # self.setMaximumHeight(self.header_widget.size().height())
        self.expand_button.setArrowType(QtCore.Qt.ArrowType.RightArrow)

    def expand_groupBox(self):
        if not self.isExpanded:
            self.isExpanded = True
        self.content_area.setVisible(True)
        self.content_area.setMaximumHeight(16777215)  # Reset to default maximum height
        self.setMaximumHeight(16777215)  # Reset to default maximum height
        self.expand_button.setArrowType(QtCore.Qt.ArrowType.DownArrow)

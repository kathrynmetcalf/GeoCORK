from PyQt6 import QtWidgets, QtCore


class CompleterInputDialog(QtWidgets.QDialog):
    """
    A dialog that allows the user to input text with a completer. This dialog contains a combo box with a completer
    that provides suggestions based on a list of strings. The user can type in the combo box, and the completer will
    suggest completions based on the input.
    """
    def __init__(self, parent: QtWidgets.QWidget, title: str, label: str, completer_list: list[str], editable: bool = False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(QtWidgets.QLabel(label))
        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.setEditable(editable)
        self.line_edit = self.combo_box.lineEdit()
        self.combo_box.addItems(completer_list)
        list_model = QtCore.QStringListModel(sorted(completer_list, key=str.casefold))
        list_proxy_model = QtCore.QSortFilterProxyModel()
        list_proxy_model.setSourceModel(list_model)
        list_proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        list_proxy_model.setSortCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.completer = QtWidgets.QCompleter()
        self.completer.setModel(list_proxy_model)
        self.completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setModelSorting(QtWidgets.QCompleter.ModelSorting.CaseInsensitivelySortedModel)
        self.completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
        self.line_edit.setCompleter(self.completer)
        self.layout().addWidget(self.combo_box)
        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.layout().addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def get_input(self):
        return self.line_edit.text()
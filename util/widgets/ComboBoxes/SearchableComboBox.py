from PyQt6 import QtWidgets, QtCore


class SearchableComboBox(QtWidgets.QComboBox):
    """
    A QComboBox subclass that allows for searching items in the dropdown list. This class extends QComboBox to provide
    functionality for searching items in the dropdown list by typing in the line edit. It uses a completer to filter
    the items containing the text entered by the user. The selection_changed signal is emitted whenever the
    selection in the combo box changes, allowing for custom handling of selection changes.
    """
    selection_changed = QtCore.pyqtSignal(QtWidgets.QComboBox)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.list_view = QtWidgets.QListView()
        self.setView(self.list_view)
        self.previous_index = -1
        # self.all_items = []
        self.completer().setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        self.completer().setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
        self.completer().model().sort(0)
        self.lineEdit().setCompleter(self.completer())
        self.lineEdit().editingFinished.connect(self.validate_input)

    def addItem(self, text: str):
        """
        Add a single item to the combo box. This method overrides the default addItem method to set the default text
        to blank after adding the item. This ensures that the combo box does not display 'None' as a default value.
        :param text: text to be added as an item to the combo box
        :return:
        """
        super().addItem(text)
        # Set the default text to blank
        self.lineEdit().setText(None)

    def addItems(self, texts: list[str]):
        """
        Add multiple items to the combo box. This method overrides the default addItems method to set the default text
        to blank after adding the items. This ensures that the combo box does not display 'None' as a default value.
        :param texts: list of text strings to be added as items to the combo box
        :return:
        """
        combo_model = self.view().model()
        from util.widgets.models.item_models import DisableItemModel
        if isinstance(combo_model, DisableItemModel):
            for text_item in texts:
                self.addItem(text_item)
        else:
            super().addItems(texts)
        # Set the default text to blank
        self.lineEdit().setText(None)

    def validate_input(self):
        """
        Validate the input in the line edit. This method checks if the text entered in the line edit matches any of
        the items in the combo box. If the text does not match any item, it sets the text to None and resets the current
        index to -1. If the text matches an item, it sets the current index to that item. This ensures that the combo box
        does not display 'None' as a default value and only shows valid selections.
        :return:
        """
        text = self.lineEdit().text()
        if self.findText(text) == -1 or text == 'None':
            self.lineEdit().setText(None)
            self.setCurrentIndex(-1)
        elif text not in [self.itemText(i) for i in range(self.count())]:
            # The text does not match anything in the combo box
            # Reset the text to blank
            self.lineEdit().setText(None)
            self.setCurrentIndex(-1)

from PyQt6 import QtWidgets, QtCore


class ReorderListView(QtWidgets.QListView):
    """
    A QListView subclass that allows for reordering items via drag-and-drop. This class extends QListView to provide
    functionality for dragging and dropping items to reorder them within the list. It sets the default drop action to
    MoveAction and enables drag-and-drop mode. The startDrag method is overridden to prevent dragging the permanent header,
    which is always at the top of the list. The dropEvent method is overridden to handle dropping items between other items
    while preventing drops before the permanent header or on an item.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.setDragDropMode(QtWidgets.QListView.DragDropMode.DragDrop)
        self.setDragEnabled(True)

    def startDrag(self, action: QtCore.Qt.DropAction):
        """
        Start the drag operation for the selected item. This method is called when the user starts dragging an item
        from the list view. It checks if the current index is valid and if the item is not the permanent header.
        :param action: DropAction to be used for the drag operation because there is no DragAction
        :return:
        """
        index = self.currentIndex()
        # The permanent header will always be at the top, so this works even with multiple selection.
        if index.isValid():
            # Do not move the permanent header
            if index.data().replace(' ','') == self.model().sourceModel().permanent_header:
                return
            super().startDrag(action)

    def dropEvent(self, event):
        """
        Handle the drop event for the list view. This method is called when the user drops an item onto the list view.
        It checks if the drop is valid, ensuring that the item is not being dropped before the permanent header or on an item.
        :param event:
        :return:
        """
        index = self.indexAt(event.pos())
        if index.isValid():
            if index.row() == 0 and self.model().sourceModel().permanent_header != '':
                # Trying to drop before the permanent header
                event.ignore()
            elif self.dropIndicatorPosition() == self.dropIndicatorPosition().OnItem:
                # Not valid or trying to drop on an item
                event.ignore()
            else:
                # Dropping between items
                super().dropEvent(event)
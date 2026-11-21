from PyQt6 import QtWidgets, QtCore

from util import geocork_logger
from util.widgets.delegates import ActiveSelectionDelegate
from util.widgets.views.tree_views import TrackExpandedTreeView


class FrozenTableView(QtWidgets.QTableView):
    """
    Custom QTableView subclass that allows freezing the first column of the table. This class extends QTableView to
    provide functionality for freezing the first column of the table, allowing it to remain visible while scrolling
    horizontally. The frozen column is displayed in a separate QTableView that is stacked over the main table view.
    The frozen table view is updated whenever the model is set or when the section sizes change. It also synchronizes
    the vertical scroll bar with the main table view to ensure that both views scroll together. The frozen column
    is updated whenever the section sizes change, and the geometry of the frozen table view is adjusted to match the
    main table view's geometry.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frozen_table_view = QtWidgets.QTableView(self)
        self.frozen_table_view.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.frozen_table_view.setEditTriggers(self.editTriggers())
        self.frozen_table_view.verticalHeader().hide()
        self.frozen_table_view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.frozen_column = 1
        # Guard to prevent handling the same header click twice
        self._sorting_in_progress = False

        self.viewport().stackUnder(self.frozen_table_view)

        self.frozen_table_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.frozen_table_view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setWordWrap(True)
        self.setTextElideMode(QtCore.Qt.TextElideMode.ElideNone)  # Prevent text truncation
        self.setItemDelegate(ActiveSelectionDelegate(self))

        self.geometry_timer = QtCore.QTimer()
        self.geometry_timer.setSingleShot(True)
        self.geometry_timer.timeout.connect(self.update_frozen_table_geometry)

        self.frozen_table_view.show()
        self.geometry_timer_start()

        self.verticalHeader().sectionResized.connect(self.update_section_height)
        self.horizontalHeader().sectionResized.connect(self.update_section_width)
        self.verticalScrollBar().valueChanged.connect(self.frozen_table_view.verticalScrollBar().setValue)
        self.frozen_table_view.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)

    def setModel(self, model):
        """
        Set the model for the frozen table view and the main table view. This method overrides the QTableView setModel
        method to ensure that both the main table view and the frozen table view are set to the same model. It also
        hides all columns except the first one in the frozen table view. The frozen table view is updated to match the
        geometry of the main table view, and the section widths are set to match the main table view's column widths.
        :param model:
        :return:
        """
        super().setModel(model)
        self.frozen_table_view.setModel(model)
        self.frozen_table_view.setItemDelegate(ActiveSelectionDelegate(self.frozen_table_view))
        self.frozen_table_view.setSelectionModel(self.selectionModel())
        self.frozen_table_view.setSelectionBehavior(self.selectionBehavior())
        self.frozen_table_view.setSelectionMode(self.selectionMode())
        for col in range(model.columnCount()):
            if col != self.frozen_column:
                self.frozen_table_view.hideColumn(col)
            else:
                self.frozen_table_view.setColumnWidth(col, self.columnWidth(col))
                delegate = self.itemDelegateForColumn(col)
                if delegate is not None:
                    self.frozen_table_view.setItemDelegateForColumn(col, delegate)
        self.geometry_timer_start()
        try:
            self.model().layoutChanged.connect(lambda *args, **kwargs: self.sync_row_heights())
        except Exception:
            pass
        try:
            self.model().modelReset.connect(lambda *args, **kwargs: self.sync_row_heights())
        except Exception:
            pass
        try:
            self.model().rowsInserted.connect(lambda *args, **kwargs: self.sync_row_heights())
            self.model().rowsRemoved.connect(lambda *args, **kwargs: self.sync_row_heights())
        except Exception:
            pass
        try:
            self.model().dataChanged.connect(lambda *args, **kwargs: self.sync_row_heights())
        except Exception:
            pass
        try:
            # Ensure we don't connect the same slot multiple times
            try:
                self.frozen_table_view.horizontalHeader().sectionClicked.disconnect(self._on_frozen_header_clicked)
            except Exception:
                pass
            self.frozen_table_view.horizontalHeader().sectionClicked.connect(self._on_frozen_header_clicked)
        except Exception:
            pass
        try:
            self.horizontalHeader().sortIndicatorChanged.connect(self._clear_frozen_sort_indicator)
        except Exception:
            pass

    def set_frozen_column(self, column):
        """
        Update which column is frozen. Default value is 1. The column index includes hidden columns.
        :param column: Index of the column to freeze on the left.
        """
        if column != self.frozen_column:
            self.frozen_column = column
            for col in range(self.model().columnCount()):
                if col != self.frozen_column:
                    self.frozen_table_view.hideColumn(col)
                else:
                    self.frozen_table_view.showColumn(col)
                    self.frozen_table_view.setColumnWidth(col, self.columnWidth(col))

            self.geometry_timer_start()

    def _on_frozen_header_clicked(self, logicalIndex):
        if not self.isSortingEnabled():
            return
        if getattr(self, '_sorting_in_progress', False):
            return
        main_header = self.horizontalHeader()
        frozen_header = self.frozen_table_view.horizontalHeader()

        current_section = main_header.sortIndicatorSection()
        current_order = main_header.sortIndicatorOrder()
        if current_section == logicalIndex:
            sort_order = QtCore.Qt.SortOrder.DescendingOrder if current_order == QtCore.Qt.SortOrder.AscendingOrder else QtCore.Qt.SortOrder.AscendingOrder
        else:
            sort_order = QtCore.Qt.SortOrder.AscendingOrder
        self._sorting_in_progress = True
        try:
            self.sortByColumn(logicalIndex, sort_order)
        finally:
            self._sorting_in_progress = False

        try:
            main_header.setSortIndicator(logicalIndex, sort_order)
        except Exception:
            pass
        try:
            frozen_header.setSortIndicator(logicalIndex, sort_order)
        except Exception:
            pass

    def _clear_frozen_sort_indicator(self, section):
        if section == self.frozen_column:
            return
        else:
            self.frozen_table_view.horizontalHeader().setSortIndicator(-1, QtCore.Qt.SortOrder.AscendingOrder)

    def update_section_height(self, logicalIndex):
        """
        Update the height of the frozen table view's row based on the logical index. This method is called whenever
        the height of a section in the main table view changes. It sets the row height of the frozen table view to
        match the row height of the main table view for the specified logical index. This ensures that the frozen column
        remains aligned with the main table view's rows even when the row heights change.
        :param logicalIndex:
        :return:
        """
        self.frozen_table_view.setRowHeight(logicalIndex, self.rowHeight(logicalIndex))

    def update_section_width(self, logicalIndex):
        """
        Update the width of the frozen table view's column based on the logical index. This method is called whenever
        the width of a section in the main table view changes. It sets the column width of the frozen table view to
        match the column width of the main table view for the specified logical index. This ensures that the frozen column
        remains aligned with the main table view's columns even when the column widths change.
        :param logicalIndex:
        :return:
        """
        self.frozen_table_view.setColumnWidth(logicalIndex, self.columnWidth(logicalIndex))
        self.geometry_timer_start()

    def sync_row_heights(self, start=0, end=None):
        model = self.model()
        if model is None:
            return
        row_count = model.rowCount()
        if end is None or end >= row_count:
            end = row_count + 1
        if end < start:
            return

        # Prevent repeated repaints
        self.frozen_table_view.setUpdatesEnabled(False)
        for row in range(start, end + 1):
            height = self.rowHeight(row)
            if self.frozen_table_view.rowHeight(row) != height:
                self.frozen_table_view.setRowHeight(row, height)

        self.frozen_table_view.setUpdatesEnabled(True)

    def resizeEvent(self, event):
        """
        Handle the resize event for the frozen table view. This method is called whenever the main table view is resized.
        It updates the geometry of the frozen table view to match the new size of the main table view. The frozen table
        view's geometry is adjusted to ensure that it occupies the same space as the first column of the main table view.
        :param event:
        :return:
        """
        super().resizeEvent(event)
        self.geometry_timer_start()

    def moveCursor(self, cursorAction, modifiers):
        """
        Move the cursor in the frozen table view based on the cursor action and modifiers. This method overrides the
        QTableView moveCursor method to handle the case where the cursor is moved left and the current column is greater
        than the frozen column. If that happens, it checks if the visual rectangle of the current index is outside the
        width of the frozen column. If it is, it adjusts the horizontal scroll bar value to ensure that the frozen
        column remains visible. This allows the user to navigate through the table while keeping the frozen column in
        view. The method returns the current index after moving the cursor.
        :param cursorAction:
        :param modifiers:
        :return: current index after moving the cursor
        """
        current = super().moveCursor(cursorAction, modifiers)
        if (
                cursorAction == QtWidgets.QAbstractItemView.CursorAction.MoveLeft and current.column() > self.frozen_column and
                self.visualRect(current).topLeft().x() < self.frozen_table_view.columnWidth(self.frozen_column)):
            new_value = (self.horizontalScrollBar().value() + self.visualRect(current).topLeft().x() -
                         self.frozen_table_view.columnWidth(self.frozen_column))
            self.horizontalScrollBar().setValue(new_value)
        return current

    def scrollTo(self, index, hint=...):
        """
        Scroll to the specified index in the frozen table view. This method overrides the QTableView scrollTo method
        to handle the case where the index is in a column greater than the frozen column. If that happens, it
        calls the superclass scrollTo method to scroll to the specified index. This ensures that the frozen column remains
        visible while scrolling through the table. The hint parameter is passed to the superclass method to specify
        how the scrolling should be performed (e.g., whether to scroll to the top, center, etc.). If the index is in
        the first two columns, it does not scroll to the index, as the frozen column is always visible.
        :param index:
        :param hint:
        :return:
        """
        if index.column() > self.frozen_column:
            super().scrollTo(index, hint)
        else:
            frozen_index = self.model().index(index.row(), self.frozen_column)
            super().scrollTo(frozen_index, hint)

    def geometry_timer_start(self):
        self.geometry_timer.start(151)

    def update_frozen_table_geometry(self):
        """
        Update the geometry of the frozen table view to match the main table view's geometry. This method is called
        whenever the model is set or when the section sizes change. It adjusts the geometry of the frozen table view
        to ensure that it occupies the same space as the first column of the main table view. The frozen table view's
        geometry is set based on the vertical header width, frame width, column width of the first column, and the
        viewport height of the main table view. This ensures that the frozen column remains aligned with the main table
        view's rows and columns, even when the table is resized or the section sizes change. The geometry is set to
        ensure that the frozen column is positioned correctly relative to the main table view's viewport and headers.
        :return:
        """
        view_port_geometry = self.viewport().geometry()
        header_height = self.horizontalHeader().height()
        header_y_pos = self.horizontalHeader().pos().y()
        x_pos = view_port_geometry.x() - self.frameWidth()
        y_pos = header_y_pos - self.frameWidth()
        width = self.columnWidth(self.frozen_column) + self.frameWidth()
        height = header_height + view_port_geometry.height() + (2 * self.frameWidth())
        self.frozen_table_view.setGeometry(x_pos, y_pos, width, height)
        self.frozen_table_view.setColumnWidth(self.frozen_column, self.columnWidth(self.frozen_column))
        self.frozen_table_view.horizontalHeader().setFixedHeight(header_height)
        self.sync_row_heights()
        geocork_logger.get_logger().debug(
            f'Frozen column geometry: (x: {x_pos}, y: {y_pos}, width: {width}, height: {height})')
        geocork_logger.get_logger().debug(
            f'Table geometry: (x: {self.x()}, y: {self.y()}, width: {self.width()}, height: {self.height()})')
        geocork_logger.get_logger().debug(
            f'Viewport geometry: (x: {self.viewport().x()}, y: {self.viewport().y()}, width: {self.viewport().width()}, height: {self.viewport().height()})')


class FrozenTreeView(TrackExpandedTreeView):
    """
    Custom TrackExpandedTreeView subclass that allows freezing the first column of the tree. This class extends QTreeView to
    provide functionality for freezing the first column of the tree, allowing it to remain visible while scrolling
    horizontally. The frozen column is displayed in a separate TrackExpandedTreeView that is stacked over the main tree view.
    The frozen tree view is updated whenever the model is set or when the section sizes change. It also synchronizes
    the vertical scroll bar with the main tree view to ensure that both views scroll together. The frozen column
    is updated whenever the section sizes change, and the geometry of the frozen tree view is adjusted to match the
    main tree view's geometry.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frozen_tree_view = TrackExpandedTreeView(self)
        self.frozen_tree_view.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.frozen_tree_view.setEditTriggers(self.editTriggers())
        self.frozen_tree_view.verticalHeader().hide()
        self.frozen_tree_view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.frozen_column = 0

        self.viewport().stackUnder(self.frozen_tree_view)

        self.frozen_tree_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.frozen_tree_view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setWordWrap(True)
        self.setTextElideMode(QtCore.Qt.TextElideMode.ElideNone)  # Prevent text truncation
        self.setItemDelegate(ActiveSelectionDelegate(self))

        self.geometry_timer = QtCore.QTimer()
        self.geometry_timer.setSingleShot(True)
        self.geometry_timer.timeout.connect(self.update_frozen_tree_geometry)

        self.frozen_tree_view.show()
        self.geometry_timer_start()

        self.verticalHeader().sectionResized.connect(self.update_section_height)
        self.horizontalHeader().sectionResized.connect(self.update_section_width)
        self.verticalScrollBar().valueChanged.connect(self.frozen_tree_view.verticalScrollBar().setValue)
        self.frozen_tree_view.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)

    def setModel(self, model):
        """
        Set the model for the frozen table view and the main table view. This method overrides the QTableView setModel
        method to ensure that both the main table view and the frozen table view are set to the same model. It also
        hides all columns except the first one in the frozen table view. The frozen table view is updated to match the
        geometry of the main table view, and the section widths are set to match the main table view's column widths.
        :param model:
        :return:
        """
        super().setModel(model)
        self.frozen_tree_view.setModel(model)
        self.frozen_tree_view.setItemDelegate(ActiveSelectionDelegate(self.frozen_tree_view))
        self.frozen_tree_view.setSelectionModel(self.selectionModel())
        self.frozen_tree_view.setSelectionBehavior(self.selectionBehavior())
        self.frozen_tree_view.setSelectionMode(self.selectionMode())
        for col in range(model.columnCount()):
            if col != self.frozen_column:
                self.frozen_tree_view.hideColumn(col)
            else:
                self.frozen_tree_view.setColumnWidth(col, self.columnWidth(col))
                delegate = self.itemDelegateForColumn(col)
                if delegate is not None:
                    self.frozen_tree_view.setItemDelegateForColumn(col, delegate)
        self.geometry_timer_start()
        try:
            self.model().layoutChanged.connect(lambda *args, **kwargs: self.sync_row_heights())
        except Exception:
            pass
        try:
            self.model().modelReset.connect(lambda *args, **kwargs: self.sync_row_heights())
        except Exception:
            pass
        try:
            self.model().rowsInserted.connect(lambda *args, **kwargs: self.sync_row_heights())
            self.model().rowsRemoved.connect(lambda *args, **kwargs: self.sync_row_heights())
        except Exception:
            pass
        try:
            self.model().dataChanged.connect(lambda *args, **kwargs: self.sync_row_heights())
        except Exception:
            pass

    def update_section_height(self, logicalIndex):
        """
        Update the height of the frozen tree view's row based on the logical index. This method is called whenever
        the height of a section in the main tree view changes. It sets the row height of the frozen tree view to
        match the row height of the main tree view for the specified logical index. This ensures that the frozen column
        remains aligned with the main tree view's rows even when the row heights change.
        :param logicalIndex:
        :return:
        """
        self.frozen_tree_view.setRowHeight(logicalIndex, self.rowHeight(logicalIndex))

    def update_section_width(self, logicalIndex):
        """
        Update the width of the frozen tree view's column based on the logical index. This method is called whenever
        the width of a section in the main tree view changes. It sets the column width of the frozen tree view to
        match the column width of the main tree view for the specified logical index. This ensures that the frozen column
        remains aligned with the main tree view's columns even when the column widths change.
        :param logicalIndex:
        :return:
        """
        self.frozen_tree_view.setColumnWidth(logicalIndex, self.columnWidth(logicalIndex))
        self.geometry_timer_start()

    def sync_row_heights(self, start=0, end=None):
        model = self.model()
        if model is None:
            return
        row_count = model.rowCount()
        if end is None or end >= row_count:
            end = row_count + 1
        if end < start:
            return

        # Prevent repeated repaints
        self.frozen_tree_view.setUpdatesEnabled(False)
        for row in range(start, end + 1):
            frozen_index = self.model().index(row, )
            height = self.rowHeight(row)
            if self.frozen_tree_view.rowHeight(row) != height:
                self.frozen_tree_view.setRowHeight(row, height)

        self.frozen_tree_view.setUpdatesEnabled(True)

    def resizeEvent(self, event):
        """
        Handle the resize event for the frozen table view. This method is called whenever the main table view is resized.
        It updates the geometry of the frozen table view to match the new size of the main table view. The frozen table
        view's geometry is adjusted to ensure that it occupies the same space as the first column of the main table view.
        :param event:
        :return:
        """
        super().resizeEvent(event)
        self.geometry_timer_start()

    def moveCursor(self, cursorAction, modifiers):
        """
        Move the cursor in the frozen tree view based on the cursor action and modifiers. This method overrides the
        QTableView moveCursor method to handle the case where the cursor is moved left and the current column is greater
        than the frozen column. If that happens, it checks if the visual rectangle of the current index is outside the
        width of the frozen column. If it is, it adjusts the horizontal scroll bar value to ensure that the frozen
        column remains visible. This allows the user to navigate through the tree while keeping the frozen column in
        view. The method returns the current index after moving the cursor.
        :param cursorAction:
        :param modifiers:
        :return: current index after moving the cursor
        """
        current = super().moveCursor(cursorAction, modifiers)
        if (
                cursorAction == QtWidgets.QAbstractItemView.CursorAction.MoveLeft and current.column() > self.frozen_column and
                self.visualRect(current).topLeft().x() < self.frozen_tree_view.columnWidth(self.frozen_column)):
            new_value = (self.horizontalScrollBar().value() + self.visualRect(current).topLeft().x() -
                         self.frozen_tree_view.columnWidth(self.frozen_column))
            self.horizontalScrollBar().setValue(new_value)
        return current

    def scrollTo(self, index, hint=...):
        """
        Scroll to the specified index in the frozen table view. This method overrides the QTableView scrollTo method
        to handle the case where the index is in a column greater than the frozen column. If that happens, it
        calls the superclass scrollTo method to scroll to the specified index. This ensures that the frozen column remains
        visible while scrolling through the table. The hint parameter is passed to the superclass method to specify
        how the scrolling should be performed (e.g., whether to scroll to the top, center, etc.). If the index is in
        the first two columns, it does not scroll to the index, as the frozen column is always visible.
        :param index:
        :param hint:
        :return:
        """
        if index.column() > self.frozen_column:
            super().scrollTo(index, hint)
        else:
            frozen_index = self.model().index(index.row(), self.frozen_column)
            super().scrollTo(frozen_index, hint)

    def geometry_timer_start(self):
        self.geometry_timer.start(151)

    def update_frozen_tree_geometry(self):
        """
        Update the geometry of the frozen tree view to match the main tree view's geometry. This method is called
        whenever the model is set or when the section sizes change. It adjusts the geometry of the frozen tree view
        to ensure that it occupies the same space as the first column of the main tree view. The frozen tree view's
        geometry is set based on the vertical header width, frame width, column width of the first column, and the
        viewport height of the main tree view. This ensures that the frozen column remains aligned with the main tree
        view's rows and columns, even when the tree is resized or the section sizes change. The geometry is set to
        ensure that the frozen column is positioned correctly relative to the main tree view's viewport and headers.
        :return:
        """
        view_port_geometry = self.viewport().geometry()
        header_height = self.header().height()
        header_y_pos = self.header().pos().y()
        x_pos = view_port_geometry.x() - self.frameWidth()
        y_pos = header_y_pos - self.frameWidth()
        width = self.columnWidth(self.frozen_column) + self.frameWidth()
        height = header_height + view_port_geometry.height() + (2 * self.frameWidth())
        self.frozen_tree_view.setGeometry(x_pos, y_pos, width, height)
        self.frozen_tree_view.setColumnWidth(self.frozen_column, self.columnWidth(self.frozen_column))
        self.frozen_tree_view.header().setFixedHeight(header_height)
        self.sync_row_heights()
        geocork_logger.get_logger().debug(
            f'Frozen column geometry: (x: {x_pos}, y: {y_pos}, width: {width}, height: {height})')
        geocork_logger.get_logger().debug(
            f'Table geometry: (x: {self.x()}, y: {self.y()}, width: {self.width()}, height: {self.height()})')
        geocork_logger.get_logger().debug(
            f'Viewport geometry: (x: {self.viewport().x()}, y: {self.viewport().y()}, width: {self.viewport().width()}, height: {self.viewport().height()})')

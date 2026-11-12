from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt, QSize, QEventLoop
from PyQt6.QtGui import QAction
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QLayout, QSizePolicy, QListWidgetItem, QPushButton, QMessageBox)

import logger_setup
from ui.DataViewerWidget import DataViewerWidget
from Functions.Widget_classes import show_loading_dialog
from ui.filters.SaveFilterDialog import SaveFilterDialog

VIEWABLE_LABELS = {
        'Samples': 'Samples',
        'Aliquots': 'Aliquots',
        'Grains': 'Grains',
        'Spots': 'Spots',
        'UPbAnalyses': 'UPb Analyses',
    }

class FiltersTab(QWidget):
    def __init__(self, parent=None):

        super().__init__(parent)
        self.setObjectName("FiltersTab")
        self.resize(1000, 700)

        # Root layout
        self.root_layout = QHBoxLayout(self)

        # Left column layout
        self.left_column_layout = QVBoxLayout()
        self.left_column_layout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.root_layout.addLayout(self.left_column_layout)

        # Title label - in left column
        self.label = QLabel("Saved Filters", self)
        label_policy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        label_policy.setHorizontalStretch(0)
        label_policy.setVerticalStretch(0)
        self.label.setSizePolicy(label_policy)
        self.label.setFixedSize(QSize(225, 50))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_column_layout.addWidget(self.label)

        # Search box - in left column
        self.filter_search_lineEdit = QLineEdit(self)
        self.filter_search_lineEdit.setMinimumSize(225, 25)
        self.filter_search_lineEdit.setMaximumSize(225, 25)
        self.filter_search_lineEdit.setPlaceholderText("search stored filters")
        self.filter_search_lineEdit.textChanged.connect(self.filter_items)
        self.left_column_layout.addWidget(self.filter_search_lineEdit)

        # Stored filters list - in left column
        self.filter_list_widget = QListWidget(self)
        list_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        list_policy.setHorizontalStretch(0)
        list_policy.setVerticalStretch(0)
        self.filter_list_widget.setSizePolicy(list_policy)
        self.filter_list_widget.setMinimumSize(225, 50)
        self.filter_list_widget.setMaximumSize(225, 800)
        self.left_column_layout.addWidget(self.filter_list_widget)
        self.update_filter_list()

        # right column layout
        self.right_column_layout = QVBoxLayout()
        self.right_column_layout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.root_layout.addLayout(self.right_column_layout)

        # Query builder goes beside the list (imported here, as before) - in right column
        from ui.filters.FilterQueryBuilder import FilterQueryBuilder
        self.querybuilder = FilterQueryBuilder(self)
        self.right_column_layout.addWidget(self.querybuilder)

        # views Samples that match the criteria - in right column/buttonset
        buttons_layout = QHBoxLayout(self)
        self.view_samples_button = QPushButton('View Samples')
        self.view_samples_button.setToolTip('View samples that pass the filter')
        buttons_layout.addWidget(self.view_samples_button)
        self.view_samples_button.clicked.connect(lambda: self.view_data('Samples'))

        # views Aliquots that match the criteria - in right column/buttonset
        self.view_aliquots_button = QPushButton('View Aliquots')
        self.view_aliquots_button.setToolTip('View aliquots that pass the filter')
        buttons_layout.addWidget(self.view_aliquots_button)
        self.view_aliquots_button.clicked.connect(lambda: self.view_data('Aliquots'))

        # views Grains that match the criteria - in right column/buttonset
        self.view_grains_button = QPushButton('View Grains')
        self.view_grains_button.setToolTip('View grains that pass the filter')
        buttons_layout.addWidget(self.view_grains_button)
        self.view_grains_button.clicked.connect(lambda: self.view_data('Grains'))

        # views Spots that match the criteria - in right column/buttonset
        self.view_spots_button = QPushButton('View Spots')
        self.view_spots_button.setToolTip('View spots that pass the filter')
        buttons_layout.addWidget(self.view_spots_button)
        self.view_spots_button.clicked.connect(lambda: self.view_data('Spots'))

        # views UPbAnalyses that match the criteria - in right column/buttonset
        self.view_analyses_button = QPushButton('View Analyses')
        self.view_analyses_button.setToolTip('View analyses that pass the filter')
        buttons_layout.addWidget(self.view_analyses_button)
        self.view_analyses_button.clicked.connect(lambda: self.view_data('UPbAnalyses'))

        # Saves the current filter - in right column/buttonset
        self.save_filter_button = QPushButton('Save Filter')
        self.save_filter_button.setToolTip('Save current filter criteria for later use')
        buttons_layout.addWidget(self.save_filter_button)
        self.save_filter_button.clicked.connect(self.save_filter)

        self.right_column_layout.addLayout(buttons_layout)

        self.filter_list_widget.itemDoubleClicked.connect(lambda state: self.querybuilder.populate_filters(state))
        self.filter_list_widget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.filter_list_widget.customContextMenuRequested.connect(self.filter_context_menu)

    def view_data(self, data_type: str):
        """
        Opens a DataViewerWidget with filtered IDs for the given data type.
        data_type must be a key in VIEWABLE_LABELS (e.g. 'Samples', 'UPbAnalyses').
        """
        if data_type not in VIEWABLE_LABELS:
            raise ValueError(f"Unsupported data type: {data_type!r}")

        label = VIEWABLE_LABELS[data_type]
        filtered_ids = self.querybuilder.get_filtered_ids(data_type)
        if filtered_ids is None:
            QMessageBox.information(self, "No results", f'No matching {label} for given filter(s)')
            return

        unique_ids = set(filtered_ids)
        count = len(unique_ids)
        if count > 1000 and not self.querybuilder.view_many_results(count):
            return

        show_loading_dialog('Loading', f'Loading {count} {label}...')
        dataviewer = DataViewerWidget(self, unique_ids, data_type)
        dataviewer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        loop = QEventLoop()
        dataviewer.destroyed.connect(loop.quit)
        loop.exec()

    def delete_filter(self, item: QListWidgetItem) -> None:
        """
        Deletes a filter from the database and filter list widget given a QListWidgetItem
        :param QListWidgetItem item:
        """
        reply = QMessageBox.question(
            self.filter_list_widget,
            "Confirm Deletion",
            f"Are you sure you want to delete '{item.text()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            row = self.filter_list_widget.row(item)
            self.filter_list_widget.takeItem(row)

            query = QSqlQuery()
            sql_query = """
                    DELETE FROM FilterGroups 
                    WHERE FilterGroupName = :filter_name COLLATE NOCASE;
                """
            query.prepare(sql_query)
            query.bindValue(":filter_name", item.text())
            if not query.exec():
                logger_setup.get_logger().critical(
                    f'Could not delete filter')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL command: {sql_query}')
                logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
            else:
                logger_setup.get_logger().info(f'Filter {item.text()} deleted')

    def update_filter_list(self):
        """
        Updates the filter list widget by querying the database for filters and repopulating the filter_list_widget.
        """
        self.filter_list_widget.clear()
        query = QSqlQuery()
        sql_query = "SELECT * FROM FilterGroups;"
        logger_setup.get_logger().debug(f'Updating filter list')
        if query.exec(sql_query):
            while query.next():
                item = QListWidgetItem()
                item.setToolTip(query.value(4))  # description
                item.setText(query.value(1))  # FilterGroupName
                self.filter_list_widget.addItem(item)
            self.filter_list_widget.sortItems()
        else:
            logger_setup.get_logger().info(f'Failed to get all filters from the database')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL command: {sql_query}')

    def filter_items(self, text: str):
        """
        Filters the list widget of Filters by a given text value
        :param str text:
        """
        # todo: Change this regex
        # Loop through all items in the list widget
        for row in range(self.filter_list_widget.count()):
            item = self.filter_list_widget.item(row)
            # Show or hide items based on the search text
            item.setHidden(text.lower() not in item.text().lower())

    def save_filter(self):
        """
        Saves a filter from the QueryBuilder to the database
        """
        # if a filter is already selected to the left, ask if the user wants to update it or create a new filter
        if self.filter_list_widget.currentItem():
            filter_name = self.filter_list_widget.currentItem().text()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setText(f"Update {filter_name} or create a new filter?")
            msg.setWindowTitle("Update or New")
            cancel_button = QPushButton("Cancel")
            new_button = QPushButton("New")
            update_button = QPushButton("Update")
            msg.addButton(cancel_button, QMessageBox.ButtonRole.RejectRole)
            msg.addButton(new_button, QMessageBox.ButtonRole.AcceptRole)
            msg.addButton(update_button, QMessageBox.ButtonRole.AcceptRole)
            msg.exec()
            reply = msg.clickedButton()
            if reply == cancel_button:
                return
            elif reply == new_button:
                filter_id = None
            elif reply == update_button:
                from Functions.Widget_classes import get_id_from_name
                filter_id = get_id_from_name('FilterGroups', filter_name)
            SaveFilterDialog(self.querybuilder.main_group_box.get_structure(), update_id=filter_id, parent=self).exec()
        else:
            SaveFilterDialog(self.querybuilder.main_group_box.get_structure(), parent=self).exec()

        self.filter_list_widget.clear()
        self.update_filter_list()

    def filter_context_menu(self, pos: QtCore.QPoint):
        """
        Shows the context menu for filters list widget. Allows the user to delete the selected filter.
        :param pos:
        """
        item: QListWidgetItem | None = self.filter_list_widget.itemAt(pos)
        if item:
            context_menu = QtWidgets.QMenu()
            delete_action = QAction("Delete", self.filter_list_widget)
            delete_action.triggered.connect(lambda: self.delete_filter(item))
            context_menu.addAction(delete_action)
            context_menu.exec(self.filter_list_widget.mapToGlobal(pos))
import os
import sys
from collections import Counter

from PyQt6 import QtCore
from PyQt6.QtCore import QSettings, QSortFilterProxyModel, QModelIndex
from PyQt6.QtGui import QDesktopServices, QStandardItemModel, QStandardItem
from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel, QSqlQuery, QSqlTableModel
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTableView,
    QGridLayout, QLabel, QCheckBox, QSpacerItem,
    QSizePolicy, QTabWidget, QInputDialog, QDialog, QListWidget, QHBoxLayout, QMessageBox, QComboBox, QErrorMessage,
    QGroupBox, QScrollArea, QListView
)
from PyQt6.uic import loadUi
from PyQt6.uic.Compiler.qtproxies import QtGui
import logger_setup
from Functions.SQLUtils import views
from Functions.Settings_manager import settings
from ui.FlowLayout import FlowLayout, ScrollableFlowWidget
from Functions import SQLUtils
from Functions.Widget_classes import ColumnListProxyModel, ColumnItemModel, get_view_name_column, get_headers

class SelectColumns(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file =os.path.join(base_path,  "SelectColumns.ui")
        loadUi(sources_ui_file, self)

        self.view_dict =  SQLUtils.view_attributes_dict
        if 'SampleIfNullView' in self.view_dict:
            self.view_dict.pop('SampleIfNullView')

        self.view_setting_dict = SQLUtils.view_setting_dict

        # Columns that view selections must have but are always hidden: parent ID fields and tree structure fields
        self.hidden_must_haves = ['SampleID', 'AliquotID', 'ParentAliquotID', 'AliquotParentRow', 'SpotID', 'UPbAnalysisID']

        self.columnselection_comboBox.addItems(self.view_dict.keys())
        self.load_list_states()

        self.columnselection_comboBox.currentIndexChanged.connect(self.switch_table_layout)

    def populate_stack(self):
        logger_setup.get_logger().info('Populating column selection stack')
        for view_name in self.view_dict:

            # Create a QListView for each table
            column_list_view = QListView()
            column_list_view.setSelectionMode(QListView.SelectionMode.MultiSelection)
            column_list_view.setDragDropMode(QListView.DragDropMode.InternalMove)
            column_list_view.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
            column_list_view.setDragEnabled(True)

            # Create a QStandardItemModel to hold the column names and populate the checks and order from the settings
            # Apply a proxy model to make them readable
            proxy_model = self.check_list_view(view_name)

            column_list_view.setModel(proxy_model)

            # Add the QListView to the stack widget
            self.columnattributes_stack.addWidget(column_list_view)

    def check_list_view(self, view_name: str):
        logger_setup.get_logger().info(f'Populating checks for {view_name}')
        model = ColumnItemModel()
        view_name_col = get_view_name_column(view_name)
        field_items = self.view_dict[view_name]
        settings_columns = settings.value(self.view_setting_dict[view_name])
        if view_name_col:
            # If there is a view name column, set it as the permanent header
            name_header = settings_columns[view_name_col]
            model.set_permanent_header(name_header)
        for column in settings_columns:
            # Do not bother to add the table ID field which must be present but is always hidden
            # Same for any parent ID fields or tree structure fields
            if column == field_items[0]:
                pass
            elif column in self.hidden_must_haves or 'ID' in column:
                pass
            elif '"' in column and column.split('"')[1] in self.hidden_must_haves:
                pass
            else:
                item = QStandardItem(column)
                item.setDragEnabled(True)
                item.setCheckable(True)
                item.setCheckState(QtCore.Qt.CheckState.Checked)
                item.setEnabled(True)
                model.appendRow(item)
        for field in field_items:
            if field not in settings_columns:
                item = QStandardItem(field)
                item.setDragEnabled(True)
                item.setCheckable(True)
                item.setCheckState(QtCore.Qt.CheckState.Unchecked)
                item.setEnabled(True)
                model.appendRow(item)
        # Create a readable proxy model for the column headers
        proxy_model = ColumnListProxyModel()
        proxy_model.setSourceModel(model)
        return proxy_model

    def switch_table_layout(self):
        # Switch the stack widget to show the layout corresponding to the selected view
        selected_view_index = self.columnselection_comboBox.currentIndex()
        self.columnattributes_stack.setCurrentIndex(selected_view_index)

    def save_list_states(self):
        # Save the state of checkboxes for all tables
        logger_setup.get_logger().info('Saving column selections')
        for index in range(self.columnattributes_stack.count()):
            view_widget = self.columnattributes_stack.widget(index)
            view_name = self.columnselection_comboBox.itemText(index)
            # Always include the ID fields
            if view_widget is not None and view_name != '':
                field_names = self.view_dict[view_name]
                view_columns = []
                for field in field_names:
                    if 'ID' in field or field in self.hidden_must_haves:
                        view_columns.append(field)
                source_model = view_widget.model().sourceModel()
                for row in range(source_model.rowCount()):
                    item = source_model.item(row)
                    if item.checkState() == QtCore.Qt.CheckState.Checked:
                        column_name = item.text()
                        view_columns.append(column_name)

                # Store list of checked columns in the settings
                settings.setValue(self.view_setting_dict[view_name], view_columns)
        self.load_list_states()


    def load_list_states(self):
        # Load the state of checkboxes and order of fields for all tables from the settings
        logger_setup.get_logger().info('Loading column selections')
        for index in range(self.columnattributes_stack.count()):
            view_widget = self.columnattributes_stack.widget(index)
            view_name = self.columnselection_comboBox.itemText(index)
            if view_widget is not None and view_name != '':
                # Reset the model adding first the fields in the settings and then the rest
                proxy_model = self.check_list_view(view_name)
                view_widget.setModel(proxy_model)
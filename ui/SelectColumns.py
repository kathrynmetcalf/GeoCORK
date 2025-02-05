import os
import sys
from collections import Counter

import pandas
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

from Functions.SQLUtils import views
from Functions.Settings_manager import settings
from ui.FlowLayout import FlowLayout, ScrollableFlowWidget
from Functions import SQLUtils
from Functions.Table_classes import CheckableSqlTableModel, CheckableComboBox
from Functions.Widget_classes import ColumnListProxyModel, ColumnItemModel

class SelectColumns(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file =os.path.join(base_path,  "SelectColumns.ui")
        loadUi(sources_ui_file, self)

        self.view_dict =  SQLUtils.view_attributes_dict
        if 'SampleIfNullView' in self.view_dict:
            self.view_dict.pop('SampleIfNullView')

        self.view_setting_dict = {
            'SampleView': 'sample_view_columns',
            'SampleEditView': 'sample_edit_columns',
            'AliquotView': 'aliquot_view_columns',
            'AliquotEditView': 'aliquot_edit_columns',
            'SpotView': 'spot_view_columns',
            'SpotEditView': 'spot_edit_columns',
            'UPbAnalysisView': 'upb_analysis_view_columns',
            'UPbAnalysisEditView': 'upb_analysis_edit_columns',
            'ColumnView': 'column_view_columns',
            'ColumnEditView': 'column_edit_columns'
        }

        self.columnselection_comboBox.addItems(self.view_dict.keys())
        self.populate_stack()
        self.load_list_states()

        self.columnselection_comboBox.currentIndexChanged.connect(self.switch_table_layout)

    def populate_stack(self):

        for view_name in self.view_dict:
            field_items = self.view_dict[view_name]
            settings_columns = settings.value(self.view_setting_dict[view_name])

            # Create a QListView for each table
            column_list_view = QListView()
            column_list_view.setSelectionMode(QListView.SelectionMode.MultiSelection)
            column_list_view.setDragDropMode(QListView.DragDropMode.InternalMove)
            column_list_view.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
            column_list_view.setDragEnabled(True)

            # Create a QStandardItemModel to hold the column names and populate the checks and order from the settings
            # Apply a proxy model to make them readable
            proxy_model = self.check_list_view(field_items, settings_columns)

            column_list_view.setModel(proxy_model)

            # Add the QListView to the stack widget
            self.columnattributes_stack.addWidget(column_list_view)

    def check_list_view(self, field_items, settings_columns):
        model = QStandardItemModel()
        for column in settings_columns:
            # Do not bother to add the table ID field which must be present but is always hidden
            if column == field_items[0]:
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

        for index in range(self.columnattributes_stack.count()):
            view_widget = self.columnattributes_stack.widget(index)
            view_name = self.columnselection_comboBox.itemText(index)
            field_names = self.view_dict[view_name]
            view_columns = [field_names[0]]  # Always include the ID field
            if view_widget:
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

        for index in range(self.columnattributes_stack.count()):
            view_widget = self.columnattributes_stack.widget(index)
            view_name = self.columnselection_comboBox.itemText(index)
            field_names = self.view_dict[view_name]
            settings_columns = settings.value(self.view_setting_dict[view_name])
            if view_widget:
                # Reset the model adding first the fields in the settings and then the rest
                proxy_model = self.check_list_view(field_names, settings_columns)
                view_widget.setModel(proxy_model)
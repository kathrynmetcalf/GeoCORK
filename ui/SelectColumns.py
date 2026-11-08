import os
import sys

from PyQt6 import QtCore
from PyQt6.QtGui import QStandardItem
from PyQt6.QtWidgets import (
    QWidget, QListView, QMessageBox
)
from PyQt6.uic import loadUi

import logger_setup
from Functions import SQLUtils
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.Widget_classes import (
    ColumnListProxyModel, ColumnItemModel, get_name_column, get_table_from_view, ReorderListView
)


class SelectColumns(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "SelectColumns.ui")
        loadUi(sources_ui_file, self)

        self.view_dict = SQLUtils.view_attributes_dict
        if 'SampleIfNullView' in self.view_dict:
            self.view_dict.pop('SampleIfNullView')

        self.view_setting_dict = SQLUtils.view_setting_dict

        # Columns that view selections must have but are always hidden: parent ID fields and tree structure fields
        self.hidden_must_haves = ['SampleID', 'AliquotID', 'ParentAliquotID', 'AliquotParentRow', 'SpotID',
                                  'UPbAnalysisID']

        self.show_per_page_comboBox.addItems(['10', '25', '50', '100', '250', '500', '1000'])
        self.show_per_page_comboBox.setCurrentText(str(settings.value('show_per_page')))
        if settings.value('show_items_missing_data') == 'true':
            self.show_missing_checkBox.setCheckState(QtCore.Qt.CheckState.Checked)
        else:
            self.show_missing_checkBox.setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.show_missing_checkBox.setToolTip(f'Show samples, aliquots, grain, and spots that are missing aliquots, grains, spots, or analyses.\nSlows down GeoCORK when enabled.')
        self.reset_table_pushButton.clicked.connect(self.reset_table_columns)
        self.columnselection_comboBox.addItems(self.view_dict.keys())
        self.load_list_states()

        self.columnselection_comboBox.currentIndexChanged.connect(self.switch_table_layout)
        self.show_missing_checkBox.stateChanged.connect(self.update_show_missing)

    def populate_stack(self):
        logger_setup.get_logger().info('Populating column selection stack')
        for view_name in self.view_dict:
            # Create a QListView for each table
            column_list_view = ReorderListView()
            column_list_view.setSelectionMode(QListView.SelectionMode.ExtendedSelection)

            # Create a QStandardItemModel to hold the column names and populate the checks and order from the settings
            # Apply a proxy model to make them readable
            proxy_model = self.check_list_view(view_name)

            column_list_view.setModel(proxy_model)

            # Add the QListView to the stack widget
            self.columnattributes_stack.addWidget(column_list_view)

    def check_list_view(self, view_name: str):
        logger_setup.get_logger().info(f'Populating checks for {view_name}')
        model = ColumnItemModel()
        view_name_col = get_name_column(view_name)
        field_items = settings.value(f'default_{self.view_setting_dict[view_name]}')
        settings_columns = settings.value(self.view_setting_dict[view_name])
        if 'Edit' not in view_name:
            field_items = self.handle_autofill(field_items)
            settings_columns = self.handle_autofill(settings_columns)
        name_header = None
        if view_name_col:
            # If there is a view name column, set it as the permanent header
            name_header = settings_columns[view_name_col]
            model.set_permanent_header(name_header)
        for column in settings_columns:
            # Do not bother to add the table ID field which must be present but is always hidden
            # Same for any parent ID fields or tree structure fields
            if column == name_header:
                # Make sure the name column cannot be moved or unchecked
                item = QStandardItem(column)
                item.setCheckable(True)
                item.setCheckState(QtCore.Qt.CheckState.Checked)
                item.setEnabled(False)
                model.appendRow(item)
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
        selected_view_name = self.columnselection_comboBox.currentText()
        self.columnattributes_stack.setCurrentIndex(selected_view_index)
        self.reset_table_pushButton.setText(f'Reset {selected_view_name}')

    def reset_table_columns(self):
        logger_setup.get_logger().info('Resetting table columns')
        selected_view_index = self.columnselection_comboBox.currentIndex()
        selected_view = self.columnselection_comboBox.currentText()
        settings.setValue(self.view_setting_dict[selected_view],
                          settings.value(f'default_{self.view_setting_dict[selected_view]}'))
        # get the list view in the current index of the stack widget
        column_list_view = self.columnattributes_stack.widget(selected_view_index)
        proxy_model = self.check_list_view(selected_view)
        column_list_view.setModel(proxy_model)
        logger_setup.get_logger().info('Reset table columns')

    def save_list_states(self):
        # Save the number of rows to show per page
        settings.setValue('show_per_page', int(self.show_per_page_comboBox.currentText()))

        # Save the state of checkboxes for all tables
        logger_setup.get_logger().info('Saving column selections')
        for index in range(self.columnattributes_stack.count()):
            view_widget = self.columnattributes_stack.widget(index)
            view_name = self.columnselection_comboBox.itemText(index)
            # Always include the ID fields
            if view_widget is not None and view_name != '':
                source_model = view_widget.model().sourceModel()
                field_names_setting = settings.value(f'default_{self.view_setting_dict[view_name]}')
                if 'Edit' not in view_name:
                    field_names = self.handle_autofill(field_names_setting)
                view_columns = []
                if 'Aliquot' in view_name:
                    # Preset the first columns. First 4 columns are set by tree model, and SampleID is hidden from the list
                    view_columns = ['AliquotID', 'ParentAliquotID', 'AliquotParentRow', 'AliquotName', 'SampleID']
                    # Skip AliquotName since we already included it
                    model_range = range(1, source_model.rowCount())
                else:
                    model_range = range(source_model.rowCount())
                    for field in field_names:
                        if 'ID' in field or field in self.hidden_must_haves:
                            view_columns.append(field)
                for row in model_range:
                    item = source_model.item(row)
                    if item.checkState() == QtCore.Qt.CheckState.Checked:
                        column_name = item.text()
                        view_columns.append(column_name)

                # Store list of checked columns in the settings
                settings.setValue(self.view_setting_dict[view_name], view_columns)
                logger_setup.get_logger().info(f'Saved {view_name} columns')
        logger_setup.get_logger().info('Saved all column selections')
        # self.load_list_states()

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

    def handle_autofill(self, field_names_setting):
        field_names = []
        if settings.value('autofill_best_age') == 'true':
            for field_name in field_names_setting:
                if 'BestAge' in field_name and 'Filled' not in field_name:
                    field_name = f'"{field_name.replace('"', '')}Filled"'
                field_names.append(field_name)
        else:
            for field_name in field_names_setting:
                if 'BestAge' in field_name and 'Filled' in field_name:
                    field_name = f'{field_name.replace('Filled', '')}'
                field_names.append(field_name)
        return field_names

    def update_show_missing(self):
        if self.show_missing_checkBox.checkState() == QtCore.Qt.CheckState.Checked:
            settings.setValue('show_items_missing_data', 'true')
            msg = QMessageBox(QMessageBox.Icon.Warning, 'Performance Warning',
                              'Data with incomplete sample, aliquot, grain, spot, and analysis records will be shown.\nThis can significantly slow down GeoCORK for large databases.',
                              QMessageBox.StandardButton.Ok)
            msg.exec()
        else:
            settings.setValue('show_items_missing_data', 'false')
            msg = QMessageBox(QMessageBox.Icon.Warning, 'Data Hidden Warning',
            'Only data with complete sample, aliquot, grain, spot, and analysis records will be shown in windows but can still be selected in dropdown menus.\nThis can speed up GeoCORK for large databases.',
                              QMessageBox.StandardButton.Ok)
            msg.exec()

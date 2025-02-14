from cgitb import reset

import PyQt6
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6.uic import loadUi
from Functions.Widget_classes import (
    TreeModel, CheckableTreeCombobox, CheckableTreeModel, CheckableTreeView, set_table, SampleAgeTableModel, CheckableSqlTableModel,
    FontDelegate, name_column, set_comboBox_text, show_column, CheckableComboBox, CheckableSqlQueryModel, SQLiteTableModel,
    get_selected_tree_ids, find_tree_model, get_headers
)
from Functions import SQLUtils
from Functions.Settings_manager import settings
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Check_triggers import validate_insert, validate_update, update_modified_timestamp
import Functions.Database_views as DB_views
from ui.EditTree import EditTree
from ui.EditTable import EditTable
from ui.AddTreeTags import AddTreeTags
from ui.AddTags import AddTags
import logger_setup
import time


class AgeFields(QtW.QWidget):
    def __init__(self, table: str, item_ids: list):
        super().__init__()
        age_ui_file = "ui/AgeFields.ui"
        loadUi(age_ui_file, self)
        self.table = table
        self.item_ids = item_ids
        self.updated = False
        self.add_age_pushButton.setAutoDefault(False)
        self.msg = QtW.QMessageBox(self)

        self.item_model = QtS.QSqlTableModel()
        self.sample_age_model = SampleAgeTableModel()
        # self.sample_age_model = CheckableSqlQueryModel()
        self.age_tree_view = QtW.QTreeView()
        self.age_model = QtS.QSqlTableModel()
        self.oldest_age_tree = TreeModel()
        self.youngest_age_tree = TreeModel()
        self.direct_age_unit_model = QtS.QSqlTableModel()
        self.error_format_model = QtS.QSqlTableModel()
        self.direct_age_error_model = QtS.QSqlTableModel()
        self.age_constraint_model = QtS.QSqlTableModel()
        self.age_constraint_tree = CheckableTreeModel()
        self.age_interpretation_model = QtS.QSqlTableModel()
        self.age_interpretation_tree = CheckableTreeModel()
        # self.age_reference_model = CheckableSqlTableModel()
        self.age_reference_model = CheckableSqlQueryModel()
        self.text_change_timer = QtC.QTimer()
        self.text_change_timer.setSingleShot(True)
        self.text_change_timer.timeout.connect(self.update_age_unit)

        self.sample_ages = []
        self.default_age_ids = []
        self.item_id_header = None

        self.add_age_pushButton.clicked.connect(self.add_age)
        self.direct_age_unit_comboBox.currentIndexChanged.connect(self.update_age_unit)
        self.direct_unit_comboBox.currentIndexChanged.connect(self.update_age_unit)

    def update_age_unit(self):
        sender = self.sender()
        if sender == self.direct_age_unit_comboBox:
            if self.direct_age_unit_comboBox.currentIndex() != self.direct_unit_comboBox.currentIndex():
                self.direct_unit_comboBox.setCurrentIndex(self.direct_age_unit_comboBox.currentIndex())
        elif sender == self.direct_unit_comboBox:
            if self.direct_unit_comboBox.currentIndex() != self.direct_age_unit_comboBox.currentIndex():
                self.direct_age_unit_comboBox.setCurrentIndex(self.direct_unit_comboBox.currentIndex())
        else:
            print(sender.objectName())

    def update_list(self, item_ids):
        logger_setup.get_logger().info(f"Populating age fields for {self.table} with item IDs {self.item_ids}")
        self.item_ids = item_ids
        self.clear_fields() # Also disconnects signals
        self.populate_dropdowns()
        self.populate_age_dropdown()
        self.populate_fields()
        self.connect_signals()

    def populate_dropdowns(self):
        start_populate_dropdowns_time = time.time()
        self.disconnect_signals()
        set_table(self.item_model, self.table)
        self.item_id_header = self.item_model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        self.sample_age_model.setQuery('SELECT * FROM SampleAges')
        set_table(self.age_model, 'Ages')
        set_table(self.direct_age_unit_model, 'AgeUnits')
        set_table(self.direct_age_error_model, 'ErrorFormats')
        self.oldest_age_tree.setSourceModel(self.age_model)
        self.youngest_age_tree.setSourceModel(self.age_model)
        set_table(self.age_constraint_model, 'AgeConstraints')
        self.age_constraint_tree.setSourceModel(self.age_constraint_model)
        set_table(self.age_interpretation_model, 'AgeInterpretations')
        self.age_interpretation_tree.setSourceModel(self.age_interpretation_model)
        self.age_reference_model.setQuery('SELECT * FROM ReferenceView')

        self.edit_age_comboBox: CheckableComboBox
        self.edit_age_comboBox.setModel(self.sample_age_model)
        show_column(self.edit_age_comboBox, 'SampleAgeDisplay')
        self.enable_context(self.edit_age_comboBox)

        self.direct_unit_comboBox.setModel(self.direct_age_unit_model)
        show_column(self.direct_unit_comboBox, 'AgeUnitAbbreviation')
        self.direct_age_unit_comboBox.setModel(self.direct_age_unit_model)
        show_column(self.direct_age_unit_comboBox, 'AgeUnitAbbreviation')
        self.direct_age_error_format_comboBox.setModel(self.direct_age_error_model)
        show_column(self.direct_age_error_format_comboBox, 'ErrorFormatAbbreviation')
        self.oldest_rel_comboBox.setModel(self.oldest_age_tree)
        self.youngest_rel_comboBox.setModel(self.youngest_age_tree)
        self.age_constraint_comboBox.setModel(self.age_constraint_tree)
        self.age_constraint_comboBox.enable_context_menu(True)
        self.age_interpretation_comboBox.setModel(self.age_interpretation_tree)
        self.age_interpretation_comboBox.enable_context_menu(True)
        self.age_reference_comboBox.setModel(self.age_reference_model)
        self.age_reference_comboBox.setModelColumn(name_column('References'))
        self.age_reference_comboBox.enable_context_menu(True)
        end_populate_dropdowns_time = time.time()
        logger_setup.get_logger().info(f"Populated age dropdowns in {end_populate_dropdowns_time - start_populate_dropdowns_time} seconds")

    def populate_age_dropdown(self):
        start_populate_age_dropdown_time = time.time()
        self.disconnect_signals()
        samples_sampleage_model = QtS.QSqlTableModel()
        sample_model = QtS.QSqlQueryModel()
        set_table(samples_sampleage_model, 'Samples_SampleAges')
        if len(self.item_ids) > 1:
            samples_sampleage_model.setFilter(f'SampleID in {tuple(self.item_ids)}')
            sample_model.setQuery(
                f'SELECT DefaultSampleAgeID FROM {self.table} WHERE {self.item_id_header} in {tuple(self.item_ids)}')
        elif len(self.item_ids) == 1:
            samples_sampleage_model.setFilter(f'SampleID = {self.item_ids[0]}')
            sample_model.setQuery(
                f'SELECT DefaultSampleAgeID FROM {self.table} WHERE {self.item_id_header} = {self.item_ids[0]}')
        else:
            samples_sampleage_model.setFilter('')
            sample_model.setQuery(f'SELECT DefaultSampleAgeID FROM {self.table}')
        self.sample_ages = []
        self.default_age_ids = []
        for row in range(sample_model.rowCount()):
            default_age_id = sample_model.index(row, 0).data()
            if default_age_id and default_age_id not in self.default_age_ids:
                self.default_age_ids.append(default_age_id)
        for row in range(samples_sampleage_model.rowCount()):
            self.sample_ages.append(samples_sampleage_model.index(row, 1).data())
        if len(self.sample_ages) > 1:
            self.sample_age_model.setQuery(f'{self.sample_age_model.default_query} WHERE SampleAgeID in {tuple(self.sample_ages)}')
        elif len(self.sample_ages) == 1:
            self.sample_age_model.setQuery(f'{self.sample_age_model.default_query} WHERE SampleAgeID = {self.sample_ages[0]}')
            # If there is only one age, select it and make it the default
            selected_id = self.sample_age_model.data(self.sample_age_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            self.sample_age_model.checked_ids = [selected_id]
            if selected_id not in self.default_age_ids:
                self.default_age_ids.append(selected_id)
        display_col = name_column('SampleAges')
        for row in range(self.sample_age_model.rowCount()):
            if self.sample_age_model.index(row, 0).data() in self.default_age_ids:
                # Make the text at that row bold
                self.sample_age_model.make_bold(self.sample_age_model.index(row, display_col))
            else:
                self.sample_age_model.make_not_bold(self.sample_age_model.index(row, display_col))
        end_populate_age_dropdown_time = time.time()
        logger_setup.get_logger().info(f"Populated age dropdowns in {end_populate_age_dropdown_time - start_populate_age_dropdown_time} seconds")

    def check_focus(self):
        if self.direct_age_groupBox.any_child_has_focus() and self.direct_age_groupBox.edited:
            self.direct_age_groupBox.focusLost.emit()
        elif self.relative_age_groupBox.any_child_has_focus() and self.relative_age_groupBox.edited:
            self.relative_age_groupBox.focusLost.emit()
        elif self.age_information_groupBox.any_child_has_focus() and self.age_information_groupBox.edited:
            self.age_information_groupBox.focusLost.emit()

    def connect_signals(self):
        # Connect signals and slots
        self.edit_age_comboBox.currentTextChanged.connect(self.populate_fields)
        self.default_age_checkBox.clicked.connect(self.update_age)
        self.direct_age_groupBox.connect_child_signals()
        self.direct_age_groupBox.focusLost.connect(self.update_age)
        self.relative_age_groupBox.connect_child_signals()
        self.relative_age_groupBox.focusLost.connect(self.update_age)
        self.age_information_groupBox.connect_child_signals()
        self.age_information_groupBox.focusLost.connect(self.update_age)
        self.age_constraint_comboBox.closing.connect(self.update_age)
        self.age_constraint_comboBox.add_triggered.connect(self.add_popup)
        self.age_constraint_comboBox.edit_triggered.connect(self.edit_popup)
        self.age_interpretation_comboBox.closing.connect(self.update_age)
        self.age_interpretation_comboBox.add_triggered.connect(self.add_popup)
        self.age_interpretation_comboBox.edit_triggered.connect(self.edit_popup)
        self.age_reference_comboBox.closing.connect(self.update_age)
        self.age_reference_comboBox.add_triggered.connect(self.add_popup)
        self.age_reference_comboBox.edit_triggered.connect(self.edit_popup)

    def disconnect_signals(self):
        self.direct_age_groupBox.disconnect_child_signals()
        self.relative_age_groupBox.disconnect_child_signals()
        self.age_information_groupBox.disconnect_child_signals()
        try:
            self.edit_age_comboBox.currentTextChanged.disconnect(self.populate_fields)
        except TypeError:
            pass
        try:
            self.default_age_checkBox.clicked.disconnect()
        except TypeError:
            pass
        try:
            self.oldest_direct_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass
        try:
            self.youngest_direct_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass
        try:
            self.direct_unit_comboBox.currentTextChanged.disconnect()
        except TypeError:
            pass
        try:
            self.direct_age_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass
        try:
            self.direct_age_error_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass
        try:
            self.direct_age_unit_comboBox.currentTextChanged.disconnect()
        except TypeError:
            pass
        try:
            self.oldest_rel_comboBox.currentTextChanged.disconnect()
        except TypeError:
            pass
        try:
            self.youngest_rel_comboBox.currentTextChanged.disconnect()
        except TypeError:
            pass
        try:
            self.direct_age_error_format_comboBox.currentTextChanged.disconnect()
        except TypeError:
            pass

    def populate_fields(self):
        logger_setup.get_logger().info("Populating age fields")
        self.disconnect_signals()
        start_populate_fields_time = time.time()
        reset_fields = False
        sample_age_id = self.sample_age_model.checked_ids[0]
        if not sample_age_id:
            # If no age is selected, select the first one
            self.sample_age_model.setData(self.sample_age_model.index(0, 0), QtC.Qt.CheckState.Checked,
                                          QtC.Qt.ItemDataRole.CheckStateRole)
            sample_age_id = self.sample_age_model.data(self.sample_age_model.index(0, 0),
                                                       QtC.Qt.ItemDataRole.DisplayRole)
        for row in range(self.sample_age_model.rowCount()):
            if self.sample_age_model.index(row, 0).data() == sample_age_id:
                sample_age_row = row
                break
        if sample_age_id in self.default_age_ids:
            self.default_age_checkBox.setChecked(True)
        else:
            self.default_age_checkBox.setChecked(False)
        info_model = SQLiteTableModel('PRAGMA table_info(SampleAges)')
        column_names = info_model.column_as_list('name')
        sample_age_table = QtS.QSqlQueryModel()
        if len(self.sample_ages) > 1:
            sample_age_table.setQuery(
                f'SELECT * FROM SampleAges WHERE SampleAgeID in {tuple(self.sample_ages)}')
        elif len(self.sample_ages) == 1:
            sample_age_table.setQuery(
                f'SELECT * FROM SampleAges WHERE SampleAgeID = {self.sample_ages[0]}')
        else:
            sample_age_table.setQuery(f'SELECT * FROM SampleAges')
        if sample_age_table.rowCount() == 0:
            logger_setup.get_logger().info("No samples to populate")
            reset_fields = True
        for header in column_names:
            if reset_fields:
                text = ""
            else:
                values = []
                for row in range(sample_age_table.rowCount()):
                    values.append(sample_age_table.index(row, column_names.index(header)).data())
                if len(set(values)) == 1 and not values[0]:
                    # If all values are the same and empty, add an empty string
                    text = ""
                elif len(set(values)) == 1 and values[0]:
                    # If all values are the same and not empty, add the value
                    text = values[0]
                else:
                    # If values are different, add '-'
                    text = "-"
            if 'ErrorFormatID' in header:
                if not text:
                    self.direct_age_error_format_comboBox.setCurrentText(settings.value('age_error_format_abbreviation'))
                else:
                    # text is the ID, so we need to get the index in the model
                    combo_index = self.direct_age_error_format_comboBox.currentIndex()
                    for row in range(self.direct_age_error_model.rowCount()):
                        if self.direct_age_error_model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole) == text:
                            combo_index = row
                            break
                    self.direct_age_error_format_comboBox.setCurrentIndex(combo_index)
            elif 'DirectAgeError' in header and 'ID' not in header:
                if not text:
                    self.direct_age_error_lineEdit.setText(self.direct_age_error_lineEdit.placeholderText())
                else:
                    self.direct_age_error_lineEdit.setText(f'{text}')
            elif 'AgeUnitID' in header:
                    if not text:
                        self.direct_age_unit_comboBox.setCurrentText(settings.value('age_unit_abbreviation'))
                    else:
                        # text is the ID, so we need to get the index in the model
                        combo_index = self.direct_age_unit_comboBox.currentIndex()
                        for row in range(self.direct_age_unit_model.rowCount()):
                            if self.direct_age_unit_model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole) == text:
                                combo_index = row
                                break
                        self.direct_age_unit_comboBox.setCurrentIndex(combo_index)
            elif 'OldestDirectAge' in header:
                if not text:
                    self.oldest_direct_lineEdit.setText(self.oldest_direct_lineEdit.placeholderText())
                else:
                    self.oldest_direct_lineEdit.setText(f'{text}')
            elif 'YoungestDirectAge' in header:
                if not text:
                    self.youngest_direct_lineEdit.setText(self.youngest_direct_lineEdit.placeholderText())
                else:
                    self.youngest_direct_lineEdit.setText(f'{text}')
            elif 'DirectAge' in header and 'Error' not in header and 'ID' not in header:
                if not text:
                    self.direct_age_lineEdit.setText(self.direct_age_lineEdit.placeholderText())
                else:
                    self.direct_age_lineEdit.setText(f'{text}')
            elif 'OldestAgeID' in header:
                if not text:
                    self.oldest_rel_comboBox.setCurrentText(self.oldest_rel_comboBox.placeholderText())
                else:
                    self.oldest_rel_comboBox.setCurrentText(text)
            elif 'YoungestAgeID' in header:
                if not text:
                    self.youngest_rel_comboBox.setCurrentText(self.youngest_rel_comboBox.placeholderText())
                else:
                    self.youngest_rel_comboBox.setCurrentText(text)
            elif 'SampleAgeDescription' in header:
                if not text:
                    self.age_description_lineEdit.setText(self.age_description_lineEdit.placeholderText())
                else:
                    self.age_description_lineEdit.setText(f'{text}')

        self.edit_age_comboBox.setItemDelegate(FontDelegate(self.edit_age_comboBox))

        # Age tags
        text = self.populate_checks('SampleAges_AgeConstraints', self.age_constraint_model,
                                    self.age_constraint_comboBox, sample_age_id)
        self.age_constraint_comboBox.setCurrentText(text)
        text = self.populate_checks('SampleAges_AgeInterpretations', self.age_interpretation_model,
                                    self.age_interpretation_comboBox, sample_age_id)
        self.age_interpretation_comboBox.setCurrentText(text)
        text = self.populate_checks('SampleAges_References', self.age_reference_model, None, sample_age_id)
        self.age_reference_comboBox.setCurrentText(text)

        end_populate_fields_time = time.time()
        logger_setup.get_logger().info(f"Populated age fields in {end_populate_fields_time - start_populate_fields_time} seconds")

    def populate_checks(self, many_to_many_table: str, table_model: QtS.QSqlTableModel | QtS.QSqlQueryModel, tree_combo: CheckableTreeCombobox = None, sample_age_id: int = None):
        logger_setup.get_logger().info(f"Populating checks for {many_to_many_table}")
        start_populate_checks_time = time.time()
        self.disconnect_signals()
        many_to_many_model = QtS.QSqlTableModel()
        many_to_many_model.setTable(many_to_many_table)
        many_to_many_model.select()
        tag_id_header = table_model.record().fieldName(0)
        items = []
        text = ""
        if tree_combo:
            model = find_tree_model(tree_combo.model())
            col = name_column(table_model.tableName())
            model.blockSignals(True)
        else:
            model = table_model
            col = name_column(table_model.tableName())
        if not sample_age_id:
            logger_setup.get_logger().info("No items selected, so uncheck everything")
            for row in range(table_model.rowCount()):
                if tree_combo:
                    model_index = model.mapFromSource(table_model.index(row, col))
                    # tree_combo.treeView.disconnect_edited_signal()
                else:
                    model_index = table_model.index(row, col)
                model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                if tree_combo:
                    err = model.source_model.lastError().text()
                else:
                    err = model.lastError().text()
                if err:
                    logger_setup.get_logger().critical(f"Error unchecking {model.tableName()}: {err}")
                    return text
            logger_setup.get_logger().info("Unchecked everything")
            if tree_combo:
                model.blockSignals(False)
            return text
        for row in range(table_model.rowCount()):
            tag_id = table_model.index(row, 0).data()
            many_to_many_model.setFilter(f"SampleAgeID = {sample_age_id} AND {tag_id_header} = {tag_id}")
            if tree_combo is not None:
                model_index = model.mapFromSource(table_model.index(row, col))
            else:
                model_index = table_model.index(row, col)
            if many_to_many_model.rowCount() > 0:
                # Selected sample age has this tag
                model.setData(model_index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                if tree_combo:
                    err = model.source_model.lastError().text()
                else:
                    err = model.lastError().text()
                if err:
                    logger_setup.get_logger().critical(f"Error setting checked for {model.tableName()}: {err}")
                items.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
            else:
                # No samples have this tag
                model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                if tree_combo:
                    err = model.source_model.lastError().text()
                else:
                    err = model.lastError().text()
                if err:
                    logger_setup.get_logger().critical(f"Error setting unchecked for {model.tableName()}: {err}")
        if not items:
            # Sample age does not have these tags
            text = ""
        else:
            # Sample age has these tags
            text = ', '.join(items)
        if tree_combo:
            if not text:
                text = tree_combo.placeholderText()
            model.blockSignals(False)
            tree_combo.treeView.connect_edited_signal()
        end_populate_checks_time = time.time()
        logger_setup.get_logger().info(
            f"Populated checks for {many_to_many_table} in {end_populate_checks_time - start_populate_checks_time} seconds")
        return text

    def update_age(self):
        logger_setup.get_logger().info("Updating age")
        if len(self.item_ids) == 0:
            logger_setup.get_logger().info("No items selected to update")
            return
        elif len(self.item_ids) > 0:
            logger_setup.get_logger().info("Collecting input age information")
            default_age = self.default_age_checkBox.isChecked()
            direct_age = self.direct_age_lineEdit.text()
            if not direct_age or direct_age == '':
                direct_age = 'Null'
            direct_age_error = self.direct_age_error_lineEdit.text()
            if not direct_age_error or direct_age_error == '':
                direct_age_error = 'Null'
            direct_age_unit = self.direct_age_unit_comboBox.currentText()
            direct_age_error_type = self.direct_age_error_format_comboBox.currentText()
            oldest_direct = self.oldest_direct_lineEdit.text()
            if not oldest_direct or oldest_direct == '':
                oldest_direct = 'Null'
            youngest_direct = self.youngest_direct_lineEdit.text()
            if not youngest_direct or youngest_direct == '':
                youngest_direct = 'Null'
            oldest_rel = self.oldest_rel_comboBox.currentText()
            youngest_rel = self.youngest_rel_comboBox.currentText()
            age_description = self.age_description_lineEdit.text()
            if not age_description or age_description == '':
                age_description = 'Null'

            row = self.edit_age_comboBox.currentIndex()
            sample_age_id = self.sample_age_model.data(self.sample_age_model.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
            old_sample_age_id = sample_age_id
            if direct_age_unit == '':
                direct_age_unit_id = 'Null'
            else:
                self.direct_age_unit_model.setFilter(f"AgeUnitAbbreviation = '{direct_age_unit}'")
                direct_age_unit_id = self.direct_age_unit_model.data(self.direct_age_unit_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            if direct_age_error_type == '':
                direct_age_error_format_id = 'Null'
            else:
                self.direct_age_error_model.setFilter(f"ErrorFormatAbbreviation = '{direct_age_error_type}'")
                direct_age_error_format_id = self.direct_age_error_model.data(self.direct_age_error_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            if oldest_rel == '':
                oldest_rel_id = 'Null'
            else:
                self.age_model.setFilter(f"AgeName = '{oldest_rel}'")
                oldest_rel_id = self.age_model.data(self.age_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            if youngest_rel == '':
                youngest_rel_id = 'Null'
            else:
                self.age_model.setFilter(f"AgeName = '{youngest_rel}'")
                youngest_rel_id = self.age_model.data(self.age_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)

            logger_setup.get_logger().info(f"Updating age information for SampleAgeID {sample_age_id}")
            create_savepoint('before_update')
            samples_sampleages_model = QtS.QSqlTableModel()
            set_table(samples_sampleages_model, 'Samples_SampleAges')
            samples_sampleages_model.setFilter(f"SampleAgeID = {sample_age_id}")
            if samples_sampleages_model.rowCount() > 0:
                for row in range(samples_sampleages_model.rowCount()):
                    if samples_sampleages_model.index(row, 0).data() not in self.item_ids:
                        logger_setup.get_logger().info(f"SampleAgeID {sample_age_id} is not associated with all selected items")
                        self.msg.setIcon(QtW.QMessageBox.Icon.Question)
                        self.msg.setText(f"SampleAgeID {sample_age_id} is not associated with all selected items. Do you want to associate it with all selected items?")
                        self.msg.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
                        response = self.msg.exec()
                        if response == QtW.QMessageBox.StandardButton.Yes:
                            logger_setup.get_logger().info("User chose to associate SampleAgeID with all selected items")
                        else:
                            logger_setup.get_logger().info("User chose not to associate SampleAgeID with all selected items")
                            return
            age_columns = ['DirectAge', 'DirectAgeError', 'DirectAgeUnitID', 'DirectAgeErrorFormatID', 'OldestDirectAge', 'YoungestDirectAge',
            'OldestAgeID', 'YoungestAgeID', 'SampleAgeDescription']
            qage_columns = ', '.join(age_columns)
            age_values = [f'{direct_age}', f'{direct_age_error}', f'{direct_age_unit_id}', f'{direct_age_error_format_id}', f'{oldest_direct}',
                          f'{youngest_direct}', f'{oldest_rel_id}', f'{youngest_rel_id}', f'{age_description}']
            query = QtS.QSqlQuery()
            if not query.exec(f"SELECT {qage_columns} FROM SampleAges WHERE SampleAgeID = {sample_age_id}"):
                logger_setup.get_logger().critical(f'Unable to get SampleAges: {query.lastError().text()}')
                return
            query.next()
            existing_values = [query.value(i) for i in range(query.record().count())]
            for s in existing_values:
                index = existing_values.index(s)
                if not s:
                    s = 'Null'
                    existing_values[index] = s
            if existing_values == age_values:
                logger_setup.get_logger().info("No changes to age information")
            elif existing_values != age_values:
                logger_setup.get_logger().info("Changes to age information")
                error, header = validate_update('SampleAges', age_columns, age_values, f'SampleAgeID = {sample_age_id}')
                if error:
                    logger_setup.get_logger().error(f'Invalid age input: {error}')
                    rollback_savepoint('before_update')
                    return
                logger_setup.get_logger().info(f"Valid age information")
                if not query.exec(f'''UPDATE SampleAges SET (DirectAge, DirectAgeError, DirectAgeUnitID, DirectAgeErrorFormatID, OldestDirectAge, YoungestDirectAge, OldestAgeID, YoungestAgeID, SampleAgeDescription) = 
                    ({direct_age}, {direct_age_error}, {direct_age_unit_id}, {direct_age_error_format_id}, {oldest_direct}, {youngest_direct}, {oldest_rel_id}, {youngest_rel_id}, "{age_description}") 
                    WHERE SampleAgeID = {sample_age_id}'''):
                    logger_setup.get_logger().critical(f'Unable to update SampleAges: {query.lastError().text()}')
                    rollback_savepoint('before_update')
                    return
                update_modified_timestamp('SampleAges', [sample_age_id])
                logger_setup.get_logger().info(f"Updated age information for SampleAgeID {sample_age_id}")
            if not self.update_age_tags(sample_age_id, self.age_constraint_comboBox):
                return
            if not self.update_age_tags(sample_age_id, self.age_interpretation_comboBox):
                return
            if not self.update_age_tags(sample_age_id, self.age_reference_comboBox):
                return
            for sample_id in self.item_ids:
                samples_sampleages_model = QtS.QSqlTableModel()
                set_table(samples_sampleages_model, 'Samples_SampleAges')
                samples_sampleages_model.setFilter(f"SampleID = {sample_id} AND SampleAgeID = {sample_age_id}")
                if samples_sampleages_model.rowCount() == 0:
                    if not query.exec(f'''INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) VALUES ({sample_id}, {sample_age_id})'''):
                        logger_setup.get_logger().critical(f'Unable to insert Samples_SampleAges: {query.lastError().text()}')
                        rollback_savepoint('before_update')
                        return
                    logger_setup.get_logger().info(f"Inserted SampleAgeID {sample_age_id} for SampleID {sample_id}")
                if default_age:
                    if not query.exec(f'''UPDATE Samples SET DefaultSampleAgeID = {sample_age_id} WHERE SampleID = {sample_id}'''):
                        logger_setup.get_logger().critical(f'Unable to update Sample default age: {query.lastError().text()}')
                        rollback_savepoint('before_update')
                        return
                    update_modified_timestamp('Samples', [sample_id])
                    logger_setup.get_logger().info(f"Updated DefaultSampleAgeID to {sample_age_id} for SampleID {sample_id}")
                if old_sample_age_id != sample_age_id:
                    if not query.exec(f'''DELETE FROM Samples_SampleAges WHERE SampleID = {sample_id} AND SampleAgeID = {old_sample_age_id}'''):
                        logger_setup.get_logger().critical(f'Unable to delete old SampleAgeID: {query.lastError().text()}')
                        rollback_savepoint('before_update')
                        return
            self.default_age_ids = []
            for item_id in self.item_ids:
                self.item_model.setFilter(f"{self.item_id_header} = {item_id}")
                if self.item_model.rowCount() > 0:
                    if self.table == 'Samples':
                        column = 8
                    else:
                        column = 1
                    default_age_id = self.item_model.index(0, column).data()
                    if default_age_id not in self.default_age_ids:
                        self.default_age_ids.append(default_age_id)
            self.updated = True
            release_savepoint('before_update')
            self.populate_age_dropdown()

    def update_age_tags(self, sample_age_id: int, combo: CheckableTreeCombobox | CheckableComboBox):
        logger_setup.get_logger().info(f"update_age_tags called with {combo.objectName()}")
        if not isinstance(combo, CheckableTreeCombobox) and not isinstance(combo, CheckableComboBox):
            logger_setup.get_logger().critical(f"Combo box is not CheckableTreeComboBox or CheckableComboBox")
            return False
        if isinstance(combo, CheckableTreeCombobox):
            model = find_tree_model(combo.model())
            if model:
                table = model.table
                id_header = get_headers(table)[0]
            else:
                logger_setup.get_logger().critical(f"Could not find model for combo box {combo.objectName()}")
                return False
            if not combo.treeView.model_edited:
                logger_setup.get_logger().info(f"No changes to {table}")
                return True
        elif isinstance(combo, CheckableComboBox):
            model = combo.model()
            table = model.table
            id_header = get_headers(table)[0]
        start_update_age_tags = time.time()
        many_to_many_model = QtS.QSqlTableModel()
        set_table(many_to_many_model, f"SampleAges_{table}")
        if len(self.item_ids) == 0:
            logger_setup.get_logger().info("No samples selected")
            return True
        else:
            logger_setup.get_logger().info(f"Updating {table} for {len(self.item_ids)} sample ages")
            query = QtS.QSqlQuery()
            if isinstance(model, CheckableTreeModel):
                checked_ids, partially_checked_ids, checked_indices, partially_checked_indices = model.traverse_checkable_tree(
                    QtC.QModelIndex())
            elif isinstance(model, CheckableSqlQueryModel):
                checked_ids, partially_checked_ids = model.return_checked_ids()
            if len(checked_ids) == 0 and len(partially_checked_ids) == 0:
                # None selected, so delete all associated with this SampleAgeID
                logger_setup.get_logger().info(f"No {table} selected for SampleAgeID {sample_age_id}")
                if not query.exec(f'''DELETE FROM SampleAges_{table} WHERE SampleAgeID = {sample_age_id}'''):
                    logger_setup.get_logger().critical(f'Unable to delete unchecked {table}: {query.lastError().text()}')
                    rollback_savepoint('before_update')
                    return False
                logger_setup.get_logger().info(f"Deleted {table} for SampleAgeID {sample_age_id}")
            else:
                many_to_many_model.setFilter(f"SampleAgeID = {sample_age_id}")
                if many_to_many_model.rowCount() == 0:
                    for age_id in checked_ids:
                        # If the age is checked, insert it if it doesn't exist
                        if not query.exec(
                                f'''INSERT INTO SampleAges_{table} (SampleAgeID, {id_header}) VALUES ({sample_age_id}, {age_id})'''):
                            if 'UNIQUE constraint failed' in query.lastError().text():
                                logger_setup.get_logger().info(
                                    f"{id_header} {age_id} already associated with SampleAgeID {sample_age_id}")
                            else:
                                logger_setup.get_logger().critical(
                                    f'Unable to insert checked {id_header} {age_id}: {query.lastError().text()}')
                                rollback_savepoint('before_update')
                                return False
                        logger_setup.get_logger().info(f"Inserted {id_header} {age_id} for SampleAgeID {sample_age_id}")
                for row in range(many_to_many_model.rowCount()):
                    age_id = many_to_many_model.data(many_to_many_model.index(row, 1), QtC.Qt.ItemDataRole.DisplayRole)
                    if age_id in checked_ids:
                        # If the age is checked, insert it if it doesn't exist
                        if not query.exec(f'''INSERT INTO SampleAges_{table} (SampleAgeID, {id_header}) VALUES ({sample_age_id}, {age_id})'''):
                            if 'UNIQUE constraint failed' in query.lastError().text():
                                logger_setup.get_logger().info(f"{id_header} {age_id} already associated with SampleAgeID {sample_age_id}")
                            else:
                                logger_setup.get_logger().critical(f'Unable to insert checked {id_header} {age_id}: {query.lastError().text()}')
                                rollback_savepoint('before_update')
                                return False
                        logger_setup.get_logger().info(f"Inserted {id_header} {age_id} for SampleAgeID {sample_age_id}")
                    elif age_id not in partially_checked_ids:
                        # If the age is unchecked, delete it if it exists
                        if not query.exec(f'''DELETE FROM SampleAges_{table} WHERE SampleAgeID = {sample_age_id} AND {id_header} = {age_id}'''):
                            logger_setup.get_logger().critical(f'Unable to delete unchecked {id_header} {age_id}: {query.lastError().text()}')
                            rollback_savepoint('before_update')
                            return False
                        logger_setup.get_logger().info(f"Deleted {id_header} {age_id} for SampleAgeID {sample_age_id}")
        end_update_age_tags = time.time()
        logger_setup.get_logger().info(f"Updated {table} in {end_update_age_tags - start_update_age_tags} seconds")
        return True

    def add_age(self):
        create_savepoint('before_add')
        query = QtS.QSqlQuery()
        # Add a new age with default values for units and a description
        if not query.exec(f'''INSERT INTO SampleAges (DirectAgeUnitID, DirectAgeErrorFormatID, SampleAgeDescription) 
                            VALUES ({settings.value('age_unit_id')}, {settings.value('age_error_format_id')}, 'New Sample Age')'''):
            errtxt = query.lastError().text()
            if 'UNIQUE constraint failed' in errtxt:
                # This age already exists, so let's find it and select it
                new_sample_age_table = QtS.QSqlQueryModel()
                new_sample_age_table.setQuery(f'''SELECT * FROM SampleAges WHERE DirectAgeUnitID = {self.direct_age_unit_comboBox.currentText()} AND DirectAgeErrorFormatID = {self.direct_age_error_format_comboBox.currentText()} AND SampleAgeDescription = 'New Sample Age' ''')
                if new_sample_age_table.rowCount() == 0:
                    logger_setup.get_logger().critical(f"Could not find new age")
                    return
                elif new_sample_age_table.rowCount() == 1:
                    sample_age_id = new_sample_age_table.data(new_sample_age_table.index(0, 0),
                                                               QtC.Qt.ItemDataRole.DisplayRole)
                elif new_sample_age_table.rowCount() > 1:
                    logger_setup.get_logger().info(f"Found more than one new age. Looking for matches with selected samples")
                    # Is there one that is already associated with the samples?
                    sample_age_id = None
                    for row in range(new_sample_age_table.rowCount()):
                        new_sample_age_id = new_sample_age_table.data(new_sample_age_table.index(row, 0),
                                                                   QtC.Qt.ItemDataRole.DisplayRole)
                        samples_sampleages_model = QtS.QSqlTableModel()
                        set_table(samples_sampleages_model, 'Samples_SampleAges')
                        if len(self.item_ids) > 1:
                            samples_sampleages_model.setFilter(f"SampleAgeID = {new_sample_age_id} and SampleID in {tuple(self.item_ids)}")
                        elif len(self.item_ids) == 1:
                            samples_sampleages_model.setFilter(f"SampleAgeID = {new_sample_age_id} and SampleID = {self.item_ids[0]}")
                        if samples_sampleages_model.rowCount() == 0:
                            logger_setup.get_logger().info(f"Existing new age ID {new_sample_age_id} is not associated with any samples")
                        else:
                            logger_setup.get_logger().info(f"Found existing new age ID {new_sample_age_id} associated with samples")
                            sample_age_id = new_sample_age_id
                            break
                    if sample_age_id is None:
                        # If none of the new ages are associated with the samples, just pick the first one
                        sample_age_id = new_sample_age_table.data(new_sample_age_table.index(0, 0),
                                                               QtC.Qt.ItemDataRole.DisplayRole)
            logger_setup.get_logger().critical(f"Error adding age: {errtxt}")
            return
        else:
            sample_age_id = query.lastInsertId()
        logger_setup.get_logger().info(f"Added age {sample_age_id}")
        for item_id in self.item_ids:
            if not query.exec(f'''INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) VALUES ({item_id}, {sample_age_id})'''):
                errtxt = query.lastError().text()
                if 'UNIQUE constraint failed' in errtxt:
                    logger_setup.get_logger().info(f"Sample {item_id} already has age {sample_age_id}")
                else:
                    logger_setup.get_logger().critical(f"Error adding age to sample {item_id}: {errtxt}")
                    return
            logger_setup.get_logger().info(f"Added age {sample_age_id} to sample {item_id}")
            sample_table = SQLiteTableModel(f"SELECT DefaultSampleAgeID FROM {self.table} WHERE {self.item_id_header} = {item_id}")
            if sample_table.rowCount() == 0:
                logger_setup.get_logger().critical(f"Sample {item_id} not found")
                return
            default_age_id = sample_table.data(sample_table.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            if default_age_id is None:
                if not query.exec(f'''UPDATE {self.table} SET DefaultSampleAgeID = {sample_age_id} WHERE {self.item_id_header} = {item_id}'''):
                    errtxt = query.lastError().text()
                    logger_setup.get_logger().critical(f"Error updating default age for sample {item_id}: {errtxt}")
                    return
                logger_setup.get_logger().info(f"Updated default age for sample {item_id} to {sample_age_id}")
                self.default_age_checkBox.setChecked(True)
        logger_setup.get_logger().info(f"Updating age fields for {self.table} with item IDs {self.item_ids}")
        release_savepoint('before_add')
        self.update_list(self.item_ids)
        self.edit_age_comboBox.setCurrentIndex(self.sample_age_model.rowCount() - 1)

    def add_popup(self, combo: QtW.QComboBox, action: QtG.QAction | None = None):
        if isinstance(combo.model(), TreeModel):
            table = combo.model().table
        else:
            table = combo.model().tableName()
        dlg_args = None
        dlg = None
        if table in SQLUtils.user_viewable_trees:
            indexes = combo.view().selectedIndexes()
            item_ids, parent_ids, parent_rows = get_selected_tree_ids(combo.model(), indexes)
            if action:
                if action.text() == 'Insert above':
                    row = parent_rows[0]
                    parent_id = parent_ids[0]
                    dlg_args = (table, parent_id, row)
                elif action.text() == 'Insert below':
                    row = parent_rows[0] + 1
                    parent_id = parent_ids[0]
                    dlg_args = (None, parent_id, row)
                elif action.text() == 'Add child':
                    parent_id = item_ids[0]
                    dlg_args = (None, parent_id)
                elif action.text() == 'Add parent':
                    dlg_args = (item_ids, parent_ids, parent_rows)
                elif action.text() == 'Add to end' or action.text() == 'Add':
                    dlg_args = (None, None)
            if dlg_args:
                dlg = AddTreeTags(table, *dlg_args)
        else:
            dlg = AddTags(table)
        if not dlg:
            return
        logger_setup.get_logger().info(f"Showing {table} add dialog")
        dlg.exec()
        self.populate_dropdowns()
        self.populate_fields()

    def edit_popup(self):
        combo = self.sender()
        if isinstance(combo.model(), TreeModel):
            table = combo.model().table
        else:
            table = combo.model().tableName()
        if table in SQLUtils.user_viewable_trees:
            dlg = EditTree(table)
        else:
            dlg = EditTable(table)
        if dlg is None:
            return
        logger_setup.get_logger().info(f"Showing {table} edit dialog")
        dlg.exec()
        self.parent().setFocus()
        self.populate_dropdowns()
        self.populate_fields()

    def clear_fields(self):
        self.disconnect_signals()
        self.default_age_checkBox.setChecked(False)
        self.edit_age_comboBox.setCurrentIndex(-1)
        self.direct_age_lineEdit.clear()
        self.direct_age_error_lineEdit.clear()
        self.direct_age_error_format_comboBox.setCurrentIndex(-1)
        self.oldest_direct_lineEdit.clear()
        self.youngest_direct_lineEdit.clear()
        self.direct_age_unit_comboBox.setCurrentIndex(-1)
        self.oldest_rel_comboBox.setCurrentIndex(-1)
        self.youngest_rel_comboBox.setCurrentIndex(-1)
        self.age_description_lineEdit.clear()
        self.age_constraint_comboBox.setCurrentIndex(-1)
        self.age_interpretation_comboBox.setCurrentIndex(-1)
        self.age_reference_comboBox.setCurrentIndex(-1)

    def enable_context(self, combo_box: CheckableComboBox | CheckableTreeCombobox):
        combo_box.enable_context_menu(True)
        combo_box.set_single_click(True)
        combo_box.edit_triggered.connect(self.handle_edit_triggered)

    def disable_context(self, combo_box: CheckableComboBox | CheckableTreeCombobox):
        combo_box.enable_context_menu(False)
        try:
            combo_box.edit_triggered.disconnect(self.handle_edit_triggered)
        except TypeError:
            pass

    def handle_edit_triggered(self, combo_box: CheckableComboBox):
        model = combo_box.model()
        table = model.tableName()
        if table == 'SampleAges':
            self.add_age()
        if isinstance(model, TreeModel):
            table_model = QtS.QSqlTableModel()
            set_table(table_model, table)
            dlg = EditTree(table_model, table)
        elif isinstance(model, QtS.QSqlTableModel | QtS.QSqlQueryModel):
            dlg = EditTable(table)
        else:
            print(f'Unknown model type: {type(model)}')
            return
        dlg.exec()
        self.populate_dropdowns()
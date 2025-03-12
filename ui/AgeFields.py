from cgitb import reset

import PyQt6
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6.uic import loadUi
from Functions.Widget_classes import (
    TreeModel, CheckableTreeCombobox, CheckableTreeModel, CheckableTreeView, set_table, SampleAgeTableModel,
    CheckableSqlTableModel,
    FontDelegate, get_name_column, set_comboBox_text, show_column, CheckableComboBox, CheckableSqlQueryModel,
    get_selected_tree_ids, find_tree_model, get_headers, add_tree_popup, populate_combo_box, save_expanded_state,
    restore_expanded_state, SQLiteTableModel
)
from Functions import SQLUtils
from Functions.Settings_manager import settings
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Check_triggers import validate_insert, validate_update, update_modified_timestamp
from Functions.Alter_database import convert_sample_age
import Functions.Database_views as DB_views
from ui.EditTree import EditTree
from ui.EditTable import EditTable
from ui.AddTreeTags import AddTreeTags
from ui.AddTags import AddTags
import logger_setup
import time


class AgeFields(QtW.QWidget):
    def __init__(self, table: str, sample_ids: list):
        super().__init__()

        logger_setup.get_logger().info('Starting AgeFields')
        age_ui_file = "ui/AgeFields.ui"
        loadUi(age_ui_file, self)
        self.table = table
        self.sample_ids = sample_ids
        self.sample_age_ids = []
        self.updated = False
        self.add_age_pushButton.setAutoDefault(False)
        self.msg = QtW.QMessageBox(self)

        self.sample_model = QtS.QSqlTableModel()
        self.sample_age_model = SampleAgeTableModel()
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
        self.age_reference_model = CheckableSqlQueryModel()
        self.text_change_timer = QtC.QTimer()
        self.text_change_timer.setSingleShot(True)
        self.text_change_timer.timeout.connect(self.update_age_unit)

        self.sample_ages = []
        self.default_age_ids = []
        self.sample_id_header = get_headers(table)[0]

        self.add_age_pushButton.clicked.connect(self.add_age)
        self.direct_age_unit_comboBox.currentIndexChanged.connect(self.update_age_unit)
        self.direct_unit_comboBox.currentIndexChanged.connect(self.update_age_unit)

        QtC.QTimer.singleShot(0, self.set_focus)

        self.update_list(self.sample_ids)

    def update_age_unit(self):
        sender = self.sender()
        if sender == self.direct_age_unit_comboBox:
            if self.direct_age_unit_comboBox.currentIndex() != self.direct_unit_comboBox.currentIndex():
                self.direct_unit_comboBox.setCurrentIndex(self.direct_age_unit_comboBox.currentIndex())
        elif sender == self.direct_unit_comboBox:
            if self.direct_unit_comboBox.currentIndex() != self.direct_age_unit_comboBox.currentIndex():
                self.direct_age_unit_comboBox.setCurrentIndex(self.direct_unit_comboBox.currentIndex())
        else:
            return

    def update_list(self, sample_ids):
        logger_setup.get_logger().info(f"Populating age fields for {self.table} with sample IDs {self.sample_ids}")
        self.sample_ids = sample_ids
        self.clear_fields() # Also disconnects signals
        self.populate_dropdowns()
        self.populate_age_dropdown()
        self.populate_fields()
        self.connect_signals()

    def populate_dropdowns(self):
        start_populate_dropdowns_time = time.time()
        logger_setup.get_logger().info("Populating age dropdowns")
        self.disconnect_signals()
        set_table(self.sample_model, self.table)
        self.sample_id_header = self.sample_model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        set_table(self.age_model, 'Ages')
        set_table(self.direct_age_unit_model, 'AgeUnits')
        set_table(self.direct_age_error_model, 'ErrorFormats')
        # self.oldest_age_tree.setSourceModel(self.age_model)
        # self.youngest_age_tree.setSourceModel(self.age_model)
        # set_table(self.age_constraint_model, 'AgeConstraints')
        # self.age_constraint_tree.setSourceModel(self.age_constraint_model)
        # set_table(self.age_interpretation_model, 'AgeInterpretations')
        # self.age_interpretation_tree.setSourceModel(self.age_interpretation_model)
        # self.age_reference_model.setQuery('SELECT * FROM ReferenceView')

        populate_combo_box(self.direct_unit_comboBox, **{'table': 'AgeUnits', 'column': 'AgeUnitAbbreviation'})
        populate_combo_box(self.direct_age_unit_comboBox, **{'table': 'AgeUnits', 'column': 'AgeUnitAbbreviation'})
        populate_combo_box(self.direct_age_error_format_comboBox, **{'table': 'ErrorFormats', 'column': 'ErrorFormatAbbreviation'})
        populate_combo_box(self.oldest_rel_comboBox, **{'table': 'Ages'})
        populate_combo_box(self.youngest_rel_comboBox, **{'table': 'Ages'})
        self.age_constraint_comboBox.model_modifiable = True
        self.age_constraint_comboBox.enable_context_menu(True)
        populate_combo_box(self.age_constraint_comboBox, **{'table': 'AgeConstraints'})
        self.age_interpretation_comboBox.model_modifiable = True
        self.age_interpretation_comboBox.enable_context_menu(True)
        populate_combo_box(self.age_interpretation_comboBox, **{'table': 'AgeInterpretations'})
        self.age_reference_comboBox.model_modifiable = True
        self.age_reference_comboBox.enable_context_menu(True)
        populate_combo_box(self.age_reference_comboBox, **{'query': 'SELECT * FROM ReferenceView'})
        end_populate_dropdowns_time = time.time()
        logger_setup.get_logger().info(f"Populated age dropdowns in {end_populate_dropdowns_time - start_populate_dropdowns_time} seconds")

    def populate_age_dropdown(self):
        start_populate_age_dropdown_time = time.time()
        logger_setup.get_logger().info("Populating sample age dropdown")
        self.disconnect_signals()
        samples_sampleage_model = QtS.QSqlTableModel()
        sample_model = QtS.QSqlQueryModel()
        set_table(samples_sampleage_model, 'Samples_SampleAges')
        if len(self.sample_ids) > 1:
            samples_sampleage_model.setFilter(f'SampleID in {tuple(self.sample_ids)}')
            sample_model.setQuery(
                f'SELECT DefaultSampleAgeID FROM {self.table} WHERE {self.sample_id_header} in {tuple(self.sample_ids)}')
        elif len(self.sample_ids) == 1:
            samples_sampleage_model.setFilter(f'SampleID = {self.sample_ids[0]}')
            sample_model.setQuery(
                f'SELECT DefaultSampleAgeID FROM {self.table} WHERE {self.sample_id_header} = {self.sample_ids[0]}')
        else:
            samples_sampleage_model.setFilter('')
            sample_model.setQuery(f'SELECT DefaultSampleAgeID FROM {self.table}')
        if samples_sampleage_model.rowCount() == 0:
            logger_setup.get_logger().info(f"No ages for selected samples {self.sample_ids}")
            self.sample_ages = []
            self.default_age_ids = []
            self.sample_age_model = SampleAgeTableModel()
            self.edit_age_comboBox.setModel(self.sample_age_model)
            return
        self.sample_ages = []
        self.default_age_ids = []
        for row in range(sample_model.rowCount()):
            default_age_id = sample_model.index(row, 0).data()
            if default_age_id and default_age_id not in self.default_age_ids:
                self.default_age_ids.append(default_age_id)
        for row in range(samples_sampleage_model.rowCount()):
            self.sample_ages.append(samples_sampleage_model.index(row, 1).data())
        self.sample_age_model = SampleAgeTableModel()
        if len(self.sample_ages) > 1:
            self.sample_age_model.setQuery(f'{self.sample_age_model.default_query} WHERE SampleAgeID in {tuple(self.sample_ages)}')
        elif len(self.sample_ages) == 1:
            self.sample_age_model.setQuery(f'{self.sample_age_model.default_query} WHERE SampleAgeID = {self.sample_ages[0]}')
            # If there is only one age, select it and make it the default
            selected_id = self.sample_age_model.data(self.sample_age_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            self.sample_age_model.checked_ids = [selected_id]
            if selected_id not in self.default_age_ids:
                self.default_age_ids.append(selected_id)
        display_col = get_name_column('SampleAges')
        for row in range(self.sample_age_model.rowCount()):
            if self.sample_age_model.index(row, 0).data() in self.default_age_ids:
                # Make the text at that row bold
                self.sample_age_model.make_bold(self.sample_age_model.index(row, display_col))
            else:
                self.sample_age_model.make_not_bold(self.sample_age_model.index(row, display_col))
        self.edit_age_comboBox: CheckableComboBox
        self.edit_age_comboBox.setModel(self.sample_age_model)
        show_column(self.edit_age_comboBox, 'SampleAgeDisplay')
        self.enable_context(self.edit_age_comboBox)
        end_populate_age_dropdown_time = time.time()
        logger_setup.get_logger().info(f"Populated sample age dropdown in {end_populate_age_dropdown_time - start_populate_age_dropdown_time} seconds")

    def check_focus(self):
        if self.direct_age_groupBox.any_child_has_focus() and self.direct_age_groupBox.edited:
            self.direct_age_groupBox.focusLost.emit()
        elif self.relative_age_groupBox.any_child_has_focus() and self.relative_age_groupBox.edited:
            self.relative_age_groupBox.focusLost.emit()
        elif self.age_information_groupBox.any_child_has_focus() and self.age_information_groupBox.edited:
            self.age_information_groupBox.focusLost.emit()

    def set_focus(self):
        if self.sample_age_model.rowCount() == 0:
            self.disable_groups()
            self.add_age_pushButton.setFocus()
            self.add_age_pushButton.setAutoDefault(True)

    def connect_signals(self):
        # Connect signals and slots
        logger_setup.get_logger().info("Connecting signals")
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
        if len(self.sample_age_model.checked_ids) == 0:
            sample_age_id = None
            reset_fields = True
        else:
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
        column_names = get_headers('SampleAges')
        if len(self.sample_ages) > 1:
            query_where_str = f' WHERE SampleAgeID in {tuple(self.sample_ages)}'
        elif len(self.sample_ages) == 1:
            query_where_str = f' WHERE SampleAgeID = {self.sample_ages[0]}'
        else:
            query_where_str = ''
        sample_age_table = SQLiteTableModel(f'SELECT * FROM SampleAges{query_where_str}')
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
        self.populate_checks('SampleAges_AgeConstraints', self.age_constraint_comboBox, sample_age_id)
        self.populate_checks('SampleAges_AgeInterpretations', self.age_interpretation_comboBox, sample_age_id)
        self.populate_checks('SampleAges_References', self.age_reference_comboBox, sample_age_id)

        end_populate_fields_time = time.time()
        logger_setup.get_logger().info(f"Populated age fields in {end_populate_fields_time - start_populate_fields_time} seconds")

    def populate_checks(self, many_to_many_table: str, combo: QtW.QComboBox, sample_age_id: int = None):
        logger_setup.get_logger().info(f"Populating checks for {many_to_many_table}")
        start_populate_checks_time = time.time()
        self.disconnect_signals()
        many_to_many_model = QtS.QSqlTableModel()
        many_to_many_model.setTable(many_to_many_table)
        many_to_many_model.select()
        samples = []
        text = ""
        if isinstance(combo, CheckableTreeCombobox):
            model, indexes = find_tree_model(combo.model(), None)
            col = 0  # Name column is always placed in the first column
            tag_id_header = model.source_model.record().fieldName(0)
            id_col = 1  # ID column is always placed in the second column
        else:
            model = combo.model()
            col = get_name_column(model.tableName())
            tag_id_header = model.record().fieldName(0)
            id_col = 0  # ID column is always in the first column
        if not sample_age_id:
            logger_setup.get_logger().info("No age selected, so uncheck everything")
            if isinstance(combo, CheckableTreeCombobox):
                model.blockSignals(True)
                # recursively uncheck everything
                def uncheck_all(model: CheckableTreeModel, index: QtC.QModelIndex):
                    for row in range(model.rowCount(index)):
                        model_index = model.index(row, col, index)
                        model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                        uncheck_all(model, model_index)
                uncheck_all(model, QtC.QModelIndex())
                model.blockSignals(False)
            else:
                for row in range(model.rowCount()):
                    model_index = model.index(row, col)
                    model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                    if model.lastError().text():
                        logger_setup.get_logger().critical(
                            f"Error setting unchecked for {model.tableName()}: {model.lastError().text()}")
            logger_setup.get_logger().info("Unchecked everything")
            combo.setCurrentText(text)
        else:
            logger_setup.get_logger().info(f"Checking {many_to_many_table}")
            if isinstance(combo, CheckableTreeCombobox):
                model.blockSignals(True)
                # recursively check data
                def check_data(model: CheckableTreeModel, index: QtC.QModelIndex):
                    for row in range(model.rowCount(index)):
                        model_index = model.index(row, col, index)
                        id_index = model.index(row, id_col, index)
                        tag_id = model.data(id_index, QtC.Qt.ItemDataRole.DisplayRole)
                        many_to_many_model.setFilter(f"SampleAgeID = {sample_age_id} AND {tag_id_header} = {tag_id}")
                        if many_to_many_model.rowCount() > 0:
                            # All samples have this tag
                            model.setData(model_index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                            samples.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
                        else:
                            # No samples have this tag
                            model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                        check_data(model, model_index)
                check_data(model, QtC.QModelIndex())
            else:
                for row in range(model.rowCount()):
                    tag_id = model.index(row, id_col).data()
                    many_to_many_model.setFilter(f"SampleAgeID = {sample_age_id} AND {tag_id_header} = {tag_id}")
                    model_index = model.index(row, col)
                    if many_to_many_model.rowCount() > 0:
                        # Selected sample age has this tag
                        model.setData(model_index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                        if model.lastError().text():
                            logger_setup.get_logger().critical(
                                f"Error setting checked for {model.tableName()}: {model.lastError().text()}")
                        samples.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
                    else:
                        # No samples have this tag
                        model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                        if model.lastError().text():
                            logger_setup.get_logger().critical(
                                f"Error setting unchecked for {model.tableName()}: {model.lastError().text()}")
        if not samples:
            # Sample age does not have these tags
            text = ""
        else:
            # Sample age has these tags
            text = ', '.join(samples)
        if isinstance(combo, CheckableTreeCombobox):
            model.blockSignals(False)
            combo.treeView.connect_edited_signal()
        if not text:
            text = combo.placeholderText()
        combo.setCurrentText(text)
        end_populate_checks_time = time.time()
        logger_setup.get_logger().info(
            f"Populated checks for {many_to_many_table} in {end_populate_checks_time - start_populate_checks_time} seconds")

    def update_age(self):
        logger_setup.get_logger().info("Updating age")
        if len(self.sample_ids) == 0:
            logger_setup.get_logger().info("No samples selected to update")
            return True
        row = self.edit_age_comboBox.currentIndex()
        sample_age_id = self.sample_age_model.data(self.sample_age_model.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        if not sample_age_id:
            logger_setup.get_logger().info("No age selected to update")
            return False

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
                if samples_sampleages_model.index(row, 0).data() not in self.sample_ids:
                    logger_setup.get_logger().info(f"SampleAgeID {sample_age_id} is not associated with all selected samples")
                    self.msg.setIcon(QtW.QMessageBox.Icon.Question)
                    self.msg.setText(f"SampleAgeID {sample_age_id} is not associated with all selected samples. Do you want to associate it with all selected samples?")
                    self.msg.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
                    response = self.msg.exec()
                    if response == QtW.QMessageBox.StandardButton.Yes:
                        logger_setup.get_logger().info("User chose to associate SampleAgeID with all selected samples")
                    else:
                        logger_setup.get_logger().info("User chose not to associate SampleAgeID with all selected samples")
                        return False
        age_columns = ['DirectAge', 'DirectAgeError', 'DirectAgeUnitID', 'DirectAgeErrorFormatID', 'OldestDirectAge', 'YoungestDirectAge',
        'OldestAgeID', 'YoungestAgeID', 'SampleAgeDescription']
        qage_columns = ', '.join(age_columns)
        age_values = [f'{direct_age}', f'{direct_age_error}', f'{direct_age_unit_id}', f'{direct_age_error_format_id}', f'{oldest_direct}',
                      f'{youngest_direct}', f'{oldest_rel_id}', f'{youngest_rel_id}', f'{age_description}']
        query = QtS.QSqlQuery()
        if not query.exec(f"SELECT {qage_columns} FROM SampleAges WHERE SampleAgeID = {sample_age_id}"):
            logger_setup.get_logger().critical(f'Unable to get SampleAges: {query.lastError().text()}')
            return False
        if not query.next():
            logger_setup.get_logger().critical(f'No results for SampleAgeID {sample_age_id}')
            return False
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
                return False
            logger_setup.get_logger().info(f"Valid age information")
            sql_placeholders = ', '.join(['?' for col in age_columns])
            query.prepare(f'''UPDATE SampleAges SET ({qage_columns}) = ({sql_placeholders}) WHERE SampleAgeID = {sample_age_id}''')
            for i in range(len(age_values)):
                query.bindValue(i, age_values[i])
            if not query.exec():
                logger_setup.get_logger().critical(f'Unable to update SampleAges: {query.lastError().text()}')
                rollback_savepoint('before_update')
                return False
            update_modified_timestamp('SampleAges', [sample_age_id])
            logger_setup.get_logger().info(f"Updated age information for SampleAgeID {sample_age_id}")
            if not convert_sample_age(sample_age_id):
                rollback_savepoint('before_update')
                return False
        if not self.update_age_tags(sample_age_id, self.age_constraint_comboBox):
            return False
        if not self.update_age_tags(sample_age_id, self.age_interpretation_comboBox):
            return False
        if not self.update_age_tags(sample_age_id, self.age_reference_comboBox):
            return False
        for sample_id in self.sample_ids:
            samples_sampleages_model = QtS.QSqlTableModel()
            set_table(samples_sampleages_model, 'Samples_SampleAges')
            samples_sampleages_model.setFilter(f"SampleID = {sample_id} AND SampleAgeID = {sample_age_id}")
            if samples_sampleages_model.rowCount() == 0:
                if not query.exec(f'''INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) VALUES ({sample_id}, {sample_age_id})'''):
                    logger_setup.get_logger().critical(f'Unable to insert Samples_SampleAges: {query.lastError().text()}')
                    rollback_savepoint('before_update')
                    return False
                logger_setup.get_logger().info(f"Inserted SampleAgeID {sample_age_id} for SampleID {sample_id}")
            if default_age:
                if not query.exec(f'''UPDATE Samples SET DefaultSampleAgeID = {sample_age_id} WHERE SampleID = {sample_id}'''):
                    logger_setup.get_logger().critical(f'Unable to update Sample default age: {query.lastError().text()}')
                    rollback_savepoint('before_update')
                    return False
                update_modified_timestamp('Samples', [sample_id])
                logger_setup.get_logger().info(f"Updated DefaultSampleAgeID to {sample_age_id} for SampleID {sample_id}")
            if old_sample_age_id != sample_age_id:
                if not query.exec(f'''DELETE FROM Samples_SampleAges WHERE SampleID = {sample_id} AND SampleAgeID = {old_sample_age_id}'''):
                    logger_setup.get_logger().critical(f'Unable to delete old SampleAgeID: {query.lastError().text()}')
                    rollback_savepoint('before_update')
                    return False
        self.default_age_ids = []
        for sample_id in self.sample_ids:
            self.sample_model.setFilter(f"{self.sample_id_header} = {sample_id}")
            if self.sample_model.rowCount() > 0:
                if self.table == 'Samples':
                    column = 8
                else:
                    column = 1
                default_age_id = self.sample_model.index(0, column).data()
                if default_age_id not in self.default_age_ids:
                    self.default_age_ids.append(default_age_id)
        self.updated = True
        release_savepoint('before_update')
        self.populate_age_dropdown()
        return True

    def update_age_tags(self, sample_age_id: int, combo: CheckableTreeCombobox | CheckableComboBox):
        logger_setup.get_logger().info(f"update_age_tags called with {combo.objectName()}")
        if not isinstance(combo, CheckableTreeCombobox) and not isinstance(combo, CheckableComboBox):
            logger_setup.get_logger().critical(f"Combo box is not CheckableTreeComboBox or CheckableComboBox")
            return False
        if isinstance(combo, CheckableTreeCombobox):
            model, indexes = find_tree_model(combo.model(), None)
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
            table = model.tableName()
            id_header = get_headers(table)[0]
        start_update_age_tags = time.time()
        many_to_many_model = QtS.QSqlTableModel()
        set_table(many_to_many_model, f"SampleAges_{table}")
        if len(self.sample_ids) == 0:
            logger_setup.get_logger().info("No samples selected")
            return True
        current_values = []
        if len(self.sample_ids) > 1:
            where_sql = f'IN {tuple(self.sample_ids)}'
        else:
            where_sql = f'= {self.sample_ids[0]}'
        many_to_many_model.setFilter(f"SampleAgeID = {sample_age_id} AND {id_header} {where_sql}")
        for row in range(many_to_many_model.rowCount()):
            current_values.append(many_to_many_model.data(many_to_many_model.index(row, 1), QtC.Qt.ItemDataRole.DisplayRole))
        logger_setup.get_logger().info(f"Updating {table} for {len(self.sample_ids)} sample ages")
        query = QtS.QSqlQuery()
        if isinstance(model, CheckableTreeModel):
            checked_ids, partially_checked_ids, checked_indices, partially_checked_indices = model.traverse_checkable_tree(
                QtC.QModelIndex())
        elif isinstance(model, CheckableSqlTableModel | CheckableSqlQueryModel):
            checked_ids, partially_checked_ids = model.return_checked_ids()
        if current_values == checked_ids:
            logger_setup.get_logger().info(f"No changes to {table}")
            return True
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
                        if len(self.sample_ids) > 1:
                            samples_sampleages_model.setFilter(f"SampleAgeID = {new_sample_age_id} and SampleID in {tuple(self.sample_ids)}")
                        elif len(self.sample_ids) == 1:
                            samples_sampleages_model.setFilter(f"SampleAgeID = {new_sample_age_id} and SampleID = {self.sample_ids[0]}")
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
        for sample_id in self.sample_ids:
            if not query.exec(f'''INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) VALUES ({sample_id}, {sample_age_id})'''):
                errtxt = query.lastError().text()
                if 'UNIQUE constraint failed' in errtxt:
                    logger_setup.get_logger().info(f"Sample {sample_id} already has age {sample_age_id}")
                else:
                    logger_setup.get_logger().critical(f"Error adding age to sample {sample_id}: {errtxt}")
                    return
            logger_setup.get_logger().info(f"Added age {sample_age_id} to sample {sample_id}")
            query.prepare(f"SELECT DefaultSampleAgeID FROM {self.table} WHERE {self.sample_id_header} = :sample_id")
            query.bindValue(':sample_id', sample_id)
            if not query.exec():
                logger_setup.get_logger().critical(f"Error getting default age for sample {sample_id}: {query.lastError().text()}")
                return
            if not query.next():
                logger_setup.get_logger().critical(f"Sample {sample_id} not found")
                return
            default_age_id = query.value(0)
            if default_age_id is None:
                if not query.exec(f'''UPDATE {self.table} SET DefaultSampleAgeID = {sample_age_id} WHERE {self.sample_id_header} = {sample_id}'''):
                    errtxt = query.lastError().text()
                    logger_setup.get_logger().critical(f"Error updating default age for sample {sample_id}: {errtxt}")
                    return
                logger_setup.get_logger().info(f"Updated default age for sample {sample_id} to {sample_age_id}")
                self.enable_groups()
                self.default_age_checkBox.setChecked(True)
        logger_setup.get_logger().info(f"Updating age fields for {self.table} with sample IDs {self.sample_ids}")
        release_savepoint('before_add')
        self.enable_groups()
        self.update_list(self.sample_ids)
        self.edit_age_comboBox.setCurrentIndex(self.sample_age_model.rowCount() - 1)

    def add_popup(self, combo: QtW.QComboBox, action: QtG.QAction | None = None):
        if isinstance(combo.model(), TreeModel):
            table = combo.model().table
        else:
            table = combo.model().tableName()
        dlg = None
        if table in SQLUtils.user_viewable_trees:
            save_expanded_state(table, combo.model(), combo.view())
            dlg_args = add_tree_popup(combo.view(), combo.model(), action)
            if dlg_args:
                dlg = AddTreeTags(table, **dlg_args)
        else:
            dlg = AddTags(table)
        if not dlg:
            return
        logger_setup.get_logger().info(f"Showing {table} add dialog")
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
            # Update this combo box
            populate_combo_box(combo, **{'table': table})
            if isinstance(combo, CheckableTreeCombobox):
                restore_expanded_state(table, combo.model(), combo.view())
            self.populate_checks(f'Samples_{table}', combo)

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

    def disable_groups(self):
        self.default_age_checkBox.setEnabled(False)
        self.edit_age_comboBox.setEnabled(False)
        self.direct_age_groupBox.setEnabled(False)
        self.relative_age_groupBox.setEnabled(False)
        self.age_information_groupBox.setEnabled(False)

    def enable_groups(self):
        self.default_age_checkBox.setEnabled(True)
        self.edit_age_comboBox.setEnabled(True)
        self.direct_age_groupBox.setEnabled(True)
        self.relative_age_groupBox.setEnabled(True)
        self.age_information_groupBox.setEnabled(True)

    def clear_fields(self):
        self.disconnect_signals()
        self.default_age_checkBox.setChecked(False)
        self.sample_age_model.clear_checks()
        self.edit_age_comboBox.setCurrentText(self.edit_age_comboBox.placeholderText())
        self.direct_age_lineEdit.clear()
        self.direct_age_error_lineEdit.clear()
        self.direct_age_error_format_comboBox.setCurrentText(settings.value('age_error_format_abbreviation'))
        self.oldest_direct_lineEdit.clear()
        self.youngest_direct_lineEdit.clear()
        self.direct_age_unit_comboBox.setCurrentText(settings.value('age_unit_abbreviation'))
        self.oldest_rel_comboBox.setCurrentText(self.oldest_rel_comboBox.placeholderText())
        self.youngest_rel_comboBox.setCurrentText(self.youngest_rel_comboBox.placeholderText())
        self.age_description_lineEdit.clear()
        self.age_constraint_comboBox.setCurrentText(self.age_constraint_comboBox.placeholderText())
        self.age_interpretation_comboBox.setCurrentText(self.age_interpretation_comboBox.placeholderText())
        self.age_reference_comboBox.setCurrentText(self.age_reference_comboBox.placeholderText())

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
            model = QtS.QSqlTableModel()
            set_table(model, table)
            dlg = EditTree(model, table)
        elif isinstance(model, QtS.QSqlTableModel | QtS.QSqlQueryModel):
            dlg = EditTable(table)
        else:
            logger_setup.get_logger().info(f'Unknown model type: {type(model)}')
            return
        dlg.exec()
        self.populate_dropdowns()
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
    restore_expanded_state, SQLiteTableModel, populate_tree_model_checks
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
        self.sample_age_id = None
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
        self.focus_timer = QtC.QTimer(self)
        self.focus_timer.setSingleShot(True)
        self.focus_timer.timeout.connect(self.update_age)
        self._isApplicationFocused = True
        QtW.QApplication.instance().installEventFilter(self)
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
        self.oldest_rel_comboBox.model_modifiable = False
        self.oldest_rel_comboBox.enable_context_menu(False)
        self.oldest_rel_comboBox.set_single_click(True)
        populate_combo_box(self.oldest_rel_comboBox, **{'table': 'Ages'})
        self.youngest_rel_comboBox.model_modifiable = False
        self.youngest_rel_comboBox.enable_context_menu(False)
        self.youngest_rel_comboBox.set_single_click(True)
        populate_combo_box(self.youngest_rel_comboBox, **{'table': 'Ages'})
        self.age_constraint_comboBox.model_modifiable = True
        self.age_constraint_comboBox.enable_context_menu(True)
        self.age_constraint_comboBox.set_single_click(True)
        populate_combo_box(self.age_constraint_comboBox, **{'table': 'AgeConstraints'})
        self.age_interpretation_comboBox.model_modifiable = True
        self.age_interpretation_comboBox.enable_context_menu(True)
        self.age_interpretation_comboBox.set_single_click(True)
        populate_combo_box(self.age_interpretation_comboBox, **{'table': 'AgeInterpretations'})
        self.age_reference_comboBox.model_modifiable = True
        self.age_reference_comboBox.enable_context_menu(True)
        self.age_reference_comboBox.set_single_click(True)
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
            QtC.QTimer.singleShot(0, self.set_focus)
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

    def eventFilter(self, obj, event):
        if event.type() == QtC.QEvent.Type.ApplicationDeactivate:
            self._isApplicationFocused = False
        elif event.type() == QtC.QEvent.Type.ApplicationActivate:
            self._isApplicationFocused = True
        return super().eventFilter(obj, event)

    def check_focus(self):
        if self.direct_age_groupBox.any_child_has_focus() and self.direct_age_groupBox.edited:
            self.direct_age_groupBox.focusLost.emit()
        elif self.relative_age_groupBox.any_child_has_focus() and self.relative_age_groupBox.edited:
            self.relative_age_groupBox.focusLost.emit()

    def set_focus(self):
        if self.sample_age_model.rowCount() == 0:
            self.clear_fields()
            self.disable_groups()
            self.add_age_pushButton.setFocus()
            self.add_age_pushButton.setAutoDefault(True)

    def focus_lost_delay(self):
        if self._isApplicationFocused:
            self.lost_group_box = self.sender()
            self.focus_timer.start(100)

    def connect_signals(self):
        # Connect signals and slots
        logger_setup.get_logger().info("Connecting signals")
        self.edit_age_comboBox.currentTextChanged.connect(self.populate_fields)
        self.default_age_checkBox.clicked.connect(self.update_age)
        self.direct_age_groupBox.connect_child_signals()
        self.direct_age_groupBox.focusLost.connect(self.focus_lost_delay)
        self.relative_age_groupBox.connect_child_signals()
        self.relative_age_groupBox.focusLost.connect(self.focus_lost_delay)
        self.age_description_lineEdit.editingFinished.connect(self.update_age)
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
        try:
            self.age_description_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass

    def populate_fields(self):
        logger_setup.get_logger().info("Populating age fields")
        self.disconnect_signals()
        start_populate_fields_time = time.time()
        reset_fields = False
        self.edit_age_comboBox.setItemDelegate(FontDelegate(self.edit_age_comboBox))
        if len(self.sample_age_model.checked_ids) == 0:
            self.sample_age_id = None
            reset_fields = True
        else:
            self.sample_age_id = self.sample_age_model.checked_ids[0]
            if not self.sample_age_id:
                # If no age is selected, select the first one
                self.sample_age_model.setData(self.sample_age_model.index(0, 0), QtC.Qt.CheckState.Checked,
                                              QtC.Qt.ItemDataRole.CheckStateRole)
                self.sample_age_id = self.sample_age_model.data(self.sample_age_model.index(0, 0),
                                                           QtC.Qt.ItemDataRole.DisplayRole)
            for row in range(self.sample_age_model.rowCount()):
                if self.sample_age_model.index(row, 0).data() == self.sample_age_id:
                    sample_age_row = row
                    break
            if self.sample_age_id in self.default_age_ids:
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
        sample_age_table = QtS.QSqlQueryModel()
        sample_age_table.setQuery(f'SELECT * FROM SampleAges{query_where_str}')
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
            if 'Calculated' in header:
                pass
            elif 'ErrorFormatID' in header:
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
                    id = text
                    self.age_model.setFilter(f'AgeID = {id}')
                    if self.age_model.rowCount() > 0:
                        text = self.age_model.data(self.age_model.index(0, 3), QtC.Qt.ItemDataRole.DisplayRole)
                    else:
                        text = ""
                    self.oldest_rel_comboBox.setCurrentText(text)
            elif 'YoungestAgeID' in header:
                if not text:
                    self.youngest_rel_comboBox.setCurrentText(self.youngest_rel_comboBox.placeholderText())
                else:
                    id = text
                    self.age_model.setFilter(f'AgeID = {id}')
                    if self.age_model.rowCount() > 0:
                        text = self.age_model.data(self.age_model.index(0, 3), QtC.Qt.ItemDataRole.DisplayRole)
                    else:
                        text = ""
                    self.youngest_rel_comboBox.setCurrentText(text)
            elif 'SampleAgeDescription' in header:
                if not text:
                    self.age_description_lineEdit.setText(self.age_description_lineEdit.placeholderText())
                else:
                    self.age_description_lineEdit.setText(f'{text}')
            elif 'SampleAgeDisplay' in header:
                self.edit_age_comboBox.setCurrentText(text)


        # Age IDs
        populate_tree_model_checks(self.oldest_rel_comboBox.model(), [self.sample_age_id], 'SampleAges', 'OldestAgeID')
        populate_tree_model_checks(self.youngest_rel_comboBox.model(), [self.sample_age_id], 'SampleAges', 'YoungestAgeID')

        # Age tags
        self.populate_checks('SampleAges_AgeConstraints', self.age_constraint_comboBox)
        self.populate_checks('SampleAges_AgeInterpretations', self.age_interpretation_comboBox)
        self.populate_checks('SampleAges_References', self.age_reference_comboBox)

        end_populate_fields_time = time.time()
        logger_setup.get_logger().info(f"Populated age fields in {end_populate_fields_time - start_populate_fields_time} seconds")

    def populate_checks(self, many_to_many_table: str, combo: QtW.QComboBox):
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
        if not self.sample_age_id:
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
                        many_to_many_model.setFilter(f"SampleAgeID = {self.sample_age_id} AND {tag_id_header} = {tag_id}")
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
                    many_to_many_model.setFilter(f"SampleAgeID = {self.sample_age_id} AND {tag_id_header} = {tag_id}")
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
        if not self.sample_age_id:
            logger_setup.get_logger().info("No age selected to update")
            return False
        if not self.lost_group_box.edited:
            logger_setup.get_logger().info(f"Age fields not edited")
            return
        logger_setup.get_logger().info("Collecting input age information")
        default_age = self.default_age_checkBox.isChecked()
        direct_age = self.direct_age_lineEdit.text()
        # if direct_age != '':
        #     try:
        #         direct_age = float(self.direct_age_lineEdit.text())
        #         if int(direct_age) == direct_age:
        #             direct_age = int(direct_age)
        #     except ValueError:
        #         logger_setup.get_logger().error("Invalid direct age input")
        #         return False
        # direct_age_error = self.direct_age_error_lineEdit.text()
        # if direct_age_error != '':
        #     try:
        #         direct_age_error = float(self.direct_age_error_lineEdit.text())
        #         if int(direct_age_error) == direct_age_error:
        #             direct_age_error = int(direct_age_error)
        #     except ValueError:
        #         logger_setup.get_logger().error("Invalid direct age error input")
        #         return False
        # oldest_direct = self.oldest_direct_lineEdit.text()
        # if oldest_direct != '':
        #     try:
        #         oldest_direct = float(self.oldest_direct_lineEdit.text())
        #         if int(oldest_direct) == oldest_direct:
        #             oldest_direct = int(oldest_direct)
        #     except ValueError:
        #         logger_setup.get_logger().error("Invalid oldest direct age input")
        #         return False
        # youngest_direct = self.youngest_direct_lineEdit.text()
        # if youngest_direct != '':
        #     try:
        #         youngest_direct = float(self.youngest_direct_lineEdit.text())
        #         if int(youngest_direct) == youngest_direct:
        #             youngest_direct = int(youngest_direct)
        #     except ValueError:
        #         logger_setup.get_logger().error("Invalid youngest direct age input")
        #         return False
        # if direct_age_unit != '':
        #     self.direct_age_unit_model.setFilter(f"AgeUnitAbbreviation = '{direct_age_unit}'")
        #     direct_age_unit_id = self.direct_age_unit_model.data(self.direct_age_unit_model.index(0, 0),
        #                                                      QtC.Qt.ItemDataRole.DisplayRole)
        # else:
        #     direct_age_unit_id = ''
        # if direct_age_error_type != '':
        #     self.direct_age_error_model.setFilter(f"ErrorFormatAbbreviation = '{direct_age_error_type}'")
        #     direct_age_error_format_id = self.direct_age_error_model.data(self.direct_age_error_model.index(0, 0),
        #                                                               QtC.Qt.ItemDataRole.DisplayRole)
        # else:
        #     direct_age_error_format_id = ''
        # if oldest_rel != '':
        #     self.age_model.setFilter(f"AgeName = '{oldest_rel}'")
        #     oldest_rel_id = self.age_model.data(self.age_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
        # else:
        #     oldest_rel_id = ''
        # if youngest_rel != '':
        #     self.age_model.setFilter(f"AgeName = '{youngest_rel}'")
        #     youngest_rel_id = self.age_model.data(self.age_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
        # else:
        #     youngest_rel_id = ''

        if not self.direct_age_lineEdit.text() or self.direct_age_lineEdit.text() == '':
            direct_age = QtC.QVariant()
        else:
            try:
                direct_age = float(self.direct_age_lineEdit.text())
                if int(direct_age) == direct_age:
                    direct_age = int(direct_age)
            except ValueError:
                logger_setup.get_logger().error("Invalid direct age input")
                return False
        if not self.direct_age_error_lineEdit.text() or self.direct_age_error_lineEdit.text() == '':
            direct_age_error = QtC.QVariant()
        else:
            try:
                direct_age_error = float(self.direct_age_error_lineEdit.text())
            except ValueError:
                logger_setup.get_logger().error("Invalid direct age error input")
                return False
        direct_age_unit = self.direct_age_unit_comboBox.currentText()
        direct_age_error_type = self.direct_age_error_format_comboBox.currentText()
        if not self.oldest_direct_lineEdit.text() or self.oldest_direct_lineEdit.text() == '':
            oldest_direct = QtC.QVariant()
        else:
            try:
                oldest_direct = float(self.oldest_direct_lineEdit.text())
                if int(oldest_direct) == oldest_direct:
                    oldest_direct = int(oldest_direct)
            except ValueError:
                logger_setup.get_logger().error("Invalid oldest direct age input")
                return False
        if not self.youngest_direct_lineEdit.text() or self.youngest_direct_lineEdit.text() == '':
            youngest_direct = QtC.QVariant()
        else:
            try:
                youngest_direct = float(self.youngest_direct_lineEdit.text())
                if int(youngest_direct) == youngest_direct:
                    youngest_direct = int(youngest_direct)
            except ValueError:
                logger_setup.get_logger().error("Invalid youngest direct age input")
                return False
        oldest_rel = self.oldest_rel_comboBox.currentText()
        youngest_rel = self.youngest_rel_comboBox.currentText()
        age_description = self.age_description_lineEdit.text()
        if not age_description or age_description == '':
            age_description = QtC.QVariant()
        old_sample_age_id = self.sample_age_id
        if direct_age_unit == '':
            direct_age_unit_id = QtC.QVariant()
        else:
            self.direct_age_unit_model.setFilter(f"AgeUnitAbbreviation = '{direct_age_unit}'")
            direct_age_unit_id = self.direct_age_unit_model.data(self.direct_age_unit_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
        if direct_age_error_type == '':
            direct_age_error_format_id = QtC.QVariant()
        else:
            self.direct_age_error_model.setFilter(f"ErrorFormatAbbreviation = '{direct_age_error_type}'")
            direct_age_error_format_id = self.direct_age_error_model.data(self.direct_age_error_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
        if oldest_rel == '':
            oldest_rel_id = QtC.QVariant()
        else:
            self.age_model.setFilter(f"AgeName = '{oldest_rel}'")
            oldest_rel_id = self.age_model.data(self.age_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
        if youngest_rel == '':
            youngest_rel_id = QtC.QVariant()
        else:
            self.age_model.setFilter(f"AgeName = '{youngest_rel}'")
            youngest_rel_id = self.age_model.data(self.age_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
        self.age_model.setFilter("")
        logger_setup.get_logger().info(f"Checking if any SampleAges exist with these values")
        age_columns = ['DirectAge', 'DirectAgeError', 'DirectAgeUnitID', 'DirectAgeErrorFormatID', 'OldestDirectAge',
                       'YoungestDirectAge', 'OldestAgeID', 'YoungestAgeID']
        qage_columns = ", ".join(age_columns)
        age_values = [direct_age, direct_age_error, direct_age_unit_id, direct_age_error_format_id, oldest_direct,
                      youngest_direct, oldest_rel_id, youngest_rel_id]
        conditions = []
        for i in range(len(age_values)):
            if isinstance(age_values[i], QtC.QVariant):
                conditions.append(f'{age_columns[i]} IS NULL')
            else:
                conditions.append(f'{age_columns[i]} = :{age_columns[i]}')
        sql_where = ' AND '.join(conditions)
        query = QtS.QSqlQuery()
        if not query.prepare(f'''SELECT SampleAgeID FROM SampleAges WHERE {sql_where}'''):
            logger_setup.get_logger().critical(f'Error checking for duplicates')
            logger_setup.get_logger().debug(f'Unable to prepare query: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.executedQuery()}')
            return False
        for i, value in enumerate(age_values):
            if not isinstance(value, QtC.QVariant):
                query.bindValue(f':{age_columns[i]}', value)
        if not query.exec():
            logger_setup.get_logger().critical(f'Error checking for duplicates')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.executedQuery()}')
            return False
        create_savepoint('before_update_age')
        if query.next():
            duplicate_id = query.value(0)
            logger_setup.get_logger().info(f"SampleAgeID {duplicate_id} already exists with these values")
            query_model = QtS.QSqlQueryModel()
            query_model.setQuery(f'SELECT AgeConstraintID FROM SampleAges_AgeConstraints WHERE SampleAgeID = {duplicate_id}')
            current_age_constraints = [query_model.index(row, 0).data() for row in range(query_model.rowCount())]
            query_model.setQuery(f'SELECT AgeInterpretationID FROM SampleAges_AgeInterpretations WHERE SampleAgeID = {duplicate_id}')
            current_age_interpretations = [query_model.index(row, 0).data() for row in range(query_model.rowCount())]
            query_model.setQuery(f'SELECT ReferenceID FROM SampleAges_References WHERE SampleAgeID = {duplicate_id}')
            current_age_references = [query_model.index(row, 0).data() for row in range(query_model.rowCount())]
            selected_age_constraints = self.age_constraint_tree.traverse_checkable_tree(QtC.QModelIndex())[0]
            selected_age_interpretations = self.age_interpretation_tree.traverse_checkable_tree(QtC.QModelIndex())[0]
            selected_age_references = self.age_reference_model.return_checked_ids()[0]
            different = False
            if (set(current_age_constraints) != set(selected_age_constraints)
                    or set(current_age_interpretations) != set(selected_age_interpretations)
                    or set(current_age_references) != set(selected_age_references)):
                different = True
            if duplicate_id != old_sample_age_id:
                # todo: check that this works
                self.msg.setIcon(QtW.QMessageBox.Icon.Question)
                self.msg.setText(f"This sample age already exists. Do you want to associate it with the selected samples?")
                self.msg.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
                response = self.msg.exec()
                if response != QtW.QMessageBox.StandardButton.Yes:
                    logger_setup.get_logger().info("User chose not to associate SampleAgeID with selected samples")
                    logger_setup.get_logger().error(
                        "Cannot duplicate data.\nChange sample age data to create a new sample age")
                    return False
                else:
                    logger_setup.get_logger().info("User chose to associate SampleAgeID with selected samples")
                    self.sample_age_id = duplicate_id
                    if different:
                        self.msg.setIcon(QtW.QMessageBox.Icon.Question)
                        self.msg.setText(f"This sample age already exists but has a different description and tags.\nDo you want to update the description and tags?")
                        self.msg.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
                        response = self.msg.exec()
                        if response != QtW.QMessageBox.StandardButton.Yes:
                            logger_setup.get_logger().info("User chose not to update tags")
                        else:
                            if not self.update_age_tags(self.age_constraint_comboBox):
                                return False
                            if not self.update_age_tags(self.age_interpretation_comboBox):
                                return False
                            if not self.update_age_tags(self.age_reference_comboBox):
                                return False
        else:
            logger_setup.get_logger().info(f"Updating age information for SampleAgeID {self.sample_age_id}")
            samples_sampleages_model = QtS.QSqlTableModel()
            set_table(samples_sampleages_model, 'Samples_SampleAges')
            samples_sampleages_model.setFilter(f"SampleAgeID = {self.sample_age_id}")
            associated_ids = []
            if samples_sampleages_model.rowCount() > 0:
                for row in range(samples_sampleages_model.rowCount()):
                    associated_ids.append(samples_sampleages_model.index(row, 0).data())
            if set(associated_ids) != set(self.sample_ids):
                for id in self.sample_ids:
                    if id not in associated_ids:
                        logger_setup.get_logger().info(f"SampleAgeID {self.sample_age_id} is not associated with all selected samples")
                        self.msg.setIcon(QtW.QMessageBox.Icon.Question)
                        self.msg.setText(f"This sample age is not associated with all selected samples. Do you want to associate it with all selected samples?")
                        self.msg.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
                        response = self.msg.exec()
                        if response == QtW.QMessageBox.StandardButton.Yes:
                            logger_setup.get_logger().info("User chose to associate SampleAgeID with all selected samples")
                        else:
                            logger_setup.get_logger().info("User chose not to associate SampleAgeID with all selected samples")
                            return False
            if not query.exec(f"SELECT {qage_columns} FROM SampleAges WHERE SampleAgeID = {self.sample_age_id}"):
                logger_setup.get_logger().critical(f'Unable to get SampleAges: {query.lastError().text()}')
                return False
            if not query.next():
                logger_setup.get_logger().critical(f'No results for SampleAgeID {self.sample_age_id}')
                return False
            existing_values = [query.value(i) for i in range(query.record().count())]
            for s in existing_values:
                index = existing_values.index(s)
                if not s:
                    s = QtC.QVariant()
                    existing_values[index] = s
            if existing_values == age_values:
                logger_setup.get_logger().info("No changes to age information")
            elif existing_values != age_values:
                logger_setup.get_logger().info("Changes to age information")
                error, header = validate_update('SampleAges', age_columns, age_values, f'SampleAgeID = {self.sample_age_id}')
                if error:
                    logger_setup.get_logger().error(f'Invalid age input: {error}')
                    rollback_savepoint('before_update_age')
                    return False
                logger_setup.get_logger().info(f"Valid age information")
                sql_placeholders = ", ".join('?' * len(age_values))
                query.prepare(f'''UPDATE SampleAges SET ({qage_columns}) = ({sql_placeholders}) WHERE SampleAgeID = {self.sample_age_id}''')
                for i, value in enumerate(age_values):
                    query.bindValue(i, value)
                if not query.exec():
                    logger_setup.get_logger().critical(f'Unable to update SampleAges')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.executedQuery()}')
                    rollback_savepoint('before_update_age')
                    return False
                error = update_modified_timestamp('SampleAges', [self.sample_age_id])
                if error:
                    logger_setup.get_logger().error(f'Unable to update modified timestamp')
                    logger_setup.get_logger().debug(f'Error : {error}')
                    rollback_savepoint('before_update_age')
                    return False
                logger_setup.get_logger().info(f"Updated age information for SampleAgeID {self.sample_age_id}")
                if not convert_sample_age(self.sample_age_id):
                    rollback_savepoint('before_update_age')
                    return False
            if not self.update_age_tags(self.age_constraint_comboBox):
                return False
            if not self.update_age_tags(self.age_interpretation_comboBox):
                return False
            if not self.update_age_tags(self.age_reference_comboBox):
                return False
        for sample_id in self.sample_ids:
            samples_sampleages_model = QtS.QSqlTableModel()
            set_table(samples_sampleages_model, 'Samples_SampleAges')
            samples_sampleages_model.setFilter(f"SampleID = {sample_id} AND SampleAgeID = {self.sample_age_id}")
            if samples_sampleages_model.rowCount() == 0:
                if not query.exec(f'''INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) VALUES ({sample_id}, {self.sample_age_id})'''):
                    logger_setup.get_logger().critical(f'Unable to insert Samples_SampleAges: {query.lastError().text()}')
                    rollback_savepoint('before_update_age')
                    return False
                logger_setup.get_logger().info(f"Inserted SampleAgeID {self.sample_age_id} for SampleID {sample_id}")
            if default_age:
                if not query.exec(f'''UPDATE Samples SET DefaultSampleAgeID = {self.sample_age_id} WHERE SampleID = {sample_id}'''):
                    logger_setup.get_logger().critical(f'Unable to update Sample default age: {query.lastError().text()}')
                    rollback_savepoint('before_update_age')
                    return False
                error = update_modified_timestamp('Samples', [sample_id])
                if error:
                    logger_setup.get_logger().error(f'Unable to update modified timestamp')
                    logger_setup.get_logger().debug(f'Error : {error}')
                    rollback_savepoint('before_update_age')
                    return False
                logger_setup.get_logger().info(f"Updated DefaultSampleAgeID to {self.sample_age_id} for SampleID {sample_id}")
            if old_sample_age_id != self.sample_age_id:
                if not query.exec(f'''DELETE FROM Samples_SampleAges WHERE SampleID = {sample_id} AND SampleAgeID = {old_sample_age_id}'''):
                    logger_setup.get_logger().critical(f'Unable to delete old SampleAgeID: {query.lastError().text()}')
                    rollback_savepoint('before_update_age')
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
        release_savepoint('before_update_age')
        self.populate_age_dropdown()
        return True

    def update_age_tags(self, combo: CheckableTreeCombobox | CheckableComboBox):
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
        many_to_many_model.setFilter(f"SampleAgeID = {self.sample_age_id} AND {id_header} {where_sql}")
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
            logger_setup.get_logger().info(f"No {table} selected for SampleAgeID {self.sample_age_id}")
            if not query.exec(f'''DELETE FROM SampleAges_{table} WHERE SampleAgeID = {self.sample_age_id}'''):
                logger_setup.get_logger().critical(f'Unable to delete unchecked {table}: {query.lastError().text()}')
                rollback_savepoint('before_update_age')
                return False
            logger_setup.get_logger().info(f"Deleted {table} for SampleAgeID {self.sample_age_id}")
        else:
            many_to_many_model.setFilter(f"SampleAgeID = {self.sample_age_id}")
            if many_to_many_model.rowCount() == 0:
                for age_id in checked_ids:
                    # If the age is checked, insert it if it doesn't exist
                    if not query.exec(
                            f'''INSERT INTO SampleAges_{table} (SampleAgeID, {id_header}) VALUES ({self.sample_age_id}, {age_id})'''):
                        if 'UNIQUE constraint failed' in query.lastError().text():
                            logger_setup.get_logger().info(
                                f"{id_header} {age_id} already associated with SampleAgeID {self.sample_age_id}")
                        else:
                            logger_setup.get_logger().critical(
                                f'Unable to insert checked {id_header} {age_id}: {query.lastError().text()}')
                            rollback_savepoint('before_update_age')
                            return False
                    logger_setup.get_logger().info(f"Inserted {id_header} {age_id} for SampleAgeID {self.sample_age_id}")
            for row in range(many_to_many_model.rowCount()):
                age_id = many_to_many_model.data(many_to_many_model.index(row, 1), QtC.Qt.ItemDataRole.DisplayRole)
                if age_id in checked_ids:
                    # If the age is checked, insert it if it doesn't exist
                    if not query.exec(f'''INSERT INTO SampleAges_{table} (SampleAgeID, {id_header}) VALUES ({self.sample_age_id}, {age_id})'''):
                        if 'UNIQUE constraint failed' in query.lastError().text():
                            logger_setup.get_logger().info(f"{id_header} {age_id} already associated with SampleAgeID {self.sample_age_id}")
                        else:
                            logger_setup.get_logger().critical(f'Unable to insert checked {id_header} {age_id}: {query.lastError().text()}')
                            rollback_savepoint('before_update_age')
                            return False
                    logger_setup.get_logger().info(f"Inserted {id_header} {age_id} for SampleAgeID {self.sample_age_id}")
                elif age_id not in partially_checked_ids:
                    # If the age is unchecked, delete it if it exists
                    if not query.exec(f'''DELETE FROM SampleAges_{table} WHERE SampleAgeID = {self.sample_age_id} AND {id_header} = {age_id}'''):
                        logger_setup.get_logger().critical(f'Unable to delete unchecked {id_header} {age_id}: {query.lastError().text()}')
                        rollback_savepoint('before_update_age')
                        return False
                    logger_setup.get_logger().info(f"Deleted {id_header} {age_id} for SampleAgeID {self.sample_age_id}")
        end_update_age_tags = time.time()
        logger_setup.get_logger().info(f"Updated {table} in {end_update_age_tags - start_update_age_tags} seconds")
        return True

    def add_age(self):
        query = QtS.QSqlQuery()
        # Search if there is already a blank age for this sample
        existing = False
        if len(self.sample_ids) == 0:
            logger_setup.get_logger().info("No samples selected to add age")
            return
        if len(self.sample_ids) > 1:
            logger_setup.get_logger().info("More than one sample selected to add age")
            self.msg.setIcon(QtW.QMessageBox.Icon.Warning)
            self.msg.setText(f"More than one sample selected. Adding a new age will add it to all selected samples.")
            self.msg.setStandardButtons(QtW.QMessageBox.StandardButton.Ok | QtW.QMessageBox.StandardButton.Cancel)
            response = self.msg.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                logger_setup.get_logger().info("User chose to associate SampleAgeID with all selected samples")
            else:
                logger_setup.get_logger().info("User chose not to associate SampleAgeID with all selected samples")
                return
        sample_names = []
        sample_model = self.sample_model
        name_col = get_name_column('Samples')
        for sample_id in self.sample_ids:
            sample_model.setFilter(f'SampleID = {sample_id}')
            sample_names.append(sample_model.index(0, name_col).data(QtC.Qt.ItemDataRole.DisplayRole))
        sample_age_query_model = QtS.QSqlQueryModel()
        find_query = f'''SELECT SampleAgeID, SampleAgeDescription FROM SampleAges WHERE (DirectAge IS NULL AND 
                            DirectAgeError IS NULL AND OldestDirectAge IS NULL AND YoungestDirectAge IS NULL AND 
                            OldestAgeID IS NULL AND YoungestAgeID IS NULL)'''
        sample_age_query_model.setQuery(find_query)
        if sample_age_query_model.lastError().isValid():
            logger_setup.get_logger().critical(f'Unable to get SampleAges')
            logger_setup.get_logger().debug(f'Error: {sample_age_query_model.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {find_query}')
            return
        if sample_age_query_model.rowCount() > 0:
            # Check if the description contains any of the sample names
            for row in range(sample_age_query_model.rowCount()):
                sample_age_description = sample_age_query_model.data(sample_age_query_model.index(row, 1), QtC.Qt.ItemDataRole.DisplayRole)
                if any(sample_name in sample_age_description for sample_name in sample_names):
                    self.sample_age_id = sample_age_query_model.data(sample_age_query_model.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
                    logger_setup.get_logger().info(f"Found existing blank age {self.sample_age_id} for samples {sample_names}")
                    existing = True
                    break
        create_savepoint('before_add_age')
        if not existing:
            # Add a new age with default values for units and a description
            if not query.exec(f'''INSERT INTO SampleAges (DirectAgeUnitID, DirectAgeErrorFormatID, SampleAgeDescription) 
                            VALUES ({settings.value('age_unit_id')}, {settings.value('age_error_format_id')}, 'New Sample Age for {", ".join(sample_names)}')'''):
                logger_setup.get_logger().critical(f'Unable to add new SampleAges')
                logger_setup.get_logger().critical(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().critical(f"SQL query: {query.executedQuery()}")
                rollback_savepoint('before_add_age')
                return
            else:
                self.sample_age_id = query.lastInsertId()
            logger_setup.get_logger().info(f"Added age {self.sample_age_id}")
        for sample_id in self.sample_ids:
            if not query.exec(f'''INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) VALUES ({sample_id}, {self.sample_age_id})'''):
                errtxt = query.lastError().text()
                if 'UNIQUE constraint failed' in errtxt:
                    logger_setup.get_logger().info(f"Sample {sample_id} already has age {self.sample_age_id}")
                else:
                    logger_setup.get_logger().critical(f"Error adding age to sample")
                    logger_setup.get_logger().debug(f"Error: {errtxt}")
                    logger_setup.get_logger().debug(f"SQL query: {query.executedQuery()}")
                    rollback_savepoint('before_add_age')
                    return
            logger_setup.get_logger().info(f"Added age {self.sample_age_id} to sample {sample_id}")
            query.prepare(f"SELECT DefaultSampleAgeID, SampleID FROM {self.table} WHERE {self.sample_id_header} = :sample_id")
            query.bindValue(':sample_id', sample_id)
            if not query.exec():
                logger_setup.get_logger().critical(f"Error getting default age for sample")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.executedQuery()}")
                rollback_savepoint('before_add_age')
                return
            if not query.next():
                logger_setup.get_logger().critical(f"Selected sample not found")
                logger_setup.get_logger().debug(f"SQL query: {query.executedQuery()}")
                rollback_savepoint('before_add_age')
                return
            default_age_id = query.value(0)
            if default_age_id is None or default_age_id == "":
                if not query.exec(f'''UPDATE {self.table} SET DefaultSampleAgeID = {self.sample_age_id} WHERE {self.sample_id_header} = {sample_id}'''):
                    logger_setup.get_logger().critical(f"Error updating default age for sample")
                    logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                    logger_setup.get_logger().debug(f"SQL query: {query.executedQuery()}")
                    rollback_savepoint('before_add_age')
                    return
                logger_setup.get_logger().info(f"Updated default age for sample {sample_id} to {self.sample_age_id}")
                self.enable_groups()
                self.default_age_checkBox.setChecked(True)
        logger_setup.get_logger().info(f"Updating age fields for {self.table} with sample IDs {self.sample_ids}")
        release_savepoint('before_add_age')
        self.updated = True
        self.enable_groups()
        self.update_list(self.sample_ids)
        for row in range(self.sample_age_model.rowCount()):
            if self.sample_age_model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole) == self.sample_age_id:
                self.edit_age_comboBox.setCurrentIndex(row)
                break

    def delete_age(self):
        # todo: Figure out why this is deleting more than the selected index
        index = self.edit_age_comboBox.currentIndex()
        if index == -1:
            logger_setup.get_logger().info("No age selected to delete")
            return
        self.sample_age_id = self.edit_age_comboBox.model().data(self.edit_age_comboBox.model().index(index, 0), QtC.Qt.ItemDataRole.DisplayRole)
        if not self.sample_age_id:
            return
        # Check if this age is associated with any other samples
        samples_sampleages_model = QtS.QSqlTableModel()
        set_table(samples_sampleages_model, 'Samples_SampleAges')
        samples_sampleages_model.setFilter(f"SampleAgeID = {self.sample_age_id}")
        delete_msg = QtW.QMessageBox()
        delete_msg.setIcon(QtW.QMessageBox.Icon.Question)
        cancel_button = QtW.QPushButton('Cancel')
        delete_button = QtW.QPushButton('Delete')
        other_samples = []
        if samples_sampleages_model.rowCount() > 0:
            for row in range(samples_sampleages_model.rowCount()):
                sample_id = samples_sampleages_model.data(samples_sampleages_model.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
                if sample_id not in self.sample_ids:
                    other_samples.append(sample_id)
        if other_samples:
            text = f'''This age is also associated with {len(other_samples)} other samples. \n
                    Do you want to delete it entirely or just remove it from the selected samples?'''
            remove_button = QtW.QPushButton('Remove')
            delete_msg.addButton(remove_button, QtW.QMessageBox.ButtonRole.ActionRole)
            delete_msg.addButton(delete_button, QtW.QMessageBox.ButtonRole.ActionRole)
            delete_msg.addButton(cancel_button, QtW.QMessageBox.ButtonRole.RejectRole)
        else:
            text = f"Are you sure you want to delete the selected age?"
            remove_button = None
            delete_msg.addButton(cancel_button, QtW.QMessageBox.ButtonRole.RejectRole)
            delete_msg.addButton(delete_button, QtW.QMessageBox.ButtonRole.ActionRole)
        delete_msg.setText(text)
        delete_msg.exec()
        reply = delete_msg.clickedButton()
        if reply == cancel_button:
            return
        elif reply == delete_button:
            logger_setup.get_logger().info(f"Deleting age {self.sample_age_id}")
            create_savepoint('before_delete')
            query = QtS.QSqlQuery()
            if not query.exec(f"DELETE FROM SampleAges WHERE SampleAgeID = {self.sample_age_id}"):
                logger_setup.get_logger().critical(f"Error deleting selected age")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.executedQuery()}")
                rollback_savepoint('before_delete')
                return
            logger_setup.get_logger().info(f"Deleted age {self.sample_age_id}")
            release_savepoint('before_delete')
            self.updated = True
            self.populate_age_dropdown()
            self.populate_fields()
        elif reply == remove_button:
            # todo: Check that this works
            logger_setup.get_logger().info(f"Removing age {self.sample_age_id} from selected samples")
            create_savepoint('before_remove')
            query = QtS.QSqlQuery()
            for sample_id in self.sample_ids:
                if not query.exec(f"DELETE FROM Samples_SampleAges WHERE SampleID = {sample_id} AND SampleAgeID = {self.sample_age_id}"):
                    logger_setup.get_logger().critical(f"Error removing age {self.sample_age_id} from sample {sample_id}")
                    logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                    logger_setup.get_logger().debug(f"SQL query: {query.executedQuery()}")
                    rollback_savepoint('before_remove')
                    return
                logger_setup.get_logger().info(f"Removed age {self.sample_age_id} from sample {sample_id}")
            release_savepoint('before_remove')
            self.updated = True
            self.populate_age_dropdown()
            self.populate_fields()

    def add_popup(self, combo: QtW.QComboBox, action: QtG.QAction | None = None):
        if isinstance(combo.model(), TreeModel):
            table = combo.model().table
        else:
            table = combo.model().tableName()
        if table == 'SampleAges':
            self.add_age()
            return
        dlg = None
        if table in SQLUtils.user_viewable_trees:
            save_expanded_state(table, combo.model(), combo.view())
            dlg_args = add_tree_popup(combo.view(), combo.model(), action)
            dlg = AddTreeTags(self, table, **dlg_args)
        else:
            dlg = AddTags(self, table)
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

    def edit_popup(self, combo: QtW.QComboBox):
        if combo == self.edit_age_comboBox:
            index = combo.currentIndex()
            if index == -1:
                return
            self.sample_age_id = combo.model().data(combo.model().index(index, 0), QtC.Qt.ItemDataRole.DisplayRole)
            combo.hidePopup()
            return
        if isinstance(combo.model(), TreeModel):
            table = combo.model().table
        else:
            table = combo.model().tableName()
        if table in SQLUtils.user_viewable_trees:
            dlg = EditTree(self, table)
        else:
            dlg = EditTable(self, table)
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
        self.add_age_pushButton.setAutoDefault(True)

    def enable_groups(self):
        self.default_age_checkBox.setEnabled(True)
        self.edit_age_comboBox.setEnabled(True)
        self.direct_age_groupBox.setEnabled(True)
        self.relative_age_groupBox.setEnabled(True)
        self.age_information_groupBox.setEnabled(True)
        self.add_age_pushButton.setAutoDefault(False)

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
        combo_box.edit_triggered.connect(self.edit_popup)
        combo_box.add_triggered.connect(self.add_popup)
        combo_box.delete_triggered.connect(self.handle_delete)

    def disable_context(self, combo_box: CheckableComboBox | CheckableTreeCombobox):
        combo_box.enable_context_menu(False)
        try:
            combo_box.edit_triggered.disconnect(self.handle_edit_triggered)
        except TypeError:
            pass

    def handle_delete(self, combo_box: CheckableComboBox):
        model = combo_box.model()
        table = model.tableName()
        if table == 'SampleAges':
            self.delete_age()
        self.populate_dropdowns()
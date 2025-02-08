import PyQt6
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6.uic import loadUi
from Functions.Table_classes import (set_table, SampleAgeTableModel, CheckableSqlTableModel, FontDelegate, name_column,
                                     set_comboBox_text, show_column, CheckableComboBox, CheckableSqlQueryModel, SQLiteTableModel)
from Functions.Tree_classes import TreeModel, CheckableTreeCombobox, CheckableTreeModel, CheckableTreeView
from Functions.Settings_manager import settings
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Check_triggers import validate_insert, validate_update, update_modified_timestamp
import Functions.Database_views as DB_views
from ui.EditTree import EditTree
from ui.EditTable import EditTable



class AgeFields(QtW.QWidget):
    def __init__(self, table: str, item_ids: list):
        super().__init__()
        age_ui_file = "ui/AgeFields.ui"
        loadUi(age_ui_file, self)
        self.table = table
        self.item_ids = item_ids
        self.updated = False
        self.msg = QtW.QMessageBox(self)

        self.item_model = QtS.QSqlTableModel()
        # self.sample_age_model = SampleAgeTableModel()
        self.sample_age_model = CheckableSqlQueryModel()
        self.age_tree_view = QtW.QTreeView()
        self.age_model = QtS.QSqlTableModel()
        self.oldest_age_tree = TreeModel()
        self.youngest_age_tree = TreeModel()
        self.direct_age_unit_model = QtS.QSqlTableModel()
        self.error_type_model = QtS.QSqlTableModel()
        self.direct_age_error_model = QtS.QSqlTableModel()
        self.age_constraint_model = QtS.QSqlTableModel()
        self.age_constraint_tree = CheckableTreeModel()
        self.age_interpretation_model = QtS.QSqlTableModel()
        self.age_interpretation_tree = CheckableTreeModel()
        # self.age_reference_model = CheckableSqlTableModel()
        self.age_reference_model = CheckableSqlQueryModel()

        self.default_age_ids = []
        self.item_id_header = None
        if table == 'Samples':
            self.item_ifnull_query = DB_views.SampleIfNullQuery()
        else:
            self.item_ifnull_query = ''

        self.populate_dropdowns()
        self.populate_fields()
        self.connect_signals()
        self.add_age_pushButton.clicked.connect(self.add_age)

    def update_list(self, item_ids):
        self.item_ids = item_ids
        self.clear_fields()
        self.disconnect_text_signals()
        self.populate_fields()
        self.connect_signals()

    def populate_dropdowns(self):
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
        self.age_reference_model.setQuery('SELECT * FROM "References"')

        self.edit_age_comboBox: CheckableComboBox
        self.edit_age_comboBox.setModel(self.sample_age_model)
        show_column(self.edit_age_comboBox, 'SampleAgeDisplay')
        self.enable_context(self.edit_age_comboBox)

        self.direct_unit_comboBox.setModel(self.direct_age_unit_model)
        show_column(self.direct_unit_comboBox, 'AgeUnitAbbreviation')
        self.direct_age_unit_comboBox.setModel(self.direct_age_unit_model)
        show_column(self.direct_age_unit_comboBox, 'AgeUnitAbbreviation')
        self.direct_age_error_type_comboBox.setModel(self.direct_age_error_model)
        show_column(self.direct_age_error_type_comboBox, 'ErrorFormatAbbreviation')
        self.oldest_rel_comboBox.setModel(self.oldest_age_tree)
        self.youngest_rel_comboBox.setModel(self.youngest_age_tree)
        self.age_constraint_comboBox.setModel(self.age_constraint_tree)
        self.age_interpretation_comboBox.setModel(self.age_interpretation_tree)
        self.age_reference_comboBox.setModel(self.age_reference_model)
        self.age_reference_comboBox.setModelColumn(name_column('"References"'))

    def populate_age_dropdown(self):
        samples_sampleage_model = QtS.QSqlTableModel()
        set_table(samples_sampleage_model, 'Samples_SampleAges')
        if len(self.checked_sample_list) > 1:
            samples_sampleage_model.setFilter(f'SampleID in {tuple(self.checked_sample_list)}')
        elif len(self.checked_sample_list) == 1:
            samples_sampleage_model.setFilter(f'SampleID = {self.checked_sample_list[0]}')
        else:
            samples_sampleage_model.setFilter('')
        sample_ages = []
        for row in range(samples_sampleage_model.rowCount()):
            sample_ages.append(samples_sampleage_model.index(row, 1).data())
        if len(sample_ages) > 1:
            self.sample_age_model.setQuery(f'{self.sample_age_model.default_query} WHERE SampleAgeID in {tuple(sample_ages)}')
        elif len(sample_ages) == 1:
            self.sample_age_model.setQuery(f'{self.sample_age_model.default_query} WHERE SampleAgeID = {sample_ages[0]}')
        for row in range(self.sample_age_model.rowCount()):
            if self.sample_age_model.index(row, 0).data() in self.default_age_ids:
                # Make the text at that row bold
                self.sample_age_model.make_bold(self.sample_age_model.index(row, 0))
            else:
                self.sample_age_model.make_not_bold(self.sample_age_model.index(row, 0))

    def connect_signals(self):
        # Connect signals and slots
        self.edit_age_comboBox.currentTextChanged.connect(self.display_age)
        self.default_age_checkBox.clicked.connect(self.update_age)
        self.direct_age_groupBox.connect_child_signals()
        self.direct_age_groupBox.focusLost.connect(self.update_age)
        self.relative_age_groupBox.connect_child_signals()
        self.relative_age_groupBox.focusLost.connect(self.update_age)
        self.age_information_groupBox.connect_child_signals()
        self.age_information_groupBox.focusLost.connect(self.update_age)

    def disconnect_text_signals(self):
        self.direct_age_groupBox.disconnect_child_signals()
        self.relative_age_groupBox.disconnect_child_signals()
        self.age_information_groupBox.disconnect_child_signals()
        try:
            self.edit_age_comboBox.currentTextChanged.disconnect(self.display_age)
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
            self.direct_age_error_type_comboBox.currentTextChanged.disconnect()
        except TypeError:
            pass

    def populate_fields(self):
        if len(self.item_ids) > 1:
            item_ifnull_model = SQLiteTableModel(f'{self.item_ifnull_query} WHERE {self.table}.{self.item_id_header} in {tuple(self.item_ids)}')
        elif len(self.item_ids) == 1:
            item_ifnull_model = SQLiteTableModel(f'{self.item_ifnull_query} WHERE {self.table}.{self.item_id_header} = {self.item_ids[0]}')
        else:
            item_ifnull_model = SQLiteTableModel(f'{self.item_ifnull_query}')
        if self.item_model.rowCount() == 0:
            self.msg.setText(f'Error: No ages found for the selected {self.table.lower()}')
            self.msg.exec()
            return
        text_values = []
        headers = []
        for col in range(item_ifnull_model.columnCount()):
            # If there is only one value concatenated in the column, add it to the list, otherwise add '-'
            text = item_ifnull_model._data[0][col]
            header = item_ifnull_model._headers[col]
            header = header.split('ifnull(')[1].split(',"Null')[0]
            headers.append(header)
            if ',' in text:
                if 'Description' in header or 'Default' in header:
                    text_values.append(text)
                else:
                    text_values.append('-')
            elif text == 'Null':
                text_values.append('')
            else:
                text_values.append(text)
        if len(text_values) > 0 and self.table == 'Samples':
            for header in headers:
                if 'Default' in header:
                    default_age_ids = text_values[headers.index(header)]
                    self.default_age_ids = []
                    if default_age_ids != '':
                        if ',' in default_age_ids:
                            self.default_age_ids = [int(x) for x in default_age_ids.split(',')]
                        else:
                            self.default_age_ids = [int(default_age_ids)]
                        for row in range(self.sample_age_model.rowCount()):
                            if self.sample_age_model.index(row, 0).data() == self.default_age_ids[0]:
                                self.edit_age_comboBox.setCurrentIndex(row)
                                break
                    self.default_age_checkBox.setChecked(self.default_age_ids != '')
                elif 'Ages.DirectAgeError' in header:
                    self.direct_age_error_lineEdit.setText(text_values[headers.index(header)])
                elif 'Ages.DirectAge' in header:
                    self.direct_age_lineEdit.setText(text_values[headers.index(header)])
                elif 'AgeUnitAbbreviation' in header:
                    self.direct_age_unit_comboBox.setCurrentText(text_values[headers.index(header)])
                elif 'ErrorFormatAbbreviation' in header:
                    self.direct_age_error_type_comboBox.setCurrentText(text_values[headers.index(header)])
                elif 'OldestDirectAge' in header:
                    self.oldest_direct_lineEdit.setText(text_values[headers.index(header)])
                elif 'YoungestDirectAge' in header:
                    self.youngest_direct_lineEdit.setText(text_values[headers.index(header)])
                elif 'OldAge' in header:
                    self.oldest_rel_comboBox.setCurrentText(text_values[headers.index(header)])
                elif 'YoungAge' in header:
                    self.youngest_rel_comboBox.setCurrentText(text_values[headers.index(header)])
                elif 'SampleAgeDescription' in header:
                    self.age_description_lineEdit.setText(text_values[headers.index(header)])
                elif 'AgeConstraintName' in header:
                    self.age_constraint_comboBox.setCurrentText(text_values[headers.index(header)])
                elif 'AgeInterpretationName' in header:
                    self.age_interpretation_comboBox.setCurrentText(text_values[headers.index(header)])
                elif 'ReferenceDisplay' in header:
                    self.age_reference_comboBox.setCurrentText(text_values[headers.index(header)])

            self.edit_age_comboBox.setItemDelegate(FontDelegate(self.edit_age_comboBox))

            # Age tags
            text = self.populate_checks('SampleAges_AgeConstraints', self.age_constraint_model,
                                        self.age_constraint_tree)
            self.age_constraint_comboBox.setCurrentText(text)
            text = self.populate_checks('SampleAges_AgeInterpretations', self.age_interpretation_model,
                                        self.age_interpretation_tree)
            self.age_interpretation_comboBox.setCurrentText(text)
            text = self.populate_checks('SampleAges_References', self.age_reference_model)
            self.age_reference_comboBox.setCurrentText(text)

    def display_age(self):
        sample_age_row = self.edit_age_comboBox.currentIndex()
        sample_age_id = self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        if sample_age_id in self.default_age_ids:
            self.default_age_checkBox.setChecked(True)
        else:
            self.default_age_checkBox.setChecked(False)
        self.direct_age_lineEdit.setText(f"{self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 2), QtC.Qt.ItemDataRole.DisplayRole)}")
        self.direct_age_error_lineEdit.setText(f"{self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 3), QtC.Qt.ItemDataRole.DisplayRole)}")
        age_error_type_id = self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 4), QtC.Qt.ItemDataRole.DisplayRole)
        for row in range(self.direct_age_error_model.rowCount()):
            if self.direct_age_error_model.index(row, 0).data() == age_error_type_id:
                age_error_abbreviation = self.direct_age_error_model.index(row, 2).data()
                set_comboBox_text(self.direct_age_error_type_comboBox, age_error_abbreviation)
                break
        self.oldest_direct_lineEdit.setText(f"{self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 5), QtC.Qt.ItemDataRole.DisplayRole)}")
        self.youngest_direct_lineEdit.setText(f"{self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 6), QtC.Qt.ItemDataRole.DisplayRole)}")
        direct_age_unit_id = self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 7), QtC.Qt.ItemDataRole.DisplayRole)
        for row in range(self.direct_age_unit_model.rowCount()):
            if self.direct_age_unit_model.index(row, 0).data() == direct_age_unit_id:
                direct_age_unit_abbreviation = self.direct_age_unit_model.index(row, 2).data()
                set_comboBox_text(self.direct_age_unit_comboBox, direct_age_unit_abbreviation)
                break
        oldest_age_id = self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 8), QtC.Qt.ItemDataRole.DisplayRole)
        for row in range(self.age_model.rowCount()):
            if self.age_model.index(row, 0).data() == oldest_age_id:
                oldest_age = self.age_model.index(row, 3).data()
                set_comboBox_text(self.oldest_rel_comboBox, oldest_age)
                break
        youngest_age_id = self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 9), QtC.Qt.ItemDataRole.DisplayRole)
        for row in range(self.age_model.rowCount()):
            if self.age_model.index(row, 0).data() == youngest_age_id:
                youngest_age = self.age_model.index(row, 3).data()
                set_comboBox_text(self.youngest_rel_comboBox, youngest_age)
                break
        self.age_description_lineEdit.setText(self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 10), QtC.Qt.ItemDataRole.DisplayRole))
        sampleage_ageconstraint_model = QtS.QSqlTableModel()
        set_table(sampleage_ageconstraint_model, 'SampleAges_AgeConstraints')
        text = self.populate_checks('SampleAges_AgeConstraints', sampleage_ageconstraint_model)
        set_comboBox_text(self.age_constraint_comboBox, text)
        sampleage_ageinterpretation_model = QtS.QSqlTableModel()
        set_table(sampleage_ageinterpretation_model, 'SampleAges_AgeInterpretations')
        text = self.populate_checks('SampleAges_AgeInterpretations', sampleage_ageinterpretation_model)
        set_comboBox_text(self.age_interpretation_comboBox, text)
        sampleage_reference_model = QtS.QSqlTableModel()
        set_table(sampleage_reference_model, 'SampleAges_References')
        text = self.populate_checks('SampleAges_References', sampleage_reference_model)
        set_comboBox_text(self.age_reference_comboBox, text)

    def populate_checks(self, many_to_many_table: str, table_model: QtS.QSqlTableModel | QtS.QSqlQueryModel, tree: CheckableTreeModel = None):
        many_to_many_model = QtS.QSqlTableModel()
        many_to_many_model.setTable(many_to_many_table)
        many_to_many_model.select()
        tag_id_header = table_model.record().fieldName(0)
        items = []
        text = ""
        if len(self.item_ids) == 0:
            # No samples selected, so uncheck everything
            for row in range(table_model.rowCount()):
                if tree is not None:
                    model = tree
                    col = name_column(table_model.tableName())
                    model_index = tree.mapFromSource(table_model.index(row, col))
                else:
                    model = table_model
                    col = name_column(table_model.tableName())
                    model_index = table_model.index(row, col)
                model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
            return text
        for row in range(table_model.rowCount()):
            tag_id = table_model.index(row, 0).data()
            if len(self.item_ids) > 1:
                many_to_many_model.setFilter(f"SampleID in {tuple(self.item_ids)} AND {tag_id_header} = {tag_id}")
            else:
                many_to_many_model.setFilter(f"SampleID = {self.item_ids[0]} AND {tag_id_header} = {tag_id}")
            if tree is not None:
                model = tree
                col = name_column(table_model.tableName())
                model_index = tree.mapFromSource(table_model.index(row, col))
            else:
                model = table_model
                col = name_column(table_model.tableName())
                model_index = table_model.index(row, col)
            if many_to_many_model.rowCount() == len(self.item_ids):
                # All samples have this tag
                model.setData(model_index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                items.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
            elif many_to_many_model.rowCount() > 0:
                # Some samples have this tag
                model.setData(model_index, QtC.Qt.CheckState.PartiallyChecked, QtC.Qt.ItemDataRole.CheckStateRole)
                items.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
            else:
                # No samples have this tag
                model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
        text = ", ".join(items)
        return text

    def update_age(self):
        print('Update_age called')
        if len(self.item_ids) > 0:
            default_age = self.default_age_checkBox.isChecked()
            direct_age = self.direct_age_lineEdit.text()
            if not direct_age or direct_age == '':
                direct_age = 'Null'
            direct_age_error = self.direct_age_error_lineEdit.text()
            if not direct_age_error or direct_age_error == '':
                direct_age_error = 'Null'
            direct_age_unit = self.direct_age_unit_comboBox.currentText()
            direct_age_error_type = self.direct_age_error_type_comboBox.currentText()
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
            age_constraint = self.age_constraint_comboBox.currentText()
            age_interpretation = self.age_interpretation_comboBox.currentText()
            age_reference = self.age_reference_comboBox.currentText()

            row = self.edit_age_comboBox.currentIndex()
            sample_age_id = self.sample_age_model.data(self.sample_age_model.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
            old_sample_age_id = sample_age_id
            if direct_age_unit == '':
                direct_age_unit_id = 'Null'
            else:
                self.direct_age_unit_model.setFilter(f"AgeUnitAbbreviation = '{direct_age_unit}'")
                direct_age_unit_id = self.direct_age_unit_model.data(self.direct_age_unit_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            if direct_age_error_type == '':
                direct_age_error_type_id = 'Null'
            else:
                self.direct_age_error_model.setFilter(f"ErrorFormatAbbreviation = '{direct_age_error_type}'")
                direct_age_error_type_id = self.direct_age_error_model.data(self.direct_age_error_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
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
            if age_constraint == '':
                age_constraint_id = 'Null'
            else:
                self.age_constraint_model.setFilter(f"AgeConstraintName = '{age_constraint}'")
                age_constraint_id = self.age_constraint_model.data(self.age_constraint_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            if age_interpretation == '':
                age_interpretation_id = 'Null'
            else:
                self.age_interpretation_model.setFilter(f"AgeInterpretationName = '{age_interpretation}'")
                age_interpretation_id = self.age_interpretation_model.data(self.age_interpretation_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            if age_reference == '':
                age_reference_id = 'Null'
            else:
                self.age_reference_model.setFilter(f"ShortCitation = '{age_reference}'")
                age_reference_id = self.age_reference_model.data(self.age_reference_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)

            create_savepoint('before_update')
            update_age = True
            samples_sampleages_model = QtS.QSqlTableModel()
            set_table(samples_sampleages_model, 'Samples_SampleAges')
            samples_sampleages_model.setFilter(f"SampleAgeID = {sample_age_id}")
            if samples_sampleages_model.rowCount() > 0:
                for row in range(samples_sampleages_model.rowCount()):
                    if samples_sampleages_model.index(row, 0).data() not in self.item_ids:
                        update_age = False
            age_columns = ['DirectAge', 'DirectAgeError', 'DirectAgeUnitID', 'DirectAgeErrorFormatID', 'OldestDirectAge', 'YoungestDirectAge',
            'OldestAgeID', 'YoungestAgeID', 'SampleAgeDescription']
            qage_columns = ', '.join(age_columns)
            age_values = [f'{direct_age}', f'{direct_age_error}', f'{direct_age_unit_id}', f'{direct_age_error_type_id}', f'{oldest_direct}',
                          f'{youngest_direct}', f'{oldest_rel_id}', f'{youngest_rel_id}', f'{age_description}']
            qage_values = ', '.join(age_values)
            query = QtS.QSqlQuery()
            if update_age:
                if not query.exec(f"SELECT {qage_columns} FROM SampleAges WHERE SampleAgeID = {sample_age_id}"):
                    errtxt = query.lastError().text()
                    self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                    return
                query.next()
                existing_values = [query.value(i) for i in range(query.record().count())]
                if existing_values != age_values:
                    error = validate_update('SampleAges', age_columns, age_values)
                    if error:
                        errtxt = error
                        print(errtxt)
                        rollback_savepoint('before_update')
                        return
                    if not query.exec(f'''UPDATE SampleAges SET (DirectAge, DirectAgeError, DirectAgeUnitID, DirectAgeErrorFormatID, OldestDirectAge, YoungestDirectAge, OldestAgeID, YoungestAgeID, SampleAgeDescription) = 
                        ({direct_age}, {direct_age_error}, {direct_age_unit_id}, {direct_age_error_type_id}, {oldest_direct}, {youngest_direct}, {oldest_rel_id}, {youngest_rel_id}, "{age_description}") 
                        WHERE SampleAgeID = {sample_age_id}'''):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                        return
                    update_modified_timestamp('SampleAges', sample_age_id)
            else:
                if not query.exec(f'''INSERT INTO SampleAges (DirectAge, DirectAgeError, DirectAgeUnitID, DirectAgeErrorFormatID, OldestDirectAge, YoungestDirectAge, OldestAgeID, YoungestAgeID, SampleAgeDescription) VALUES 
                    ({direct_age}, {direct_age_error}, {direct_age_unit_id}, {direct_age_error_type_id}, {oldest_direct}, {youngest_direct}, {oldest_rel_id}, {youngest_rel_id}, "{age_description}")'''):
                    errtxt = query.lastError().text()
                    self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                    rollback_savepoint('before_update')
                    return
                sample_age_id = query.lastInsertId()
            if age_constraint_id != 'Null':
                sampleages_ageconstraints_model = QtS.QSqlTableModel()
                set_table(sampleages_ageconstraints_model, 'SampleAges_AgeConstraints')
                sampleages_ageconstraints_model.setFilter(f"SampleAgeID = {sample_age_id} AND AgeConstraintID = {age_constraint_id}")
                if sampleages_ageconstraints_model.rowCount() == 0:
                    if not query.exec(f'''INSERT INTO SampleAges_AgeConstraints (SampleAgeID, AgeConstraintID) VALUES ({sample_age_id}, {age_constraint_id})'''):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                    return
            if age_interpretation_id != 'Null':
                sampleages_ageinterpretations_model = QtS.QSqlTableModel()
                set_table(sampleages_ageinterpretations_model, 'SampleAges_AgeInterpretations')
                sampleages_ageinterpretations_model.setFilter(f"SampleAgeID = {sample_age_id} AND AgeInterpretationID = {age_interpretation_id}")
                if sampleages_ageinterpretations_model.rowCount() == 0:
                    if not query.exec(f'''INSERT INTO SampleAges_AgeInterpretations (SampleAgeID, AgeInterpretationID) VALUES ({sample_age_id}, {age_interpretation_id})'''):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                    return
            if age_reference_id != 'Null':
                sampleages_references_model = QtS.QSqlTableModel()
                set_table(sampleages_references_model, 'SampleAges_References')
                sampleages_references_model.setFilter(f"SampleAgeID = {sample_age_id} AND ReferenceID = {age_reference_id}")
                if sampleages_references_model.rowCount() == 0:
                    if not query.exec(f'''INSERT INTO SampleAges_References (SampleAgeID, ReferenceID) VALUES ({sample_age_id}, {age_reference_id})'''):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                    return
            for sample_id in self.item_ids:
                samples_sampleages_model = QtS.QSqlTableModel()
                set_table(samples_sampleages_model, 'Samples_SampleAges')
                samples_sampleages_model.setFilter(f"SampleID = {sample_id} AND SampleAgeID = {sample_age_id}")
                if samples_sampleages_model.rowCount() == 0:
                    if not query.exec(f'''INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) VALUES ({sample_id}, {sample_age_id})'''):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                        return
                if default_age:
                    if not query.exec(f'''UPDATE Samples SET DefaultSampleAgeID = {sample_age_id} WHERE SampleID = {sample_id}'''):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                        return
                    update_modified_timestamp('Samples', [sample_id])
                    print(f"Updated DefaultSampleAgeID to {sample_age_id} for SampleID {sample_id}")
                if old_sample_age_id != sample_age_id:
                    if not query.exec(f'''DELETE FROM Samples_SampleAges WHERE SampleID = {sample_id} AND SampleAgeID = {old_sample_age_id}'''):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
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

    def add_age(self):
        create_savepoint('before_add')
        query = QtS.QSqlQuery()
        if not query.exec(f'''INSERT INTO SampleAges (DirectAge, DirectAgeError, DirectAgeUnitID, DirectAgeErrorFormatID, OldestDirectAge, YoungestDirectAge, OldestAgeID, YoungestAgeID, SampleAgeDescription) 
                            VALUES (NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)'''):
            errtxt = query.lastError().text()
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
            return
        sample_age_id = query.lastInsertId()
        for sample_id in self.item_ids:
            if not query.exec(f'''INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) VALUES ({sample_id}, {sample_age_id})'''):
                errtxt = query.lastError().text()
                self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                return
        self.updated = True
        release_savepoint('before_add')
        self.clear_fields()
        self.populate_age_dropdown()
        self.edit_age_comboBox.setCurrentIndex(self.sample_age_model.rowCount() - 1)

    def clear_fields(self):
        self.disconnect_text_signals()
        self.default_age_checkBox.setChecked(False)
        self.edit_age_comboBox.setCurrentIndex(-1)
        self.direct_age_lineEdit.clear()
        self.direct_age_error_lineEdit.clear()
        self.direct_age_error_type_comboBox.setCurrentIndex(-1)
        self.oldest_direct_lineEdit.clear()
        self.youngest_direct_lineEdit.clear()
        self.direct_age_unit_comboBox.setCurrentIndex(-1)
        self.oldest_rel_comboBox.setCurrentIndex(-1)
        self.youngest_rel_comboBox.setCurrentIndex(-1)
        self.age_description_lineEdit.clear()
        self.age_constraint_comboBox.setCurrentIndex(-1)
        self.age_interpretation_comboBox.setCurrentIndex(-1)
        self.age_reference_comboBox.setCurrentIndex(-1)
        self.connect_signals()

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
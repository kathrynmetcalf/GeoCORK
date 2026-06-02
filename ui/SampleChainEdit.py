import os
import sys
import time

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS

import logger_setup

from Functions.Widget_classes import (
    CheckableTreeCombobox, populate_combo_box, CheckableComboBox, find_current_sub_items, get_name_from_id,
    find_tree_model, show_loading_dialog, close_loading_dialog, find_child_ids, update_modified_timestamp,
    get_id_from_name
)
from Functions import SQLUtils
from Functions.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint, SavepointManager
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.Database_views import ViewQuery

class SampleChainEdit(QtW.QDialog):
    def __init__(self, parent_window, child_table: str, current_parents: dict, child_ids: list):
        super().__init__(parent=parent_window)
        self.child_table = child_table
        self.current_parents = current_parents
        self.child_ids = child_ids
        self.updated = False
        self.close_by_dialog = False

        if not self.child_ids or not self.child_table:
            return
        if child_table not in ['Aliquots', 'Grains', 'Spots', 'UPbAnalyses']:
            logger_setup.get_logger().critical(f'Child table {child_table} not recognized')
            return

        logger_setup.get_logger().info(f'Opening new SampleChainEdit window for {self.child_table}')

        self.current_sample_id = None
        self.current_aliquot_id = None
        self.current_grain_id = None
        self.current_spot_id = None

        self.new_sample_id = None
        self.new_aliquot_id = None
        self.new_grain_id = None
        self.new_spot_id = None
        self.modes = ['Existing', 'Move', 'New']
        self.mode_tooltips = ['Assign subitems to an existing item', 'Move items at this level under a new item', 'Create a new item at this level']

        self.grid_layout = QtW.QGridLayout()
        self.horizontal_layout = QtW.QHBoxLayout()
        self.vertical_layout = QtW.QVBoxLayout()
        self.sample_mode_comboBox = QtW.QComboBox()
        self.sample_comboBox = CheckableComboBox()
        self.sample_comboBox.set_single_click(True)
        self.sample_current_label = QtW.QLabel()
        self.sample_lineEdit = None
        self.aliquot_mode_comboBox = QtW.QComboBox()
        self.aliquot_comboBox = CheckableTreeCombobox()
        self.aliquot_comboBox.set_single_click(True)
        self.aliquot_current_label = QtW.QLabel()
        self.aliquot_lineEdit = None
        self.grain_mode_comboBox = QtW.QComboBox()
        self.grain_comboBox = CheckableComboBox()
        self.grain_comboBox.set_single_click(True)
        self.grain_current_label = QtW.QLabel()
        self.grain_lineEdit = None
        self.spot_mode_comboBox = QtW.QComboBox()
        self.spot_comboBox = CheckableComboBox()
        self.spot_comboBox.set_single_click(True)
        self.spot_current_label = QtW.QLabel()
        self.spot_lineEdit = None
        self.commit_button = QtW.QPushButton('Commit')
        self.commit_button.setAutoDefault(False)
        self.cancel_button = QtW.QPushButton('Cancel')
        self.cancel_button.setAutoDefault(False)
        self.horizontal_layout.addWidget(self.cancel_button)
        self.horizontal_layout.addWidget(self.commit_button)
        self.vertical_layout.addLayout(self.grid_layout)
        self.vertical_layout.addLayout(self.horizontal_layout)
        self.setLayout(self.vertical_layout)

        self.msg = QtW.QMessageBox()

        self.populate_dialog()

        self.sample_mode_comboBox.currentIndexChanged.connect(self.mode_changed)
        self.aliquot_mode_comboBox.currentIndexChanged.connect(self.mode_changed)
        self.grain_mode_comboBox.currentIndexChanged.connect(self.mode_changed)
        self.spot_mode_comboBox.currentIndexChanged.connect(self.mode_changed)
        self.commit_button.clicked.connect(self.commit_question)
        self.cancel_button.clicked.connect(self.close)

    def populate_dialog(self):
        # Always include Samples
        show_loading_dialog('Loading', f'Populating window...')
        for i, value in enumerate(self.modes):
            if value != 'Move':
                self.sample_mode_comboBox.addItem(value)
                self.sample_mode_comboBox.setItemData(i, self.mode_tooltips[i], QtC.Qt.ItemDataRole.ToolTipRole)
        view_query = ViewQuery('Samples', True, **{'show_columns': settings.value('sample_edit_columns')[0:4]})
        populate_combo_box(self.sample_comboBox, **{'table': 'Samples', 'query': view_query.table_query, 'view_query': view_query})
        if 'Samples' in self.current_parents and self.current_parents["Samples"]:
            self.current_sample_id = self.current_parents["Samples"][0]
            current_sample_name = get_name_from_id('Samples', self.current_sample_id)
            if len(self.current_parents['Samples']) > 1:
                self.sample_current_label.setText(f'Current sample: Multiple')
            else:
                self.sample_current_label.setText(f'Current sample: {current_sample_name}')
            # Just check the first one regardless of how many there are, since the sample level is required and they should all be the same
            self.sample_comboBox.source_model().update_model_checks({self.current_sample_id}, {})
        else:
            self.sample_comboBox.clear_all_checks()
        self.new_sample_id = None
        self.grid_layout.addWidget(self.sample_current_label, 0, 0)
        self.grid_layout.addWidget(self.sample_mode_comboBox, 0, 1)
        self.grid_layout.addWidget(self.sample_comboBox, 0, 2)

        if self.child_table in ['Grains', 'Spots', 'UPbAnalyses']:
            for i, value in enumerate(self.modes):
                self.aliquot_mode_comboBox.addItem(value)
                self.aliquot_mode_comboBox.setItemData(i, self.mode_tooltips[i], QtC.Qt.ItemDataRole.ToolTipRole)
            self.update_aliquots()
            if 'Aliquots' in self.current_parents and self.current_parents["Aliquots"]:
                self.current_aliquot_id = self.current_parents["Aliquots"][0]
                current_aliquot_name = get_name_from_id('Aliquots', self.current_aliquot_id)
                aliquot_tree_model = find_tree_model(self.aliquot_comboBox.model(), None)[0]
                if len(self.current_parents['Aliquots']) > 1:
                    self.aliquot_current_label.setText(f'Current aliquot: Multiple')
                else:
                    self.aliquot_current_label.setText(f'Current aliquot: {current_aliquot_name}')
                aliquot_tree_model.update_model_checks({self.current_aliquot_id}, {})
            else:
                self.aliquot_comboBox.clear_all_checks()
            self.new_aliquot_id = self.current_aliquot_id
            self.aliquot_mode_comboBox.setCurrentIndex(0)
            self.grid_layout.addWidget(self.aliquot_current_label, 1, 0)
            self.grid_layout.addWidget(self.aliquot_mode_comboBox, 1, 1)
            self.grid_layout.addWidget(self.aliquot_comboBox, 1, 2)
            self.sample_comboBox.source_model().checksChanged.connect(self.update_aliquots)
            self.aliquot_comboBox.tree_model.checksChanged.connect(self.update_grains_spots)
        if self.child_table in ['Spots', 'UPbAnalyses']:
            for i, value in enumerate(self.modes):
                self.grain_mode_comboBox.addItem(value)
                self.grain_mode_comboBox.setItemData(i, value, QtC.Qt.ItemDataRole.ToolTipRole)
            if self.child_table == 'UPbAnalyses':
                for i, value in enumerate(self.modes):
                    self.spot_mode_comboBox.addItem(value)
                    self.spot_mode_comboBox.setItemData(i, value, QtC.Qt.ItemDataRole.ToolTipRole)
            self.update_grains_spots()
            if 'Grains' in self.current_parents:
                self.current_grain_id = self.current_parents["Grains"][0]
                if self.current_grain_id:
                    current_grain_name = get_name_from_id('Grains', self.current_grain_id)
                    if len(self.current_parents['Grains']) > 1:
                        current_grain_name = 'Multiple'
                    self.grain_comboBox.source_model().update_model_checks({self.current_grain_id}, {})
                else:
                    current_grain_name = 'None'
                    self.grain_comboBox.clear_all_checks()
                self.grain_current_label.setText(f'Current grain (optional): {current_grain_name}')
            else:
                self.grain_comboBox.setCurrentText('')
            self.new_grain_id = self.current_grain_id
            self.grain_mode_comboBox.setCurrentIndex(0)
            self.grid_layout.addWidget(self.grain_current_label, 2, 0)
            self.grid_layout.addWidget(self.grain_mode_comboBox, 2, 1)
            self.grid_layout.addWidget(self.grain_comboBox, 2, 2)
            self.grain_comboBox.source_model().checksChanged.connect(self.update_spots)
        if self.child_table == 'UPbAnalyses':
            self.update_spots()
            if 'Spots' in self.current_parents:
                self.current_spot_id = self.current_parents["Spots"][0]
                current_spot_name = get_name_from_id('Spots', self.current_spot_id)
                if len(self.current_parents['Spots']) > 1:
                    self.spot_current_label.setText(f'Current spot: Multiple')
                else:
                    self.spot_current_label.setText(f'Current spot: {current_spot_name}')
                self.spot_comboBox.source_model().update_model_checks({self.current_spot_id}, {})
            else:
                self.spot_comboBox.setCurrentText('')
            self.new_spot_id = self.current_spot_id
            self.grid_layout.addWidget(self.spot_current_label, 3, 0)
            self.grid_layout.addWidget(self.spot_mode_comboBox, 3, 1)
            self.grid_layout.addWidget(self.spot_comboBox, 3, 2)
        close_loading_dialog('Loading', 'Populating window...')

    def update_aliquots(self):
        if self.aliquot_mode_comboBox.currentText() != 'Existing':
            return
        show_loading_dialog('Loading', 'Updating aliquots...')
        if self.sample_comboBox.source_model().checked_ids:
            new_sample_id = list(self.sample_comboBox.source_model().checked_ids)[0]
        else:
            new_sample_id = None
        if not new_sample_id and self.sample_comboBox.model().rowCount()>0:
            # Check the first one
            new_sample_id = self.sample_comboBox.source_model().index(0, 1).data(QtC.Qt.ItemDataRole.DisplayRole)
            self.sample_comboBox.source_model().update_model_checks({new_sample_id}, {})
        elif not new_sample_id and (self.sample_mode_comboBox.currentText() == 'New' or self.sample_comboBox.model().rowCount()==0):
            self.aliquot_comboBox.clear()
            close_loading_dialog('Loading', 'Updating aliquots...')
        if new_sample_id != self.new_sample_id:
            self.new_sample_id = new_sample_id
        query_args = {'show_columns': settings.value(SQLUtils.view_setting_dict['AliquotEditView']), 'where': f' WHERE SampleID = {self.new_sample_id}'}
        view_query = ViewQuery('Aliquots', True, **query_args)
        table_query = view_query.table_query
        populate_combo_box(self.aliquot_comboBox, **{'table': 'Aliquots', 'query': table_query, 'view_query': view_query})
        close_loading_dialog('Loading', 'Updating aliquots...')

    def update_grains_spots(self):
        if self.grain_mode_comboBox.currentText() != 'Existing':
            return
        show_loading_dialog('Loading', 'Updating grains...')
        aliquot_tree_model = self.aliquot_comboBox.tree_model
        if aliquot_tree_model.checked_ids:
            new_aliquot_id = list(aliquot_tree_model.checked_ids)[0]
        else:
            new_aliquot_id = None
        if not new_aliquot_id and aliquot_tree_model.rowCount(QtC.QModelIndex())>0:
            # Check the first one
            new_aliquot_id = aliquot_tree_model.index(0, 1, QtC.QModelIndex()).data(QtC.Qt.ItemDataRole.DisplayRole)
            aliquot_tree_model.update_model_checks({new_aliquot_id}, {})
        if new_aliquot_id != self.new_aliquot_id:
            self.new_aliquot_id = new_aliquot_id
        show_columns = settings.value(SQLUtils.view_setting_dict['GrainEditView'])
        query_args = {'show_columns': show_columns, 'where': f'WHERE AliquotID = {self.new_aliquot_id}'}
        view_query = ViewQuery('Grains', True, **query_args)
        table_query = view_query.table_query
        populate_combo_box(self.grain_comboBox, **{'table': 'Grains', 'query': table_query, 'view_query': view_query})
        self.grain_comboBox.setCurrentText('')
        close_loading_dialog('Loading', 'Updating grains...')
        self.update_spots()

    def update_spots(self):
        if self.spot_mode_comboBox.currentText() != 'Existing':
            return
        show_loading_dialog('Loading', 'Updating spots...')
        if self.grain_comboBox.source_model().checked_ids:
            new_grain_id = list(self.grain_comboBox.source_model().checked_ids)[0]
        else:
            new_grain_id = None
        if not new_grain_id:
            query_args = {'show_columns': settings.value(SQLUtils.view_setting_dict['SpotEditView']), 'where': f'WHERE AliquotID = {self.new_aliquot_id}'}
            view_query = ViewQuery('Spots', True, **query_args)
            table_query = view_query.table_query
            populate_combo_box(self.spot_comboBox, **{'table': 'Spots', 'query': table_query, 'view_query': view_query})
        else:
            if new_grain_id != self.new_grain_id:
                self.new_grain_id = new_grain_id
            populate_combo_box(self.spot_comboBox, **{'table': 'Spots', 'query': f'SELECT * FROM Spots WHERE AliquotID = {self.new_aliquot_id} AND GrainID = {self.new_grain_id}'})
        close_loading_dialog('Loading', 'Updating spots...')

    def mode_changed(self):
        mode_combo: QtW.QComboBox() = self.sender()
        if mode_combo == self.sample_mode_comboBox:
            name_combo: CheckableComboBox = self.sample_comboBox
            line_edit = self.sample_lineEdit
            edit_row = 0
        elif mode_combo == self.aliquot_mode_comboBox:
            name_combo: CheckableTreeCombobox = self.aliquot_comboBox
            line_edit = self.aliquot_lineEdit
            edit_row = 1
        elif mode_combo == self.grain_mode_comboBox:
            name_combo: CheckableComboBox = self.grain_comboBox
            line_edit = self.grain_lineEdit
            edit_row = 2
        elif mode_combo == self.spot_mode_comboBox:
            name_combo: CheckableComboBox = self.spot_comboBox
            line_edit = self.spot_lineEdit
            edit_row = 3
        else:
            return
        if mode_combo.currentText() == 'Existing':
            name_combo.setHidden(False)
            name_combo.setEnabled(True)
            if line_edit:
                line_edit = None
        elif mode_combo.currentText() == 'Move':
            name_combo.setHidden(False)
            name_combo.setEnabled(False)
            if line_edit:
                line_edit = None
        elif mode_combo.currentText() == 'New':
            name_combo.setHidden(True)
            name_combo.setEnabled(False)
            line_edit = QtW.QLineEdit()
            self.grid_layout.addWidget(line_edit, edit_row, 2)
        if mode_combo == self.sample_mode_comboBox:
            self.sample_lineEdit = line_edit
            self.new_sample_id = None
        elif mode_combo == self.aliquot_mode_comboBox:
            self.aliquot_lineEdit = line_edit
            self.new_aliquot_id = None
        elif mode_combo == self.grain_mode_comboBox:
            self.grain_lineEdit = line_edit
            self.new_grain_id = None
        elif mode_combo == self.spot_mode_comboBox:
            self.spot_lineEdit = line_edit
            self.new_spot_id = None

    def save_changes(self):
        self.check_updated()
        if self.updated:
            if not self.new_sample_id and self.sample_mode_comboBox.currentText() == 'Existing':
                logger_setup.get_logger().error(f'Sample required for {self.child_table}')
                return False
            create_savepoint('before_update_chain')
            changes_msg = ''
            query = QtS.QSqlQuery()
            new_sample_name = None
            new_aliquot_name = None
            new_grain_name = None
            new_spot_name = None
            # If there is a new sample name
            if self.sample_lineEdit and self.sample_lineEdit.text() and self.sample_mode_comboBox.currentText() == 'New':
                new_sample_name = self.sample_lineEdit.text()
                query.prepare(f'INSERT INTO Samples(SampleName) VALUES (?)')
                query.bindValue(0, new_sample_name)
                if not query.exec():
                    if 'UNIQUE constraint failed: Samples.SampleName' in query.lastError().text():
                        logger_setup.get_logger().error(f'Sample name "{new_sample_name}" already exists in the database. Names must be unique.')
                    else:
                        logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                    rollback_savepoint('before_update_chain')
                    return False
                self.new_sample_id = query.lastInsertId()
            # If there is a new aliquot name
            if self.aliquot_lineEdit and self.aliquot_lineEdit.text() and self.aliquot_mode_comboBox.currentText() == 'New':
                new_aliquot_name = self.aliquot_lineEdit.text()
                aliquot_rows = []
                if not query.exec(f'SELECT AliquotParentRow FROM Aliquots WHERE ParentAliquotID IS NULL'):
                    logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    rollback_savepoint('before_update_chain')
                    return False
                while query.next():
                    aliquot_rows.append(query.value(0))
                aliquot_rows.sort(reverse=True)
                parent_row = aliquot_rows[0] + 1
                query.prepare(f'INSERT INTO Aliquots(AliquotParentRow, AliquotName, SampleID) VALUES (?, ?, ?)')
                query.bindValue(0, parent_row)
                query.bindValue(1, new_aliquot_name)
                query.bindValue(2, self.new_sample_id)
                if not query.exec():
                    if 'UNIQUE constraint failed: Aliquots.AliquotName' in query.lastError().text():
                        logger_setup.get_logger().error(f'Aliquot name {new_aliquot_name} already exists in the database. Names must be unique.')
                    else:
                        logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                    rollback_savepoint('before_update_chain')
                    return False
                self.new_aliquot_id = query.lastInsertId()
            elif self.aliquot_mode_comboBox.currentText() == 'Move':
                if not self.new_aliquot_id:
                    logger_setup.get_logger().error(f'Aliquot required for {self.child_table}')
                    return False
                if not query.exec(f'SELECT ParentAliquotID, AliquotParentRow, SampleID FROM Aliquots WHERE AliquotID = {self.new_aliquot_id}'):
                    logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    rollback_savepoint('before_update_chain')
                    return False
                query.next()
                parent_id = query.value(0)
                parent_row = query.value(1)
                sample_id = query.value(2)
                if sample_id != self.new_sample_id:
                    # Need to update the sample ID for this Aliquot
                    if parent_id not in ['', 'NULL', None]:
                        # Sub aliquot, so make it its own top-level aliquot
                        aliquot_rows = []
                        if not query.exec(f'SELECT AliquotParentRow FROM Aliquots WHERE ParentAliquotID IS NULL'):
                            logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                            rollback_savepoint('before_update_chain')
                            return False
                        while query.next():
                            aliquot_rows.append(query.value(0))
                        aliquot_rows.sort(reverse=True)
                        parent_row = aliquot_rows[0] + 1
                    if not query.exec(f'UPDATE Aliquots SET (SampleID, ParentAliquotID, AliquotParentRow) = ({self.new_sample_id}, NULL, {parent_row}) WHERE AliquotID = {self.new_aliquot_id}'):
                        logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        rollback_savepoint('before_update_chain')
                        return False
                    update_modified_timestamp('Aliquots', [self.new_aliquot_id])
                changes_msg += f'Aliquot {get_name_from_id("Aliquots", self.new_aliquot_id)} with all its spots and analyses moved to sample {get_name_from_id("Samples", self.new_sample_id)}.\n'
            if self.grain_lineEdit and self.grain_lineEdit.text() and self.grain_mode_comboBox.currentText() == 'New':
                new_grain_name = self.grain_lineEdit.text()
                query.prepare(f'INSERT INTO Grains(GrainName) VALUES (?)')
                query.bindValue(0, new_grain_name)
                if not query.exec():
                    if 'UNIQUE constraint failed: Grains.GrainName' in query.lastError().text():
                        logger_setup.get_logger().error(f'Grain name "{new_grain_name}" already exists in the database. Names must be unique.')
                    else:
                        logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                    rollback_savepoint('before_update_chain')
                    return False
                self.new_grain_id = query.lastInsertId()
            if self.spot_lineEdit and self.spot_lineEdit.text() and self.spot_mode_comboBox.currentText() == 'New':
                new_spot_name = self.spot_lineEdit.text()
                query.prepare(f'INSERT INTO Spots(SpotName, AliquotID, GrainID) VALUES (?,?,?)')
                query.bindValue(0, new_spot_name)
                query.bindValue(1, self.new_aliquot_id)
                if self.new_grain_id:
                    query.bindValue(2, self.new_grain_id)
                else:
                    query.bindValue(2, QtC.QVariant())
                if not query.exec():
                    if 'UNIQUE constraint failed: Spots.SpotName' in query.lastError().text():
                        logger_setup.get_logger().error(f'Spot name "{new_spot_name}" already exists in the database. Names must be unique.')
                    else:
                        logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                    rollback_savepoint('before_update_chain')
                    return False
                self.new_spot_id = query.lastInsertId()
            elif self.spot_mode_comboBox.currentText() == 'Move':
                if self.child_table == 'UPbAnalyses' and not self.new_spot_id:
                    logger_setup.get_logger().error(f'Spot required for {self.child_table}')
                    return False
                if not query.prepare(f'UPDATE Spots SET (AliquotID, GrainID) = (?,?) WHERE SpotID = {self.new_spot_id}'):
                    logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    rollback_savepoint('before_update_chain')
                    return False
                update_modified_timestamp('Spots', [self.new_spot_id])
                query.bindValue(0, self.new_aliquot_id)
                if self.new_grain_id:
                    query.bindValue(1, self.new_grain_id)
                else:
                    query.bindValue(1, QtC.QVariant())
                if not query.exec():
                    logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                    rollback_savepoint('before_update_chain')
                    return False
            elif self.grain_mode_comboBox.currentText() == 'Move' and self.new_grain_id:
                related_spot_ids = find_current_sub_items([self.new_grain_id], 'Grains')[0]
                if len(related_spot_ids) > 1:
                    sql_where = f'IN ({", ".join(str(spot_id) for spot_id in related_spot_ids)})'
                elif len(related_spot_ids) == 1:
                    sql_where = f'= {related_spot_ids[0]}'
                if not query.prepare(f'UPDATE Spots SET (AliquotID, GrainID) = (?,?) WHERE SpotID = {sql_where}'):
                    logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    rollback_savepoint('before_update_chain')
                    return False
                query.bindValue(0, self.new_aliquot_id)
                query.bindValue(1, self.new_grain_id)
                if not query.exec():
                    logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                    rollback_savepoint('before_update_chain')
                    return False
                update_modified_timestamp('Spots', related_spot_ids)
                changes_msg += f'Grain {get_name_from_id("Grains", self.new_grain_id)} with all its spots and analyses moved to aliquot {get_name_from_id("Aliquots", self.new_aliquot_id)}.\n'
            if len(self.child_ids) == 1:
                sql_where = f'= {self.child_ids[0]}'
            else:
                sql_where = f'IN ({", ".join(str(child_id) for child_id in self.child_ids)})'
            if self.child_table == 'UPbAnalyses':
                if not self.new_spot_id:
                    logger_setup.get_logger().error(f'Spot required for {self.child_table}')
                    return False
                if not query.exec(f'UPDATE UPbAnalyses SET SpotID = {self.new_spot_id} WHERE UPbAnalysisID {sql_where}'):
                    logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    rollback_savepoint('before_update_chain')
                    return False
                update_modified_timestamp('UPbAnalyses', self.child_ids)
            elif self.child_table == 'Spots':
                if not self.new_aliquot_id:
                    logger_setup.get_logger().error(f'Aliquot required for {self.child_table}')
                    return False
                query.prepare(f'UPDATE Spots SET (AliquotID, GrainID) = (?, ?) WHERE SpotID {sql_where}')
                query.bindValue(0, self.new_aliquot_id)
                if self.new_grain_id:
                    query.bindValue(1, self.new_grain_id)
                else:
                    query.bindValue(1, QtC.QVariant())
                if not query.exec():
                    logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                    rollback_savepoint('before_update_chain')
                    return False
                update_modified_timestamp('Spots', self.child_ids)
            elif self.child_table == 'Grains':
                if not self.new_aliquot_id:
                    logger_setup.get_logger().error(f'Aliquot required for {self.child_table}')
                    return False
                select_query = QtS.QSqlQuery()
                if not select_query.exec(f'SELECT SpotID FROM Spots WHERE AliquotID = {self.new_aliquot_id} AND GrainID {sql_where}'):
                    logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    rollback_savepoint('before_update_chain')
                    return False
                spot_ids = []
                while select_query.next():
                    spot_ids.append(select_query.value(0))
                if not query.exec(f'UPDATE Spots SET AliquotID = {self.new_aliquot_id} WHERE GrainID {sql_where}'):
                    logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    rollback_savepoint('before_update_chain')
                    return False
                update_modified_timestamp('Spots', spot_ids)
            elif self.child_table == 'Aliquots':
                if not self.new_sample_id:
                    logger_setup.get_logger().error(f'Sample required for {self.child_table}')
                    return False
                update_sample_ids = []
                update_aliquot_parent_ids = []
                if not query.exec(f'SELECT AliquotID, ParentAliquotID, SampleID FROM Aliquots WHERE AliquotID {sql_where}'):
                    logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    rollback_savepoint('before_update_chain')
                    return False
                while query.next():
                    sample_id = query.value(2)
                    if sample_id != self.new_sample_id:
                        aliquot_id = query.value(0)
                        update_sample_ids.append(aliquot_id)
                        parent_id = query.value(1)
                        if parent_id and parent_id not in self.child_ids:
                            update_aliquot_parent_ids.append(aliquot_id)
                if update_aliquot_parent_ids:
                    aliquot_rows = []
                    if not query.exec(f'SELECT AliquotParentRow FROM Aliquots WHERE ParentAliquotID IS NULL'):
                        logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        rollback_savepoint('before_update_chain')
                        return False
                    while query.next():
                        aliquot_rows.append(query.value(0))
                    aliquot_rows.sort(reverse=True)
                    parent_row = aliquot_rows[0]
                    for aliquot_id in self.child_ids:
                        parent_row += 1
                        if not query.exec(f'UPDATE Aliquots SET (ParentAliquotID, AliquotParentRow) = (NULL, {parent_row}) WHERE AliquotID = {aliquot_id}'):
                            logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                            rollback_savepoint('before_update_chain')
                            return False
                    update_modified_timestamp('Aliquots', self.child_ids)
                if update_sample_ids:
                    child_ids = []
                    for parent_aliquot_id in update_sample_ids:
                        child_ids.extend(find_child_ids('Aliquots', parent_aliquot_id))
                    update_sample_ids.extend(child_ids)
                    if len(update_sample_ids) == 1:
                        aliquot_where = f'= {update_sample_ids[0]}'
                    else:
                        aliquot_where = f'IN ({", ".join(str(update_id) for update_id in update_sample_ids)})'
                    if not query.exec(f'UPDATE Aliquots SET SampleID = {self.new_sample_id} WHERE AliquotID {aliquot_where}'):
                        logger_setup.get_logger().critical(f'Error updating sample chain for {self.child_table}')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        rollback_savepoint('before_update_chain')
                        return False
                    update_modified_timestamp('Aliquots', update_sample_ids)
            if changes_msg:
                dlg = QtW.QMessageBox()
                dlg.setIcon(QtW.QMessageBox.Icon.Information)
                dlg.setText(f'Changes extend beyond selected {self.child_table}.')
                dlg.setInformativeText(changes_msg)
                dlg.setStandardButtons(QtW.QMessageBox.StandardButton.Ok | QtW.QMessageBox.StandardButton.Cancel)
                dlg.setDefaultButton(QtW.QMessageBox.StandardButton.Ok)
                response = dlg.exec()
                if response == QtW.QMessageBox.StandardButton.Cancel:
                    rollback_savepoint('before_update_chain')
                    return False
        logger_setup.get_logger().info(f'Sample chain for {self.child_table} has been updated.')
        return True

    def check_updated(self):
        if self.sample_comboBox.source_model().checked_ids and not self.sample_lineEdit:
            self.new_sample_id = list(self.sample_comboBox.source_model().checked_ids)[0]
        else:
            self.new_sample_id = None
        if self.aliquot_comboBox.model().rowCount(QtC.QModelIndex())>0:
            aliquot_tree_model = find_tree_model(self.aliquot_comboBox.model(), None)[0]
            if aliquot_tree_model.checked_ids and not self.aliquot_lineEdit:
                self.new_aliquot_id = list(aliquot_tree_model.checked_ids)[0]
            else:
                self.new_aliquot_id = None
        if self.grain_comboBox.model().rowCount()>0 and self.grain_comboBox.source_model().checked_ids and not self.grain_lineEdit:
            self.new_grain_id = list(self.grain_comboBox.source_model().checked_ids)[0]
        else:
            self.new_grain_id = None
        if self.spot_comboBox.model().rowCount()>0 and self.spot_comboBox.source_model().checked_ids and not self.spot_lineEdit:
            self.new_spot_id = list(self.spot_comboBox.source_model().checked_ids)[0]
        else:
            self.new_spot_id = None
        if (self.new_sample_id == self.current_sample_id and self.new_aliquot_id == self.current_aliquot_id
                and (self.new_grain_id==self.current_grain_id or (not self.new_grain_id and not self.current_grain_id))
                and self.new_spot_id == self.new_spot_id):
            self.updated = False
        else:
            self.updated = True
        if ((self.sample_lineEdit and self.sample_lineEdit.text()) or
                (self.aliquot_lineEdit and self.aliquot_lineEdit.text()) or
                (self.grain_lineEdit and self.grain_lineEdit.text()) or
                (self.spot_lineEdit and self.spot_lineEdit.text())):
            self.updated = True

    def commit(self):
        self.accept()
        self.close_by_dialog = True
        release_savepoint('before_update_chain')
        self.close()
        self.close_by_dialog = False
        self.accept()

    def commit_question(self):
        self.check_updated()
        if self.updated:
            if not self.save_changes():
                return
            msg_box = QtW.QMessageBox()
            msg_box.setIcon(QtW.QMessageBox.Icon.Question)
            msg_box.setText('Are you sure you want to commit all changes to the database?')
            msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
            response = msg_box.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                self.commit()
            else:
                pass
        else:
            self.close_by_dialog = True
            self.close()

    def discard_question(self):
        self.check_updated()
        if self.updated:
            response = self.msg.question(self, 'Discard changes', 'Are you sure you want to discard all changes?',
                                         QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No,
                                         QtW.QMessageBox.StandardButton.No)
            if response == QtW.QMessageBox.StandardButton.Yes:
                rollback_savepoint('before_update_chain')
                self.updated = False
                self.close_by_dialog = True
                self.close()
            else:
                pass
        else:
            self.close_by_dialog = True
            self.close()

    def close(self):
        if not self.close_by_dialog:
            self.discard_question()
        else:
            logger_setup.get_logger().info(f'Closing {self.child_table} chain edit dialog')
            super().close()
import os
import sys
import time
from operator import index

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import QPoint, QSize
from PyQt6.uic import loadUi
import Functions.Text_manipulations as TxM
import logger_setup
import difflib
from Functions.Widget_classes import (
    TreeModel, CheckableTreeCombobox, CheckableTreeModel, CheckableTreeView, ReadableProxyModel, DisplayRoundedModel,
    SQLiteTableModel, CheckableComboBox, CheckableSqlTableModel, CheckableSqlQueryModel, get_headers, name_column,
    set_table, VerifiableSqlTableModel, VerifiableSqlViewModel
)
from Functions import SQLUtils
from Functions.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint, SavepointManager
from Functions.Settings_manager import settings
from Functions.Database_manager import update_database
from ui.AddTags import AddTags
from ui.GPSDialog import GPSDialog
from ui.New_reference import NewReference
from ui.AgeDialog import AgeDialog

class EditView(QtW.QDialog):
    def __init__(self, table_name, parent_id: int=None, parent_type: str=None):
        super().__init__()
        logger_setup.get_logger().info(f'Creating a new EditView for {table_name}')
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "EditTable.ui")
        loadUi(sources_ui_file, self)
        self.setModal(True)
        self.setWindowTitle(f'Edit {TxM.add_spaces_camel(table_name)}')
        self.updated = False

        self.table = TxM.remove_spaces(table_name)
        self.msg = QtW.QMessageBox(self)
        self.view = None
        self.model = None
        self.show_cols = []
        self.where = ''
        if self.table in SQLUtils.trigger_tables:
            if self.table == 'Columns':
                self.view = 'ColumnEditView'
                self.show_cols = settings.value('column_edit_columns')
            elif self.table == 'Samples':
                self.view = 'SampleEditView'
                self.show_cols = settings.value('sample_edit_columns')
            elif self.table == 'Spots' or self.table == 'UPbAnalyses':
                self.parent_id = parent_id
                self.parent_type = parent_type
                self.parent_id_header = 'SampleID' if self.parent_type == 'Sample' else 'AliquotID' if self.parent_type == 'Aliquot' else 'SpotID' if parent_type == 'Spot' else None
                if self.table == 'Spots':
                    self.view = 'SpotEditView'
                    self.show_cols = settings.value('spot_edit_columns')
                elif self.table == 'UPbAnalyses':
                    self.view = 'UPbEditView'
                    self.show_cols = ', '.join(settings.value('upb_analysis_edit_columns'))
                self.where = f' WHERE {self.parent_id_header} = {self.parent_id}'
            elif self.table == 'References':
                self.view = 'ReferenceEditView'
                self.show_cols = settings.value('reference_edit_columns')
            self.update_model()
        self.tree_combo = None
        self.combo = None
        self.combo_index = QtC.QModelIndex()
        self.combo_model = None
        self.lineEdit = None
        # self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnFieldChange)
        self.msg = QtW.QMessageBox(self)
        self.close_by_dialog = False
        self.view_headers = []
        if self.view is not None:
            self.view_headers = get_headers(self.view)
        self.table_headers = get_headers(self.table)
        self.proxy_model = ReadableProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.display_table()
        create_savepoint('before_edit')

        self.proxy_model.dataChanged.connect(self.update_model)
        # self.combo.closing.connect(self.destroy_dropdown)
        # self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        self.cancel_pushButton.clicked.connect(self.rollback)
        self.edit_tableView.clicked.connect(self.display_widget)

    def update_model(self):
        self.model = SQLiteTableModel(f'SELECT {', '.join(self.show_cols)} FROM {self.view} {self.where}')


    def eventFilter(self, object, event):
        if self.combo:
            objects_statement = object is self.combo or object is self.lineEdit or object is self.combo.view()
        else:
            objects_statement = object is self.lineEdit
        if objects_statement:
            # the object is one of the widgets we are interested in
            if event.type() == QtC.QEvent.Type.KeyPress and event.key() == QtC.Qt.Key.Key_Tab:
                self.advance_tab()
                self.display_widget()
                return True
            if event.type() == QtC.QEvent.Type.KeyPress and event.key() == QtC.Qt.Key.Key_Backtab:
                self.reverse_tab()
                self.display_widget()
                return True
            return super().eventFilter(object, event)
        if object is self.lineEdit:
            if event.type() == QtC.QEvent.Type.KeyPress and event.key() in (QtC.Qt.Key.Key_Return, QtC.Qt.Key.Key_Enter):
                self.destroy_lineedit()
                return True
        return super().eventFilter(object, event)

    def show_context_menu(self, pos):
        indexes = self.edit_tableView.selectedIndexes()
        if not indexes:
            return
        menu = QtW.QMenu()
        if len(indexes) == 1:
            if not indexes[0].isValid():
                return
            clear_action = menu.addAction('Clear value')
        else:
            clear_action = None
        edit_action = menu.addAction('Edit')
        delete_action = menu.addAction('Delete row')
        action = menu.exec(self.edit_tableView.viewport().mapToGlobal(pos))
        if action == clear_action:
            self.model.setData(indexes[0], '', QtC.Qt.ItemDataRole.EditRole)
        elif action == edit_action:
            self.display_widget()
        elif action == delete_action:
            self.msg.warning(self, 'Delete row', 'Are you sure you want to delete the selected rows?', QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
            self.msg.setDefaultButton(QtW.QMessageBox.StandardButton.No)
            response = self.msg.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                # get all the rows in the selected indexes
                rows = []
                for index in indexes:
                    if index.row() not in rows:
                        rows.append(index.row())
                for row in rows:
                    if not self.model.deleteRowFromTable(row):
                        errtxt = f'Failed to delete row {row} from {self.table}: {self.model.lastError().text()}'
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def display_table(self):
        self.edit_tableView.setModel(self.proxy_model)
        # self.edit_tableView.setModel(self.filter_proxy_model)
        for column in range(self.proxy_model.columnCount()):
            header = self.model.headerData(column, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            if 'ID' in header:
                self.edit_tableView.hideColumn(column)
        self.edit_tableView.resizeColumnsToContents()
        self.edit_tableView.setSortingEnabled(True)

    def display_widget(self):
        logger_setup.get_logger().info('Displaying widget')
        selected_index = self.edit_tableView.selectedIndexes()[0]
        if not selected_index.isValid():
            return
        if self.lineEdit is not None:
            self.destroy_lineedit()
            if self.lineEdit is not None:
                logger_setup.get_logger().info('Error destroying previous line edit')
                return
        elif self.combo is not None:
            self.destroy_dropdown()
            if self.combo is not None:
                logger_setup.get_logger().info('Error destroying previous dropdown')
                return
        header = self.model.headerData(selected_index.column(), QtC.Qt.Orientation.Horizontal,
                                                    QtC.Qt.ItemDataRole.DisplayRole)

        if 'GPS' in header or 'Elevation' in header:
            if not self.tabbed_from_editor:
                # Do not open the popup if tabbing here, only when double-clicking
                if self.table == 'Samples':
                    item_id_header = 'SampleID'
                elif self.table == 'Columns':
                    item_id_header = 'ColumnID'
                else:
                    return
                item_ids = []
                row = selected_index.row()
                item_ids.append(self.model.record(row).value(item_id_header))
                dlg = GPSDialog(self.table, item_ids)
                dlg.exec()
                self.display_table()
            else:
                self.edit_tableView.setFocus()
        elif 'SampleAgeCalculated' in header:
            if not self.tabbed_from_editor:
                if self.table == 'Samples':
                    item_id_header = 'SampleID'
                else:
                    return
                item_ids = []
                row = selected_index.row()
                item_ids.append(self.model.record(row).value(item_id_header))
                dlg = AgeDialog(self.table, item_ids)
                dlg.exec()
                self.display_table()
            else:
                self.edit_tableView.setFocus()
        else:
            dropdown_table = ''
            if 'Rejected' in header:
                # todo: add functionality to change accepted/rejected status
                dropdown_table = 'Rejected'
            else:
                for key, values in SQLUtils.many_editable.items():
                    if key == self.table:
                        for col_key in values.keys():
                            if header == col_key:
                                dropdown_table = values[header]
                                break
                        if dropdown_table == '':
                            logger_setup.get_logger().info(f'No matches found for {header} in {key}')
                            break
                if dropdown_table == '':
                    for key, values in SQLUtils.one_editable.items():
                        if key == self.table:
                            for col_key in values.keys():
                                if header == col_key:
                                    dropdown_table = values[header]
                                    break
                            if dropdown_table == '':
                                logger_setup.get_logger().info(f'No matches found for {header} in {key}')
                                break
            if dropdown_table == '':
                for key, values in SQLUtils.non_editable.items():
                    if key == self.table:
                        for col in values:
                            if header == col:
                                logger_setup.get_logger().info(f'{header} is non-editable')
                                return
                        break
                self.display_lineedit()
            else:
                self.display_dropdown(dropdown_table)

    def display_lineedit(self):
        selected_index = self.edit_tableView.selectedIndexes()[0]
        self.edit_index = selected_index
        self.lineEdit = QtW.QLineEdit()
        # self.lineEdit.setValidator(QtG.QRegularExpressionValidator(QtC.QRegularExpression("[0-9]*")))
        if not selected_index.data(QtC.Qt.ItemDataRole.DisplayRole):
            self.lineEdit.setText('')
        else:
            self.lineEdit.setText(str(selected_index.data(QtC.Qt.ItemDataRole.DisplayRole)))
            self.lineEdit.selectAll()
        self.lineEdit.installEventFilter(self)
        self.lineEdit.returnPressed.connect(self.destroy_lineedit)
        self.lineEdit.editingFinished.connect(self.destroy_lineedit)
        self.edit_tableView.setIndexWidget(selected_index, self.lineEdit)
        self.lineEdit.setFocus()

    def destroy_lineedit(self):
        if self.lineEdit is not None:
            value = self.lineEdit.text()
            # print(f'Typed: {value}')
            if self.model.setData(self.edit_index, value, QtC.Qt.ItemDataRole.EditRole):
                if self.edit_tableView.currentIndex() == self.edit_index:
                    self.tabbed_from_editor = False
                self.lineEdit.removeEventFilter(self)
                self.lineEdit.editingFinished.disconnect(self.destroy_lineedit)
                self.lineEdit.returnPressed.disconnect(self.destroy_lineedit)
                self.edit_tableView.setIndexWidget(self.edit_index, None)
                self.lineEdit = None
                self.edit_index = QtC.QModelIndex()
                self.edit_tableView.setFocus()
            else:
                errtxt = f'Failed to set data: {self.model.lastError().text()}'
                self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                self.lineEdit.setFocus()

    def display_dropdown(self, dropdown_table: str):
        logger_setup.get_logger().info(f'Displaying dropdown for {dropdown_table}')
        selected_index = self.edit_tableView.selectedIndexes()[0]
        self.combo_index = selected_index
        self.model = QtS.QSqlTableModel()
        set_table(self.model, dropdown_table)
        name_col = name_column(dropdown_table)
        self.combo = QtW.QComboBox()
        if dropdown_table in SQLUtils.user_viewable_trees:
            self.combo = CheckableTreeCombobox()
            self.combo_model = CheckableTreeModel()
            self.combo_model.setSourceModel(self.model)
        elif dropdown_table == 'Rejected':
            self.combo = QtW.QComboBox()
            self.combo.addItem('Accepted')
            self.combo.addItem('Rejected')
        else:
            if 'Abbreviation' in self.model.headerData(name_col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole):
                self.combo = QtW.QComboBox()
                self.combo_model = self.model
            else:
                self.combo = CheckableComboBox()
                self.combo_model = CheckableSqlTableModel()
                self.combo_model.setTable(dropdown_table)
            self.combo.setModel(self.combo_model)
            self.combo.setModelColumn(name_column(dropdown_table))
            for col in range(1,self.combo_model.columnCount()):
                header = self.combo_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
                if 'Abbreviation' in header:
                    # Only show the abbreviation column and hide all the others
                    self.combo.setModelColumn(col)
                    break
        selected_text = self.combo_index.data(QtC.Qt.ItemDataRole.DisplayRole)
        self.combo.setCurrentText(selected_text)
        # print(f"Selected text: {selected_text}")
        self.edit_tableView.setIndexWidget(selected_index, self.combo)
        self.combo.installEventFilter(self)
        self.combo.view().installEventFilter(self)
        self.combo.activated.connect(self.destroy_dropdown)
        self.combo.setFocus()
        # print("showing popup")
        self.combo.showPopup()

    def destroy_dropdown(self):
        logger_setup.get_logger().info('Saving data from dropdown')
        self.edit_tableView: QtW.QTableView
        if self.combo is not None:
            combo = self.combo
        elif self.tree_combo is not None:
            combo = self.tree_combo
        self.model.setData(self.combo_index, combo.currentText(), QtC.Qt.ItemDataRole.EditRole)
        if self.edit_tableView.currentIndex() == self.combo_index:
            self.tabbed_from_editor = False
        combo.activated.disconnect(self.destroy_dropdown)
        combo.removeEventFilter(self)
        combo.view().removeEventFilter(self)
        self.edit_tableView.setIndexWidget(self.combo_index, None)
        if self.combo is not None:
            self.combo = None
        elif self.tree_combo is not None:
            self.tree_combo = None
        self.combo_index = QtC.QModelIndex()

    def advance_tab(self):
        currentIndex = self.edit_tableView.currentIndex()
        if currentIndex.isValid():
            if currentIndex.column() == self.model.columnCount() - 1:
                if currentIndex.row() == self.model.rowCount() - 1:
                    # advance to the beginning of the table
                    next_index = self.model.index(0, 0)
                else:
                    # advance to the beginning of the next row
                    next_index = self.model.index(currentIndex.row() + 1, 0)
            else:
                # advance to the next column
                next_index = self.model.index(currentIndex.row(), currentIndex.column() + 1)
            if next_index.isValid():
                self.edit_tableView.setCurrentIndex(next_index)
                self.tabbed_from_editor = True

    def reverse_tab(self):
        currentIndex = self.edit_tableView.currentIndex()
        if currentIndex.isValid():
            if currentIndex.column() == 1:
                # ID column is hidden, so can't go back to it
                if currentIndex.row() == 0:
                    # reverse to the end of the table
                    next_index = self.model.index(self.model.rowCount() - 1, self.model.columnCount() - 1)
                else:
                    # reverse to the end of the previous row
                    next_index = self.model.index(currentIndex.row() - 1, self.model.columnCount() - 1)
            else:
                # reverse to the next column
                next_index = self.model.index(currentIndex.row(), currentIndex.column() - 1)
            if next_index.isValid():
                self.edit_tableView.setCurrentIndex(next_index)
                self.tabbed_from_editor = True

    def on_row_change(self, selected, deselected):
        column = None
        def highlight_error():
            if column is not None:
                index = self.model.index(self.model.edited_indexes[0].row(), column)
                if index.isValid():
                    self.edit_tableView.selectionModel().select(index, QtC.QItemSelectionModel.SelectionFlag.Select)
            else:
                selection = QtC.QItemSelection(self.model.index(self.model.edited_indexes[0].row(), 0),
                                                 self.model.index(self.model.edited_indexes[0].row(), self.model.columnCount() - 1))
                self.edit_tableView.selectionModel().select(selection,
                                                            QtC.QItemSelectionModel.SelectionFlag.ClearAndSelect | QtC.QItemSelectionModel.SelectionFlag.Rows)
            self.edit_tableView.scrollTo(self.model.edited_indexes[0])
            self.edit_tableView.setFocus()

        # Check if the row has changed and if the model has been edited
        if selected.row() != deselected.row():
            if isinstance(self.model, SQLiteTableModel):
                if self.view == 'SampleEditView':
                    if not self.sample_submit(selected.row()):
                        return False
            if isinstance(self.model, VerifiableSqlTableModel | VerifiableSqlViewModel):
                if not self.model.edited_indexes:
                    # No uncommitted changes, so nothing to do
                    return True
            if not self.model.submit():
                # There was an error submitting the changes
                if isinstance(self.model, VerifiableSqlTableModel | VerifiableSqlViewModel):
                    if self.model.submitError != '':
                        errtxt = f'Failed to save changes to {self.table}: {self.model.submitError}'
                        header_to_select = self.model.headerToFix
                        header_list = self.view_headers if self.view_headers else self.table_headers
                        for col in enumerate(header_list):
                            if col[1] == header_to_select:
                                column = col[0]
                                break
                    else:
                        errtxt = f'Failed to save changes to {self.table}: {self.model.lastError().text()}'
                else:
                    errtxt = f'Failed to save changes to {self.table}: {self.model.lastError().text()}'
                self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

                QtC.QTimer.singleShot(0, highlight_error)
                return False
            else:
                self.updated = True
                return True

    def sample_submit(self, row):
        logger_setup.get_logger().info('Submitting sample changes')
        row_id = self.model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole)
        update_cols = {}
        update_col_values = {}
        where_col_ids = {}
        for key in SQLUtils.one_editable.keys():
            update_cols[key] = []
            update_col_values[key] = []
            where_col_ids[key] = []
        update_tags = {}
        update_tag_values = {}
        # where_tag_ids = {}
        for key in SQLUtils.many_editable.keys():
            update_tags[key] = []
            update_tag_values[key] = []
            # where_tag_ids[key] = []
        query = QtS.QSqlQuery()
        for header in self.show_cols:
            if 'GPS' in header or 'Elevation' in header:
                continue
            elif 'SampleAgeCalculated' in header:
                continue
            elif 'Rejected' in header:
                text = self.model.index(row, self.model.fieldIndex(header)).data(QtC.Qt.ItemDataRole.DisplayRole)
                if text == 'Accepted':
                    update_cols['UPbAnalyses'].append('Rejected')
                    update_col_values['UPbAnalyses'].append(0)
                elif text == 'Rejected':
                    update_cols['UPbAnalyses'].append('Rejected')
                    update_col_values['UPbAnalyses'].append(1)
                else:
                    update_cols['UPbAnalyses'].append('Rejected')
                    update_col_values['UPbAnalyses'].append('Null')
                if not query.exec(f'SELECT UPbAnalysisID FROM UPbEditView WHERE {self.show_cols[0]} = {row_id}'):
                    logger_setup.get_logger().critical(f'Failed to get UPbAnalysisID for {row_id}: {query.lastError().text()}')
                    return False
                while query.next():
                    where_col_ids['UPbAnalyses'].append(query.value(0))
            else:
                for key, values in SQLUtils.non_editable.items():
                    if header in values:
                        continue
                for key, values in SQLUtils.many_editable.items():
                    for col_key in values.keys():
                        if header == col_key:
                            text = self.model.index(row, self.model.fieldIndex(header)).data(QtC.Qt.ItemDataRole.DisplayRole)
                            if text == '' or text is None:
                                ids = 'Null'
                            else:
                                ids = self.retrieve_checked_ids(key, text.split(','))
                                if not ids:
                                    break
                            update_tags[key].append(name_column(key))
                            update_tag_values[key].append(ids)
                            break
                for key, values in SQLUtils.one_editable.items():
                    for col_key in values.keys():
                        if header == col_key:
                            text = self.model.index(row, self.model.fieldIndex(header)).data(QtC.Qt.ItemDataRole.DisplayRole)
                            if text == '' or text is None:
                                id = 'Null'
                            else:
                                id = self.retrieve_id(key, text)
                                if not id:
                                    break
                            update_cols[key].append(values[header])
                            update_col_values[key].append(id)
                            if key != self.table:
                                # todo: figure out how to get the correct IDs for the where clause
                                pass
                            break
        for table in update_cols.keys():
            if update_col_values[table]:
                sql_cols = ', '.join(update_cols[table])
                sql_values = ', '.join(update_col_values[table])
                table_headers = get_headers(table)
                if table == self.table:
                    item_id = self.model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole)
                else:
                    for header in self.table_headers:
                        if header in table_headers:
                            edit_table_col = header
                            break
                        elif table_headers[0] in self.table_headers:
                            edit_table_col = table_headers[0]
                    edit_table_col
                    item_id = self.retrieve_id(table, )
                if not query.exec(f'UPDATE {table} SET {sql_cols} = {sql_values} WHERE {table_headers[0]} = {item_id}'):
                    logger_setup.get_logger().critical(f'Failed to update {table}: {query.lastError().text()}')
                    return False


    def retrieve_id(self, table, value):
        if value == '':
            return 'Null'
        table_headers = get_headers(table)
        id_header = table_headers[0]
        query = QtS.QSqlQuery()
        if not query.exec(f'SELECT {id_header} FROM {table} WHERE {name_column(table)} = "{value}"'):
            logger_setup.get_logger().critical(f'Failed to get ID for {value}: {query.lastError().text()}')
            return None
        if query.next():
            return query.value(0)
        else:
            return None

    def retrieve_checked_ids(self, table, values):
        if not values:
            return []
        table_headers = get_headers(table)
        id_header = table_headers[0]
        query = QtS.QSqlQuery()
        ids = []
        for value in values:
            if not query.exec(f'SELECT {id_header} FROM {table} WHERE {name_column(table)} = "{value}"'):
                logger_setup.get_logger().critical(f'Failed to get {name_column(table)} for {value}: {query.lastError().text()}')
                return None
            if query.next():
                ids.append(query.value(0))
            else:
                return None
        return ids

    def add_popup(self):
        # if not self.add_pushButton.hasFocus():
        #     return
        if not self.model.submit():
            errtxt = f'Failed to save changes to {self.table}: {self.model.lastError().text()}'
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
            return
        # if self.table == 'Samples' or self.table == '"References"' or self.table == 'Aliquots' or self.table == 'UPbData':
        #     pass
        if self.table == '"References"' or self.table == 'References':
            dlg = NewReference()
        else:
            dlg = AddTags(self.model, self.table)
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
        self.display_table()

    def rollback(self):
        rollback_savepoint('before_edit')
        self.reject()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        if self.edit_tableView.currentIndex().isValid() and not self.on_row_change(QtC.QModelIndex(), self.edit_tableView.currentIndex()):
            # There is a valid index selected and the row change failed
            logger_setup.get_logger().critical('Failed to save changes')
            return
        else:
            release_savepoint('before_edit')
            # Check if there is another existing savepoint. If not, go ahead and update the database
            if not SavepointManager.get_instance().active_savepoints():
                update_database()
            self.accept()
            self.msg.information(self, 'Success', 'Changes saved', QtW.QMessageBox.StandardButton.Ok)
            self.close_by_dialog = True
            self.close()
            self.close_by_dialog = False
            self.accept()

    def discard_question(self):
        self.msg.question(self, 'Discard changes', 'Are you sure you want to discard all changes?',QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        self.msg.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = self.msg.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            self.rollback()
        else:
            pass

    def closeEvent(self, event: QtG.QCloseEvent):
        if not self.close_by_dialog:
            if self.updated:
                self.discard_question()
                event.ignore()
            else:
                logger_setup.get_logger().info(f'Closing {self.table} edit dialog')
                event.accept()
        else:
            logger_setup.get_logger().info(f'Closing {self.table} edit dialog')
            event.accept()

    def saveWindowState(self):
        settings.setValue("ui/EditSampleTable/pos", self.pos())
        settings.setValue("ui/EditSampleTable/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/EditSampleTable/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/EditSampleTable/size", defaultValue=QSize(810, 569)))

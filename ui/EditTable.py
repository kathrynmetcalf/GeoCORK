import sys
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import QModelIndex
from PyQt6.uic import loadUi
from pandas.plotting import table

import Functions.Text_manipulations as TxM
import Functions.Errors as Er
import Functions.Table_classes as TbC
from ui.AddTags import AddTags
from ui.GPSDialog import GPSDialog
import Functions.SQLUtils as SQLUtils
from ui.New_reference import NewReference


class EditTable(QtW.QDialog):
    def __init__(self, model, table_name):
        super().__init__()

        self.edit_tableView: QtW.QTableView
        tags_ui_file = "ui/EditTable.ui"
        loadUi(tags_ui_file, self)
        self.table = TxM.remove_spaces(table_name)
        self.model = TbC.VerifiableSqlTableModel()
        self.msg = QtW.QMessageBox(self)
        if self.table == 'Samples' or self.table == 'Aliquots' or self.table == 'UPbData':
            pass
        elif self.table in SQLUtils.trigger_tables:
            if self.table == 'Columns':
                self.model = TbC.VerifiableSqlViewModel()
                TbC.set_table(self.model, 'ColumnEditView')
            else:
                self.model = TbC.VerifiableSqlTableModel()
                TbC.set_table(self.model, self.table)
            self.edit_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnRowChange)
            self.edit_tableView.doubleClicked.connect(self.display_widget)
        else:
            self.model = QtS.QSqlTableModel()
            TbC.set_table(self.model, self.table)
        self.view_headers = []
        self.table_headers = []
        self.get_headers()
        self.display_table()
        self.model.submitAll()
        self.createSavepoint()

        self.close_by_dialog = False
        self.lineEdit = None
        self.edit_index = QModelIndex()
        self.combo = None
        self.combo_index = QModelIndex()
        self.tabbed_from_editor = False
        self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        self.cancel_pushButton.clicked.connect(self.rollback)
        self.edit_tableView.selectionModel().currentRowChanged.connect(self.on_row_change)
        self.edit_tableView.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.edit_tableView.customContextMenuRequested.connect(self.show_context_menu)

    def createSavepoint(self):
        query = QtS.QSqlQuery()
        if query.exec('SAVEPOINT before_edit') is False:
            errtxt = f'Failed to create savepoint for {self.table}: {query.lastError().text()}'
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def releaseSavepoint(self):
        query = QtS.QSqlQuery()
        if query.exec('RELEASE SAVEPOINT before_edit') is False:
            errtxt = f'Failed to release savepoint for {self.table}: {query.lastError().text()}'
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

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

    def get_headers(self):
        for col in range(self.model.columnCount()):
            self.table_headers.append(self.model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
        if isinstance(self.model, TbC.VerifiableSqlViewModel):
            self.view_headers = self.table_headers
            self.table_headers = []
            column_model = QtS.QSqlTableModel()
            TbC.set_table(column_model, 'Columns')
            for col in range(column_model.columnCount()):
                self.table_headers.append(column_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))

    def display_table(self):
            self.edit_tableView.setModel(self.model)
            # self.edit_tableView.setModel(self.filter_proxy_model)
            self.edit_tableView.hideColumn(0)  # don't show ID column
            self.edit_tableView.resizeColumnsToContents()
            self.edit_tableView.setSortingEnabled(True)

    def display_widget(self):
        selected_index = self.edit_tableView.selectedIndexes()[0]
        if not selected_index.isValid():
            return
        if self.lineEdit is not None:
            self.destroy_lineedit()
            if self.lineEdit is not None:
                print('Error destroying line edit')
                return
        elif self.combo is not None:
            self.destroy_dropdown()
            if self.combo is not None:
                print('Error destroying dropdown')
                return
        header = self.model.headerData(selected_index.column(), QtC.Qt.Orientation.Horizontal,
                                                    QtC.Qt.ItemDataRole.DisplayRole)
        if 'GPS' in header:
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
        elif 'Unit' in header or 'Format' in header:
            self.edit_index = selected_index
            self.display_dropdown()
        else:
            if 'Created' not in header and 'Modified' not in header:
                self.display_lineedit()

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
                self.edit_index = QModelIndex()
                self.edit_tableView.setFocus()
            else:
                errtxt = f'Failed to set data: {self.model.lastError().text()}'
                self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                self.lineEdit.setFocus()

    def display_dropdown(self):
        selected_index = self.edit_tableView.selectedIndexes()[0]
        header = self.model.headerData(selected_index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        # print(f"Clicked column: {header}")
        header = TxM.remove_spaces(header)
        dropdown_table = ''
        for list in SQLUtils.many_editable:
            if list[0] == self.table:
                matches = []
                for item in list:
                    if header in item:
                        matches.append(item)
                if not matches:
                    dropdown_table = ''
                    print(f'No matches found for {header}')
                elif len(matches) == 1:
                    dropdown_table = matches[0]
                else:
                    # There is more than one match, so we have to figure it out
                    print(f'More than one match for {header}: f{matches}')
        if dropdown_table == '':
            for list in SQLUtils.one_editable:
                if list[0] == self.table:
                    matches = []
                    for item in list:
                        if header in item:
                            matches.append(item)
                        elif ('Unit' in item and 'Unit' in header) or ('Format' in item and 'Format' in header):
                            matches.append(item)
                    if not matches:
                        dropdown_table = ''
                        print(f'No matches found for {header}')
                    elif len(matches) == 1:
                        dropdown_table = matches[0]
                    else:
                        # There is more than one match, so we have to figure it out
                        print(f'More than one match for {header}: f{matches}')
                    break
        if dropdown_table == '':
            return
        self.combo_index = selected_index
        self.combo = QtW.QComboBox()
        self.combo_model = QtS.QSqlTableModel()
        TbC.set_table(self.combo_model, dropdown_table)
        self.combo.setModel(self.combo_model)
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
        self.edit_tableView: QtW.QTableView
        if self.combo is not None:
            # print("Start destroying dropdown")
            self.model.setData(self.combo_index, self.combo.currentText(), QtC.Qt.ItemDataRole.EditRole)
            if self.model.lastError().text() != '':
                print('Could not set data')
            if self.edit_tableView.currentIndex() == self.combo_index:
                self.tabbed_from_editor = False
            self.combo.activated.disconnect(self.destroy_dropdown)
            self.combo.removeEventFilter(self)
            self.combo.view().removeEventFilter(self)
            self.edit_tableView.setIndexWidget(self.combo_index, None)
            self.combo = None
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

        if selected.row() != deselected.row():
            if isinstance(self.model, TbC.VerifiableSqlTableModel | TbC.VerifiableSqlViewModel):
                if not self.model.edited_indexes:
                    return
                elif self.model.edited_indexes[0].row() == selected.row():
                    return
            if not self.model.submit():
                if isinstance(self.model, TbC.VerifiableSqlTableModel | TbC.VerifiableSqlViewModel):
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
                return True

    def add_popup(self):
        # if not self.add_pushButton.hasFocus():
        #     return
        if not self.model.submit():
            errtxt = f'Failed to save changes to {self.table}: {self.model.lastError().text()}'
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
        # if self.table == 'Samples' or self.table == '"References"' or self.table == 'Aliquots' or self.table == 'UPbData':
        #     pass
        if self.table == '"References"':
            dlg = NewReference()
            dlg.exec()
        else:
            dlg = AddTags(self.model, self.table)
            dlg.exec()
            self.display_table()

    def rollback(self):
        query = QtS.QSqlQuery()
        if query.exec('ROLLBACK TO SAVEPOINT before_edit') is False:
            errtxt = f'Failed to rollback changes to {self.table}: {query.lastError().text()}'
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
        else:
            self.close_by_dialog = True
            self.close()
            self.close_by_dialog = False
            self.reject()

    def commit(self):
        if self.on_row_change(QtC.QModelIndex(), self.edit_tableView.currentIndex()):
            self.releaseSavepoint()
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
            self.discard_question()
            event.ignore()
        else:
            event.accept()

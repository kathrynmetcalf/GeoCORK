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


class EditTable(QtW.QDialog):
    def __init__(self, model, table_name):
        super().__init__()

        self.edit_tableView: QtW.QTableView
        tags_ui_file = "ui/EditTable.ui"
        loadUi(tags_ui_file, self)
        self.table = TxM.remove_spaces(table_name)
        self.model = TbC.VerifiableSqlTableModel()
        self.msg = QtW.QMessageBox(self)
        self.display_table()
        if 'View' in self.table:
            self.model.setEditable(False)
        self.model.submitAll()
        self.createSavepoint()

        self.lineEdit = None
        self.edit_index = QModelIndex()
        self.combo = None
        self.combo_index = QModelIndex()
        self.edit_tableView.doubleClicked.connect(self.display_widget)
        self.edit_tableView.tabKeyNavigation.connect(self.display_widget)
        self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        self.cancel_pushButton.clicked.connect(self.rollback)
        self.edit_tableView.selectionModel().currentRowChanged.connect(self.on_row_change)

    def update_model(self):
        try:
            value = self.lineEdit.text()
            # print(f'Typed: {value}')
            if self.model.setData(self.edit_index, value, QtC.Qt.ItemDataRole.EditRole):
                self.destroy_lineedit()
        except:
            pass

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

    def display_table(self):
        if self.table == 'Samples' or self.table == 'Sources' or self.table == 'Aliquots' or self.table == 'UPbData':
            pass
        elif self.table == 'Columns':
            self.model = TbC.VerifiableSqlViewModel()
            TbC.set_table(self.model, 'ColumnEditView')
        else:
            self.model = TbC.VerifiableSqlTableModel()
            TbC.set_table(self.model, self.table)
            self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnRowChange)
        self.edit_tableView.setModel(self.model)
        # self.edit_tableView.setModel(self.filter_proxy_model)
        self.edit_tableView.hideColumn(0)  # don't show ID column
        self.edit_tableView.resizeColumnsToContents()
        self.edit_tableView.setSortingEnabled(True)

    def display_widget(self):
        selected_index = self.edit_tableView.selectedIndexes()
        header = self.model.headerData(selected_index[0].column(), QtC.Qt.Orientation.Horizontal,
                                                    QtC.Qt.ItemDataRole.DisplayRole)
        if self.edit_tableView.indexWidget(selected_index[0]) is not None:
            if self.lineEdit is not None:
                self.update_model()
            elif self.combo is not None:
                self.destroy_dropdown()
        # print(f"Clicked column: {header}")
        column_types = TbC.get_column_types(self.model.tableName())
        col_type = column_types[selected_index[0].column()]
        if len(selected_index) > 1:
            self.msg.critical(self, 'Error', 'Please select only one cell to edit', QtW.QMessageBox.StandardButton.Ok)
        elif len(selected_index) == 1:
            if not selected_index[0].isValid():
                return
            if 'GPS' in header:
                if self.table == 'Samples':
                    item_id_header = 'SampleID'
                elif self.table == 'Columns':
                    item_id_header = 'ColumnID'
                item_ids = []
                for index in selected_index:
                    row = index.row()
                    item_ids.append(self.model.record(row).value(item_id_header))
                dlg = GPSDialog(self.table, item_ids)
                dlg.exec()
                self.display_table()
            elif 'Unit' in header or 'Format' in header:
                self.edit_index = selected_index[0]
                self.display_dropdown()
            else:
                if (col_type == 'INTEGER' or col_type == 'REAL') and 'ID' not in header:
                    self.display_lineedit()

    def display_lineedit(self):
        selected_index = self.edit_tableView.selectedIndexes()
        self.edit_index = selected_index[0]
        self.lineEdit = QtW.QLineEdit()
        self.lineEdit.setValidator(QtG.QRegularExpressionValidator(QtC.QRegularExpression("[0-9]*")))
        self.lineEdit.setText(str(selected_index[0].data()))
        self.edit_tableView.setIndexWidget(selected_index[0], self.lineEdit)
        self.lineEdit.editingFinished.connect(self.update_model)

    def destroy_lineedit(self):
        if self.lineEdit is not None:
            self.edit_tableView.setIndexWidget(self.edit_index, None)
            self.lineEdit = None
            self.edit_index = QModelIndex()

    def display_dropdown(self):
        selected_index = self.edit_tableView.selectedIndexes()
        header = self.model.headerData(selected_index[0].column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        # print(f"Clicked column: {header}")
        header = TxM.remove_spaces(header)
        if len(selected_index) == 1:
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
            self.combo_index = selected_index[0]
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
            self.edit_tableView.setIndexWidget(selected_index[0], self.combo)
            self.combo.activated.connect(self.destroy_dropdown)
            # print("showing popup")
            self.combo.showPopup()

    def destroy_dropdown(self):
        self.edit_tableView: QtW.QTableView
        if self.combo is not None:
            # print("Start destroying dropdown")
            self.model.setData(self.combo_index, self.combo.currentText(), QtC.Qt.ItemDataRole.EditRole)
            if self.model.lastError().text() != '':
                print('Could not set data')
            self.combo.activated.disconnect(self.destroy_dropdown)
            self.edit_tableView.setIndexWidget(self.combo_index, None)
            self.combo = None

            self.update_model()
            # Only update the model if the text has changed
            # previous_text = self.combo_index.data(QtC.Qt.ItemDataRole.DisplayRole)
            # if checked_text != previous_text:
            #     self.recreate_sample_model()
            self.combo_index = QtC.QModelIndex()

    def on_row_change(self, selected, deselected):
        if selected.row() != deselected.row():
            self.model.submit()

    def add_popup(self):
        if self.table == 'Samples' or self.table == 'Sources' or self.table == 'Aliquots' or self.table == 'UPbData':
            pass
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
            self.reject()

    def commit(self):
        if self.model.isDirty():
            self.update_model()
        self.releaseSavepoint()
        self.msg.information(self, 'Success', 'Changes saved', QtW.QMessageBox.StandardButton.Ok)
        self.close()

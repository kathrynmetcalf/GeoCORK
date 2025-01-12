import sys
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.uic import loadUi
import Functions.Text_manipulations as TxM
import Functions.Errors as Er
import Functions.Table_classes as TbC
from ui.AddTags import AddTags
from ui.GPSDialog import GPSDialog


class EditTable(QtW.QDialog):
    def __init__(self, model, table_name):
        super().__init__()

        # Define any widgets here
        tags_ui_file = "ui/EditTable.ui"
        loadUi(tags_ui_file, self)
        self.table = TxM.remove_spaces(table_name)
        self.model = TbC.VerifiableSqlTableModel()
        self.msg = QtW.QMessageBox(self)
        self.display_table()
        self.model.submitAll()
        self.createSavepoint()

        # self.edit_tableView.closeEditor.connect(self.update_model)
        # self.edit_tableView.currentChanged.connect(self.connect_signals())
        # self.filter_proxy_model.dataChanged.connect(self.update_model)
        self.edit_tableView.doubleClicked.connect(self.display_widget)
        self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        self.cancel_pushButton.clicked.connect(self.rollback)

    def connect_signals(self):
        self.edit_tableView.indexWidget(self.edit_tableView.currentIndex()).valueChanged.connect(self.update_model)

    def update_model(self):
        value = self.lineEdit.text()
        print(f'Typed: {value}')
        if self.model.setData(self.edit_index, value, QtC.Qt.ItemDataRole.EditRole):
            self.destroy_lineedit()

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
        foreign_keys = TbC.foreign_key_columns(self.table)
        if self.table == 'Samples' or self.table == 'Sources' or self.table == 'Aliquots' or self.table == 'UPbData':
            pass
        elif foreign_keys is not None:
            self.model = TbC.VerifiableRelationalTableModel()
            self.model.setTable(self.table)
            # self.model.select()
            for key in foreign_keys:
                key_column = self.model.fieldIndex(key)
                self.model.setRelation(key_column,
                                       QtS.QSqlRelation(foreign_keys[key]['table'], foreign_keys[key]['id_column'],
                                                        foreign_keys[key]['display_column']))
                print(f'Set relation for {key_column}: {self.model.relation(key_column).tableName()}, {self.model.relation(key_column).indexColumn()}, {self.model.relation(key_column).displayColumn()}')
                print(f'Valid relation: {self.model.relation(key_column).isValid()}')
                print(f'Query: {self.model.query().lastQuery()}')
            if not self.model.select():
                print(f'Failed to select table {self.table}: {self.model.lastError().text()}')
        else:
            self.model = TbC.VerifiableSqlTableModel()
            self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnRowChange)
        self.edit_tableView.setModel(self.model)
        # if self.model is a relational table model, set the delegate to allow editing of foreign key columns
        if isinstance(self.model, TbC.VerifiableRelationalTableModel):
            self.edit_tableView.setItemDelegate(QtS.QSqlRelationalDelegate(self.edit_tableView))
        # self.edit_tableView.setModel(self.filter_proxy_model)
        self.edit_tableView.hideColumn(0)  # don't show ID column
        self.edit_tableView.resizeColumnsToContents()
        # self.edit_tableView.setSortingEnabled(True)

    def display_widget(self):
        selected_index = self.edit_tableView.selectedIndexes()
        header = self.model.headerData(selected_index[0].column(), QtC.Qt.Orientation.Horizontal,
                                                    QtC.Qt.ItemDataRole.DisplayRole)
        print(f"Clicked column: {header}")
        if len(selected_index) > 1:
            self.msg.critical(self, 'Error', 'Please select only one cell to edit', QtW.QMessageBox.StandardButton.Ok)
        elif len(selected_index) == 1:
            type = TbC.column_type(self.table, header)
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
            elif (type == 'INTEGER' or type == 'REAL') and 'ID' not in header:
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
        self.releaseSavepoint()
        self.msg.information(self, 'Success', 'Changes saved', QtW.QMessageBox.StandardButton.Ok)
        self.close()

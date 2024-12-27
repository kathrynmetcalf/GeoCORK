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


class EditTable(QtW.QDialog):
    def __init__(self, model, table_name):
        super().__init__()

        # Define any widgets here
        tags_ui_file = "ui/EditTable.ui"
        loadUi(tags_ui_file, self)
        self.table = TxM.remove_spaces(table_name)
        if self.table == 'Samples' or self.table == 'Sources' or self.table == 'Aliquots' or self.table == 'UPbData':
            pass
        elif self.table == 'Columns':
            self.model = TbC.VerifiableRelationalTableModel()
            self.model.setTable(self.table)
            self.model.select()
            self.model.setRelation(3, QtS.QSqlRelation('DistanceUnits', 'DistanceUnitID', 'DistanceUnitAbbreviation'))
            self.model.setRelation(4, QtS.QSqlRelation('GPSLocations', 'GPSLocationID', 'GPSLocationConverted'))
            self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnRowChange)
        else:
            self.model = model
            self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnRowChange)
            # self.filter_proxy_model = TbC.VerifiableProxyModel()
            # self.filter_proxy_model.setSourceModel(self.model)
            # self.filter_proxy_model.setFilterKeyColumn(-1)  # search all columns
        self.msg = QtW.QMessageBox(self)
        self.display_table()
        self.model.submitAll()
        self.createSavepoint()

        # self.edit_tableView.closeEditor.connect(self.update_model)
        # self.edit_tableView.currentChanged.connect(self.connect_signals())
        # self.filter_proxy_model.dataChanged.connect(self.update_model)
        self.edit_tableView.doubleClicked.connect(self.display_lineedit)
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
            errtxt = Er.savepoint_fail(self.table)
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def releaseSavepoint(self):
        query = QtS.QSqlQuery()
        if query.exec('RELEASE SAVEPOINT before_edit') is False:
            errtxt = Er.savepoint_release_fail(self.table)
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def display_table(self):
        self.edit_tableView.setModel(self.model)
        if self.table == 'Columns':
            self.edit_tableView.setItemDelegateForColumn(3, QtS.QSqlRelationalDelegate(self.edit_tableView))
        # delegate = TbC.NullDoubleSpinBoxDelegate()
        # self.edit_tableView.setItemDelegateForColumn(2, delegate)
        # self.edit_tableView.setModel(self.filter_proxy_model)
        self.edit_tableView.hideColumn(0)  # don't show ID column
        self.edit_tableView.resizeColumnsToContents()
        # self.edit_tableView.setSortingEnabled(True)

    def display_lineedit(self):
        selected_index = self.edit_tableView.selectedIndexes()
        header = self.model.headerData(selected_index[0].column(), QtC.Qt.Orientation.Horizontal,
                                                    QtC.Qt.ItemDataRole.DisplayRole)
        print(f"Clicked column: {header}")
        # todo: Determine if this column only takes number values. Only open the line edit if it does
        if len(selected_index) == 1:
            self.edit_index = selected_index[0]
            self.lineEdit = QtW.QLineEdit()
            self.lineEdit.setValidator(QtG.QRegularExpressionValidator(QtC.QRegularExpression("[0-9]*")))
            self.lineEdit.setText(str(selected_index[0].data()))
            self.edit_tableView.setIndexWidget(selected_index[0], self.lineEdit)
            self.lineEdit.editingFinished.connect(self.update_model)
        if len(selected_index) > 1:
            self.msg.critical(self, 'Error', 'Please select only one cell to edit', QtW.QMessageBox.StandardButton.Ok)

    def destroy_lineedit(self):
        if self.lineEdit is not None:
            self.edit_tableView.setIndexWidget(self.edit_index, None)
            self.lineEdit = None

    def add_popup(self):
        if self.table == 'Samples' or self.table == 'Sources' or self.table == 'Aliquots' or self.table == 'UPbData':
            pass
        else:
            dlg = AddTags(self.db, self.model, self.table)
            dlg.exec()
            self.display_table()


    def rollback(self):
        query = QtS.QSqlQuery()
        if query.exec('ROLLBACK TO SAVEPOINT before_edit') is False:
            errtxt = Er.rollback_fail(self.table)
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
        else:
            self.reject()

    def commit(self):
        self.releaseSavepoint()
        self.msg.information(self, 'Success', 'Changes saved', QtW.QMessageBox.StandardButton.Ok)
        self.close()

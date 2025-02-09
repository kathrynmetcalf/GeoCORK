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
from Functions.Tree_classes import TreeModel, CheckableTreeCombobox, CheckableTreeModel, CheckableTreeView
from Functions.Table_classes import ReadableProxyModel
import Functions.Text_manipulations as TxM
from Functions import SQLUtils
from Functions.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint
from Functions.Settings_manager import settings
from Functions.Database_manager import update_database
from ui.AddTags import AddTags
import Functions.Table_classes as TbC

class EditSampleTable(QtW.QDialog):
    def __init__(self, sample_model: TbC.DisplayRoundedModel):
        super().__init__()

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "EditSampleTable.ui")
        loadUi(sources_ui_file, self)
        self.loadWindowState()

        self.table = 'Samples'
        self.view = 'SampleView'
        self.sample_model = sample_model
        self.table_model = QtS.QSqlTableModel()
        self.combo = CheckableTreeCombobox()
        self.combo_index = QtC.QModelIndex()
        # self.model.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnFieldChange)
        self.filter_proxy_model = ReadableProxyModel()
        self.msg = QtW.QMessageBox(self)
        self.close_by_dialog = False
        self.display_table()
        create_savepoint('before_edit')

        self.filter_proxy_model.dataChanged.connect(self.update_model)
        # self.combo.closing.connect(self.destroy_dropdown)
        # self.add_pushButton.clicked.connect(self.add_popup)
        self.commit_pushButton.clicked.connect(self.commit)
        self.cancel_pushButton.clicked.connect(self.rollback)
        self.edit_tableView.clicked.connect(self.display_dropdown)

    def update_model(self):
        if not self.sample_model.submitAll():
            errtxt = self.sample_model.lastError().text()
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)


    def get_items(self, table):
        headers = []
        items = []
        query = QtS.QSqlQuery()
        if query.exec(f"SELECT name from pragma_table_info('{table}')"):
            while query.next():
                headers.append(query.value(0))
            name_header = headers[1]
            if query.exec(f"SELECT {name_header} FROM {table}"):
                while query.next():
                    items.append(query.value(0))
                return items

    def display_table(self):
        self.filter_proxy_model.setSourceModel(self.sample_model)
        self.filter_proxy_model.setFilterKeyColumn(-1)  # search all columns
        self.edit_tableView: QtW.QTableView
        # self.edit_tableView.setModel(self.sample_model)
        self.edit_tableView.setModel(self.filter_proxy_model)
        self.edit_tableView.hideColumn(0)  # don't show ID column
        self.edit_tableView.resizeColumnsToContents()
        self.edit_tableView.setSortingEnabled(True)

    def display_dropdown(self):
        selected_index = self.edit_tableView.selectedIndexes()
        header = self.filter_proxy_model.headerData(selected_index[0].column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        print(f"Clicked column: {header}")
        header = TxM.remove_spaces(header)
        if len(selected_index) == 1:
            table = ''
            for list in SQLUtils.many_editable:
                if header in list:
                    table = header
                    break
            if table == '':
                return
            self.combo_index = selected_index[0]
            self.combo = CheckableTreeCombobox()
            self.combo.closing.connect(self.destroy_dropdown)
            self.table_model.setTable(table)
            self.table_model.select()
            tree_model = CheckableTreeModel()
            tree_model.setSourceModel(self.table_model)
            row = self.combo_index.row()
            sample_ID = self.filter_proxy_model.index(row, 0).data()
            tree_model.set_sample(sample_ID)
            selected_text = self.combo_index.data(QtC.Qt.ItemDataRole.DisplayRole)
            # print(f"Selected text: {selected_text}")
            self.combo.setModel(tree_model)
            self.combo.set_line_edit_text(selected_text)
            self.edit_tableView.setIndexWidget(self.combo_index, self.combo)
            # print("showing popup")
            self.combo.showPopup()

    def destroy_dropdown(self):
        self.edit_tableView: QtW.QTableView
        if self.combo is not None:
            # print("Start destroying dropdown")
            self.combo.closing.disconnect(self.destroy_dropdown)
            checked_text = self.combo.lineEdit().text()
            checked_list = checked_text.split(',')
            print(f"Checked text: {checked_text}")
            print(f"Checked list: {checked_list}")
            self.combo.model().update_db(checked_list)

            self.verticalLayout.removeWidget(self.combo)
            self.combo.deleteLater()
            self.combo = None

            self.recreate_sample_model()
            # Only update the model if the text has changed
            # previous_text = self.combo_index.data(QtC.Qt.ItemDataRole.DisplayRole)
            # if checked_text != previous_text:
            #     self.recreate_sample_model()
            # self.combo_index = QtC.QModelIndex()

    def recreate_sample_model(self):
        self.sample_model.setQuery(f"SELECT * FROM {self.view}")
        self.display_table()

    # def update_edited_row(self):
    # todo: update the row in the sample table with the new values

    def rollback(self):
        rollback_savepoint('before_edit')
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False
        self.reject()

    def commit(self):
        update_database()
        release_savepoint('before_edit')
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
            self.saveWindowState()
            event.accept()

    def saveWindowState(self):
        settings.setValue("ui/EditSampleTable/pos", self.pos())
        settings.setValue("ui/EditSampleTable/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/EditSampleTable/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/EditSampleTable/size", defaultValue=QSize(810, 569)))

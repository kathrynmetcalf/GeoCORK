import sqlite3
from random import sample

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import Qt, QEventLoop, QStandardPaths, QPoint, QSettings, QSize, QSortFilterProxyModel, QTimer
from PyQt6.QtSql import QSqlQueryModel, QSqlTableModel
from PyQt6.QtWidgets import QFileDialog, QWidget, QComboBox, QTableView, QTreeView
from PyQt6.sip import array
from PyQt6.uic import loadUi
import Functions.Table_classes as TbC
import Functions.Tree_classes as TrC
import Functions.Text_manipulations as TxM
from Functions import SQLUtils
from ui.EditTable import EditTable


class DataViewerWidget(QWidget):
    def __init__(self, db_file,  ids_to_show, table_type):
        super().__init__()
        self.db_file = db_file
        self.table_type = table_type
        self.ids_to_show = '('

        if len(ids_to_show) > 0:
            for sample in ids_to_show:
                self.ids_to_show += str(sample[0]) + ", "
            self.ids_to_show = self.ids_to_show[0:-2]
            self.ids_to_show += ")"

        self.db = QtS.QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(self.db_file)
        self.settings = QSettings("CSUF", "GeoChron")

        ok = self.db.open()
        print("Database is open: " + str(ok))

        self.loadWindowState()
        # Define any widgets here

        sources_ui_file = "ui/DataViewerWidget.ui"
        loadUi(sources_ui_file, self)


        self.switch_to_table(self.db_stackedWidget)
        self.switch_to_table(self.db_stackedWidget_2)

        # list of all user-viewable tables in the database
        self.user_view_tables = ['Ages', 'Age Signatures', 'Aliquots', 'Aliquot Context', 'Columns', 'Lab Facilities',
                                 'Instruments',
                                 'Regions', 'Rock Types', 'Sample Context', 'Samples', 'Sampling Methods', 'Settings',
                                 'Sources',
                                 'Spot Compositions', 'Spot Context', 'UPb Data', 'Analysis Methods', 'Units', 'UPb Analysis Methods']
        # list of tables to display as a tree structure
        self.dbtree_list = ['Ages', 'AgeSignatures', 'AliquotContext', 'Regions', 'RockTypes', 'SampleContext',
                            'SamplingMethods', 'Settings', 'SpotCompositions', 'SpotContext', 'Units']
        self.dbtable_list = ['Aliquots', 'Columns', 'LabFacilities', 'Instruments', 'Sources', 'UPbData', 'Spots', 'UPbAnalysisMethods']

        self.dbTable_comboBox_2.addItems(self.user_view_tables)
        self.dbTable_comboBox_2.removeItem(10) # remove sample table index

        if self.table_type == 'sample':
            self.dbTable_comboBox.addItem('Samples')
        elif self.table_type == 'aliquot':
            self.dbTable_comboBox.addItem('Aliquots')
        elif self.table_type == 'spot':
            self.dbTable_comboBox.addItem('Spots')

        self.display_sample_table(self.db_stackedWidget, self.dbTable_tableView,
                                  self.dbTable_comboBox, self.edit_pushButton)

        # Display the selected table
        self.dbTable_comboBox_2.currentTextChanged.connect(lambda: self.display_table_with_sample_filter(
            self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2, self.dbTable_comboBox_2,
            self.edit_pushButton_2, self.dbTable_tableView, table_type))

        self.dbTable_tableView: QTableView


        # Signal for clicked add button in main window
        # self.edit_pushButton.clicked.connect(
        #     lambda: self.display_table(self.db_stackedWidget, self.dbTable_tableView, self.dbTable_treeView,
        #                        self.dbTable_comboBox, self.edit_pushButton))
        # self.edit_pushButton_2.clicked.connect(
        #      lambda: self.display_table(self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2,
        #                        self.dbTable_comboBox_2, self.edit_pushButton_2))

        self.show()

    def closeEvent(self, a0):
        self.saveWindowState()
        super().closeEvent(a0)

    def switch_to_table(self, db_stackedWidget):
        """
        Sets the current widget to a table view
        :return:
        """
        db_stackedWidget: QtW.QStackedWidget
        db_stackedWidget.setCurrentIndex(0)

    def switch_to_tree(self, db_stackedWidget):
        """
        Sets the current widget to a tree view
        :return:
        """
        db_stackedWidget: QtW.QStackedWidget
        db_stackedWidget.setCurrentIndex(1)

    def display_sample_table(self, db_stackedWidget, dbTable_tableView, dbTable_comboBox, edit_pushButton):
        """
        Displays the sample table
        :return:
        """
        table_name = dbTable_comboBox.currentText()
        print("current table: " + table_name)

        # Remove spaces from display names
        table = TxM.remove_spaces(table_name)
        if table == 'Samples':
            self.switch_to_table(db_stackedWidget)
            sample_model = QtS.QSqlQueryModel()
            sample_proxy_model = QtC.QSortFilterProxyModel()
            sample_model.setQuery(f"Select Samples.* FROM Samples WHERE Samples.SampleID IN {self.ids_to_show}")
            sample_proxy_model.setSourceModel(sample_model)
            sample_proxy_model.setFilterKeyColumn(-1)  # search all columns
            dbTable_tableView.setModel(sample_proxy_model)
            dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            # self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.OnManualSubmit)
            # Signal for search bar
            self.search_lineEdit.textChanged.connect(lambda: self.search(self.search_lineEdit, sample_proxy_model))
        elif table == 'Aliquots':
            self.switch_to_table(db_stackedWidget)
            sample_model = QtS.QSqlQueryModel()
            sample_proxy_model = QtC.QSortFilterProxyModel()
            sample_model.setQuery(f"Select Aliquots.* FROM Aliquots WHERE Aliquots.AliquotID IN {self.ids_to_show}")
            sample_proxy_model.setSourceModel(sample_model)
            sample_proxy_model.setFilterKeyColumn(-1)  # search all columns
            dbTable_tableView.setModel(sample_proxy_model)
            dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            # self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.OnManualSubmit)
            self.search_lineEdit.textChanged.connect(lambda: self.search(self.search_lineEdit, sample_proxy_model))
        elif table == 'Spots':
            self.switch_to_table(db_stackedWidget)
            query = TbC.SpotTableModel().setupQuery(self.ids_to_show)
            print(query)
            sample_model = QtS.QSqlQueryModel()
            sample_proxy_model = QtC.QSortFilterProxyModel()
            sample_model.setQuery(f"Select Spots.* FROM Spots WHERE Spots.SpotID IN {self.ids_to_show}")
            sample_proxy_model.setSourceModel(sample_model)
            sample_proxy_model.setFilterKeyColumn(-1)  # search all columns
            dbTable_tableView.setModel(sample_proxy_model)
            dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            # self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.OnManualSubmit)
            self.search_lineEdit.textChanged.connect(lambda: self.search(self.search_lineEdit, sample_proxy_model))
        elif table == 'UPbData':
            self.switch_to_table(db_stackedWidget)
            sample_model = QtS.QSqlQueryModel()
            sample_proxy_model = QtC.QSortFilterProxyModel()
            sample_model.setQuery(f"Select UPbData.* FROM UPbData WHERE UPbData.UPbDataID IN {self.ids_to_show}")
            sample_proxy_model.setSourceModel(sample_model)
            sample_proxy_model.setFilterKeyColumn(-1)  # search all columns
            dbTable_tableView.setModel(sample_proxy_model)
            dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            # self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.OnManualSubmit)
            self.search_lineEdit.textChanged.connect(lambda: self.search(self.search_lineEdit, sample_proxy_model))
        else:
            print("Error: Tried to switch to a table with no table or tree..Don't know how it got here")


        self.selectionTimer = QTimer()
        self.selectionTimer.setSingleShot(True)
        self.selectionTimer.timeout.connect(lambda: self.display_table_with_sample_filter(
            self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2, self.dbTable_comboBox_2,
            self.edit_pushButton_2, self.dbTable_tableView, self.table_type))

        # Connect the selectionChanged signal to the onSelectionChanged method
        self.dbTable_tableView.selectionModel().selectionChanged.connect(self.on_select_changed)

        edit_pushButton.setText(f"Edit {table_name}")

    def on_select_changed(self):
        """
        This method is called whenever the selection changes.
        It restarts the timer to batch rapid selection changes.
        """
        # Restart the timer every time the selection changes
        self.selectionTimer.start(250)  # Delay in milliseconds

    def display_table_with_sample_filter(self, db_stackedWidget, dbTable_tableView, dbTable_treeView,
                                         dbTable_comboBox, edit_pushButton, sample_filter, table_type, selected=None, deselected=None):
        """
        Displays the selected table
        :return:
        """
        self.dbTable_tableView: QTableView
        dbTable_treeView: QTreeView
        sample_filter: QTableView

        table_name = dbTable_comboBox.currentText()
        table = TxM.remove_spaces(table_name)

        condition_ids = []
        ids_to_show = []
        if sample_filter.selectionModel().hasSelection():
            for index in self.dbTable_tableView.selectionModel().selectedIndexes():
                condition_id = sample_filter.model().index(index.row(), 0).data()
                condition_ids.append(str(condition_id))

            table_condition = ''
            sql = self.get_query_from_table(table)
            if condition_ids:
                if table_type == 'sample':
                    table_condition = f" WHERE Samples.SampleID IN ({', '.join(condition_ids)})"
                elif table_type == 'aliquot':
                    table_condition = f" WHERE Aliquots.AliquotID IN ({', '.join(condition_ids)})"
                    if SQLUtils.aliquot_join not in sql:
                        sql += SQLUtils.aliquot_join + '\n'
                elif table_type == 'spot':
                    table_condition = f" WHERE Spots.SpotID IN ({', '.join(condition_ids)})"
                    if SQLUtils.aliquot_join not in sql:
                        sql += SQLUtils.aliquot_join + '\n'
                    if SQLUtils.spot_join not in sql:
                        sql += SQLUtils.spot_join + '\n'
                # "(19,39,58)"

            sql += table_condition
            conn = sqlite3.connect(self.db_file)
            with conn:
                c = conn.cursor()
                print (sql)
                if c.execute(sql):
                    existing = c.fetchall()
                    for row in existing:
                        if row[0] is not None:
                            ids_to_show.append(str(row[0]))

        id_condition = f'({", ".join(ids_to_show)})'
        print(id_condition)

        if table in self.dbtree_list:
            self.switch_to_tree(db_stackedWidget)
            model = QtS.QSqlTableModel(db=self.db)
            model.setTable(table)
            model.select()
            if table not in ["UPbData", "LabFacilities"]:
                model.setFilter(f'{table[0:-1]}ID  IN ( '
                                f'WITH RECURSIVE ParentTree AS '
                                f'(SELECT * FROM {table} '
                                f'WHERE {table[0:-1]}ID IN {id_condition} '
                                f'UNION ALL '
                                f'SELECT {table}.* FROM {table} '
                                f'INNER JOIN ParentTree ON {table}.{table[0:-1]}ID = ParentTree.Parent{table[0:-1]}ID) '
                                f'SELECT {table[0:-1]}ID FROM ParentTree) ')
            tree_model = TrC.TreeModel(model, None)

            dbTable_treeView.setModel(tree_model)
            dbTable_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
            # dbTable_treeView.hideColumn(1)  # don't show ID column
            # dbTable_treeView.hideColumn(2)  # don't show parent ID column
            dbTable_treeView.setSortingEnabled(True)

            self.search_lineEdit_2.textChanged.connect(lambda: self.search(self.search_lineEdit_2, tree_model))

        elif table in self.dbtable_list:
            self.switch_to_table(db_stackedWidget)
            model = QtS.QSqlTableModel(db=self.db)
            model.setTable(table)
            model.select()
            if table == "LabFacilities":
                model.setFilter(f'{table}ID IN {id_condition}')
            elif table == "UPbData":
                model.setFilter(f'UPbAnalysisID in {id_condition}')

            table_proxy_model = QSortFilterProxyModel()
            for col in range(model.columnCount()):
                header = TxM.add_spaces_camel(
                    model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
                model.setHeaderData(col, QtC.Qt.Orientation.Horizontal, header, QtC.Qt.ItemDataRole.DisplayRole)
            table_proxy_model.setSourceModel(model)
            # if self.case_checkBox.isChecked():
            #     self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseSensitive)
            # else:
            #     self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
            table_proxy_model.setFilterKeyColumn(-1)  # search all columns
            dbTable_tableView.setModel(table_proxy_model)
            # dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.verticalHeader().setVisible(False)
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)

            self.search_lineEdit_2.textChanged.connect(lambda: self.search(self.search_lineEdit_2, table_proxy_model))

        else:
            print("Error: Tried to switch to a table with no table or tree..Don't know how it got here")
        # todo change to only add rows to table that are needed, not add all and only show some, performance is tanking
        # todo fix QTableView only showing about first 250 rows only, canFetchMore and pagenation


        edit_pushButton.setText(f"Edit {table_name}")

    def get_query_from_table(self, table):

        join = f'SELECT DISTINCT {table}.* FROM Samples '
        match (table):
            case 'Ages':
                if SQLUtils.old_age_join not in join:
                    join += SQLUtils.old_age_join + '\n'
            case 'AgeSignatures':
                if SQLUtils.age_signature_join not in join:
                    join += SQLUtils.age_signature_join + '\n'
            case 'Aliquots':
                if SQLUtils.aliquot_join not in join:
                    join += SQLUtils.aliquot_join + '\n'
            case 'AliquotContext':
                if SQLUtils.aliquot_join not in join:
                    join += SQLUtils.aliquot_join + '\n'
                if SQLUtils.aliquot_context_join not in join:
                    join += SQLUtils.aliquot_context_join + '\n'
            case 'Columns':
                if SQLUtils.column_join not in join:
                    join += SQLUtils.column_join + '\n'
            case 'LabFacilities':
                if SQLUtils.aliquot_join not in join:
                    join += SQLUtils.aliquot_join + '\n'
                if SQLUtils.spot_join not in join:
                    join += SQLUtils.spot_join + '\n'
                if SQLUtils.upb_data_join not in join:
                    join += SQLUtils.upb_data_join + '\n'
                if SQLUtils.labs_join not in join:
                    join += SQLUtils.labs_join + '\n'
            case 'Instruments':
                if SQLUtils.aliquot_join not in join:
                    join += SQLUtils.aliquot_join + '\n'
                if SQLUtils.spot_join not in join:
                    join += SQLUtils.spot_join + '\n'
                if SQLUtils.upb_data_join not in join:
                    join += SQLUtils.upb_data_join + '\n'
                if SQLUtils.instruments_join not in join:
                    join += SQLUtils.instruments_join + '\n'
            case 'Regions':
                if SQLUtils.region_join not in join:
                    join += SQLUtils.region_join + '\n'
            case 'RockTypes':
                if SQLUtils.rock_type_join not in join:
                    join += SQLUtils.rock_type_join + '\n'
            case 'Sample Context':
                if SQLUtils.sample_context_join not in join:
                    join += SQLUtils.sample_context_join + '\n'
            case 'Samples':
                pass
            case 'SamplingMethods':
                if SQLUtils.sampling_method_join not in join:
                    join += SQLUtils.sampling_method_join + '\n'
            case 'Settings':
                if SQLUtils.setting_join not in join:
                    join += SQLUtils.setting_join + '\n'
            case 'Sources':
                if SQLUtils.aliquot_join not in join:
                    join += SQLUtils.aliquot_join + '\n'
                if SQLUtils.spot_join not in join:
                    join += SQLUtils.spot_join + '\n'
                if SQLUtils.upb_data_join not in join:
                    join += SQLUtils.upb_data_join + '\n'
                if SQLUtils.source_join not in join:
                    join += SQLUtils.source_join + '\n'
            case 'SpotCompositions':
                if SQLUtils.aliquot_join not in join:
                    join += SQLUtils.aliquot_join + '\n'
                if SQLUtils.spot_join not in join:
                    join += SQLUtils.spot_join + '\n'
                if SQLUtils.spot_composition_join not in join:
                    join += SQLUtils.spot_composition_join + '\n'
            case 'SpotContext':
                if SQLUtils.aliquot_join not in join:
                    join += SQLUtils.aliquot_join + '\n'
                if SQLUtils.spot_join not in join:
                    join += SQLUtils.spot_join + '\n'
                if SQLUtils.spot_context_join not in join:
                    join += SQLUtils.spot_context_join + '\n'
            case 'UPbData':
                if SQLUtils.aliquot_join not in join:
                    join += SQLUtils.aliquot_join + '\n'
                if SQLUtils.spot_join not in join:
                    join += SQLUtils.spot_join + '\n'
                if SQLUtils.upb_data_join not in join:
                    join += SQLUtils.upb_data_join + '\n'
            case 'UPbAnalysisMethods':
                if SQLUtils.aliquot_join not in join:
                    join += SQLUtils.aliquot_join + '\n'
                if SQLUtils.spot_join not in join:
                    join += SQLUtils.spot_join + '\n'
                if SQLUtils.upb_data_join not in join:
                    join += SQLUtils.upb_data_join + '\n'
                if SQLUtils.upb_method_join not in join:
                    join += SQLUtils.upb_method_join + '\n'
            case 'Units':
                if SQLUtils.unit_join not in join:
                    join += SQLUtils.unit_join + '\n'
        print(join)
        return join

    def search(self, search_lineEdit, proxy_model):
        """
        Search the current table for the text in the search box
        Check if the case-sensitive box is checked or not
        :return:
        """
        search_lineEdit: QtW.QLineEdit
        # if self.case_checkBox.isChecked():
        #     self.sample_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseSensitive)
        #     self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseSensitive)
        #     self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseSensitive)
        # else:
        #     self.sample_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        #     self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        #     self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        search_expression = QtC.QRegularExpression(search_lineEdit.text())
        proxy_model.setFilterRegularExpression(search_expression)


    def get_existing(self, field, table):
        conn = sqlite3.connect(self.db_file)
        with conn:
            c = conn.cursor()
            sql = f'''SELECT {field} FROM {table}'''
            if c.execute(sql):
                existing = c.fetchall()
                return existing

    # def edit_popup(self, db_stackedWidget, dbTable_tableView, dbTable_treeView, dbTable_comboBox, edit_pushButton):
    #     dbTable_comboBox: QComboBox
    #     table_name = dbTable_comboBox.currentText()
    #     table = TxM.remove_spaces(table_name)
    #     if table_name == 'Samples':
    #         dlg = EditTable(self.db, self.sample_model, table_name, self.dbtree_list, 'table')
    #     elif table_name == 'Aliquots' or table_name == 'Spots' or table_name == 'UPb Data':
    #         return
    #     elif table in self.dbtree_list:
    #         dlg = EditTable(self.db, self.tree_model, table_name, self.dbtree_list, 'tree')
    #     else:
    #         dlg = EditTable(self.db, self.model, table_name, self.dbtree_list, 'table')
    #     dlg.exec()
    #     self.display_table(db_stackedWidget, dbTable_tableView, dbTable_treeView, dbTable_comboBox, edit_pushButton)

    def saveWindowState(self):
        self.settings.setValue("ui/GeoChronMain/pos", self.pos())
        self.settings.setValue("ui/GeoChronMain/size", self.size())

    def loadWindowState(self):
        self.move(self.settings.value("ui/GeoChronMain/pos", defaultValue=QPoint(410, 241)))
        self.resize(self.settings.value("ui/GeoChronMain/size", defaultValue=QSize(810, 569)))

import sqlite3
from random import sample

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import Qt, QEventLoop, QStandardPaths, QPoint, QSettings, QSize, QSortFilterProxyModel
from PyQt6.QtWidgets import QFileDialog, QWidget, QComboBox, QTableView, QTreeView
from PyQt6.sip import array
from PyQt6.uic import loadUi
import Functions.Table_classes as TbC
import Functions.Tree_classes as TrC
import Functions.Text_manipulations as TxM
from ui.EditTable import EditTable
class CustomFilterProxyModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.visible_rows = set()  # Track visible rows instead of hidden rows

    def show_row(self, row):
        self.visible_rows.add(row)
        self.invalidateFilter()  # Re-apply filter

    def hide_row(self, row):
        if row in self.visible_rows:
            self.visible_rows.remove(row)
        self.invalidateFilter()  # Re-apply filter

    def filterAcceptsRow(self, source_row, source_parent):
        # By default, hide all rows unless they are in the visible_rows set
        return source_row in self.visible_rows

    def reset_visible_rows(self):
        self.visible_rows = set()
        self.invalidateFilter()

class DataViewerWidget(QWidget):
    def __init__(self, db_file, sample_ids):
        super().__init__()
        self.db_file = db_file

        self.sample_ids = ''

        if len(sample_ids) > 0:
            for sample in sample_ids[0]:
                self.sample_ids += str(sample) + ", "
            self.sample_ids = self.sample_ids[0:-2]
            print("sampleids:")
            print(self.sample_ids)

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

        self.display_table_list(self.dbTable_comboBox)
        self.display_table_list(self.dbTable_comboBox_2)
        self.dbTable_comboBox_2.removeItem(10) # remove sample table index

        self.display_table(self.db_stackedWidget, self.dbTable_tableView, self.dbTable_treeView,
                                self.dbTable_comboBox, self.edit_pushButton)

        self.display_table(self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2,
                                self.dbTable_comboBox_2, self.edit_pushButton_2)

        # Display the selected table
        self.dbTable_comboBox.currentTextChanged.connect(lambda: self.display_table(self.db_stackedWidget, self.dbTable_tableView, self.dbTable_treeView, self.dbTable_comboBox, self.edit_pushButton))
        self.dbTable_comboBox_2.currentTextChanged.connect(lambda: self.display_table_with_sample_filter(
            self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2, self.dbTable_comboBox_2,
            self.edit_pushButton_2, self.dbTable_tableView))

        # self.dbTable_tableView.selectionModel().selectionChanged.connect(lambda: self.display_table_with_sample_filter(
        #     self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2, self.dbTable_comboBox_2,
        #     self.edit_pushButton_2, self.dbTable_tableView))

        self.dbTable_tableView: QTableView
        self.dbTable_tableView.selectionModel().selectionChanged.connect(lambda x: print(x.selected, x.deselected))

        self.display_table(self.db_stackedWidget, self.dbTable_tableView, self.dbTable_treeView,
                           self.dbTable_comboBox, self.edit_pushButton)
        # self.display_table_with_sample_filter(self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2,
        #                    self.dbTable_comboBox_2, self.edit_pushButton_2, self.dbTable_tableView)

        # Signal for search bar
        self.search_lineEdit.textChanged.connect(self.search)
        self.search_lineEdit_2.textChanged.connect(self.search)
        # Signal for clicked add button in main window
        self.edit_pushButton.clicked.connect(
            lambda: self.display_table(self.db_stackedWidget, self.dbTable_tableView, self.dbTable_treeView,
                               self.dbTable_comboBox, self.edit_pushButton))
        self.edit_pushButton_2.clicked.connect(
             lambda: self.display_table(self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2,
                               self.dbTable_comboBox_2, self.edit_pushButton_2))

        self.show()

    def closeEvent(self, a0):
        self.saveWindowState()
        print("closed")
        super().closeEvent(a0)

    # def open_db(self):
    #     """
    #     Opens a file dialog to select an existing database file, must be in the format .db
    #     :return: database file name with path
    #     """
    #     home_dir = str(Path.home())
    #     db_file = QFileDialog.getOpenFileName(self, 'Open file', home_dir, 'db(*.db)')
    #     return db_file[0]

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

    def display_table_list(self, dbTable_comboBox):
        """
        Populates the tables combo box with the editable tables
        Displays the default table
        :return:
        """
        dbTable_comboBox: QtW.QComboBox
        dbTable_comboBox.addItems(self.user_view_tables)
        dbTable_comboBox.setCurrentText('Samples')


    def display_table(self, db_stackedWidget, dbTable_tableView, dbTable_treeView, dbTable_comboBox, edit_pushButton):
        """
        Displays the selected table
        :return:
        """
        table_name = dbTable_comboBox.currentText()
        print("current table: " + table_name)

        # Remove spaces from display names
        table = TxM.remove_spaces(table_name)
        if table == 'Samples':
            self.switch_to_table(db_stackedWidget)
            query = TbC.SampleTableModel().setupQuery()
            sample_model = QtS.QSqlQueryModel()
            sample_proxy_model = QtC.QSortFilterProxyModel()
            sample_model.setQuery(QtS.QSqlQuery(query, self.db))
            sample_proxy_model.setSourceModel(sample_model)
            sample_proxy_model.setFilterKeyColumn(-1)  # search all columns
            dbTable_tableView.setModel(sample_proxy_model)
            dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            # self.dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.OnManualSubmit)
        elif table in self.dbtree_list:
            self.switch_to_tree(db_stackedWidget)
            model = QtS.QSqlTableModel(db=self.db)
            model.setTable(table)
            model.select()
            tree_model = TrC.TreeModel(model, None, self.db)
            tree_proxy_model = QtC.QSortFilterProxyModel()
            tree_proxy_model.setSourceModel(tree_model)

            dbTable_treeView.setModel(tree_proxy_model)
            dbTable_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
            dbTable_treeView.hideColumn(1)  # don't show ID column
            dbTable_treeView.hideColumn(2)  # don't show parent ID column
            dbTable_treeView.setSortingEnabled(True)
        elif table in self.dbtable_list:
            self.switch_to_table(db_stackedWidget)
            model = QtS.QSqlTableModel(db=self.db)
            model.setTable(table)

            model.select()
            table_proxy_model = QtC.QSortFilterProxyModel()
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
            dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
        else:
            print("Error: Tried to switch to a table with no table or tree..Don't know how it got here")

        self.dbTable_tableView.selectionModel().selectionChanged.connect(lambda selected, deselected: self.display_table_with_sample_filter(
            self.db_stackedWidget_2, self.dbTable_tableView_2, self.dbTable_treeView_2, self.dbTable_comboBox_2,
            self.edit_pushButton_2, self.dbTable_tableView, selected, deselected))

        # dbTable_tableView.reset()
        # dbTable_treeView.reset()
        edit_pushButton.setText(f"Edit {table_name}")

    def display_table_with_sample_filter(self, db_stackedWidget, dbTable_tableView, dbTable_treeView,
                                         dbTable_comboBox, edit_pushButton, sample_filter, selected=None, deselected=None):
        """
        Displays the selected table
        :return:
        """
        print("DB TABLE 2 CHANGED")
        self.dbTable_tableView: QTableView
        dbTable_treeView: QTreeView
        table_name = dbTable_comboBox.currentText()
        # Remove spaces from display names
        table = TxM.remove_spaces(table_name)
        print("current table: " + table_name)
        sample_filter: QTableView
        sample_id = '('
        rows_to_show = []
        if sample_filter.selectionModel().hasSelection():
            for row in self.dbTable_tableView.selectionModel().selectedIndexes():
                sample_id += str(self.dbTable_tableView.model().index(row.row(), 0).data()) + ','
            # "(19,39,58)"
            sample_id = sample_id[0:-1] + ')'
            conn = sqlite3.connect(self.db_file)

            with conn:
                c = conn.cursor()
                sql = self.get_query_from_table(table) + f'WHERE Samples.SampleID IN {sample_id}'
                print(sql)
                if c.execute(sql):
                    existing = c.fetchall()
                    for row in existing:
                        if row[0] is not None:
                            print(row)
                            rows_to_show.append(row[0]-1)

        if table in self.dbtree_list:
            self.switch_to_tree(db_stackedWidget)
            model = QtS.QSqlTableModel(db=self.db)
            model.setTable(table)
            model.select()
            tree_model = TrC.TreeModel(model, None, self.db)
            tree_proxy_model = CustomFilterProxyModel()
            tree_proxy_model.setSourceModel(tree_model)
            dbTable_treeView.setModel(tree_proxy_model)
            dbTable_treeView.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
            dbTable_treeView.hideColumn(1)  # don't show ID column
            dbTable_treeView.hideColumn(2)  # don't show parent ID column
            dbTable_treeView.setSortingEnabled(True)

            tree_proxy_model.reset_visible_rows()
            for row in rows_to_show:
                tree_proxy_model.show_row(row)
                # todo fix child items not being seen due to parent not showing


        elif table in self.dbtable_list:
            self.switch_to_table(db_stackedWidget)
            model = QtS.QSqlTableModel(db=self.db)
            model.setTable(table)

            model.select()
            table_proxy_model = CustomFilterProxyModel()
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
            dbTable_tableView.hideColumn(0)  # don't show ID column
            dbTable_tableView.verticalHeader().setVisible(False)
            dbTable_tableView.resizeColumnsToContents()
            dbTable_tableView.setSortingEnabled(True)
            dbTable_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)

            for row in rows_to_show:
                table_proxy_model.show_row(row)
            dbTable_tableView.reset()
        else:
            print("Error: Tried to switch to a table with no table or tree..Don't know how it got here")
        # todo change to only add rows to table that are needed, not add all and only show some, performance is tanking
        # todo fix QTableView only showing about first 250 rows only, canFetchMore and pagenation

        edit_pushButton.setText(f"Edit {table_name}")

    def get_query_from_table(self, table):
        # Join lines
        old_age_join = 'LEFT JOIN Ages ON Samples.OldestAgeID=Ages.AgeID'
        young_age_join = 'LEFT JOIN Ages ON Samples.YoungestAgeID=Ages.AgeID'
        age_signature_join = '''LEFT JOIN Samples_AgeSignatures ON Samples.SampleID=Samples_AgeSignatures.SampleID
                                                    LEFT JOIN AgeSignatures ON AgeSignatures.AgeSignatureID=Samples_AgeSignatures.AgeSignatureID'''
        column_join = '''LEFT JOIN Samples_Columns ON Samples.SampleID=Samples_Columns.SampleID
                                                    LEFT JOIN Columns ON Columns.ColumnID=Samples_Columns.ColumnID'''
        rock_type_join = '''LEFT JOIN Samples_RockTypes ON Samples.SampleID=Samples_RockTypes.SampleID
                                                LEFT JOIN RockTypes ON RockTypes.RockTypeID=Samples_RockTypes.RockTypeID'''
        region_join = '''LEFT JOIN Samples_Regions ON Samples.SampleID=Samples_Regions.SampleID
                                                LEFT JOIN Regions ON Regions.RegionID=Samples_Regions.RegionID'''
        setting_join = '''LEFT JOIN Samples_Settings ON Samples.SampleID=Samples_Settings.SampleID
                                                LEFT JOIN Settings ON Settings.SettingID=Samples_Settings.SettingID'''
        unit_join = '''LEFT JOIN Samples_Units ON Samples.SampleID=Samples_Units.SampleID
                                                LEFT JOIN Units ON Units.UnitID=Samples_Units.UnitID'''
        sample_context_join = '''LEFT JOIN Samples_SampleContext ON Samples.SampleID=Samples_SampleContext.SampleID
                                                LEFT JOIN SampleContext ON SampleContext.SampleContextID=Samples_SampleContext.SampleContextID'''
        sampling_method_join = '''LEFT JOIN Samples_SamplingMethods ON Samples.SampleID=Samples_SamplingMethods.SampleID
                                                LEFT JOIN SamplingMethods ON SamplingMethods.SamplingMethodID=Samples_SamplingMethods.SamplingMethodID'''

        aliquot_join = 'LEFT JOIN Aliquots ON Aliquots.SampleID=Samples.SampleID'
        spot_join = 'LEFT JOIN Spots ON Spots.AliquotID=Aliquots.AliquotID'
        upb_data_join = 'LEFT JOIN UPbData ON UPbData.SpotID=Spots.SpotID'
        source_join = 'LEFT JOIN Sources ON Sources.SourceID=UPbData.SourceID'
        upb_method_join = 'LEFT JOIN UPbAnalysisMethods ON UPbAnalysisMethods.UPbAnalysisMethodID=UPbData.UPbAnalysisMethodID'
        instruments_join = 'LEFT JOIN Instruments ON Instruments.InstrumentID=UPbData.InstrumentID'
        labs_join = 'LEFT JOIN LabFacilities ON LabFacilities.LabFacilityID=UPbData.LabFacilityID'
        spot_context_join = '''LEFT JOIN Spots_SpotContext ON Spots.SpotID=Spots_SpotContext.SpotID
                                                LEFT JOIN SpotContext ON SpotContext.SpotContextID=Spots_SpotContext.SpotContextID'''
        spot_composition_join = '''LEFT JOIN SpotCompositions ON SpotCompositions.SpotCompositionID=Spots.SpotCompositionID'''
        aliquot_context_join = '''LEFT JOIN Aliquots_AliquotContext ON Aliquots.AliquotID=Aliquots_AliquotContext.AliquotID
                                                LEFT JOIN AliquotContext ON AliquotContext.AliquotContextID=Aliquots_AliquotContext.AliquotContextID'''

        join = f'SELECT {table}.* FROM Samples '
        match (table):
            case 'Ages':
                if old_age_join not in join:
                    join += old_age_join + '\n'
            case 'AgeSignatures':
                if age_signature_join not in join:
                    join += age_signature_join + '\n'
            case 'Aliquots':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
            case 'AliquotContext':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if aliquot_context_join not in join:
                    join += aliquot_context_join + '\n'
            case 'Columns':
                if column_join not in join:
                    join += column_join + '\n'
            case 'LabFacilities':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if spot_join not in join:
                    join += spot_join + '\n'
                if upb_data_join not in join:
                    join += upb_data_join + '\n'
                if labs_join not in join:
                    join += labs_join + '\n'
            case 'Instruments':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if spot_join not in join:
                    join += spot_join + '\n'
                if upb_data_join not in join:
                    join += upb_data_join + '\n'
                if instruments_join not in join:
                    join += instruments_join + '\n'
            case 'Regions':
                if region_join not in join:
                    join += region_join + '\n'
            case 'RockTypes':
                if rock_type_join not in join:
                    join += rock_type_join + '\n'
            case 'Sample Context':
                if sample_context_join not in join:
                    join += sample_context_join + '\n'
            case 'Samples':
                pass
            case 'SamplingMethods':
                if sampling_method_join not in join:
                    join += sampling_method_join + '\n'
            case 'Settings':
                if setting_join not in join:
                    join += setting_join + '\n'
            case 'Sources':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if spot_join not in join:
                    join += spot_join + '\n'
                if upb_data_join not in join:
                    join += upb_data_join + '\n'
                if source_join not in join:
                    join += source_join + '\n'
            case 'SpotCompositions':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if spot_join not in join:
                    join += spot_join + '\n'
                if spot_composition_join not in join:
                    join += spot_composition_join + '\n'
            case 'SpotContext':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if spot_join not in join:
                    join += spot_join + '\n'
                if spot_context_join not in join:
                    join += spot_context_join + '\n'
            case 'UPbData':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if spot_join not in join:
                    join += spot_join + '\n'
                if upb_data_join not in join:
                    join += upb_data_join + '\n'
            case 'UPbAnalysisMethods':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if spot_join not in join:
                    join += spot_join + '\n'
                if upb_data_join not in join:
                    join += upb_data_join + '\n'
                if upb_method_join not in join:
                    join += upb_method_join + '\n'
            case 'Units':
                if unit_join not in join:
                    join += unit_join + '\n'

        return join

    def search(self, search_lineEdit, dbTable_comboBox):
        """
        Search the current table for the text in the search box
        Check if the case-sensitive box is checked or not
        :return:
        """
        search_lineEdit: QtW.QLineEdit
        dbtable_comboBox: QtW.QComboBox
        # if self.case_checkBox.isChecked():
        #     self.sample_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseSensitive)
        #     self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseSensitive)
        #     self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseSensitive)
        # else:
        #     self.sample_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        #     self.tree_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        #     self.table_proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        search_expression = QtC.QRegularExpression(search_lineEdit.text())
        table_name = dbTable_comboBox.currentText()
        # Remove spaces from display names
        table = table_name.replace(" ", "")
        # if table == 'Samples':
        #     self.sample_proxy_model.setFilterRegularExpression(search_expression)
        # elif table in self.dbtree_list:
        #     self.tree_proxy_model.setFilterRegularExpression(search_expression)
        # else:
        #     self.table_proxy_model.setFilterRegularExpression(search_expression)

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

import os
import sys
from wsgiref import headers

from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6 import QtWidgets as QtW
from PyQt6.QtWidgets import QLabel
from PyQt6.uic import loadUi

import Functions.Text_manipulations as TxM
import logger_setup
from Functions.Database_manager import update_database
from Functions.Database_views import ViewQuery
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
import Functions.SQLUtils as SQLUtils
from Functions.Widget_classes import set_table, get_headers, get_name_column, description_column, ReadableProxyModel, \
    get_edit_view_from_table, SQLiteTableModel, close_loading_dialog, show_loading_dialog


class AddTags(QtW.QDialog):
    """
    A dialog for adding tags to a table in the database.
    """

    def __init__(self, parent_window, table):
        super().__init__(parent=parent_window)
        logger_setup.get_logger().info(f'Starting AddTags dialog for {table}...')
        # Define any widgets here
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "AddTags.ui")
        loadUi(sources_ui_file, self)
        self.setModal(True)
        self.setWindowTitle(f'Add tags to {TxM.add_spaces_camel(table)}')
        self.updated = False
        self.ids_added = []

        self.table = table
        self.model = QtS.QSqlTableModel()
        self.table_name = TxM.add_spaces_camel(self.table)
        self.selectTags_label.setText(self.table_name)
        self.errmsg = QtW.QMessageBox(self)
        self.clear_warning()
        self.cancel_pushButton.setAutoDefault(False)
        self.ok_pushButton.setAutoDefault(True)

        self.filter_proxy_model = ReadableProxyModel()
        self.newName_lineEdit.textChanged.connect(self.filter_proxy_model.setFilterRegularExpression)

        self.existing_names = set()

        self.close_by_dialog = False
        self.display_tags()
        create_savepoint('before_add')
        self.ok_pushButton.clicked.connect(self.add_tag)
        self.cancel_pushButton.clicked.connect(self.discard_question)
        self.finish_pushButton.clicked.connect(self.commit)

        close_loading_dialog('Loading', f'Opening add window for {self.table}...')

    def display_tags(self):
        """
        Displays the tags in the table view.
        :return:
        """
        self.model = QtS.QSqlTableModel()
        set_table(self.model, self.table)
        self.columns = get_headers(self.table)
        self.name_header = self.columns[get_name_column(self.table)]
        self.description_header = self.columns[description_column(self.table)]
        while self.model.canFetchMore():
            self.model.fetchMore()
        self.filter_proxy_model.setSourceModel(self.model)
        self.filter_proxy_model.setFilterKeyColumn(1)
        self.tags_tableView.setModel(self.filter_proxy_model)
        self.tags_tableView.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tags_tableView.hideColumn(0)  # Hide the ID column
        self.tags_tableView.resizeColumnsToContents()
        self.tags_tableView.horizontalHeader().setDefaultAlignment(QtC.Qt.AlignmentFlag.AlignLeft)
        query = QtS.QSqlQuery()

        # Get a list of the existing tag names
        query.prepare(f'SELECT {self.name_header} FROM {self.table}')
        if not query.exec():
            logger_setup.get_logger().critical(
                f'Error selecting display column from {self.table}: {query.lastError().text()}')
            return False
        self.existing_names = set()
        while query.next():
            self.existing_names.add(query.value(0))
        completer = QtW.QCompleter(self.existing_names)
        completer.setFilterMode(QtC.Qt.MatchFlag.MatchStartsWith)
        completer.setCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QtW.QCompleter.CompletionMode.PopupCompletion)
        self.newName_lineEdit.setCompleter(completer)

    def clear_warning(self):
        """
        Hide the warning label if it is visible. Warning label is used when a duplicate name is entered.
        """
        self.warning_label.hide()

    def add_tag(self):
        """
        Adds the tag to the database. Since a savepoint is created before the dialog is opened, this function
        is not commited to the database, ensures any errors are rolled back.
        :return:
        """
        name = self.newName_lineEdit.text()
        description = self.newDescription_lineEdit.text()
        query = QtS.QSqlQuery()
        query.prepare(f'INSERT INTO {self.table}({self.name_header}, {self.description_header}) VALUES(?, ?)')
        query.addBindValue(name)
        query.addBindValue(None if description=='' else description)

        logger_setup.get_logger().info(f'Inserting {name}, {description} into {self.table}')

        if not query.exec():
            error = query.lastError().text()
            header = TxM.add_spaces_camel(self.columns[1])
            if 'UNIQUE constraint failed:' in error:
                duplicates = []
                for entry in self.existing_names:
                    if name.casefold() == entry.casefold():
                        duplicates.append(entry)
                logger_setup.get_logger().error(
                    f'Each entry in {header} must be unique (case insensitive)\nDuplicates: {duplicates}')
                logger_setup.get_logger().debug(f'Error: {error}')
                logger_setup.get_logger().debug(f'SQL command: {query.lastQuery()}')
            elif 'CHECK constraint failed:' in error:
                logger_setup.get_logger().error(f'{header} cannot be blank')
                logger_setup.get_logger().debug(f'Error: {error}')
                logger_setup.get_logger().debug(f'SQL command: {query.lastQuery()}')
            else:
                logger_setup.get_logger().critical(f'Error: {error}')
                logger_setup.get_logger().debug(f'SQL command: {query.lastQuery()}')
            rollback_savepoint('before_add')
            return False

        logger_setup.get_logger().info(f'Successfully inserted {name} into {self.table}')
        self.updated = True
        self.ids_added.append(query.lastInsertId())
        self.model.select()
        while self.model.canFetchMore():
            self.model.fetchMore()
        self.newName_lineEdit.clear()
        self.newDescription_lineEdit.clear()
        self.display_tags()

        logger_setup.get_logger().info(f'Successfully inserted {name}, {description} into {self.table}')
        return True

    def discard_question(self):
        """
        Asks the user if they want to discard changes. If they do, the changes are rolled back.
        """
        msg_box = QtW.QMessageBox()
        msg_box.setIcon(QtW.QMessageBox.Icon.Question)
        msg_box.setText('Are you sure you want to discard all changes?')
        msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            self.rollback()
        else:
            pass

    def rollback(self):
        """
        Rolls back the changes to the database. Rejects the dialog and closes the the window.
        """
        rollback_savepoint('before_add')
        self.reject()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        """
        Commits the changes to the database. If there is an active savepoint, it is released.
        """
        if self.newName_lineEdit.text():
            if not self.add_tag():
                return False
        release_savepoint('before_add')
        logger_setup.get_logger().info(f'Changes committed to {self.table}')
        # Check if there is another existing savepoint. If not, go ahead and update the database
        if not SavepointManager.get_instance().active_savepoints():
            logger_setup.get_logger().info('No active save points - updating the database')
            if not update_database():
                logger_setup.get_logger().critical(f'Error updating and displaying the database')
                self.close_by_dialog = True
                self.close()
        self.accept()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def closeEvent(self, event: QtG.QCloseEvent):
        """
        Overridden close event to handle the case where the user tries to close the dialog
        :param QCloseEvent event:
        """
        if not self.close_by_dialog:
            if self.updated:
                self.discard_question()
                event.ignore()
            else:
                logger_setup.get_logger().info(f'Closing {self.table} add dialog')
                release_savepoint('before_add')
                event.accept()
        else:
            logger_setup.get_logger().info(f'Closing {self.table} add dialog')
            release_savepoint('before_add')
            event.accept()

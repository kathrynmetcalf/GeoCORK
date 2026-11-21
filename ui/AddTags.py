from PyQt6 import QtWidgets, QtSql, QtCore, QtGui
from PyQt6.QtCore import QPoint, QSize
from PyQt6.QtWidgets import QDialogButtonBox, QLabel, QFormLayout, QLineEdit, QHBoxLayout, QVBoxLayout, QPushButton

import util.Text_manipulations as TxM
from util import logger
from util.database.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from util.database.database_helper import set_table, get_headers, get_name_column, get_description_column, \
    update_database
from util.loading_dialog_manager import close_loading_dialog
from util.settings_manager import SettingsManager
from util.widgets.models.proxy_models import ReadableProxyModel
from util.widgets.views.frozen_views import FrozenTableView

settings = SettingsManager().settings


class AddTags(QtWidgets.QDialog):

    def __init__(self, parent_window, table):
        """
        A dialog window for adding tags to a normal table in the database. The dialog allows the user to enter a name and
        description for the new item. The dialog also displays the existing items in the table view,
        allowing the user to see existing items. A completer is provided for the name field to avoid duplicates,
        and a warning label is shown if a duplicate name is entered.
        :param parent_window:
        :param table:
        """
        super().__init__(parent=parent_window)
        logger.get_logger().info(f'Starting AddTags dialog for {table}...')

        self.table = table
        """Database table used for internal or query use"""

        self.table_name = TxM.add_spaces_camel(self.table)
        """Display name of the table with spaces and capitalization"""

        self.build_ui()
        self.loadWindowState()

        self.setModal(True)
        self.setWindowTitle(f'Add tags to {self.table_name}')
        self.updated = False
        self.ids_added = []

        self.model = QtSql.QSqlTableModel()

        self.errmsg = QtWidgets.QMessageBox(self)
        self.clear_warning()

        self.filter_proxy_model = ReadableProxyModel()
        self.newName_lineEdit.textChanged.connect(self.filter_proxy_model.setFilterRegularExpression)

        self.existing_names = set()

        self.close_by_dialog = False
        self.display_tags()
        create_savepoint('before_add')

        close_loading_dialog('Loading', f'Opening add window for {self.table_name}...')

    def build_ui(self):
        self.main_layout = QVBoxLayout(self)

        self.main_layout.addWidget(QLabel("Adding new item to top level at new row"))

        # ---- Top row: Add button, search ----
        self.input_form_layout = QFormLayout()
        # todo figure out this alignment issue
        self.input_form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        name_label = QLabel('<span style="color: #FF0000; font-weight: bold;">*</span> New Unique Name:')
        self.newName_lineEdit = QLineEdit()
        self.newName_lineEdit.setPlaceholderText('e.g., abc123')
        self.newName_lineEdit.setToolTip("The name must be unique across all tags in the same table_name")
        self.input_form_layout.addRow(name_label, self.newName_lineEdit)

        self.newDescription_lineEdit = QLineEdit()
        self.newDescription_lineEdit.setPlaceholderText('e.g., abc123')
        self.newDescription_lineEdit.setToolTip("Optional description for the tag to be added")
        self.input_form_layout.addRow('New Description:',
                                      self.newDescription_lineEdit)

        self.main_layout.addLayout(self.input_form_layout)

        self.central_layout = QHBoxLayout()
        required_label = QLabel('<span style="color: #FF0000; font-weight: bold;">*</span> Required')
        self.central_layout.addWidget(required_label)

        self.warning_label = QLabel("Error: Duplicate tag name")
        self.central_layout.addWidget(self.warning_label)
        self.central_layout.addStretch()

        self.add_pushButton = QPushButton(f'Add {self.table_name}')
        self.add_pushButton.setObjectName("add_pushButton")
        self.add_pushButton.setAutoDefault(False)
        self.add_pushButton.setToolTip("Adds the tag with a unique name and description")
        self.central_layout.addWidget(self.add_pushButton)
        self.add_pushButton.clicked.connect(self.add_tag)

        self.main_layout.addLayout(self.central_layout)

        # frozen table view
        self.tags_tableView = FrozenTableView()
        self.main_layout.addWidget(self.tags_tableView)

        # ---- Bottom row: Cancel / Commit ----
        self.buttonBox = QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        self.buttonBox.accepted.connect(self.commit)
        self.buttonBox.rejected.connect(self.discard_question)

        self.main_layout.addWidget(self.buttonBox)

    def display_tags(self):
        """
        Displays the tags in the table_name view.
        :return:
        """
        self.model = QtSql.QSqlTableModel()
        set_table(self.model, self.table_name)
        self.columns = get_headers(self.table_name)
        self.name_header = self.columns[get_name_column(self.table)]
        self.description_header = self.columns[get_description_column(self.table)]
        while self.model.canFetchMore():
            self.model.fetchMore()
        self.filter_proxy_model.setSourceModel(self.model)
        self.filter_proxy_model.setFilterKeyColumn(1)
        self.tags_tableView.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tags_tableView.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.tags_tableView.setModel(self.filter_proxy_model)
        self.tags_tableView.hideColumn(0)  # Hide the ID column
        self.tags_tableView.resizeColumnsToContents()
        for column in range(self.filter_proxy_model.columnCount()):
            if self.tags_tableView.columnWidth(column) > 400:
                self.tags_tableView.setColumnWidth(column, 400)
        query = QtSql.QSqlQuery()

        # Get a list of the existing tag names
        query.prepare(f'SELECT {self.name_header} FROM {self.table}')
        if not query.exec():
            logger.get_logger().critical(
                f'Error selecting display column from {self.table_name}: {query.lastError().text()}')
            return False
        self.existing_names = set()
        while query.next():
            self.existing_names.add(query.value(0))
        completer = QtWidgets.QCompleter(self.existing_names)
        completer.setFilterMode(QtCore.Qt.MatchFlag.MatchStartsWith)
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
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
        query = QtSql.QSqlQuery()
        query.prepare(f'INSERT INTO {self.table}({self.name_header}, {self.description_header}) VALUES(?, ?)')
        query.addBindValue(name)
        query.addBindValue(None if description == '' else description)

        logger.get_logger().info(f'Inserting {name}, {description} into {self.table_name}')
        create_savepoint(f'before_add_item')
        if not query.exec():
            error = query.lastError().text()
            header = TxM.add_spaces_camel(self.columns[1])
            if 'UNIQUE constraint failed:' in error:
                duplicates = []
                for entry in self.existing_names:
                    if name.casefold() == entry.casefold():
                        duplicates.append(entry)
                logger.get_logger().error(
                    f'Each entry in {header} must be unique (case insensitive)\nDuplicates: {duplicates}')
                logger.get_logger().debug(f'Error: {error}')
                logger.get_logger().debug(f'SQL command: {query.lastQuery()}')
            elif 'CHECK constraint failed:' in error:
                logger.get_logger().error(f'{header} cannot be blank')
                logger.get_logger().debug(f'Error: {error}')
                logger.get_logger().debug(f'SQL command: {query.lastQuery()}')
            else:
                logger.get_logger().critical(f'Error: {error}')
                logger.get_logger().debug(f'SQL command: {query.lastQuery()}')
            rollback_savepoint('before_add_item')
            return False

        logger.get_logger().info(f'Successfully inserted {name} into {self.table_name}')
        release_savepoint('before_add_item')
        self.updated = True
        self.ids_added.append(query.lastInsertId())
        self.model.select()
        while self.model.canFetchMore():
            self.model.fetchMore()
        self.newName_lineEdit.clear()
        self.newDescription_lineEdit.clear()
        self.display_tags()

        logger.get_logger().info(f'Successfully inserted {name}, {description} into {self.table_name}')
        return True

    def discard_question(self):
        """
        Asks the user if they want to discard changes. If they do, the changes are rolled back.
        """
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Icon.Question)
        msg_box.setText('Are you sure you want to discard all changes?')
        msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response == QtWidgets.QMessageBox.StandardButton.Yes:
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
        logger.get_logger().info(f'Changes committed to {self.table_name}')
        # Check if there is another existing savepoint. If not, go ahead and update the database
        if not SavepointManager.get_instance().active_savepoints():
            logger.get_logger().info('No active save points - updating the database')
            if not update_database():
                logger.get_logger().critical(f'Error updating and displaying the database')
                self.close_by_dialog = True
                self.close()
        self.accept()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def closeEvent(self, event: QtGui.QCloseEvent):
        """
        Overridden close event to handle the case where the user tries to close the dialog
        :param QCloseEvent event:
        """
        self.saveWindowState()
        if not self.close_by_dialog:
            if self.updated:
                self.discard_question()
                event.ignore()
            else:
                logger.get_logger().info(f'Closing {self.table_name} add dialog')
                release_savepoint('before_add')
                event.accept()
        else:
            logger.get_logger().info(f'Closing {self.table_name} add dialog')
            release_savepoint('before_add')
            event.accept()

    def saveWindowState(self):
        settings.setValue(f"ui/{self.table}/pos", self.pos())
        settings.setValue(f"ui/{self.table}/size", self.size())

    def loadWindowState(self):
        self.move(settings.value(f"ui/{self.table}/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value(f"ui/{self.table}/size", defaultValue=QSize(810, 569)))

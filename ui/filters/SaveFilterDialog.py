from PyQt6.QtSql import QSqlQuery
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QTextEdit, QMessageBox

import logger_setup
from Functions.Widget_classes import get_name_from_id, get_id_from_name


class SaveFilterDialog(QDialog):
    """
    Assists the user with inserting or updating a valid FilterQueryBuilder to the database
    """

    def __init__(self, sql_structure, update_id=None, parent=None):
        """
        :param sql_structure: json dict structure for the filter group
        :param update_id: id of the filter group to update, None if inserting a new one
        :param parent:
        """
        super().__init__(parent)
        self.sql_structure = sql_structure
        self.update_id = update_id

        if self.update_id:
            self.setWindowTitle("Update Filter Group")
        else:
            self.setWindowTitle("Insert New Filter Group")

        layout = QVBoxLayout()
        self.name_label = QLabel("Filter Group Name:")
        self.name_input = QLineEdit()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)

        self.warning_label = QLabel()
        layout.addWidget(self.warning_label)

        self.description_label = QLabel("Filter Group Description:")
        self.description_input = QTextEdit()
        layout.addWidget(self.description_label)
        layout.addWidget(self.description_input)

        if self.update_id:
            self.update_button = QPushButton("Update")
            self.update_button.clicked.connect(self.update_data)
        else:
            self.insert_button = QPushButton("Insert")
            self.insert_button.clicked.connect(self.insert_data)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout = QHBoxLayout()
        if self.update_id:
            buttons_layout.addWidget(self.update_button)
        else:
            buttons_layout.addWidget(self.insert_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        if self.update_id:
            self.populate_fields()

    def populate_fields(self):
        """
        Populates the fields with the existing filter group data.
        :return:
        """
        query = QSqlQuery()
        sql_query = """
            SELECT FilterGroupName, FilterGroupDescription 
            FROM FilterGroups 
            WHERE FilterGroupID = :filter_id;
        """
        query.prepare(sql_query)
        query.bindValue(":filter_id", self.update_id)
        logger_setup.get_logger().info(f'Populating fields for filter: {self.update_id}')
        if query.exec():
            if query.next():
                self.name_input.setText(query.value(0))
                self.description_input.setText(query.value(1))
            else:
                filter_name = get_name_from_id('FilterGroups', self.update_id)
                logger_setup.get_logger().critical(f'No filter group "{filter_name}" found.')
                logger_setup.get_logger().debug(f'SQL command: {sql_query}')
        else:
            logger_setup.get_logger().critical(
                f'Error in populating existing Filters')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL command: {sql_query}')
            logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')

    def insert_data(self):
        """
        Inserts a new filter group into the database. If the name already exists, it prompts the user to update
        the existing one
        """
        name = self.name_input.text()
        if not name:
            self.warning_label.setText('Please enter a filter name')

        description = self.description_input.toPlainText()

        query = QSqlQuery()

        check_query = "SELECT FilterGroupName FROM FilterGroups WHERE FilterGroupName = :name COLLATE NOCASE"
        query.prepare(check_query)
        query.bindValue(":name", name)
        logger_setup.get_logger().info(f'Checking if name: {name} already exists in FilterGroups table')
        if not query.exec():
            logger_setup.get_logger().critical(
                f'Error in checking for existing Filters')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL command: {check_query}')
            logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
            return

        if query.next():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setText(f"Filter {name} already exists. Do you want to update it?")
            msg.setWindowTitle("Duplicate Filter Name")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.No)
            reply = msg.exec()
            if reply == QMessageBox.StandardButton.Yes:
                self.update_id = get_id_from_name('FilterGroups', name)
                self.update_data()
            else:
                return
        else:
            insert_query = """
                INSERT INTO FilterGroups (FilterGroupName, SQLQuery, FilterGroupDescription)
                VALUES (:name, :sql_query, :description)
            """
            query.prepare(insert_query)
            query.bindValue(":name", name)
            query.bindValue(":sql_query", f'\'{self.sql_structure}\'')
            query.bindValue(":description", None if description=='' else description)

            if not query.exec():
                logger_setup.get_logger().critical(
                    f'Error could not add filter')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL command: {check_query}')
                logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
            else:
                logger_setup.get_logger().info(f'Filter {name} added')
                self.accept()

    def update_data(self):
        name = self.name_input.text()
        description = self.description_input.toPlainText()

        query = QSqlQuery()
        update_query = """
            UPDATE FilterGroups
            SET FilterGroupName = :name, SQLQuery = :sql_query, FilterGroupDescription = :description
            WHERE FilterGroupID = :id
        """
        query.prepare(update_query)
        query.bindValue(":name", name)
        query.bindValue(":sql_query", f'\'{self.sql_structure}\'')
        query.bindValue(":description", description)
        query.bindValue(":id", self.update_id)
        if not query.exec():
            logger_setup.get_logger().critical(
                f'Error could not update filter')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL command: {update_query}')
            logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
        else:
            logger_setup.get_logger().info(f'Filter {name} updated')
            self.accept()

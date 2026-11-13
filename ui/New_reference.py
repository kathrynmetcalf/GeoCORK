from PyQt6 import QtWidgets
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtWidgets import QDialogButtonBox

from Functions.Widget_classes import close_loading_dialog, show_loading_dialog
import logger_setup


class NewReference(QtWidgets.QDialog):
    def __init__(self, parent_window):
        super().__init__(parent=parent_window)

        logger_setup.get_logger().info(f'Opening reference add dialog')
        show_loading_dialog('Loading', 'Opening add window for References...')

        self.build_ui()

        self.setWindowTitle('Add Reference')
        self.setModal(True)
        self.updated = False
        self.ids_added = []

        close_loading_dialog('Loading', 'Opening add window for References...')

    def build_ui(self):
        self.form_layout = QtWidgets.QFormLayout(self)
        self.setLayout(self.form_layout)

        self.authors_lineEdit = QtWidgets.QLineEdit()
        self.authors_lineEdit.setPlaceholderText('e.g., Metcalf and Burges, Metcalf et al.')
        self.form_layout.addRow('Authors:', self.authors_lineEdit)

        self.title_lineEdit = QtWidgets.QLineEdit()
        self.title_lineEdit.setPlaceholderText('e.g., abc123')
        self.form_layout.addRow('Title:', self.title_lineEdit)

        self.year_lineEdit = QtWidgets.QLineEdit()
        self.year_lineEdit.setPlaceholderText('e.g., 2026')
        self.form_layout.addRow('Year:', self.year_lineEdit)

        self.source_lineEdit = QtWidgets.QLineEdit()
        self.source_lineEdit.setPlaceholderText('e.g., abc123')
        self.form_layout.addRow('Source:', self.source_lineEdit)

        self.doi_lineEdit = QtWidgets.QLineEdit()
        self.doi_lineEdit.setPlaceholderText('e.g., 10.xxxx/xxxx')
        self.form_layout.addRow('DOI:', self.doi_lineEdit)

        self.description_lineEdit = QtWidgets.QLineEdit()
        self.description_lineEdit.setPlaceholderText('e.g., abc123')
        self.form_layout.addRow('Description:', self.description_lineEdit)

        self.buttonBox = QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        self.form_layout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.add_reference)
        self.buttonBox.rejected.connect(self.rejected)

    def add_reference(self):
        authors = self.authors_lineEdit.text()
        year = self.year_lineEdit.text()
        title = self.title_lineEdit.text()
        source = self.source_lineEdit.text()
        doi = self.doi_lineEdit.text()
        description = self.description_lineEdit.text()

        query = QSqlQuery()
        query.prepare('SELECT * FROM "References" WHERE Authors = ? AND Year = ? AND Title = ? AND Source = ? AND DOI = ?')
        query.addBindValue(None if authors=='' else authors)
        query.addBindValue(None if year=='' else year)
        query.addBindValue(None if title=='' else title)
        query.addBindValue(None if source=='' else source)
        query.addBindValue(None if doi=='' else doi)
        if not query.exec():
            logger_setup.get_logger().critical('Error checking for duplicate reference')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
            return
        if query.next():
            logger_setup.get_logger().info('Reference already exists')
            return
        query.prepare('INSERT INTO "References" (Authors, Year, Title, Source, DOI, ReferenceDescription) VALUES (?, ?, ?, ?, ?, ?)')
        query.addBindValue(None if authors=='' else authors)
        query.addBindValue(None if year=='' else year)
        query.addBindValue(None if title=='' else title)
        query.addBindValue(None if source=='' else source)
        query.addBindValue(None if doi=='' else doi)
        query.addBindValue(None if description=='' else description)
        if not query.exec():
            logger_setup.get_logger().critical('Error adding reference')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
            return
        logger_setup.get_logger().info('Reference added successfully')
        self.updated = True
        self.ids_added.append(query.lastInsertId())
        self.accept()

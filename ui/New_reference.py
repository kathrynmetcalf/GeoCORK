import os
import sys
import sqlite3
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6.uic import loadUi
from PyQt6.QtSql import QSqlQuery

from Functions.Widget_classes import close_loading_dialog, show_loading_dialog
import logger_setup


class NewReference(QtW.QDialog):
    def __init__(self, parent_window):
        super().__init__(parent=parent_window)

        logger_setup.get_logger().info(f'Opening reference add dialog')

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        base_path = os.path.normpath(base_path)
        sources_ui_file = fr'{os.path.join(base_path, "New_reference.ui")}'
        sources_ui_file = os.path.normpath(sources_ui_file)
        loadUi(sources_ui_file, self)
        self.setWindowTitle('Add Reference')
        self.setModal(True)
        self.updated = False
        self.ids_added = []

        self.ok_buttonBox.accepted.connect(self.add_reference)
        self.ok_buttonBox.rejected.connect(self.rejected)

        close_loading_dialog('Loading', 'Opening add window for References...')

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

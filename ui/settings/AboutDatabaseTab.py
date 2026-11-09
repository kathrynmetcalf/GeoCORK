"""'About Database' tab of the Settings dialog."""
from PyQt6 import QtWidgets as QtW, QtCore
from PyQt6.QtCore import QStandardPaths
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtSql import QSqlQueryModel, QSqlQuery

import logger_setup
from ui.settings.UnitsFormatsTab import fixed_height


class AboutDatabaseTab(QtW.QWidget):
    """
    Database About table fields plus logs/backups folder buttons.
    """
    title = 'About Database'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('about_db_tab')
        self.about_db_model = QSqlQueryModel()
        self.build_ui()

    def build_ui(self):
        layout = QtW.QVBoxLayout(self)
        layout.setObjectName('verticalLayout_4')

        grid = QtW.QGridLayout()
        grid.setObjectName('gridLayout_4')
        rows = [('db_name', 'Database Name*', 'e.g. abc123'),
                ('db_description', 'Database Description', 'e.g. abc123'),
                ('db_created_by', 'Created By*', 'e.g. abc123'),
                ('db_authors', 'Database Author(s)*', 'e.g. abc123'),
                ('db_reference', 'Reference', 'e.g. journal or publication source'),
                ('db_reference_link', 'Reference Link', 'e.g doi or url')]
        for row, (name, text, placeholder) in enumerate(rows):
            label = QtW.QLabel(text, self)
            label.setObjectName(f'{name}_label')
            line_edit = fixed_height(QtW.QLineEdit(self))
            line_edit.setObjectName(f'{name}_lineEdit')
            line_edit.setPlaceholderText(placeholder)
            setattr(self, f'{name}_label', label)
            setattr(self, f'{name}_lineEdit', line_edit)
            grid.addWidget(label, row, 0)
            grid.addWidget(line_edit, row, 1)

        self.geocork_version_label = QtW.QLabel('GeoCORK version', self)
        self.geocork_version_label.setObjectName('geocork_version_label')
        self.geocork_version_text = QtW.QLabel('version', self)
        self.geocork_version_text.setObjectName('geocork_version_text')

        grid.addWidget(self.geocork_version_label, 6, 0)
        grid.addWidget(self.geocork_version_text, 6, 1)
        layout.addLayout(grid)

        layout.addItem(QtW.QSpacerItem(20, 40, QtW.QSizePolicy.Policy.Minimum, QtW.QSizePolicy.Policy.Expanding))

        self.label_3 = QtW.QLabel('Warning: Use the below functions carefully, create backups before any use', self)
        self.label_3.setObjectName('label_3')
        layout.addWidget(self.label_3)
        self.label_4 = QtW.QLabel('We recommend checking the logs folder and clearing every so often to avoid a '
                                  'buildup of logs', self)
        self.label_4.setObjectName('label_4')
        layout.addWidget(self.label_4)

        buttons = QtW.QHBoxLayout()
        self.openlogs_pushButton = QtW.QPushButton('Open Logs Folder', self)
        self.openlogs_pushButton.setObjectName('openlogs_pushButton')
        self.openbackup_pushButton = QtW.QPushButton('Open Backups Folder', self)
        self.openbackup_pushButton.setObjectName('openbackup_pushButton')
        buttons.addWidget(self.openlogs_pushButton)
        buttons.addWidget(self.openbackup_pushButton)
        layout.addLayout(buttons)

    def tab_order(self) -> list[QtW.QWidget]:
        return [self.db_name_lineEdit, self.db_description_lineEdit, self.db_created_by_lineEdit,
                self.db_authors_lineEdit, self.db_reference_lineEdit, self.db_reference_link_lineEdit,
                self.openlogs_pushButton, self.openbackup_pushButton]

    def connect_signals(self):
        self.openlogs_pushButton.clicked.connect(self.open_logs)
        self.openbackup_pushButton.clicked.connect(self.open_backups)

    def populate(self):
        self.about_db_model.setQuery('SELECT * FROM About WHERE AboutID = 1')
        while self.about_db_model.canFetchMore():
            self.about_db_model.fetchMore()
        self.db_name_lineEdit.setText(self.about_db_model.record(0).value('Name'))
        self.db_authors_lineEdit.setText(self.about_db_model.record(0).value('Authors'))
        self.db_description_lineEdit.setText(self.about_db_model.record(0).value('Description'))
        self.db_reference_link_lineEdit.setText(self.about_db_model.record(0).value('ReferenceLink'))
        self.db_created_by_lineEdit.setText(self.about_db_model.record(0).value('CreatedBy'))
        self.db_reference_lineEdit.setText(self.about_db_model.record(0).value('Citation'))
        self.geocork_version_text.setText(self.about_db_model.record(0).value('Version'))

    def save(self):
        about_values = [self.db_name_lineEdit.text(), self.db_authors_lineEdit.text(),
                        self.db_description_lineEdit.text(), self.db_reference_link_lineEdit.text(),
                        self.db_created_by_lineEdit.text(), self.db_reference_lineEdit.text()]
        query = QSqlQuery()
        about_qry = f"""UPDATE About SET (Name, Authors, Description, ReferenceLink, CreatedBy, Citation) =
            ({', '.join('?'*len(about_values))}) WHERE AboutID = 1"""
        query.prepare(about_qry)
        for value in about_values:
            query.addBindValue(value)
        if not query.exec():
            logger_setup.get_logger().critical(f'Error updating About table')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')

    def open_logs(self):
        """
        Opens the logs directory in the file explorer.
        """
        dirname = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation) + f"/logs/"
        QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(dirname))

    def open_backups(self):
        """
        Opens the backups directory in the file explorer.
        """
        dirname = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation) + f"/backups/"
        QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(dirname))

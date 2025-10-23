from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS

from Functions.Widget_classes import get_name_from_id, get_headers, get_name_column, get_id_from_name, loading_manager
from Functions import SQLUtils
import logger_setup
from Functions.LoadingDialog_manager import LoadingDialogManager
from Functions.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint

class MergeDialog(QtW.QDialog):
    def __init__(self, table, merge_ids, parent=None):
        super(MergeDialog, self).__init__(parent)
        self.loading_manager = LoadingDialogManager.get_instance()

        self.table = table
        self.merge_ids = merge_ids
        self.setWindowTitle(f"Merge {table}")

        self.name_to_keep = None
        self.id_to_keep = None
        self.change_dictionary = {}
        self.overwrite_ids = []
        self.id_header = get_headers(self.table)[0]
        self.merge_text = ""

        name_column = get_name_column(self.table)
        name_header = get_headers(self.table)[name_column]
        keep_combo_label = QtW.QLabel(f"Select {name_header} to keep:")
        self.keep_combo = QtW.QComboBox()
        for record_id in merge_ids:
            record_name = get_name_from_id(table, record_id)
            if record_name:
                self.keep_combo.addItem(record_name)
        self.keep_combo.setCurrentIndex(-1)
        self.keep_combo.currentIndexChanged.connect(self.prepare_merge)

        vertical_layout = QtW.QVBoxLayout()
        vertical_layout.addWidget(keep_combo_label)
        vertical_layout.addWidget(self.keep_combo)
        merge_button = QtW.QPushButton("Merge")
        button_box = QtW.QDialogButtonBox()
        button_box.addButton(merge_button, QtW.QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(QtW.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.merge_records)
        button_box.rejected.connect(self.reject)
        vertical_layout.addWidget(button_box)
        self.merge_label = QtW.QLabel()
        vertical_layout.addWidget(self.merge_label)
        self.setLayout(vertical_layout)

    def prepare_merge(self):
        """
        Prepares the merge operation based on the selected record to keep.
        :return:
        """
        self.name_to_keep = self.keep_combo.currentText()
        self.id_to_keep = get_id_from_name(self.table, self.name_to_keep)
        self.overwrite_ids = [id for id in self.merge_ids if id != self.id_to_keep]
        self.change_dictionary = {}
        query = QtS.QSqlQuery()
        foreign_key_tables = SQLUtils.foreign_key_tables
        self.loading_manager.show_loading_dialog(f'Preparing', f'Preparing merge for {self.table}...')

        for fk_table in foreign_key_tables:
            # Standard foreign key table
            # Get the Create table statement to find the foreign key column
            logger_setup.get_logger().info(f"Preparing {fk_table}")
            id_header = get_headers(self.table)[0]
            pragma_query = f"PRAGMA foreign_key_list({fk_table})"
            if not query.exec(pragma_query):
                logger_setup.get_logger().critical(f"Error merging {self.table}")
                logger_setup.get_logger().debug(f"Error executing PRAGMA query on {fk_table}")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {pragma_query}")
                self.loading_manager.close_loading_dialog(f'Preparing', f'Preparing merge for {self.table}...')
                self.reject()
            while query.next():
                if query.value(2) == self.table:
                    fk_column = query.value(3)
                    if not fk_table in self.change_dictionary:
                        self.change_dictionary[fk_table] = {}
                    if not fk_column in self.change_dictionary[fk_table]:
                        self.change_dictionary[fk_table][fk_column] = []
            self.loading_manager.close_loading_dialog(f'Preparing', f'Preparing merge for {self.table}...')

        for fk_table in self.change_dictionary:
            logger_setup.get_logger().info(f"Getting IDs for {fk_table}")
            self.loading_manager.show_loading_dialog(f'Preparing', f'Getting IDs for {fk_table}...')
            id_header = get_headers(fk_table)[0]
            for fk_column in self.change_dictionary[fk_table]:
                for overwrite_id in self.overwrite_ids:
                    overwrite_query = f'SELECT {id_header} FROM "{fk_table}" WHERE {fk_column} = {overwrite_id}'
                    if not query.exec(overwrite_query):
                        logger_setup.get_logger().critical(f"Error merging {self.table}")
                        logger_setup.get_logger().debug(f"Error finding values that need to be changed in {fk_table}")
                        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                        logger_setup.get_logger().debug(f"SQL query: {overwrite_query}")
                        self.loading_manager.close_loading_dialog(f'Preparing', f'Getting IDs for {fk_table}...')
                        self.reject()
                    while query.next():
                        record_id = query.value(0)
                        self.change_dictionary[fk_table][fk_column].append(record_id)
            self.loading_manager.close_loading_dialog(f'Preparing', f'Getting IDs for {fk_table}...')

        self.merge_text = f"The following changes will be made when merging {self.table} records into '{self.name_to_keep}':\n\n"
        for fk_table in self.change_dictionary:
            for fk_column in self.change_dictionary[fk_table]:
                record_ids = self.change_dictionary[fk_table][fk_column]
                if record_ids:
                    self.merge_text += f"{fk_table}: {len(record_ids)} {fk_column}\n"

        self.merge_label.setText(self.merge_text)

    def merge_records(self):
        """
        Executes the merge operation.
        :return:
        """
        query = QtS.QSqlQuery()
        logger_setup.get_logger().info(f"Merging {len(self.merge_ids)} {self.table}...")
        create_savepoint(f"before_merge")
        self.loading_manager.show_loading_dialog('Merging', f'Merging {len(self.merge_ids)} {self.table}...')

        # First, handle the children records that need to be updated
        if self.table in SQLUtils.user_viewable_trees:
            existing_children = []
            find_children_query = f'SELECT {self.id_header} FROM "{self.table}" WHERE {get_headers(self.table)[1]} = {self.id_to_keep}'
            if not query.exec(find_children_query):
                logger_setup.get_logger().critical(f"Error merging {self.table}")
                logger_setup.get_logger().debug(f"Error finding existing children during merge")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {find_children_query}")
                rollback_savepoint(f"before_merge")
                self.loading_manager.close_loading_dialog('Merging', f'Merging {len(self.merge_ids)} {self.table}...')
                self.reject()
            while query.next():
                existing_children.append(query.value(0))
            children_to_add = []
            for overwrite_id in self.overwrite_ids:
                find_children_query = f'SELECT {self.id_header} FROM "{self.table}" WHERE {get_headers(self.table)[1]} = {overwrite_id}'
                if not query.exec(find_children_query):
                    logger_setup.get_logger().critical(f"Error merging {self.table}")
                    logger_setup.get_logger().debug(f"Error finding children to add during merge")
                    logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                    logger_setup.get_logger().debug(f"SQL query: {find_children_query}")
                    rollback_savepoint(f"before_merge")
                    self.loading_manager.close_loading_dialog('Merging', f'Merging {len(self.merge_ids)} {self.table}...')
                    self.reject()
                while query.next():
                    child_id = query.value(0)
                    if child_id not in existing_children:
                        children_to_add.append(child_id)
            parent_row = len(existing_children)
            for child_id in children_to_add:
                add_child_query = (f'UPDATE "{self.table}" SET {get_headers(self.table)[1]} = {self.id_to_keep}, '
                                   f'{get_headers(self.table)[2]} = {parent_row} WHERE {self.id_header} = {child_id}')
                if not query.exec(add_child_query):
                    logger_setup.get_logger().critical(f"Error merging {self.table}")
                    logger_setup.get_logger().debug(f"Error adding child during merge")
                    logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                    logger_setup.get_logger().debug(f"SQL query: {add_child_query}")
                    rollback_savepoint(f"before_merge")
                    self.loading_manager.close_loading_dialog('Merging', f'Merging {len(self.merge_ids)} {self.table}...')
                    self.reject()
                parent_row += 1

        for fk_table in self.change_dictionary:
            for fk_column in self.change_dictionary[fk_table]:
                record_ids = self.change_dictionary[fk_table][fk_column]
                for record_id in record_ids:
                    update_query = f'UPDATE "{fk_table}" SET {fk_column} = {self.id_to_keep} WHERE {get_headers(fk_table)[0]} = {record_id}'
                    if not query.exec(update_query):
                        if "UNIQUE constraint failed" not in query.lastError().text():
                            logger_setup.get_logger().critical(f"Error merging {self.table}")
                            logger_setup.get_logger().debug(f"Error updating {fk_table} during merge")
                            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                            logger_setup.get_logger().debug(f"SQL query: {update_query}")
                            rollback_savepoint(f"before_merge")
                            self.loading_manager.close_loading_dialog('Merging', f'Merging {len(self.merge_ids)} {self.table}...')
                            self.reject()

        # Finally, delete the overwritten records
        for overwrite_id in self.overwrite_ids:
            delete_query = f'DELETE FROM "{self.table}" WHERE {self.id_header} = {overwrite_id}'
            if not query.exec(delete_query):
                logger_setup.get_logger().critical(f"Error merging {self.table}")
                logger_setup.get_logger().debug(f"Error deleting record from {self.table} during merge")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {delete_query}")
                rollback_savepoint(f"before_merge")
                self.loading_manager.close_loading_dialog('Merging', f'Merging {len(self.merge_ids)} {self.table}...')
                self.reject()

        logger_setup.get_logger().info(f"Finished merging {self.table}")
        self.loading_manager.close_loading_dialog('Merging', f'Merging {len(self.merge_ids)} {self.table}...')
        release_savepoint(f"before_merge")
        QtW.QMessageBox.information(self, "Success", f"Successfully merged {len(self.merge_ids)} {self.table}.")
        self.accept()



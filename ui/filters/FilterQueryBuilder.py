import ast
import re
import sqlite3
import time

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt, QEventLoop
from PyQt6.QtGui import QAction
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtWidgets import QVBoxLayout, QScrollArea, QSizePolicy, QWidget, QListWidgetItem, QMessageBox, QLabel

from Functions import SQLUtils
import logger_setup
from DataViewerWidget import DataViewerWidget
from Functions.Widget_classes import show_loading_dialog, close_loading_dialog
from ui.filters.FilterHelpers import process_group
from ui.filters.FilterGroupBox import FilterGroupBox


class FilterQueryBuilder(QWidget):
    """
    Main Query Builder widget that allows the user to filter and display data. The query builder allows nested
    FilterGroupBoxes to allow full customization. A single root FilterGroupBox is created on initialization and build beneath.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.layout1 = QVBoxLayout(self)
        self.setLayout(self.layout1)

        self.scrollarea = QScrollArea(self)
        self.scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        # the root level FilterGroupBox that all filters are within
        self.main_group_box = FilterGroupBox()
        self.main_group_box.setParent(self)
        self.layout1.addWidget(self.scrollarea)
        self.scrollarea.setWidget(self.main_group_box)

        self.layout1.addWidget(QLabel('Note: Select which view based on desired filtered subset'))


    def populate_filters(self, item: QListWidgetItem) -> None:
        """
        Populates the QueryBuilder based on a given filter name.
        :param item: QListWidgetItem containing the name of the filter to populate from
        """
        # query for the SQLQuery and name for a given name
        filter_name = item.text()
        show_loading_dialog('Loading', f'Populating from {filter_name}...')
        query = QSqlQuery()
        sql_query = """
                SELECT SQLQuery, FilterGroupName 
                FROM FilterGroups 
                WHERE FilterGroupName = :filter_name COLLATE NOCASE;
            """
        query.prepare(sql_query)
        query.bindValue(":filter_name", filter_name)
        logger_setup.get_logger().info(f'Populating QueryBuilder from stored filter: {filter_name}')

        if query.exec():
            if query.next():
                sql_query_result = query.value(0)

                # Rebuild UI, delete old FilterGroupBox
                self.main_group_box.deleteLater()
                # give the FilterGroupBox a sql query to build from
                self.main_group_box = FilterGroupBox(ast.literal_eval(sql_query_result[1:-1]))
                self.main_group_box.setParent(self)
                self.layout1.insertWidget(0, self.scrollarea)
                self.scrollarea.setWidget(self.main_group_box)
                self.show()
            else:
                logger_setup.get_logger().error(
                    f'No matching filter group for: {filter_name}')
        else:
            logger_setup.get_logger().critical(
                f'Error in populating existing Filters')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL command: {sql_query}')
            logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
        close_loading_dialog('Loading', f'Populating from {filter_name}...')



    def view_many_results(self, number: int) -> bool:
        """
        Prompts the user if they want to view many results. If they do, it returns True, otherwise False.
        :param number: number of filtered ids
        :return: bool
        """
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle('Many results')
        msg.setText(f'Would you like to view {number} results? This may take a while to load.')
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        reply = msg.exec()
        if reply == QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

    def get_filtered_ids(self, type) -> list | None:
        """
        Queries the database with the generated filter sql query at the given type scope
        :param str type: Samples, Aliquots, Spots, or UPbAnalyses to query the database for
        :return: list of ids of given type or None
        """
        filter_start = time.time()
        show_loading_dialog('Filtering', f'Filtering {type} based on current criteria...\n\nThis may take minutes for complex filters or large databases.')
        sql_query = self.get_sql(type)
        database = logger_setup.settings.value('db_file', type=str)
        uri = f'file:{database}?mode=ro&immutable=1'
        try:
            conn = sqlite3.connect(uri, uri=True)
            with conn:
                cursor = conn.cursor()
                cursor.execute(sql_query)
                data = cursor.fetchall()
                results = [row[0] for row in data]
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger_setup.get_logger().critical("Error filtering data")
            logger_setup.get_logger().debug(f"Failed to get filtered ids")
            logger_setup.get_logger().debug(f"Error: {e}")
            logger_setup.get_logger().debug(f"SQL query: {sql_query}")
            close_loading_dialog('Filtering', f'Filtering {type} based on current criteria...\n\nThis may take minutes for complex filters or large databases.')
            return None
        logger_setup.get_logger().debug(f'Filtered ids: {results}')
        logger_setup.get_logger().info('Gathered filtered ids successfully in {:.2f} seconds'.format(time.time() - filter_start))
        close_loading_dialog('Filtering', f'Filtering {type} based on current criteria...\n\nThis may take minutes for complex filters or large databases.')
        return results if results else None

    def get_sql(self, type: str) -> str:
        """
        Generates a full SQL query based on the given main group box structuree of RuleWidgets and FilterGroupBoxes
        :param type: Samples, Aliquots, Grains, Spots, or UPbAnalyses to query the database for
        :return: final SQL query
        :rtype str
        """
        # json dict containing the nested filters
        structure = self.main_group_box.get_structure()
        # converts json to sql
        where_clause, cte_list = process_group(structure)
        full_sql = ""

        # code to allow for tree like tables to work as expected. If a parent item is being filtered, then child
        # items should be included.
        if cte_list:
            full_sql += "WITH " + ",\n".join(cte_list) + "\n"

        # gathers the join statements with found tables
        join = SQLUtils.get_join_from_table("", self.main_group_box.get_tables())
        logger_setup.get_logger().debug(f'SQL Join: {join}')
        selects = self.main_group_box.get_selects()
        logger_setup.get_logger().debug(f'SQL Selects: {selects}')

        def extract_as_tables(join):
            as_tables = None
            select_tables = None
            where_tables = None
            if ' AS ' in join:
                pattern = r'\s+\bAS\s+(\w+)'  # regex pattern to match ' AS ' and return the table name right after it
                as_tables = re.findall(pattern, join)
            if '.[' in selects:
                pattern = r'\b(\w+)\.\['  # regex pattern to match the table name before '.['
                select_tables = re.findall(pattern, selects)
            if '.[' in where_clause:
                pattern = r'\b(\w+)\.\['  # regex pattern to match the table name before '.['
                where_tables = re.findall(pattern, where_clause)
            return as_tables, select_tables, where_tables

        as_tables, select_tables, where_tables = extract_as_tables(join)
        if as_tables is not None:
            for as_table in as_tables:
                replace_table = SQLUtils.as_table_dict[as_table]
                if select_tables and replace_table in select_tables:
                    selects = selects.replace(replace_table, as_table)
                if where_tables and replace_table in where_tables:
                    where_clause = where_clause.replace(replace_table, as_table)

        # final code to determine the scope of query based on type, also ensures the selected type's table is found
        # in the join code
        where = where_clause.replace('Items', 'Samples').replace('ItemID', 'SampleID')
        # If the where clause is not empty and does not start with 'GROUP BY', then add a WHERE clause
        if not where.startswith('WHERE') and not where.startswith('GROUP BY') and where.strip():
            where = 'WHERE ' + where


        if type == 'Samples':
            # where = where_clause.replace('Items', 'Samples').replace('ItemID', 'SampleID')
            sql_query = full_sql + f"""
            SELECT DISTINCT Samples.SampleID
            FROM Samples
            {join}
            {where}
            """

        elif type == 'Aliquots':
            # where = where_clause.replace('Items', 'Aliquots').replace('ItemID', 'AliquotID')
            # Generate join string
            join = SQLUtils.get_join_from_table(join, ['Aliquots'])

            # Recursive CTE: start from records matching `where_clause`, then gather parents
            cte = f"""
            WITH RECURSIVE Aliquots_cte AS (
                SELECT Aliquots.AliquotID, Aliquots.ParentAliquotID
                FROM Samples
                {join}
                {where}

                UNION ALL

                SELECT a.AliquotID, a.ParentAliquotID
                FROM Aliquots a
                INNER JOIN Aliquots_cte r ON a.AliquotID = r.ParentAliquotID
            )
            """

            aliquot_select = f"""
            SELECT DISTINCT AliquotID FROM (
                SELECT Aliquots.AliquotID
                FROM Samples
                {join}
                WHERE Aliquots.AliquotID IN (SELECT AliquotID FROM Aliquots_cte)
            )
            WHERE AliquotID IS NOT NULL;
            """

            # Main query using the CTE
            if cte_list:
                if 'WITH RECURSIVE' in full_sql:
                    sql_query = cte + ',\n' + full_sql.split('WITH RECURSIVE')[1] + aliquot_select
                else:
                    sql_query = cte + ',\n' + full_sql.split('WITH ')[1] + aliquot_select
            else:
                sql_query = cte + aliquot_select

        elif type == 'Grains':
            join = SQLUtils.get_join_from_table(join, ['Spots'])
            sql_query = full_sql + f"""
            SELECT DISTINCT GrainID FROM (
            SELECT Spots.GrainID
            FROM Samples {join}
            {where})
            WHERE GrainID IS NOT NULL;"""

        elif type == 'Spots':
            # where = where_clause.replace('Items', 'Spots').replace('ItemID', 'SpotID')
            join = SQLUtils.get_join_from_table(join, ['Spots'])
            sql_query = full_sql + f"""SELECT DISTINCT SpotID FROM (
                SELECT Spots.SpotID
                FROM Samples {join}
                {where})
                WHERE SpotID IS NOT NULL;"""

        elif type == 'UPbAnalyses':
            # where = where_clause.replace('Items', 'UPbAnalyses').replace('ItemID', 'UPbAnalysisID')
            join = SQLUtils.get_join_from_table(join, ['UPbAnalyses'])
            sql_query = full_sql + f"""SELECT DISTINCT UPbAnalysisID FROM (
                SELECT UPbAnalyses.UPbAnalysisID
                FROM Samples {join}
                {where})
                WHERE UPbAnalysisID IS NOT NULL;"""

        else:
            logger_setup.get_logger().critical(f'Unknown Type Given: {type}')
            return None

        logger_setup.get_logger().debug(f'Filtered SQL command: {sql_query}')

        return sql_query



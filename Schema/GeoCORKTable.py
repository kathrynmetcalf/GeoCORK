from enum import Enum
from typing import Self

from PyQt6 import QtSql
from PyQt6.QtSql import QSqlQuery

import logger_setup


class TableType(Enum):
    """
    Enum representing different types of table structures within GeoCORK.

    :var TABLE: Represents a standard table structure. Must follow the format of
        TableID, TableName, any[...], TableCreated (auto appended), TableModified (auto appended).
    :var TREE: Represents a tree structure where data is hierarchical. Must follow the format of
        TreeID, TreeParentID, TreeParentRow, TreeName, any[...], TreeCreated (auto appended), TreeModified (auto appended).
    :var VIEW: Represents a view, primarily used for abstraction or
        computed data.
    :var MANYTOMANY: Represents a many-to-many relationship between two tables.
    :var INTERNAL: Represents an internal table or structure. Requires
        InternalID, any[...], InternalCreated (auto appended), InternalModified (auto appended).
    :var CONVERSION: Represents a conversion table for mapping or
        transforming data. Does not require any specific order of attributes.
    :var UNITS: Represents a table that manages or defines measurement units. Does not require any specific order of attributes.
    :var FORMATS: Represents a table for various data formats or configurations. Does not require any specific order of attributes.

    """
    TABLE = 0
    TREE = 1
    VIEW = 2
    MANYTOMANY = 3
    INTERNAL = 4
    CONVERSION = 5
    UNITS = 6
    FORMATS = 7


class GeoCORKTableAttribute:
    """

    """

    def __init__(self, attribute_name: str = None, data_type: str = None,
                 primary_key=False, not_null=False, not_empty=False, as_case: str = '',
                 visible_to_user: bool = True, foreign_key_table: str = None):
        """

        :param attribute_name:
        :param data_type:
        :param primary_key:
        :param unique:
        :param not_null:
        :param not_empty:
        :param as_case:
        :param visible_to_user:
        :param foreign_key_table: Assumes and references to the PK of the foreign table.
        """
        self.attribute_name = attribute_name
        self.data_type = data_type
        self.primary_key = primary_key
        self.not_null = not_null
        self.not_empty = not_empty
        self.foreign_key_table = foreign_key_table
        self.visible_to_user = visible_to_user

        # any primary key will not be visible to the user
        if primary_key:
            self.visible_to_user = False

        if self.data_type == 'AS':
            self.as_case = 'NULL'

    def __str__(self):
        return (f'"{self.attribute_name}" '
                f"{self.data_type} "
                f"{'PRIMARY KEY ' if self.primary_key else ''}"
                f"{'NOT NULL ' if self.not_null else ''}"
                f"{'CHECK (' + self.attribute_name + " <> '') " if self.not_empty else ''}"
                f"{'REFERENCES ' + self.foreign_key_table + ' ON DELETE SET NULL' if self.foreign_key_table else ''}"
                f"{'DEFAULT CURRENT_TIMESTAMP' if self.data_type == 'DATETIME' else ''}"
                f"{'(' + self.as_case + ') STORED' if self.data_type == 'AS' else ''}".strip())


class GeoCORKTable:
    """

    """

    def __init__(self, table_name: str = '', attributes: list[GeoCORKTableAttribute] = [],
                 table_type: TableType = TableType.TABLE,
                 user_viewable: bool = False, conditionally_editable: bool = False,
                 static_table: bool = False, contains_foreign_keys: bool = False, as_table_name: list[str] = None,
                 bridge_table: Self = None, bridge_from_column: str = None, bridge_to_column: str = None,
                 child_tables: list[Self] = None, parent_tables: list[Self] = None,
                 unique_constraints: list[list[str]] = None):
        """
        Represents a GeoCORK table definition with attributes, relationships, and metadata for
        database operations. This class manages attributes, child-parent relationships, unique keys,
        and type-specific constraints for database tables while ensuring integrity standards such
        as primary keys, foreign keys, and hierarchical structures.

        If a table is an M:N relationship, it must have exactly two attributes. Automatically creates unique constraint for
        the two attributes.

        :param table_name: The name of the database table.
        :type table_name: str
        :param attributes: A list of attributes (columns) for the table.
        :type attributes: list[GeoCORKTableAttribute]
        :param table_type: The type of table (e.g., TABLE, TREE). Defaults to TableType.TABLE.
        :type table_type: TableType, optional
        :param user_viewable: Whether the table is viewable by the user. Defaults to False.
        :type user_viewable: bool, optional
        :param conditionally_editable: Whether the table is conditionally editable. Defaults to False.
        :type conditionally_editable: bool, optional
        :param static_table: Whether the table is static (non-editable). Defaults to False.
        :type static_table: bool, optional
        :param contains_foreign_keys: Whether the table contains foreign key references. Defaults to False.
        :type contains_foreign_keys: bool, optional
        :param as_table_name: A list of aliases for the table name. Defaults to None.
        :type as_table_name: list[str], optional
        :param bridge_table: The bridge table associating two tables (if applicable). Defaults to None.
        :type bridge_table: GeoCORKTable, optional
        :param bridge_from_column: The source column in the bridge table. Defaults to None.
        :type bridge_from_column: str, optional
        :param bridge_to_column: The destination column in the bridge table. Defaults to None.
        :type bridge_to_column: str, optional
        :param child_tables: A list of child tables referencing this table. Defaults to None.
        :type child_tables: list[GeoCORKTable], optional
        :param parent_tables: A list of parent tables that this table references. Defaults to None.
        :type parent_tables: list[GeoCORKTable], optional
        :param unique_constraints: A list of unique constraints defined for the table. Defaults to None.
        :type unique_constraints: list[str], optional

        :raises CriticalError: If attributes are not provided or critical integrity standards
            (e.g., primary key) are not met for the table structure.
        """

        self._table_name = table_name
        self.cte_table_name = f'Recursive{self.table_name}'
        self.table_type: TableType = table_type
        self.user_viewable = user_viewable
        self.conditionally_editable = conditionally_editable
        self.static_table = static_table
        self.contains_foreign_keys = contains_foreign_keys
        self.as_table_name = as_table_name
        self.unique_constraints = unique_constraints if unique_constraints is not None else []

        self.limited_table_name = f'Limited{self.table_name}'

        self.bridge_table = bridge_table
        self.bridge_from_column = bridge_from_column
        self.bridge_to_column = bridge_to_column

        self.child_tables: list[GeoCORKTable] = child_tables
        self.parent_tables: list[GeoCORKTable] = parent_tables

        self.attributes: list[GeoCORKTableAttribute] = attributes

        self.id_column = ''
        self.id_column_index = -1

        self.name_column = ''
        self.name_column_index = -1

        self.parent_column = ''
        self.parent_column_index = -1

        self.parent_row_column = ''
        self.parent_row_column_index = -1


        if len(self.attributes) == 0:
            # logger_setup.get_logger().critical('No attributes given for table.')
            return

        # checks to make sure an ID column exists
        if self.table_type == TableType.TABLE or self.table_type == TableType.INTERNAL:
            self.id_column: GeoCORKTableAttribute = None
            for i in range(0, len(self.attributes)):
                if self.attributes[i].primary_key and i == 0:
                    self.id_column = self.attributes[i]
                    self.id_column_index = i + 1
                elif self.attributes[i].attribute_name == self.id_column.attribute_name.replace('ID', 'Name'):
                    self.name_column: GeoCORKTableAttribute = self.attributes[i]
                    self.name_column_index = i + 1
            if self.id_column is None:
                # logger_setup.get_logger().critical("No primary key column for table")
                return False

        elif self.table_type == TableType.TREE:
            self.parent_column: GeoCORKTableAttribute = None
            for i in range(0, len(self.attributes)):
                if self.attributes[i].primary_key and i == 0:
                    self.id_column = self.attributes[i]
                    self.id_column_index = i + 1
                elif self.attributes[i].attribute_name == f'Parent{self.id_column.attribute_name}' and i == 1:
                    # set Parent id to not be visible to user
                    self.attributes[i].visible_to_user = False
                    self.parent_column = self.attributes[i]
                    self.parent_column_index = i + 1
                elif self.attributes[i].attribute_name == f'{self.id_column.attribute_name.replace('ID','')}ParentRow' and i == 2:
                    # set Parent row to not be visible to user
                    self.attributes[i].visible_to_user = False
                    self.parent_row_column = self.attributes[i]
                    self.parent_row_column_index = i + 1
                elif self.attributes[i].attribute_name == f'{self.id_column.attribute_name.replace('ID', '')}Name' and i == 3:
                    self.name_column = self.attributes[i]
                    self.name_column_index = i + 1
        elif self.table_type == TableType.MANYTOMANY:
            if len(self.attributes) != 2:
                logger_setup.get_logger().critical("Many-to-many tables must have exactly two attributes.")
                return

            self.unique_constraints.append([self.attributes[0].attribute_name, self.attributes[1].attribute_name])

            # if self.id_column is None:
            #     logger_setup.get_logger().critical("No primary key column for table")
            # if self.parent_column is None:
            #     logger_setup.get_logger().critical("No parent column for tree table or invalid name scheme")
            # if self.parent_row_column is None:
            #     logger_setup.get_logger().critical("No parent row column for tree table or invalid name scheme")

        # add Modified and Created Attributes
        if self.table_type == TableType.TABLE or self.table_type == TableType.TREE or self.table_type == TableType.INTERNAL:
            self.attributes.append(
                GeoCORKTableAttribute(f'{self.id_column.attribute_name.replace('ID', 'Created')}', 'DATETIME'))
            self.attributes.append(
                GeoCORKTableAttribute(f'{self.id_column.attribute_name.replace('ID', 'Modified')}', 'DATETIME'))




    @property
    def table_name(self):
        """
        Returns a non-SQL safe version of the table name. Will not protect against protected keywords
        :return:
        """
        return self._table_name

    @property
    def id_select(self):
        """
        Returns a SQL select-as statement for the id column of the table.
        :return:
        """
        return f"{self.table_name}.{self.id_column.attribute_name} AS {self.id_column.attribute_name}"

    @property
    def name_select(self):
        """
        Returns a SQL select-as statement for the name column of the table.
        :return:
        """
        return f"{self.table_name}.{self.name_column.attribute_name} AS {self.name_column.attribute_name}"

    def table_attributes_dict(self):
        """
        Returns a dictionary of the table's attributes in a dictionary format where the key is the table name and a
        list of values for attributes.
        :return:
        """
        return {self.table_name: [attribute.attribute_name for attribute in self.attributes]}

    @property
    def user_viewable_attributes(self) -> list[GeoCORKTableAttribute]:
        """
        Returns a list of GeoCORKAttribute objects that are visible to the user.
        :return:
        """
        attributes = []
        for attribute in self.attributes:
            if attribute.visible_to_user:
                attributes.append(attribute)
        return attributes

    def get_total_records(self, where: str = '') -> int:
        """
        Get the total number of records in a table. Optional where clause can be included.
        :param table: name of the table to query
        :param where: optional where clause to append to the count query
        :return: integer of the total number of records
        """
        query = QSqlQuery()
        sql_query = f'SELECT COUNT() FROM {self.__str__()} {where}'
        # if 'View' in table:
        #     table = get_table_from_view(table)
        #     if table in ['Samples', 'Aliquots', 'Spots', 'UPbAnalyses']:
        #         sql_query = f'SELECT COUNT() FROM (Select * FROM Samples {SQLUtils.get_join_from_table('', [table])}) {where}'

        # Execute the query
        logger_setup.get_logger().info(f'Fetching total records for {self.table_name}')
        if not query.exec(sql_query):
            # Handle query execution error
            logger_setup.get_logger().critical(f'Error fetching total records')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            return 0

        # Fetch the count
        if query.next():
            return query.value(0)
        return 0

    def get_headers(self) -> list:
        """
        Return all headers for the given table
        :param table: Name of the SQL database table
        :return: list of headers if successful, empty list if not
        """
        query = QtSql.QSqlQuery()
        if not query.exec(f'PRAGMA table_xinfo({self.__str__()})'):
            logger_setup.get_logger().critical(f"Failed to get headers for {self.table_name}")
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            return []
        headers = []
        while query.next():
            headers.append(query.value(1))
        return headers

    def create_query(self) -> str | None:
        """
        Returns a generated SQL query to create the table.
        :return:
        """
        return (f"CREATE TABLE IF NOT EXISTS {self.__str__()} (\n\t"
                f"{',\n\t'.join(str(attr) for attr in self.attributes)}"
                f"{(', \n\t' + ',\n\t'.join(str('UNIQUE (' + ", ".join(unique) + ')') for unique in self.unique_constraints)) if self.unique_constraints else ''}"
                f"\n)")

        # limited_sample_hierarchy_join = f'''
        #                         JOIN LimitedAliquots la ON ls.SampleID = la.SampleID
        #                         JOIN LimitedSpots lsp ON la.AliquotID = lsp.AliquotID
        #                         JOIN LimitedUPbAnalyses lu ON lsp.SpotID = lu.SpotID
        #                         '''
        #
        # many_editable = {
        #     'Samples': {'SampleAgeSignatureName': 'AgeSignatures', 'RegionName': 'Regions', 'RockTypeName': 'RockTypes',
        #                 'SampleContexName': 'SampleContexts', 'SamplingMethodName': 'SamplingMethods',
        #                 'SettingName': 'Settings',
        #                 'UnitName': 'Units'},
        #     'Aliquots': {'AliquotContextName': 'AliquotContexts'},
        #     'Spots': {'SpotCompositionName': 'SpotCompositions', 'SpotContextName': 'SpotContexts'},
        #     'UPbAnalyses': {'RejectionReasonName': 'RejectionReasons', 'UPbAnalysisContextName': 'UPbAnalysisContexts'},
        #     'References': {}
        # }
        # # One-to-many columns for each table key, key-value pairs for column in the view and table to edit that information, populate single selection dropdowns
        # one_editable = {
        #     'Samples': {'SampleGPSLocationDisplay': 'GPSLocations', 'SampleAgeCalculated': 'SampleAges',
        #                 'ColumnName': 'Columns',
        #                 'ColumnHeightDepthUnitAbbreviation': 'DistanceUnits', 'AliquotName': 'Aliquots'},
        #     'Columns': {'ColumnTotalHeightDepthUnitAbbreviation': 'DistanceUnits',
        #                 'ColumnBaseGPSDisplay': 'GPSLocations'},
        #     'Aliquots': {'SampleName': 'Samples', 'SpotName': 'Spots'},
        #     'Spots': {'AliquotName': 'Aliquots', 'SpotCompositionName': 'SpotCompositions'},
        #     'UPbAnalyses': {'SpotName': 'Spots', 'AliquotName': 'Aliquots', 'SampleName': 'Samples',
        #                     'UPbReference': 'References',
        #                     'LabFacilityName': 'LabFacilities', 'InstrumentName': 'Instruments',
        #                     'UPbAnalysisMethodName': 'UPbAnalysisMethods',
        #                     'RatioErrorFormatAbbreviation': 'ErrorFormats', 'AgeUnitAbbreviation': 'AgeUnits',
        #                     'AgeErrorFormatAbbreviation': 'ErrorFormats',
        #                     'ConcordanceFormatAbbreviation': 'ConcordanceFormats',
        #                     'SpotSizeUnitAbbreviation': 'DistanceUnits'},
        #     'References': {}
        # }

    def __str__(self):
        """
        Returns a SQL safe version(quoted) of the table_name. Protects against reserved keywords.
        :return:
        """
        return str('"' + self.table_name + '"')

    def __eq__(self, other):
        if isinstance(other, GeoCORKTable):
            return self.table_name.replace('"', '') == other.table_name.replace('"', '')
        return False

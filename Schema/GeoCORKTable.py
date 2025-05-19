from enum import Enum
from typing import Self

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
                 primary_key=False, unique=False, not_null=False, not_empty=False, as_case: str = '',
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
        self.unique = unique
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

    def __init__(self, table_name, attributes: list[GeoCORKTableAttribute], table_type: TableType = TableType.TABLE,
                 user_viewable: bool = False, conditionally_editable: bool = False,
                 static_table: bool = False, contains_foreign_keys: bool = False, as_table_name: list[str] = None,
                 bridge_table: Self = None, bridge_from_column: str = None, bridge_to_column: str = None,
                 child_tables: list[Self] = None, parent_tables: list[Self] = None, unique_constraints: list[list[str]] = None):
        """
        Represents a GeoCORK table definition with attributes, relationships, and metadata for
        database operations. This class manages attributes, child-parent relationships, unique keys,
        and type-specific constraints for database tables while ensuring integrity standards such
        as primary keys, foreign keys, and hierarchical structures.

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

        self.table_name = table_name
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

        if self.attributes is None:
            # logger_setup.get_logger().critical('No attributes given for table.')
            return False



        # checks to make sure an ID column exists
        if self.table_type == TableType.TABLE or self.table_type == TableType.INTERNAL:
            self.id_column: GeoCORKTableAttribute = None
            for i in range(0, len(self.attributes)):
                if self.attributes[i].primary_key and i == 0:
                    self.id_column = self.attributes[i]
                elif self.attributes[i].attribute_name == self.attributes[0].attribute_name.replace('ID', 'Name'):
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
                elif self.attributes[i].attribute_name == f'Parent{self.attributes[i].attribute_name}' and i == 1:
                    # set Parent id to not be visible to user
                    self.attributes[i].visible_to_user = False
                    self.parent_column = self.attributes[i]
                elif self.attributes[i].attribute_name == f'{self.attributes[0].attribute_name}ParentRow' and i == 2:
                    # set Parent row to not be visible to user
                    self.attributes[i].visible_to_user = False
                    self.parent_row_column = self.attributes[i]
                elif self.attributes[i].attribute_name == f'{self.attributes[0].attribute_name}Name' and i == 3:
                    self.name_column = self.attributes[i]
                    self.name_column_index = i + 1
                else:
                    pass

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

        self.indexes = {
            'idx_name': ['name'],
            'idx_latitude_longitude': ['latitude', 'longitude']
        }

    @property
    def id_select(self):
        return f"{self.table_name}.{self.id_column.attribute_name} AS {self.id_column.attribute_name}"

    @property
    def name_select(self):
        return f"{self.table_name}.{self.name_column.attribute_name} AS {self.name_column.attribute_name}"

    def table_attributes_dict(self):
        """
        Returns a dictionary of the table's attributes in a dictionary format where the key is the table name and a
        list of values for attributes.
        :return:
        """
        return {self.table_name: [attribute.attribute_name for attribute in self.attributes]}

    @property
    def user_viewable_attributes(self) -> list[GeoCORKTableAttribute] :
        """

        :return:
        """
        attributes = []
        for attribute in self.attributes:
            if attribute.visible_to_user:
                attributes.append(attribute)
        return attributes

    def create_query(self) -> str | None:
        """
        Returns a generate SQL query to create the table.
        :return:
        """
        return (f"CREATE TABLE IF NOT EXISTS {self.table_name} (\n\t"
                f"{',\n\t'.join(str(attr) for attr in self.attributes)}"
                f"{',\n'.join(str(",".join(unique)) for unique in self.unique_constraints)}"
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
        return str(self.table_name)

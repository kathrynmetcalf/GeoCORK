class VerifiableSqlTableModel(DisplayRoundedModel):
    """
    Custom DisplayRoundedModel (subclass of QSqlTableModel) to verify data before submitting changes to the database
    upon row change.
    """
    row_submitted = QtC.pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.edited_indexes = []
        self.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnRowChange)
        self.submitError = ''
        self.headerToFix = ''

    def setData(self, index, value, role = ...):
        """Minor screening to prevent adding decimals to integers and set empty values to None. Keeps track of edited
        indexes."""
        field_type = self.record().field(index.column()).typeID()
        logger_setup.get_logger().info(f"Setting {field_type} to {value}")
        if role == QtC.Qt.ItemDataRole.EditRole:
            if value == '' and field_type in (QMetaType.Type.Double.value, QMetaType.Type.Float.value, QMetaType.Type.Float16.value, QMetaType.Type.Int.value, QMetaType.Type.UInt.value):
                # Set the value to NULL
                value = None
            elif '.' not in str(value):
                # Make sure integers don't have decimals added on
                try:
                    value = int(value)
                except ValueError:
                    pass
            self.edited_indexes.append(index)
            # return super().setData(index, value, role)
        return super().setData(index, value, role)

    def submit(self):
        """Validate data as necessary before submitting"""
        if not self.edited_indexes:
            # no changes to submit
            return True
        # get the edited row
        edited_row = self.edited_indexes[0].row()
        if self.tableName() in SQLUtils.trigger_tables:
            if not self.verify_row(edited_row):
                return False
        if super().submit():
            self.row_submitted.emit(edited_row)
            self.edited_indexes = []
            self.submitError = ''
            self.headerToFix = ''
            return True
        else:
            if self.submitError:
                logger_setup.get_logger().error(self.submitError)
            return False

    def verify_row(self, edited_row: int) -> bool:
        """
        Make sure ID columns contain IDs, collect columns and values to submit, and validates data to update
        :param edited_row: edited row being submitted
        :return: True if no error, False if there is
        """
        columns = []
        values = []
        id_header = self.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        id = self.data(self.index(edited_row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        for column in range(1, self.columnCount()):
            header = self.headerData(column, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            value = self.data(self.index(edited_row, column), QtC.Qt.ItemDataRole.DisplayRole)
            if 'ID' in header and type(value) is not int:
                # name is given instead of ID
                set_value, foreign_table = get_foreign_id_table(self.tableName(), header, value)
            else:
                set_value = value
            columns.append(header)
            values.append(set_value)
        where = f'{id_header}={id}'
        error, header = validate_update(self.tableName(), columns, values, where)
        if error is not None:
            self.submitError = error
            self.headerToFix = header
            return False
        return True

class VerifiableSqlViewModel(VerifiableSqlTableModel):
    """
    Custom DisplayRoundedQueryModel (subclass of QSqlTableModel) to verify data before submitting changes to the database
    upon row change.
    """
    row_submitted = QtC.pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.table = ''
        self.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnManualSubmit)

    def setTable(self, tableName):
        if 'View' in tableName:
            if 'Sample' in tableName:
                self.table = 'Samples'
            elif 'Aliquot' in tableName:
                self.table = 'Aliquots'
            elif 'Spot' in tableName:
                self.table = 'Spots'
            elif 'UPbAnalysis' in tableName:
                self.table = 'UPbAnalyses'
            elif 'Column' in tableName:
                self.table = 'Columns'
            elif 'Reference' in tableName:
                self.table = 'References'
            super().setTable(self.table)
        else:
            logger_setup.get_logger().error(f'Table {tableName} is not a view')

    def submit(self):
        if not self.isDirty():
            return True
        # get the edited row
        current_row = self.edited_indexes[0].row()
        columns = []
        values = []
        id_header = self.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        id = self.data(self.index(current_row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        foreign_table = QtS.QSqlTableModel()
        # Need to map the joined columns to the actual table columns
        for column in range(1, self.columnCount()):
            header = self.headerData(column, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            value = self.unrounded_data(self.index(current_row, column), QtC.Qt.ItemDataRole.DisplayRole)
            # if header == 'Total Height/Depth':
            #     set_header = 'ColumnTotalHeightDepth'
            #     set_value = value
            if 'Unit' in header:
                set_header = 'ColumnTotalHeightDepthUnitID'
                set_table(foreign_table, 'DistanceUnits')
                foreign_table.setFilter(f'DistanceUnitAbbreviation="{value}"')
                set_value = foreign_table.record(0).value('DistanceUnitID')
            elif 'GPS' in header:
                set_header = 'ColumnBaseGPSID'
                query = QtS.QSqlQuery()
                if not query.exec(f'SELECT GPSLocationID FROM GPSLocations WHERE GPSLocationDisplay="{value}"'):
                    logger_setup.get_logger().critical(f'Failed to get GPSLocationID for {value}')
                    logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                    logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                    return False
                query.next()
                set_value = query.value(0)
                # set_value = foreign_table.record(0).value('GPSLocationID')
            else:
                set_header = header
                set_value = value
            columns.append(set_header)
            values.append(set_value)

        error, header = validate_update(self.table, columns, values, f'{id_header}={id}')
        if error is not None:
            self.submitError = error
            self.headerToFix = header
            return False
        column_str = ", ".join(columns)
        # create a string of question marks separated by commas for the values
        value_str = ", ".join('?' * len(values))
        query = QtS.QSqlQuery()
        query.prepare(f'UPDATE {self.table} SET ({column_str}) = ({value_str}) WHERE {id_header}={id}')
        for i, value in enumerate(values):
            query.bindValue(i, value)
        if not query.exec():
            logger_setup.get_logger().critical(f'Failed to update {self.table} with {column_str}={value_str}')
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            logger_setup.get_logger().debug(f"Bound values: {query.boundValues()}")
            return False
        self.row_submitted.emit(current_row)
        if not self.on_row_submitted(current_row):
            return False
        self.edited_indexes = []
        self.submitError = ''
        self.headerToFix = ''
        return True

    def on_row_submitted(self, row):
        record_id = self.data(self.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        error = update_modified_timestamp(self.table, [record_id])
        if error is not None:
            logger_setup.get_logger().error(error)
            return False

    def deleteRowFromTable(self, row):
        id_header = self.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        id = self.data(self.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        query = QtS.QSqlQuery()
        if not query.exec(f'DELETE FROM {self.table} WHERE {id_header}={id}'):
            logger_setup.get_logger().critical(f'Failed to delete {id} from {self.table}')
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            return False
        return True

def get_foreign_id_table(table: str, header: str, value, uncommitted=False):
    if 'ID' not in header:
        logger_setup.get_logger().error(f"Header {header} does not contain ID")
        return value, None
    if uncommitted:
        foreign_keys = foreign_key_columns(table, True)
        if header in foreign_keys.keys():
            foreign_table = foreign_keys[header]['table']
            id_column = foreign_keys[header]['id_column']
            display_column = foreign_keys[header]['display_column']
            query = QtS.QSqlQuery()
            if not query.exec(f'SELECT {id_column} FROM {foreign_table} WHERE {display_column}="{value}"'):
                logger_setup.get_logger().critical(f"Failed to get ID for {value} in {foreign_table}")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                return value, foreign_table
            query.next()
            return query.value(0), foreign_table
    else:
        foreign_keys = foreign_key_columns(table)
        if header in foreign_keys.keys():
            foreign_table = foreign_keys[header]['table']
            id_column = foreign_keys[header]['id_column']
            display_column = foreign_keys[header]['display_column']
            sql_query = f'SELECT {id_column} FROM {foreign_table} WHERE {display_column}="{value}"'
            model = SQLiteTableModel(sql_query)
            if model.last_error:
                logger_setup.get_logger().critical(f"Failed to get ID for {value} in {foreign_table}")
                logger_setup.get_logger().debug(f"Error: {model.last_error}")
                logger_setup.get_logger().debug(f"SQL query: {sql_query}")
                return value, foreign_table
            if model.rowCount() > 0:
                return model.index(0,0).data(QtC.Qt.ItemDataRole.DisplayRole), foreign_table
    return value, None

def foreign_key_columns(table: str):
    foreign_keys = {}
    sql_query = f'PRAGMA foreign_key_list("{table}")'
    model = SQLiteTableModel(sql_query)
    if model.last_error:
        logger_setup.get_logger().error(f"Failed to get columns for {foreign_table}")
        logger_setup.get_logger().debug(f"Error: {model.last_error}")
        logger_setup.get_logger().debug(f"SQL query: {sql_query}")
        return foreign_keys
    for row in range(model.rowCount()):
        foreign_table = model.index(row, 2).data(QtC.Qt.ItemDataRole.DisplayRole)
        table_display_column = get_name_column(foreign_table)
        foreign_query = f'PRAGMA table_info("{foreign_table}")'
        foreign_model = SQLiteTableModel(foreign_query)
        if foreign_model.last_error:
            logger_setup.get_logger().error(f"Failed to get columns for {foreign_table}")
            logger_setup.get_logger().debug(f"Error: {foreign_model.last_error}")
            logger_setup.get_logger().debug(f"SQL query: {foreign_query}")
            return foreign_keys
        table_display_header = None
        for foreign_row in range(foreign_model.rowCount()):
            if foreign_model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole) == table_display_column:
                table_display_header = foreign_model.index(row, 1).data(QtC.Qt.ItemDataRole.DisplayRole)
                break
        if not table_display_header:
            logger_setup.get_logger().error(f"Failed to get display column for {foreign_table}")
            return {}
        foreign_keys[foreign_model.index(row, 3).data(QtC.Qt.ItemDataRole.DisplayRole)] = \
            {'table': foreign_model.index(row, 2).data(QtC.Qt.ItemDataRole.DisplayRole),
             'id_column': foreign_model.index(row, 4).data(QtC.Qt.ItemDataRole.DisplayRole), 'display_column': table_display_header}
    return foreign_keys


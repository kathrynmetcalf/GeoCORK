import sqlite3
import Functions.Create_database as Create_db


def remove_old(db_file):
    selected_file = db_file
    try:
        db_conn = sqlite3.connect(selected_file)
    except sqlite3.OperationalError as e:
        print(e)
        return False
    # Drop all views
    cursor = db_conn.cursor()
    try:
        sql = 'SELECT name FROM sqlite_master WHERE type="view"'
        views = cursor.execute(sql).fetchall()
    except sqlite3.OperationalError as e:
        print(f"Error getting views: {e}")
        return False
    for view in views:
        try:
            cursor.execute(f'DROP VIEW IF EXISTS {view[0]}')
        except sqlite3.OperationalError as e:
            print(f"Error dropping view {view[0]}: {e}")
    edit_dict = {
        'SampleAges_old':
            {'SampleAges_AgeConstraints': Create_db.CREATE_SAMPLEAGES_AGECONSTRAINTS_TABLE,
             'SampleAges_AgeInterpretations': Create_db.CREATE_SAMPLEAGES_AGEINTERPRETATIONS_TABLE,
             'SampleAges_References': Create_db.CREATE_SAMPLEAGES_REFERENCES_TABLE,
             'Samples_SampleAges': Create_db.CREATE_SAMPLES_SAMPLEAGES_TABLE},
        'Samples_old':
            {'Samples_SampleAges': Create_db.CREATE_SAMPLES_SAMPLEAGES_TABLE,
             'Aliquots': Create_db.CREATE_ALIQUOTS_TABLE,
             'Samples_AgeSignatures': Create_db.CREATE_SAMPLES_AGESIGNATURES_TABLE,
             'Samples_Regions': Create_db.CREATE_SAMPLES_REGIONS_TABLE,
             'Samples_RockTypes': Create_db.CREATE_SAMPLES_ROCKTYPES_TABLE,
             'Samples_SampleContexts': Create_db.CREATE_SAMPLES_SAMPLECONTEXT_TABLE,
             'Samples_SamplingMethods': Create_db.CREATE_SAMPLES_SAMPLINGMETHODS_TABLE,
             'Samples_Settings': Create_db.CREATE_SAMPLES_SETTINGS_TABLE,
             'Samples_Units': Create_db.CREATE_SAMPLES_UNITS_TABLE},
        'References_old': {'SampleAges_References': Create_db.CREATE_SAMPLEAGES_REFERENCES_TABLE},
        'UPbAnalyses_old': {'UPbAnalyses_RejectionReasons': Create_db.CREATE_UPBANALYSES_REJECTIONREASONS_TABLE},
    }

    def get_columns(table):
        cursor = db_conn.cursor()
        try:
            results = cursor.execute(f'PRAGMA table_xinfo("{table}")').fetchall()
        except sqlite3.OperationalError as e:
            print(f"Failed to get columns for {table}")
            print(f"Error: {e}")
            return [], [], []
        virtual = []
        stored = []
        columns = []
        modified_column = False
        for result in results:
            if not modified_column:
                if 'Modified' in result[1]:
                    modified_column = True
                    columns.append(f'"{result[1]}"')
                elif 'Calculated' in result[1] or 'Display' in result[1]:
                    stored.append(f'"{result[1]}"')
                else:
                    columns.append(f'"{result[1]}"')
            else:
                virtual.append(f'"{result[1]}"')
        return virtual, stored, columns

    for old_table, table_dict in edit_dict.items():
        for table, create_sql in table_dict.items():
            virtual, stored, columns = get_columns(table)
            # Create a new table with the same original columns as the old one
            print(f'Creating table: {table}_new')
            if table == 'References':
                column_creation = create_sql.split(f'CREATE TABLE IF NOT EXISTS "{table}"')[1]
            else:
                column_creation = create_sql.split(f'CREATE TABLE IF NOT EXISTS {table}')[1]
            create_sql = f'CREATE TABLE IF NOT EXISTS {table}_new{column_creation}'
            cursor = db_conn.cursor()
            try:
                cursor.execute(create_sql)
            except sqlite3.OperationalError as e:
                print(f'Error creating {table}_new table: {e}')
                break
            print(f'Successfully created table: {table}_new')

            # Select only the stored columns, not the virtual ones
            column_str = ', '.join(columns)
            insert_new_table = f'INSERT INTO {table}_new SELECT {column_str} FROM "{table}"'
            try:
                cursor.execute(insert_new_table)
            except sqlite3.OperationalError as e:
                print(f'Error inserting {table}_new table: {e}')
                break
            print(f'Successfully inserted into new table: {table}_new')

            # Drop the original table
            drop_original_table = f'DROP TABLE "{table}"'
            try:
                cursor.execute(drop_original_table)
            except sqlite3.OperationalError as e:
                print(f'Error dropping original {table} table: {e}')
                break
            print(f'Successfully dropped original table: {table}')

            # Rename the new table to the original table name
            alter_table_qry = f'ALTER TABLE {table}_new RENAME TO "{table}"'
            try:
                cursor.execute(alter_table_qry)
            except sqlite3.OperationalError as e:
                print(f'Error renaming {table} table: {e}')
                break
            print(f'Successfully altered table rename: {table}_new to {table}')

            # Get the columns of the new table to compare to the original table
            new_virtual, new_stored, new_columns = get_columns(table)
            if new_columns != columns:
                print(f'Error copying new table {table} columns')
                print(f'Original columns: {columns}')
                print(f'New columns: {new_columns}')
                break

            try:
                out = cursor.execute(f'SELECT name, sql FROM sqlite_master WHERE name = "{table}"').fetchall()
            except sqlite3.OperationalError as e:
                print(f'Error getting table info for {table}: {e}')
                break
            create_sql = create_sql.replace(f"IF NOT EXISTS {table}_new", f'"{table}"')
            if out[0][1] != create_sql:
                print(f'Error creating table {table}')
                print(f'Original: {create_sql}')
                print(f'New: {out[0][1]}')
                break

    try:
        cursor.close()
        db_conn.commit()
        db_conn.close()
    except sqlite3.OperationalError as e:
        print(f'Error closing database: {e}')


if __name__ == "__main__":
    # remove_old("/Users/kametcalf/Documents/Research/GeoChron_non_git/GeoChron v.0 copy.db")
    # remove_old("C:/Users/jburges/Downloads/GeoChronDB/new geochron.db")
    remove_old("C:/Users/jburges/Downloads/Klamaths.db")
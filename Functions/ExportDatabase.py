from typing import List, Dict, Any, Set, Optional, Tuple

from PyQt6.QtSql import QSqlDatabase, QSqlQuery

from Functions import SQLUtils
from Functions.Database_manager import turn_on_foreign_keys, turn_off_foreign_keys
import logger_setup


def open_sqlite_db(db_path: str, connection_name: str) -> QSqlDatabase:
    """
    Open a SQLite database file and return the QSqlDatabase object.
    :param str db_path: full file path to the SQLite database file.
    :param str connection_name: connection name to open the database with.
    :return: The opened QSqlDatabase object.
    :rtype: QSqlDatabase
    :raises RuntimeError: If the database could not be opened.
    """
    db = QSqlDatabase.addDatabase('QSQLITE', connection_name)
    db.setDatabaseName(db_path)
    if not db.open():
        raise RuntimeError(f"Could not open database at {db_path}: {db.lastError().text()}")
    if not turn_on_foreign_keys():
        raise RuntimeError("Could not enable foreign keys")
    return db


def copy_table(table_name, conn_source, conn_target):
    cols_info = fetchall(f"PRAGMA table_info('{table_name}')", conn_source)
    insert_cols_info = [c[1] for c in cols_info]

    results = fetchall(
        f'SELECT {','.join([f"[{item}]" for item in insert_cols_info])} FROM "{table_name}"',
        conn_source
    )
    if results:
        insert_rows(conn_target, table_name, results, insert_cols_info)

def fetchall(query_str: str, database: QSqlDatabase=QSqlDatabase(), params: Optional[Tuple] = None) -> List[tuple]:
    """
    Emulates a 'fetchall' using QSqlQuery and a given database connection, if no database is
    provided the default database will be used. Returns rows as list of tuples.
    :param query_str: SQL query to execute on the database
    :param QSqlDatabase database: QSqlDatabase instance to enable foreign keys
    :param Optional[Tuple] params: list of parameters to bind to the query
    :return: list of tuples containing the rows returned by the query
    """
    result_rows = []
    query = QSqlQuery(database)
    query.prepare(query_str)
    if params:
        for i, val in enumerate(params):
            query.bindValue(i, val)
    if not query.exec():
        logger_setup.get_logger().critical(f'Error fetching total records')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
        return result_rows

    while query.next():
        # build a tuple of the columns
        row = tuple(query.value(col) for col in range(query.record().count()))
        result_rows.append(row)

    return result_rows

def execute_sql(query_str: str, database: QSqlDatabase) -> bool:
    """
    Helper function to execute a single SQL query on a given database connection.
    :param query_str:
    :param database:
    :return:
    """
    query = QSqlQuery(database)
    if not query.exec(query_str):
        logger_setup.get_logger().critical(f'Error executing SQL')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    return True

def insert_rows(database: QSqlDatabase, table_name: str, rows: list[tuple], insert_cols: list[str]):
    """
    Inserts multiple rows into the given table. Equivalent to 'executemany'.
    :param QSqlDatabase database:
    :param str table_name:
    :param list[tuple] rows:
    :param insert_cols:
    :return:
    """
    if not rows:
        return

    insert_cols = [f"[{item}]" for item in insert_cols]

    table_name = table_name.replace('_old', '')
    insert_stmt = f"INSERT INTO '{table_name}' ({','.join(insert_cols)}) VALUES ({", ".join(["?"] * len(insert_cols))})"

    query = QSqlQuery(database)
    logger_setup.get_logger().debug(f'SQL query: {insert_stmt}')
    for row in rows:
        query.prepare(insert_stmt)
        for i, val in enumerate(row):
            if val is '':
                val = None
            logger_setup.get_logger().debug(f'{table_name}: Binding value {i}:{val}')
            query.bindValue(i, val)
        if not query.exec():
            if "UNIQUE constraint failed: " in query.lastError().text():
                logger_setup.get_logger().info(f'Record already in database, skipping: {query.lastError().text()}')
            else:
                logger_setup.get_logger().critical(f'Error fetching total records')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                return

def copy_schema(conn_source: QSqlDatabase, conn_target: QSqlDatabase):
    """
    Copy all user-defined table schemas from the source DB to the target DB.
    Ignores 'sqlite_' internal tables or views.
    :param conn_source:
    :param conn_target:
    :return:
    """
    # Read all tables + their CREATE statements from the source
    table_rows = fetchall(
        "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        conn_source
    )
    for table_name, create_sql in table_rows:
        if create_sql:
            success = execute_sql(create_sql, conn_target)
            if not success:
                logger_setup.get_logger().critical(f'Error creating table {table_name}')
                logger_setup.get_logger().debug(f'Error: {conn_target.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {create_sql}')

    # Copy Indexes (regular and unique)
    index_rows = fetchall(
        "SELECT name, sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' AND sql IS NOT NULL",
        conn_source
    )
    for index_name, create_index_sql in index_rows:
        if create_index_sql:
            success = execute_sql(create_index_sql, conn_target)
            if not success:
                logger_setup.get_logger().critical(f'Error creating index {index_name}')
                logger_setup.get_logger().debug(f'Error: {conn_target.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {create_index_sql}')

    # Copy Views
    view_rows = fetchall(
        "SELECT name, sql FROM sqlite_master WHERE type='view' AND name NOT LIKE 'sqlite_%'",
        conn_source
    )
    for view_name, create_view_sql in view_rows:
        if create_view_sql:
            success = execute_sql(create_view_sql, conn_target)
            if not success:
                logger_setup.get_logger().critical(f'Error creating view {view_name}')
                logger_setup.get_logger().debug(f'Error: {conn_target.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {create_view_sql}')


def copy_static_tables(conn_source: QSqlDatabase, conn_target: QSqlDatabase) -> None:
    """
    Helper function to copy over the static tables that are always present in the database.
    :param QSqlDatabase conn_source:
    :param QSqlDatabase conn_target:
    """
    for table in SQLUtils.static_tables:
        logger_setup.get_logger().info(f"Copying table {table} from source to target connection")
        copy_table(table, conn_source, conn_target)


def find_bridge_tables(table: str, database: QSqlDatabase=QSqlDatabase()) -> List[Dict[str, Any]]:
    """
    Dynamically discover many-to-many 'bridge' tables in a dataabase that reference the
    given table and exactly one other table (2 foreign keys total). If no database is provided
    the default database will be used.
    :param QSqlDatabase database: database connection to search
    :param str table:
    :return:
    """
    # All tables
    table_rows = fetchall(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        database
    )
    all_tables = [row[0] for row in table_rows]

    bridge_tables_info = []

    for table_name in all_tables:
        # Check foreign key list
        table_name = table_name.replace('_old', '')
        fk_list = fetchall(f"PRAGMA foreign_key_list('{table_name}')", database)
        # PRAGMA result shape: (id, seq, table, from_col, to_col, on_update, on_delete, match)

        # We want exactly 2 foreign keys, one referencing table
        if any(fk[2].replace('_old', '') == table.replace('_old', '') for fk in fk_list):
            ref_data = []
            for fk in fk_list:
                ref_data.append({
                    "parent_table": fk[2].replace('_old', ''),  # the table referenced
                    "child_col":    fk[3],  # column in this table
                    "parent_col":   fk[4],  # column in parent_table
                })

            # Check if one references table
            if any(rd["parent_table"] == table for rd in ref_data):
                bridge_tables_info.append({
                    "bridge_table": table_name,
                    "refs": ref_data
                })

    return bridge_tables_info

def subset_many_to_many_bridges(
    conn_source: QSqlDatabase,
    conn_target: QSqlDatabase,
    sample_ids: Set[int],
    bridges_info: List[Dict[str, Any]],
    samples_table_name="Samples"
):
    """
    For each discovered bridge table referencing 'Samples' and another table,
    copy only the rows referencing the given sample_ids, then copy the
    associated rows from the 'other' table.
    """
    for bridge_info in bridges_info:
        bridge_table = bridge_info["bridge_table"]
        refs = bridge_info["refs"]

        # Identify which reference is to 'Samples' and which is 'other'
        sample_ref = None
        other_ref = None
        for rd in refs:
            if rd["parent_table"] == samples_table_name:
                sample_ref = rd
            else:
                other_ref = rd

        if not sample_ref or not other_ref:
            continue  # Not a valid bridging scenario

        sample_fk_col = sample_ref["child_col"]
        other_table_name = other_ref["parent_table"]
        other_fk_col = other_ref["child_col"]
        other_pk_col = other_ref["parent_col"]

        # 1) Fetch bridging rows for these sample_ids
        if not sample_ids:
            continue

        col_info_bridge = fetchall(f"PRAGMA table_info('{bridge_table}')", conn_source)
        insert_cols_bridge = [c[1] for c in col_info_bridge]
        # insert_cols_bridge = [f"[{item}]" for item in insert_cols_bridge]

        placeholder = ",".join(["?"] * len(sample_ids))

        bridge_table = bridge_table.replace('_old', '')

        bridge_rows = fetchall(
            f"""
            SELECT {','.join([f"[{item}]" for item in insert_cols_bridge])} FROM {bridge_table}
            WHERE {sample_fk_col} IN ({placeholder})
            """,
            conn_source,
            tuple(sample_ids)
        )

        if not bridge_rows:
            continue

        # Insert bridging rows into subset DB

        insert_rows(conn_target, bridge_table, bridge_rows, insert_cols_bridge)

        # 2) Gather 'other' IDs from these bridging rows
        col_names_bridge = [c[1] for c in col_info_bridge]
        other_idx = col_names_bridge.index(other_fk_col)
        other_ids = {row[other_idx] for row in bridge_rows if row[other_idx] is not None}
        if not other_ids:
            continue

        # 3) Fetch the matching rows from the other table
        # Insert them into the subset DB
        col_info_other = fetchall(f"PRAGMA table_info('{other_table_name}')", conn_source)
        insert_cols_other = [c[1] for c in col_info_other]
        # insert_cols_other = [f"[{item}]" for item in insert_cols_other]

        placeholder_2 = ",".join(["?"] * len(other_ids))

        other_table_name = other_table_name.replace('_old', '')

        other_rows = fetchall(
            f"""
            SELECT {','.join([f"[{item}]" for item in insert_cols_other])} FROM {other_table_name}
            WHERE {other_pk_col} IN ({placeholder_2})
            """,
            conn_source,
            tuple(other_ids)
        )
        if not other_rows:
            continue

        insert_rows(conn_target, other_table_name, other_rows, insert_cols_other)

###############################################################################
# 3. KNOWN ONE-TO-MANY CHAIN: Samples -> Aliquots -> Spots -> UPbAnalyses
#    AND references in UPbAnalyses to other tables
###############################################################################

def subset_one_to_many_chain(
    conn_source: QSqlDatabase,
    conn_target: QSqlDatabase,
    sample_ids: Set[int]
):
    """
    Hardcoded logic for the known chain:
      Samples -> Aliquots -> Spots -> UPbAnalyses
    Then from each UPbAnalyses row, gather foreign keys to:
      References, Instruments, LabFacilities, UPbAnalysisMethod
    """
    if not sample_ids:
        return

    # -------------------------------------------------------------------------
    # A) Aliquots referencing Samples
    # -------------------------------------------------------------------------
    col_info_aliq = fetchall("PRAGMA table_info('Aliquots')", conn_source)
    insert_cols_info_aliq = [c[1] for c in col_info_aliq]

    placeholder = ",".join(["?"] * len(sample_ids))
    aliq_rows = fetchall(
        f"SELECT {','.join([f"[{item}]" for item in insert_cols_info_aliq])} FROM Aliquots WHERE SampleID IN ({placeholder})",
        conn_source,
        tuple(sample_ids)
    )

    if aliq_rows:
        insert_rows(conn_target, 'Aliquots', aliq_rows, insert_cols_info_aliq)

    # Collect AliquotIDs
    aliquot_id_idx = insert_cols_info_aliq.index("AliquotID") if "AliquotID" in insert_cols_info_aliq else None
    aliquot_ids = set()

    if aliq_rows and aliquot_id_idx is not None:
        aliquot_ids = {row[aliquot_id_idx] for row in aliq_rows}

    # -------------------------------------------------------------------------
    # B) Spots referencing Aliquots
    # -------------------------------------------------------------------------
    spot_ids = set()
    if aliquot_ids:
        col_info_spots = fetchall("PRAGMA table_info('Spots')", conn_source)
        insert_cols_info_spots = [c[1] for c in col_info_spots]

        placeholder = ",".join(["?"] * len(aliquot_ids))
        spot_rows = fetchall(
            f"SELECT {','.join([f"[{item}]" for item in insert_cols_info_spots])} FROM Spots WHERE AliquotID IN ({placeholder})",
            conn_source,
            tuple(aliquot_ids)
        )
        if spot_rows:
            insert_rows(conn_target, "Spots", spot_rows, insert_cols_info_spots)

        # Collect SpotIDs
        spot_id_idx = insert_cols_info_spots.index("SpotID") if "SpotID" in insert_cols_info_spots else None
        if spot_id_idx is not None:
            spot_ids = {row[spot_id_idx] for row in spot_rows}

    # -------------------------------------------------------------------------
    # C) UPbAnalyses referencing Spots
    # -------------------------------------------------------------------------
    if spot_ids:
        col_info_upb = fetchall("PRAGMA table_info('UPbAnalyses')", conn_source)
        insert_cols_info_upb = [c[1] for c in col_info_upb]

        placeholder = ",".join(["?"] * len(spot_ids))
        UPbAnalyses_rows = fetchall(
            f"SELECT {','.join([f"[{item}]" for item in insert_cols_info_upb])} FROM UPbAnalyses WHERE SpotID IN ({placeholder})",
            conn_source,
            tuple(spot_ids)
        )
        if UPbAnalyses_rows:
            insert_rows(conn_target, "UPbAnalyses", UPbAnalyses_rows, insert_cols_info_upb)

            # Try to locate these columns

            ref_idx  = insert_cols_info_upb.index("ReferenceID")
            inst_idx = insert_cols_info_upb.index("InstrumentID")
            labf_idx = insert_cols_info_upb.index("LabFacilityID")
            meth_idx = insert_cols_info_upb.index("UPbAnalysisMethodID")


            reference_ids = set()
            instrument_ids = set()
            labfac_ids = set()
            method_ids = set()

            for row in UPbAnalyses_rows:
                if row[ref_idx]  is not None: reference_ids.add(row[ref_idx])
                if row[inst_idx] is not None: instrument_ids.add(row[inst_idx])
                if row[labf_idx] is not None: labfac_ids.add(row[labf_idx])
                if row[meth_idx] is not None: method_ids.add(row[meth_idx])

            def fetch_and_insert(table_name, pk_col, pk_values):
                if not pk_values:
                    return
                cols_info = fetchall(f"PRAGMA table_info('{table_name}')", conn_source)
                insert_cols_info = [c[1] for c in cols_info]

                ph = ",".join(["?"] * len(pk_values))
                results = fetchall(
                    f'SELECT {','.join([f"[{item}]" for item in insert_cols_info])} FROM "{table_name}" WHERE {pk_col} IN ({ph})',
                    conn_source,
                    tuple(pk_values)
                )
                if results:
                    insert_rows(conn_target, table_name, results, insert_cols_info)

            fetch_and_insert("References", "ReferenceID", reference_ids)
            fetch_and_insert("Instruments", "InstrumentID", instrument_ids)
            fetch_and_insert("LabFacilities", "LabFacilityID", labfac_ids)
            fetch_and_insert("UPbAnalysisMethods", "UPbAnalysisMethodID", method_ids)

        # -------------------------------------------------------------------------
        # D) GPSLocations referencing Samples
        #
        # Many schemas have a column in "Samples" like "GPSLocationID"
        # that references "GPSLocations(GPSLocationID)".
        # So we need to copy the matching GPSLocations rows for each Sample.
        # -------------------------------------------------------------------------
        # 1) Grab the GPSLocations table structure
    col_info_gps = fetchall("PRAGMA table_info('GPSLocations')", conn_source)
    insert_cols_info_gps = [c[1] for c in col_info_gps]

    if sample_ids:  # sample_ids is a set
        placeholder = ",".join(["?"] * len(sample_ids))

        # 2) For all sample_ids in 'Samples', gather the GPSLocationIDs used
        gps_rows = fetchall(
            f"""
               SELECT {','.join([f"[{col}]" for col in insert_cols_info_gps])}
               FROM GPSLocations
               WHERE GPSLocationID IN (
                   SELECT SampleGPSLocationID FROM Samples
                   WHERE SampleID IN ({placeholder})
                   AND SampleGPSLocationID IS NOT NULL
               )
               """,
            conn_source,
            tuple(sample_ids)
        )

        if gps_rows:
            insert_rows(conn_target, 'GPSLocations', gps_rows, insert_cols_info_gps)

###############################################################################
# 4. DETECTING 'TREE' TABLES (HIERARCHIES)
###############################################################################

def find_tree_tables(conn: QSqlDatabase) -> List[Dict[str, Any]]:
    """
    Find tables that are likely 'tree' structures by:
      - having a column that starts with 'Parent'
      OR
      - referencing themselves (self-reference) in foreign_key_list.
    """
    table_rows = fetchall(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        conn
    )
    table_names = [t[0] for t in table_rows]

    results = []

    for table_name in table_names:
        # Check columns
        col_info = fetchall(f"PRAGMA table_info('{table_name}')", conn)
        parent_cols = [c[1] for c in col_info if c[1].lower().startswith("parent")]

        # Check foreign keys
        fk_list = fetchall(f"PRAGMA foreign_key_list('{table_name}')", conn)
        self_ref = any(fk[2] == table_name for fk in fk_list)

        if parent_cols or self_ref:
            results.append({
                "table_name": table_name,
                "parent_cols": parent_cols,
                "self_referencing_fk": self_ref,
                "fk_list": fk_list
            })

    return results

def subset_tree_table_downstream(
    conn_source: QSqlDatabase,
    conn_target: QSqlDatabase,
    table_name: str,
    parent_col: str,
    child_col: str,
    root_ids: Set[int]
):
    """
    Recursively gather all rows from 'table_name' that descend from 'root_ids'
    via parent_col -> child_col chain, then insert them in conn_target.
    Prevents looping upward (only moves downward).
    """
    col_info = fetchall(f"PRAGMA table_info('{table_name}')", conn_source)
    col_names = [c[1] for c in col_info]

    if parent_col not in col_names or child_col not in col_names:
        # Can't do traversal
        return

    to_visit = list(root_ids)
    visited = set()

    while to_visit:
        current_id = to_visit.pop()
        if current_id in visited:
            continue
        visited.add(current_id)

        # Find rows where parent_col == current_id
        rows = fetchall(
            f"SELECT {','.join([f"[{item}]" for item in col_names])} FROM {table_name} WHERE {parent_col} = ?",
            conn_source,
            (current_id,)
        )
        if rows:
            insert_rows(conn_target, table_name, rows, col_names)

            # Gather child IDs
            child_idx = col_names.index(child_col)
            new_child_ids = [r[child_idx] for r in rows if r[child_idx] is not None]

            to_visit.extend(new_child_ids)

###############################################################################
# 5. MASTER FUNCTION: subset_database
###############################################################################

def subset_sample_ages_m2m(
    conn_source: QSqlDatabase,
    conn_target: QSqlDatabase,
    sample_ids: Set[int]
):
    """
    Handles the known dual many-to-many relationships:

    Samples <-> Samples_SampleAges <-> SampleAges <-> SampleAges_AgeConstraints <-> AgeConstraints
                                                        and
                                         SampleAges <-> SampleAges_AgeInterpretations <-> AgeInterpretations

    For each SampleID in sample_ids, this function:
      1) Finds rows in Samples_SampleAges referencing those SampleIDs, inserts them into the target.
      2) From those rows, collects SampleAgeIDs -> fetches SampleAges.
      3) Inserts SampleAges into the target.
      4) Finds bridging rows in SampleAges_AgeConstraints for those SampleAgeIDs -> inserts them.
      5) Gathers AgeConstraintIDs -> fetches AgeConstraints -> inserts them.
      6) Finds bridging rows in SampleAges_AgeInterpretations for those SampleAgeIDs -> inserts them.
      7) Gathers AgeInterpretationIDs -> fetches AgeInterpretations -> inserts them.
    """

    if not sample_ids:
        return

    logger_setup.get_logger().info(f"Subsetting SampleAges M2M relationships for sample_ids={sample_ids}")

    # -------------------------------------------------------------------------
    # (1) Samples_SampleAges referencing our sample_ids
    # -------------------------------------------------------------------------
    # PRAGMA table_info to figure out columns in the bridging table
    col_info_samples_sampleages = fetchall("PRAGMA table_info('Samples_SampleAges')", conn_source)
    insert_cols_samples_sampleages = [c[1] for c in col_info_samples_sampleages]

    # We need a placeholder string for the IN clause
    placeholder = ",".join(["?"] * len(sample_ids))

    samples_sampleages_rows = fetchall(
        f"""
        SELECT {",".join([f"[{col}]" for col in insert_cols_samples_sampleages])}
        FROM Samples_SampleAges
        WHERE SampleID IN ({placeholder})
        """,
        conn_source,
        tuple(sample_ids)
    )
    if samples_sampleages_rows:
        insert_rows(conn_target, "Samples_SampleAges", samples_sampleages_rows, insert_cols_samples_sampleages)
    else:
        # No bridging rows => nothing further to do
        return

    # Gather SampleAgeIDs
    col_names_samples_sampleages = [c[1] for c in col_info_samples_sampleages]
    try:
        sampleAgeID_idx = col_names_samples_sampleages.index("SampleAgeID")
    except ValueError:
        # The bridging table doesn't have the expected column name
        logger_setup.get_logger().warning("Samples_SampleAges table doesn't have 'SampleAgeID' column!")
        return

    sampleAge_ids = {
        row[sampleAgeID_idx]
        for row in samples_sampleages_rows
        if row[sampleAgeID_idx] is not None
    }
    if not sampleAge_ids:
        return

    # -------------------------------------------------------------------------
    # (2) & (3) SampleAges
    # -------------------------------------------------------------------------
    col_info_sampleages = fetchall("PRAGMA table_info('SampleAges')", conn_source)
    insert_cols_sampleages = [c[1] for c in col_info_sampleages]

    placeholder_2 = ",".join(["?"] * len(sampleAge_ids))
    sampleages_rows = fetchall(
        f"""
        SELECT {",".join([f"[{col}]" for col in insert_cols_sampleages])}
        FROM SampleAges
        WHERE SampleAgeID IN ({placeholder_2})
        """,
        conn_source,
        tuple(sampleAge_ids)
    )
    if sampleages_rows:
        insert_rows(conn_target, "SampleAges", sampleages_rows, insert_cols_sampleages)
    else:
        return  # No sampleage rows => no further bridging references

    # -------------------------------------------------------------------------
    # (4) & (5) SampleAges_AgeConstraints -> AgeConstraints
    # -------------------------------------------------------------------------
    col_info_sa_ageconstraints = fetchall("PRAGMA table_info('SampleAges_AgeConstraints')", conn_source)
    insert_cols_sa_ageconstraints = [c[1] for c in col_info_sa_ageconstraints]

    placeholder_3 = ",".join(["?"] * len(sampleAge_ids))
    sa_ageconstraints_rows = fetchall(
        f"""
        SELECT {",".join([f"[{col}]" for col in insert_cols_sa_ageconstraints])}
        FROM SampleAges_AgeConstraints
        WHERE SampleAgeID IN ({placeholder_3})
        """,
        conn_source,
        tuple(sampleAge_ids)
    )
    if sa_ageconstraints_rows:
        insert_rows(conn_target, "SampleAges_AgeConstraints", sa_ageconstraints_rows, insert_cols_sa_ageconstraints)

        # Gather AgeConstraintIDs
        col_names_sa_ageconstraints = [c[1] for c in col_info_sa_ageconstraints]
        try:
            ageConstraintID_idx = col_names_sa_ageconstraints.index("AgeConstraintID")
        except ValueError:
            logger_setup.get_logger().warning("SampleAges_AgeConstraints doesn't have 'AgeConstraintID' column!")
            ageConstraintID_idx = None

        if ageConstraintID_idx is not None:
            ageConstraint_ids = {
                row[ageConstraintID_idx]
                for row in sa_ageconstraints_rows
                if row[ageConstraintID_idx] is not None
            }
            if ageConstraint_ids:
                # Insert those AgeConstraints
                col_info_ageconstraints = fetchall("PRAGMA table_info('AgeConstraints')", conn_source)
                insert_cols_ageconstraints = [c[1] for c in col_info_ageconstraints]

                placeholder_4 = ",".join(["?"] * len(ageConstraint_ids))
                ageconstraints_rows = fetchall(
                    f"""
                    SELECT {",".join([f"[{col}]" for col in insert_cols_ageconstraints])}
                    FROM AgeConstraints
                    WHERE AgeConstraintID IN ({placeholder_4})
                    """,
                    conn_source,
                    tuple(ageConstraint_ids)
                )
                if ageconstraints_rows:
                    insert_rows(conn_target, "AgeConstraints", ageconstraints_rows, insert_cols_ageconstraints)

    # -------------------------------------------------------------------------
    # (6) & (7) SampleAges_AgeInterpretations -> AgeInterpretations
    # -------------------------------------------------------------------------
    col_info_sa_ageinterpretations = fetchall("PRAGMA table_info('SampleAges_AgeInterpretations')", conn_source)
    insert_cols_sa_ageinterpretations = [c[1] for c in col_info_sa_ageinterpretations]

    placeholder_5 = ",".join(["?"] * len(sampleAge_ids))
    sa_ageinterpretations_rows = fetchall(
        f"""
        SELECT {",".join([f"[{col}]" for col in insert_cols_sa_ageinterpretations])}
        FROM SampleAges_AgeInterpretations
        WHERE SampleAgeID IN ({placeholder_5})
        """,
        conn_source,
        tuple(sampleAge_ids)
    )
    if sa_ageinterpretations_rows:
        insert_rows(
            conn_target,
            "SampleAges_AgeInterpretations",
            sa_ageinterpretations_rows,
            insert_cols_sa_ageinterpretations
        )

        # Gather AgeInterpretationIDs
        col_names_sa_ageinterpretations = [c[1] for c in col_info_sa_ageinterpretations]
        try:
            ageInterpretationID_idx = col_names_sa_ageinterpretations.index("AgeInterpretationID")
        except ValueError:
            logger_setup.get_logger().warning("SampleAges_AgeInterpretations doesn't have 'AgeInterpretationID' column!")
            ageInterpretationID_idx = None

        if ageInterpretationID_idx is not None:
            ageInterpretation_ids = {
                row[ageInterpretationID_idx]
                for row in sa_ageinterpretations_rows
                if row[ageInterpretationID_idx] is not None
            }
            if ageInterpretation_ids:
                # Insert those AgeInterpretations
                col_info_ageinterpretations = fetchall("PRAGMA table_info('AgeInterpretations')", conn_source)
                insert_cols_ageinterpretations = [c[1] for c in col_info_ageinterpretations]

                placeholder_6 = ",".join(["?"] * len(ageInterpretation_ids))
                ageinterpretations_rows = fetchall(
                    f"""
                    SELECT {",".join([f"[{col}]" for col in insert_cols_ageinterpretations])}
                    FROM AgeInterpretations
                    WHERE AgeInterpretationID IN ({placeholder_6})
                    """,
                    conn_source,
                    tuple(ageInterpretation_ids)
                )
                if ageinterpretations_rows:
                    insert_rows(conn_target, "AgeInterpretations", ageinterpretations_rows, insert_cols_ageinterpretations)

def subset_database(conn_source: QSqlDatabase, conn_target: QSqlDatabase, sample_ids: list[int]) -> bool:
    """
    Creates a new subset DB that includes:
      - The specified SampleID row from 'Samples',
      - Dynamically discovered many-to-many references (bridge tables),
      - Known one-to-many chain: Samples -> Aliquots -> Spots -> UPbAnalyses,
      - The 'parent' references from UPbAnalyses,
      - Any 'tree' tables that have 'Parent...' columns or self-reference,
        traversing them downward (schema-dependent).
    """

    # 2) Copy schema
    copy_schema(conn_source, conn_target)

    copy_static_tables(conn_source, conn_target)

    for sample_id in sample_ids:
        # 3) Retrieve the requested Sample row from source
        col_info_samples = fetchall("PRAGMA table_info('Samples')", conn_source)

        row = fetchall(
            f"SELECT {','.join([item[1] for item in col_info_samples])} FROM Samples WHERE SampleID = ?",
            conn_source,
            (sample_id,)
        )
        if not row:
            conn_source.close()
            conn_target.close()
            return False

        # Insert the sample row
        insert_cols_info_samples = [c[1] for c in col_info_samples]
        insert_rows(conn_target, "Samples", row, insert_cols_info_samples)
        sample_ids = {sample_id}

        # 4) Dynamically find bridging (many-to-many) tables referencing Samples
        bridges_info = find_bridge_tables('Samples', conn_source)

        # 5) Subset those bridging tables + their 'other' table references
        subset_many_to_many_bridges(
            conn_source,
            conn_target,
            sample_ids=sample_ids,
            bridges_info=bridges_info,
            samples_table_name="Samples"
        )

        # 6) Known one-to-many chain
        subset_one_to_many_chain(conn_source, conn_target, sample_ids)

        subset_sample_ages_m2m(conn_source, conn_target, sample_ids)

        # 7) Handle any 'tree' tables
        tree_tables = find_tree_tables(conn_source)
        # Example usage (schema-dependent). If you had a table "Hierarchy" with columns
        # "HierarchyID" and "ParentHierarchyID", you could do:

        for tinfo in tree_tables:
            tbl_name = tinfo["table_name"]
            tbl_name = tbl_name.replace("_old", " ")
            parent_cols = tinfo["parent_cols"]
            # Suppose we want "ParentID" and "TreeID"
            # (In practice, adapt to your actual child column name)
            # We'll do a naive check:
            col_info = fetchall(f"PRAGMA table_info('{tbl_name}')", conn_source)
            col_names = [c[1] for c in col_info]

            if f"Parent{tbl_name[0:-1]}ID" in col_names and f"{tbl_name[0:-1]}ID" in col_names:
                # Let's assume we have some "root_ids" for "TreeID" from somewhere.
                # Or, if you want to subset all from a known root, you might have:
                root_ids = set()  # fill in if you have a known starting ID(s)

                # If you want to start from all rows that are linked to your sample_id,
                # you'd need additional logic to discover that. For now, demonstration:
                # If your tree table also has a 'SampleID' column, you can do:
                #   SELECT TreeID FROM tbl_name WHERE SampleID = sample_id
                #   as a root set. Then descend.

                # Gather potential "root" items that belong to sample_id
                rows = fetchall(f"SELECT {f'Parent{tbl_name[0:-1]}ID'} FROM {tbl_name}", conn_target)
                root_ids = {r[0] for r in rows}

                if root_ids:
                    # Subset the entire downstream from those root IDs
                    subset_tree_table_downstream(
                        conn_source=conn_source,
                        conn_target=conn_target,
                        table_name=tbl_name,
                        child_col=f'Parent{tbl_name[0:-1]}ID',
                        parent_col=f'{tbl_name[0:-1]}ID',
                        root_ids=root_ids
                    )

    QSqlDatabase.removeDatabase(conn_source.connectionName())
    QSqlDatabase.removeDatabase(conn_target.connectionName())

    return True


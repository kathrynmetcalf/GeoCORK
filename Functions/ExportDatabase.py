import os
import sqlite3
import sys
from inspect import AGEN_SUSPENDED
from tkinter.constants import UNITS
from typing import List, Dict, Any, Set, Optional, Tuple

from PyQt6 import QtSql, QtCore
from PyQt6.QtCore import QCoreApplication, QVariant, QMetaType
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import QApplication

import logger_setup
from ui.GPSDialog import GPSDialog


def open_sqlite_db(db_path: str, connection_name: str) -> QSqlDatabase:
    """
    Convenience to open a QSQLITE database under a unique connection name.
    """
    db = QSqlDatabase.addDatabase('QSQLITE', connection_name)
    db.setDatabaseName(db_path)
    if not db.open():
        raise RuntimeError(f"Could not open database at {db_path}: {db.lastError().text()}")
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

def fetchall(query_str: str, db: QSqlDatabase, params: Optional[Tuple] = None) -> List[tuple]:
    """
    Emulate a 'fetchall' using QSqlQuery. Returns rows as list of tuples.
    """
    result_rows = []
    query = QSqlQuery(db)
    query.prepare(query_str)
    if params:
        for i, val in enumerate(params):
            query.bindValue(i, val)
    logger_setup.get_logger().debug(f'SQL Command: {query_str}')
    if not query.exec():
        logger_setup.get_logger().critical(
            f'Error fetching total records: {query.lastError().text()}')
        logger_setup.get_logger().critical(f'SQL command: {query_str}')
        return result_rows

    while query.next():
        # build a tuple of the columns
        row = tuple(query.value(col) for col in range(query.record().count()))
        result_rows.append(row)

    return result_rows

def execute_sql(statement: str, db: QSqlDatabase) -> bool:
    """
    Helper to execute a single SQL statement (without parameters).
    """
    query = QSqlQuery(db)
    if not query.exec(statement):
        logger_setup.get_logger().critical(f'Error executing SQL: {query.lastError().text()}')
        return False
    return True

def insert_rows(db: QSqlDatabase, table_name: str, rows: List[tuple], insert_cols: List[str]):
    """
    Inserts multiple rows into the given table. Equivalent to 'executemany'.
    """
    if not rows:
        return

    insert_cols = [f"[{item}]" for item in insert_cols]

    table_name = table_name.replace('_old', '')
    insert_stmt = f"INSERT INTO '{table_name}' ({','.join(insert_cols)}) VALUES ({", ".join(["?"] * len(insert_cols))})"

    query = QSqlQuery(db)
    logger_setup.get_logger().debug(f'SQL command: {insert_stmt}')
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
                logger_setup.get_logger().critical(
                f'Error fetching total records: {query.lastError().text()}')
                logger_setup.get_logger().critical(f'SQL command: {insert_stmt}')

###############################################################################
# 1. SCHEMA COPY
###############################################################################

def copy_schema(conn_source: QSqlDatabase, conn_target: QSqlDatabase):
    """
    Copy all user-defined table schemas from the source DB to the target DB.
    Ignores 'sqlite_' internal tables or views.
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
                logger_setup.get_logger().critical(f'SQL command: {create_sql}')

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
                logger_setup.get_logger().critical(f'SQL command: {create_index_sql}')

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
                logger_setup.get_logger().critical(f'SQL command: {create_view_sql}')


def copy_static_tables(conn_source: QSqlDatabase, conn_target: QSqlDatabase):
    static_tables = ['About',
                     'AgeUnitConversions',
                     'AgeUnits',
                     'ConcordanceFormatConversions',
                     'ConcordanceFormats',
                     'DirectionUnits',
                     'DistanceUnitConversions',
                     'DistanceUnits',
                     'ErrorFormatConversions',
                     'ErrorFormats',
                     'GPSFormatConversions',
                     'GPSFormats']
    for table in static_tables:
        logger_setup.get_logger().info(f"Copying table {table} from source to target connection")
        copy_table(table, conn_source, conn_target)

###############################################################################
# 2. DETECTING MANY-TO-MANY BRIDGE TABLES
###############################################################################

def find_bridge_tables(conn: QSqlDatabase, samples_table_name="Samples") -> List[Dict[str, Any]]:
    """
    Dynamically discover many-to-many 'bridge' tables that reference the
    'Samples' table and exactly one other table (2 foreign keys total).
    """
    # All tables
    table_rows = fetchall(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        conn
    )
    all_tables = [row[0] for row in table_rows]

    bridge_tables_info = []

    for table_name in all_tables:
        # Check foreign key list
        table_name = table_name.replace('_old', '')
        fk_list = fetchall(f"PRAGMA foreign_key_list('{table_name}')", conn)
        # PRAGMA result shape: (id, seq, table, from_col, to_col, on_update, on_delete, match)

        # We want exactly 2 foreign keys, one referencing 'Samples'
        if any(fk[2].replace('_old', '') == samples_table_name.replace('_old', '') for fk in fk_list):
            ref_data = []
            for fk in fk_list:
                ref_data.append({
                    "parent_table": fk[2].replace('_old', ''),  # the table referenced
                    "child_col":    fk[3],  # column in this table
                    "parent_col":   fk[4],  # column in parent_table
                })

            # Check if one references samples_table_name
            if any(rd["parent_table"] == samples_table_name for rd in ref_data):
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

def subset_database(
    conn_source: QSqlDatabase,
    conn_target: QSqlDatabase,
    sample_ids: list[int]
):
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
            return

        # Insert the sample row
        insert_cols_info_samples = [c[1] for c in col_info_samples]
        insert_rows(conn_target, "Samples", row, insert_cols_info_samples)
        sample_ids = {sample_id}

        # 4) Dynamically find bridging (many-to-many) tables referencing Samples
        bridges_info = find_bridge_tables(conn_source, "Samples")

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


# EXAMPLE USAGE
if __name__ == "__main__":
    app = QCoreApplication(sys.argv)

    src_db_file = "C:\\Users\\jburges\\Downloads\\GeoChronDB\\GeoChron.db"

    if os.path.isfile("C:\\Users\\jburges\\Downloads\\GeoChronDB\\test.db"):
        os.remove("C:\\Users\\jburges\\Downloads\\GeoChronDB\\test.db")

    tgt_db_file = "C:\\Users\\jburges\\Downloads\\GeoChronDB\\test.db"
    conn = sqlite3.connect(tgt_db_file)

    # Close the connection (creates an empty database file)
    conn.close()

    sample_id_to_subset = [191]  # Provide the SampleID you want to subset
    # sample id 191 should get rocktype id 100
    srcDatabase = QtSql.QSqlDatabase.addDatabase('QSQLITE', 'src')
    srcDatabase.setDatabaseName(src_db_file)

    tgtDatabase = QtSql.QSqlDatabase.addDatabase('QSQLITE', 'tgt')
    tgtDatabase.setDatabaseName(tgt_db_file)

    srcDatabase.open()
    tgtDatabase.open()

    print('Subsetting db')
    subset_database(srcDatabase, tgtDatabase, sample_id_to_subset)

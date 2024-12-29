from typing import List, Dict, Any, Set, Optional, Tuple

from PyQt6.QtSql import QSqlDatabase, QSqlQuery


def open_sqlite_db(db_path: str, connection_name: str) -> QSqlDatabase:
    """
    Convenience to open a QSQLITE database under a unique connection name.
    """
    db = QSqlDatabase.addDatabase('QSQLITE', connection_name)
    db.setDatabaseName(db_path)
    if not db.open():
        raise RuntimeError(f"Could not open database at {db_path}: {db.lastError().text()}")
    return db

def fetchall(query_str: str, db: QSqlDatabase, params: Optional[Tuple] = None) -> List[tuple]:
    """
    Emulate a 'fetchall' using QSqlQuery. Returns rows as list of tuples.
    """
    result_rows = []
    q = QSqlQuery(db)
    q.prepare(query_str)
    if params:
        for i, val in enumerate(params):
            q.bindValue(i, val)

    if not q.exec():
        print("Query failed:", q.lastError().text())
        return result_rows

    while q.next():
        # build a tuple of the columns
        row = tuple(q.value(col) for col in range(q.record().count()))
        result_rows.append(row)

    return result_rows

def execute_sql(statement: str, db: QSqlDatabase) -> bool:
    """
    Helper to execute a single SQL statement (without parameters).
    """
    q = QSqlQuery(db)
    return q.exec(statement)

def insert_rows(db: QSqlDatabase, table_name: str, rows: List[tuple], col_count: int):
    """
    Inserts multiple rows into the given table. Equivalent to 'executemany'.
    """
    if not rows:
        return
    placeholders = ", ".join(["?"] * col_count)
    insert_stmt = f"INSERT INTO {table_name} VALUES ({placeholders})"

    q = QSqlQuery(db)
    for row in rows:
        q.prepare(insert_stmt)
        for i, val in enumerate(row):
            q.bindValue(i, val)
        if not q.exec():
            print(f"Insert failed into {table_name}:", q.lastError().text())
    # If desired, you can call db.commit() here or wrap in transactions as needed.


###############################################################################
# 1. SCHEMA COPY
###############################################################################

def copy_schema(conn_source: QSqlDatabase, conn_target: QSqlDatabase):
    """
    Copy all user-defined table schemas from the source DB to the target DB.
    Ignores 'sqlite_' internal tables or views.
    """
    # Read all tables + their CREATE statements from the source
    rows = fetchall(
        "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        conn_source
    )
    for table_name, create_sql in rows:
        if create_sql:
            success = execute_sql(create_sql, conn_target)
            if not success:
                print(f"Failed to create table {table_name} in target DB.")

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
        fk_list = fetchall(f"PRAGMA foreign_key_list('{table_name}')", conn)
        # PRAGMA result shape: (id, seq, table, from_col, to_col, on_update, on_delete, match)

        # We want exactly 2 foreign keys, one referencing 'Samples'
        if len(fk_list) == 2:
            ref_data = []
            for fk in fk_list:
                ref_data.append({
                    "parent_table": fk[2],  # the table referenced
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

# def insert_rows(conn_target: sqlite3.Connection, table_name: str, rows: List[tuple], col_count: int):
#     """
#     Utility to insert multiple rows into a table with a given column count.
#     """
#     if not rows:
#         return
#     placeholders = ", ".join(["?"] * col_count)
#     conn_target.executemany(
#         f"INSERT INTO {table_name} VALUES ({placeholders})",
#         rows
#     )
#     conn_target.commit()

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
        placeholder = ",".join(["?"] * len(sample_ids))
        bridge_rows = fetchall(
            f"""
            SELECT * FROM {bridge_table}
            WHERE {sample_fk_col} IN ({placeholder})
            """,
            conn_source,
            tuple(sample_ids)
        )

        if not bridge_rows:
            continue

        # Insert bridging rows into subset DB
        col_info_bridge = fetchall(f"PRAGMA table_info('{bridge_table}')", conn_source)
        col_count_bridge = len(col_info_bridge)
        insert_rows(conn_target, bridge_table, bridge_rows, col_count_bridge)

        # 2) Gather 'other' IDs from these bridging rows
        col_names_bridge = [c[1] for c in col_info_bridge]
        other_idx = col_names_bridge.index(other_fk_col)
        other_ids = {row[other_idx] for row in bridge_rows if row[other_idx] is not None}
        if not other_ids:
            continue

        # 3) Fetch the matching rows from the other table
        placeholder_2 = ",".join(["?"] * len(other_ids))
        other_rows = fetchall(
            f"""
            SELECT * FROM {other_table_name}
            WHERE {other_pk_col} IN ({placeholder_2})
            """,
            conn_source,
            tuple(other_ids)
        )
        if not other_rows:
            continue

        # Insert them into the subset DB
        col_info_other = fetchall(f"PRAGMA table_info('{other_table_name}')", conn_source)
        col_count_other = len(col_info_other)
        insert_rows(conn_target, other_table_name, other_rows, col_count_other)

###############################################################################
# 3. KNOWN ONE-TO-MANY CHAIN: Samples -> Aliquots -> Spots -> UPbData
#    AND references in UPbData to other tables
###############################################################################

def subset_one_to_many_chain(
    conn_source: QSqlDatabase,
    conn_target: QSqlDatabase,
    sample_ids: Set[int]
):
    """
    Hardcoded logic for the known chain:
      Samples -> Aliquots -> Spots -> UPbData
    Then from each UPbData row, gather foreign keys to:
      References, Instruments, LabFacilities, UPbAnalysisMethod
    """
    if not sample_ids:
        return

    # -------------------------------------------------------------------------
    # A) Aliquots referencing Samples
    # -------------------------------------------------------------------------
    placeholder = ",".join(["?"] * len(sample_ids))
    aliq_rows = fetchall(
        f"SELECT * FROM Aliquots WHERE SampleID IN ({placeholder})",
        conn_source,
        tuple(sample_ids)
    )
    print(aliq_rows)

    if aliq_rows:
        col_info_aliq = fetchall("PRAGMA table_info('Aliquots')", conn_source)
        insert_rows(conn_target, "Aliquots", aliq_rows, len(col_info_aliq))

    # Collect AliquotIDs
    col_names_aliq = [c[1] for c in fetchall("PRAGMA table_info('Aliquots')", conn_source)]
    aliquot_id_idx = col_names_aliq.index("AliquotID") if "AliquotID" in col_names_aliq else None
    aliquot_ids = set()

    if aliq_rows and aliquot_id_idx is not None:
        aliquot_ids = {row[aliquot_id_idx] for row in aliq_rows}

    # -------------------------------------------------------------------------
    # B) Spots referencing Aliquots
    # -------------------------------------------------------------------------
    spot_ids = set()
    if aliquot_ids:
        placeholder = ",".join(["?"] * len(aliquot_ids))
        spot_rows = fetchall(
            f"SELECT * FROM Spots WHERE AliquotID IN ({placeholder})",
            conn_source,
            tuple(aliquot_ids)
        )
        if spot_rows:
            col_info_spots = fetchall("PRAGMA table_info('Spots')", conn_source)
            insert_rows(conn_target, "Spots", spot_rows, len(col_info_spots))

            # Collect SpotIDs
            col_names_spots = [c[1] for c in col_info_spots]
            spot_id_idx = col_names_spots.index("SpotID") if "SpotID" in col_names_spots else None
            if spot_id_idx is not None:
                spot_ids = {row[spot_id_idx] for row in spot_rows}

    # -------------------------------------------------------------------------
    # C) UPbData referencing Spots
    # -------------------------------------------------------------------------
    if spot_ids:
        placeholder = ",".join(["?"] * len(spot_ids))
        upbdata_rows = fetchall(
            f"SELECT * FROM UPbData WHERE SpotID IN ({placeholder})",
            conn_source,
            tuple(spot_ids)
        )
        if upbdata_rows:
            col_info_upb = fetchall("PRAGMA table_info('UPbData')", conn_source)
            insert_rows(conn_target, "UPbData", upbdata_rows, len(col_info_upb))

            # Now handle the *foreign keys* in UPbData that reference:
            #   References, Instruments, LabFacilities, UPbAnalysisMethod
            col_names_upb = [c[1] for c in col_info_upb]

            # Try to locate these columns
            try:
                ref_idx  = col_names_upb.index("SourceID")
                inst_idx = col_names_upb.index("InstrumentID")
                labf_idx = col_names_upb.index("LabFacilityID")
                meth_idx = col_names_upb.index("UPbAnalysisMethodID")
            except ValueError:
                # If any column doesn't exist, skip
                return

            reference_ids = set()
            instrument_ids = set()
            labfac_ids = set()
            method_ids = set()

            for row in upbdata_rows:
                if row[ref_idx]  is not None: reference_ids.add(row[ref_idx])
                if row[inst_idx] is not None: instrument_ids.add(row[inst_idx])
                if row[labf_idx] is not None: labfac_ids.add(row[labf_idx])
                if row[meth_idx] is not None: method_ids.add(row[meth_idx])
                print(reference_ids)

            def fetch_and_insert(table_name, pk_col, pk_values):
                if not pk_values:
                    return
                ph = ",".join(["?"] * len(pk_values))
                results = fetchall(
                    f"SELECT * FROM {table_name} WHERE {pk_col} IN ({ph})",
                    conn_source,
                    tuple(pk_values)
                )
                if results:
                    cols_info = fetchall(f"PRAGMA table_info('{table_name}')", conn_source)
                    insert_rows(conn_target, table_name, results, len(cols_info))

            fetch_and_insert("Sources",        "SourceID",       reference_ids)
            fetch_and_insert("Instruments",       "InstrumentID",       instrument_ids)
            fetch_and_insert("LabFacilities",     "LabFacilityID",      labfac_ids)
            fetch_and_insert("UPbAnalysisMethod", "UPbAnalysisMethodID",   method_ids)

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
        parent_cols = [c[1] for c in col_info if c[1].startswith("Parent")]

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
    col_count = len(col_info)
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
            f"SELECT * FROM {table_name} WHERE {parent_col} = ?",
            conn_source,
            (current_id,)
        )
        if rows:
            insert_rows(conn_target, table_name, rows, col_count)

            # Gather child IDs
            child_idx = col_names.index(child_col)
            new_child_ids = [r[child_idx] for r in rows if r[child_idx] is not None]

            to_visit.extend(new_child_ids)

###############################################################################
# 5. MASTER FUNCTION: subset_database
###############################################################################

def subset_database(
    source_db_path: str,
    subset_db_path: str,
    sample_ids: list[int]
):
    """
    Creates a new subset DB that includes:
      - The specified SampleID row from 'Samples',
      - Dynamically discovered many-to-many references (bridge tables),
      - Known one-to-many chain: Samples -> Aliquots -> Spots -> UPbData,
      - The 'parent' references from UPbData,
      - Any 'tree' tables that have 'Parent...' columns or self-reference,
        traversing them downward (schema-dependent).
    """
    # 1) Open source & target DBs via QSqlDatabase
    conn_source = open_sqlite_db(source_db_path, "source_connection")
    conn_target = open_sqlite_db(subset_db_path, "target_connection")

    # 2) Copy schema
    copy_schema(conn_source, conn_target)

    for sample_id in sample_ids:
        # 3) Retrieve the requested Sample row from source
        row = fetchall(
            "SELECT * FROM Samples WHERE SampleID = ?",
            conn_source,
            (sample_id,)
        )
        if not row:
            print(f"No Samples found with SampleID={sample_id}")
            conn_source.close()
            conn_target.close()
            return

        # Insert the sample row
        col_info_samples = fetchall("PRAGMA table_info('Samples')", conn_source)
        insert_rows(conn_target, "Samples", row, len(col_info_samples))

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

    # Close DBs
    conn_source.close()
    conn_target.close()


# EXAMPLE USAGE
if __name__ == "__main__":
    import os
    src_db = "/Users/jarrodburges/Downloads/newschema.db"
    if os.path.isfile("test.db"):
        os.remove("test.db")
    tgt_db_file = "test.db"

    sample_id_to_subset = [1]  # Provide the SampleID you want to subset

    subset_database(src_db, tgt_db_file, sample_id_to_subset)


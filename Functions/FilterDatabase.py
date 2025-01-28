from typing import List, Dict, Any, Set, Optional, Tuple

from PyQt6.QtSql import QSqlDatabase, QSqlQuery


###############################################################################
# HELPER FUNCTIONS
###############################################################################

def open_sqlite_db(db_path: str, connection_name: str) -> QSqlDatabase:
    """
    Convenience to open a QSQLITE database under a unique connection name.
    """
    db = QSqlDatabase.addDatabase('QSQLITE', connection_name)
    db.setDatabaseName(db_path)
    if not db.open():
        raise RuntimeError(
            f"Could not open database at {db_path}: {db.lastError().text()}"
        )
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


def get_single_integer_pk_col(db: QSqlDatabase, table_name: str) -> Optional[Tuple[int, str]]:
    """
    Returns (pk_index_in_record, pk_col_name) if the table has exactly
    one integer primary key column. Otherwise returns None.
    """
    col_info = fetchall(f"PRAGMA table_info('{table_name}')", db)
    # col_info columns: [cid, name, type, notnull, dflt_value, pk]
    pk_cols = [(i, c[1]) for (i, c) in enumerate(col_info) if c[5] == 1]
    if table_name == 'UPbData':
        return (0, 'UPbAnalysisID')
    if len(pk_cols) == 1:
        # We have exactly one PK column
        return pk_cols[0]  # (index_in_table_info, col_name)
    return None


###############################################################################
# DISCOVERING MANY-TO-MANY BRIDGE TABLES
###############################################################################

def find_bridge_tables(conn: QSqlDatabase, samples_table_name="Samples") -> List[Dict[str, Any]]:
    """
    Dynamically discover many-to-many 'bridge' tables that reference the
    'Samples' table and exactly one other table (2 foreign keys total).
    """
    table_rows = fetchall(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        conn
    )
    all_tables = [row[0] for row in table_rows]

    bridge_tables_info = []

    for table_name in all_tables:
        fk_list = fetchall(f"PRAGMA foreign_key_list('{table_name}')", conn)
        # PRAGMA result shape: (id, seq, table, from_col, to_col, on_update, on_delete, match)

        # We want exactly 2 foreign keys, one referencing 'Samples'
        if len(fk_list) == 2:
            ref_data = []
            for fk in fk_list:
                ref_data.append({
                    "parent_table": fk[2],  # the table referenced
                    "child_col": fk[3],  # column in this table
                    "parent_col": fk[4],  # column in parent_table
                })

            # Check if one references samples_table_name
            if any(rd["parent_table"] == samples_table_name for rd in ref_data):
                bridge_tables_info.append({
                    "bridge_table": table_name,
                    "refs": ref_data
                })

    return bridge_tables_info


###############################################################################
# ADDING PRIMARY KEYS TO A DICTIONARY
###############################################################################

def add_pk_from_rows(
        db: QSqlDatabase,
        table_name: str,
        rows: List[tuple],
        table_ids_dict: Dict[str, Set[int]]
):
    """
    For each row in `rows`, attempt to extract the single integer PK and
    insert it into `table_ids_dict[table_name]`.
    If the table does not have a single integer PK, we skip.
    """
    pk_info = get_single_integer_pk_col(db, table_name)
    if pk_info is None:
        if rows:
            print(f"WARNING: Table '{table_name}' has no single integer PK. Skipping ID collection.")
        return

    # pk_info is (index_in_table_info, col_name). But we need the column *index in each row*.
    # The order from "PRAGMA table_info" matches the order of columns returned by "SELECT *".
    pk_index = pk_info[0]

    # Add each PK value to our set
    for row in rows:
        pk_val = row[pk_index]
        if pk_val is not None:
            table_ids_dict.setdefault(table_name, set()).add(pk_val)


###############################################################################
# SUBSET MANY-TO-MANY BRIDGES: Collect IDs
###############################################################################

def subset_many_to_many_bridges_ids(
        conn_source: QSqlDatabase,
        sample_ids: Set[int],
        bridges_info: List[Dict[str, Any]],
        table_ids_dict: Dict[str, Set[int]],
        samples_table_name="Samples"
):
    """
    For each discovered bridge table referencing 'Samples' and another table,
    collect:
      - The bridge row PK IDs (if any),
      - The 'other' table's PK IDs
    based on the provided sample_ids.
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

        if not sample_ids:
            continue

        # 1) Fetch bridging rows for these sample_ids
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

        # Collect the PK of each bridging row
        add_pk_from_rows(conn_source, bridge_table, bridge_rows, table_ids_dict)

        # 2) Gather 'other' IDs from these bridging rows
        col_info_bridge = fetchall(f"PRAGMA table_info('{bridge_table}')", conn_source)
        col_names_bridge = [c[1] for c in col_info_bridge]
        if other_fk_col not in col_names_bridge:
            continue  # can't collect if we don't have the child's col

        other_idx = col_names_bridge.index(other_fk_col)
        other_ids = {row[other_idx] for row in bridge_rows if row[other_idx] is not None}

        # 3) Fetch the rows from the other table (so we can gather PKs)
        if other_ids:
            placeholder_2 = ",".join(["?"] * len(other_ids))
            other_rows = fetchall(
                f"""
                SELECT * FROM {other_table_name}
                WHERE {other_pk_col} IN ({placeholder_2})
                """,
                conn_source,
                tuple(other_ids)
            )

            # Collect PK from those 'other' table rows
            add_pk_from_rows(conn_source, other_table_name, other_rows, table_ids_dict)


###############################################################################
# KNOWN ONE-TO-MANY CHAIN: Samples -> Aliquots -> Spots -> UPbData
# plus references in UPbData to other tables
###############################################################################

def subset_one_to_many_chain_ids(
        conn_source: QSqlDatabase,
        sample_ids: Set[int],
        table_ids_dict: Dict[str, Set[int]]
):
    """
    Hardcoded logic for the known chain:
      Samples -> Aliquots -> Spots -> UPbData
    Then from each UPbData row, gather foreign keys to:
      References, Instruments, LabFacilities, UPbAnalysisMethod
    This function simply collects PKs that should be included.
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
    add_pk_from_rows(conn_source, "Aliquots", aliq_rows, table_ids_dict)

    # Collect AliquotIDs
    col_info_aliq = fetchall("PRAGMA table_info('Aliquots')", conn_source)
    col_names_aliq = [c[1] for c in col_info_aliq]
    if "AliquotID" in col_names_aliq:
        aliquot_id_idx = col_names_aliq.index("AliquotID")
        aliquot_ids = {row[aliquot_id_idx] for row in aliq_rows}
    else:
        aliquot_ids = set()

    # -------------------------------------------------------------------------
    # B) Spots referencing Aliquots
    # -------------------------------------------------------------------------
    if aliquot_ids:
        placeholder = ",".join(["?"] * len(aliquot_ids))
        spot_rows = fetchall(
            f"SELECT * FROM Spots WHERE AliquotID IN ({placeholder})",
            conn_source,
            tuple(aliquot_ids)
        )
        add_pk_from_rows(conn_source, "Spots", spot_rows, table_ids_dict)

        col_info_spots = fetchall("PRAGMA table_info('Spots')", conn_source)
        col_names_spots = [c[1] for c in col_info_spots]
        if "SpotID" in col_names_spots:
            spot_id_idx = col_names_spots.index("SpotID")
            spot_ids = {row[spot_id_idx] for row in spot_rows}
        else:
            spot_ids = set()
    else:
        spot_ids = set()

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
        add_pk_from_rows(conn_source, "UPbData", upbdata_rows, table_ids_dict)

        if upbdata_rows:
            col_info_upb = fetchall("PRAGMA table_info('UPbData')", conn_source)
            col_names_upb = [c[1] for c in col_info_upb]

            # We'll attempt to find these four FKs:
            #   [SourceID, InstrumentID, LabFacilityID, UPbAnalysisMethodID]
            needed_fk_cols = [
                ("Sources", "SourceID"),
                ("Instruments", "InstrumentID"),
                ("LabFacilities", "LabFacilityID"),
                ("UPbAnalysisMethod", "UPbAnalysisMethodID")
            ]

            # For each row, gather the IDs for each of these columns (if present)
            for (table_fk_name, col_fk_name) in needed_fk_cols:
                if col_fk_name in col_names_upb:
                    fk_idx = col_names_upb.index(col_fk_name)
                    fk_vals = {row[fk_idx] for row in upbdata_rows if row[fk_idx] is not None}
                    if fk_vals:
                        # Now fetch the actual rows from that table to get their PK
                        placeholder_fk = ",".join(["?"] * len(fk_vals))
                        fetched_fk_rows = fetchall(
                            f"SELECT * FROM {table_fk_name} WHERE {col_fk_name} IN ({placeholder_fk})",
                            conn_source,
                            tuple(fk_vals)
                        )
                        add_pk_from_rows(conn_source, table_fk_name, fetched_fk_rows, table_ids_dict)


###############################################################################
# DETECTING 'TREE' TABLES (HIERARCHIES)
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


def subset_tree_table_downstream_ids(
        conn_source: QSqlDatabase,
        table_name: str,
        parent_col: str,
        child_col: str,
        root_ids: Set[int],
        table_ids_dict: Dict[str, Set[int]]
):
    """
    Recursively gather all rows from 'table_name' that descend from 'root_ids'
    via parent_col -> child_col chain, then record their PK in `table_ids_dict`.
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
            f"SELECT * FROM {table_name} WHERE {parent_col} = ?",
            conn_source,
            (current_id,)
        )
        if rows:
            # Record their PK in our dictionary
            add_pk_from_rows(conn_source, table_name, rows, table_ids_dict)

            # Gather child IDs
            child_idx = col_names.index(child_col)
            new_child_ids = [r[child_idx] for r in rows if r[child_idx] is not None]
            to_visit.extend(new_child_ids)


###############################################################################
# MASTER FUNCTION: gather_ids_for_subset
###############################################################################

def gather_ids_for_subset(
        conn_source: QSqlDatabase,
        sample_ids: List[int]
) -> Dict[str, Set[int]]:
    """
    Collects (table_name -> set of PK IDs) that should be included for the
    given sample_ids, based on:
      - The specified Sample(s) in 'Samples',
      - Many-to-many bridging references to those samples,
      - The known one-to-many chain (Samples -> Aliquots -> Spots -> UPbData),
      - The foreign-key references in UPbData,
      - Optionally, any 'tree' tables that must be traversed downward.

    Returns a dictionary: {table_name: set_of_primary_key_values}.
    """
    table_ids_dict: Dict[str, Set[int]] = {}

    # 1) For each sample, collect its PK in table_ids_dict (assuming PK is SampleID).
    for sid in sample_ids:
        row = fetchall(
            "SELECT * FROM Samples WHERE SampleID = ?",
            conn_source,
            (sid,)
        )
        if not row:
            print(f"No Samples found with SampleID={sid}")
            continue
        add_pk_from_rows(conn_source, "Samples", row, table_ids_dict)

    # Convert the list to a set for repeated usage
    sample_ids_set = set(sample_ids)

    # 2) Find bridging tables
    bridges_info = find_bridge_tables(conn_source, "Samples")

    # 3) Subset bridging references
    subset_many_to_many_bridges_ids(
        conn_source,
        sample_ids_set,
        bridges_info,
        table_ids_dict,
        samples_table_name="Samples"
    )

    # 4) Known one-to-many chain: Samples -> Aliquots -> Spots -> UPbData
    subset_one_to_many_chain_ids(conn_source, sample_ids_set, table_ids_dict)

    # 5) Find tree tables (optional / schema-dependent usage)
    tree_tables = find_tree_tables(conn_source)
    # In practice, you'd figure out which tree tables matter, and how they link to 'Samples' or others.
    # Here is a simplified example that you'd adapt to your schema:
    #
    # For each tree table, if it has columns "ParentSomethingID" and "SomethingID",
    # we may want to pick certain "root_ids" from the table_ids_dict. This is
    # entirely up to your data model. The example below is just a placeholder:
    #
    for tinfo in tree_tables:
        tbl_name = tinfo["table_name"]
        col_info = fetchall(f"PRAGMA table_info('{tbl_name}')", conn_source)
        col_names = [c[1] for c in col_info]

        # Suppose the table name is "Hierarchy", with columns "HierarchyID" (PK),
        # and "ParentHierarchyID". We guess "Parent<tbl_base_name>ID" and
        # "<tbl_base_name>ID" is the PK. We'll do a naive approach:
        base_name = tbl_name[:-1]  # e.g. "Hierarchy" -> "Hierarch"
        parent_col = f"Parent{base_name}ID"
        child_col = f"{base_name}ID"
        if parent_col in col_names and child_col in col_names:
            # Let's define "root_ids" as any IDs we have *already*
            # decided to copy from this table. This implies that if we
            # have 5 known IDs in "Hierarchy" from prior steps, we'll
            # gather all their descendants, too:
            root_ids = table_ids_dict.get(tbl_name, set())
            if root_ids:
                subset_tree_table_downstream_ids(
                    conn_source=conn_source,
                    table_name=tbl_name,
                    parent_col=child_col,
                    child_col=parent_col,
                    root_ids=root_ids,
                    table_ids_dict=table_ids_dict
                )

    return table_ids_dict


###############################################################################
# EXAMPLE USAGE
###############################################################################

if __name__ == "__main__":

    src_db = "/Users/jarrodburges/Downloads/newschema.db"

    # 1. Open the source database
    conn_source = open_sqlite_db(src_db, "source_connection")

    # 2. Choose which SampleIDs you want
    sample_id_to_subset = [1]

    # 3. Collect all IDs that would be copied
    ids_dict = gather_ids_for_subset(conn_source, sample_id_to_subset)

    # 4. Print or inspect the dictionary of IDs
    for table_name, pk_set in ids_dict.items():
        print(f"Table {table_name}: {pk_set}")

    # 5. Close the DB connection
    conn_source.close()
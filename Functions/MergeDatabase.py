import sqlite3
from typing import Dict, List
from Functions.Widget_classes import get_name_column

import Functions.SQLUtils as SQLUtils
import logger_setup


def merge_database(source_db_path: str, incoming_db_path: str) -> bool:
    """
    Merge 'incoming_db_path' into 'source_db_path', handling self-referential
    'tree' tables by inserting parent rows first so the parent's new PK is known.
    :return: True if successful, False for failure.
    :rtype: bool
    """

    # ----------------------------------------------------------------
    # 1. Open the connections for both source and incoming, return errors and exit merge if failed
    # ----------------------------------------------------------------
    try:
        source_conn = sqlite3.connect(source_db_path)
        incoming_conn = sqlite3.connect(incoming_db_path)
    except sqlite3.Error as e:
        logger_setup.get_logger().critical(f"Error opening database: {e.sqlite_errorname}")
        logger_setup.get_logger().debug(f"Error: {e}")
        return False


    # For faster inserts
    source_conn.isolation_level = None
    incoming_conn.isolation_level = None

    source_conn.execute("PRAGMA foreign_keys = OFF;")
    source_conn.execute("BEGIN;")  # begin transaction

    # ----------------------------------------------------------------
    # 2. Utility: get tables, schema, detect PK column, detect FKs
    # ----------------------------------------------------------------
    def get_tables(conn: sqlite3.Connection) -> list[str] :
        """
        Gets all tables in the database, returning a list
        :param sqlite3.Connection conn:
        :return list[str]: list of all table names, exludes sqlite core tables
        """
        try:
            # get all tables in the database from the connection
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            ).fetchall()
        except sqlite3.Error as e:
            logger_setup.get_logger().critical(f"Error opening database and executing query: {e.sqlite_errorname}")
            logger_setup.get_logger().debug(f'SQl error: {e.__str__()}')
            raise e

        table_names = ["\"" + r[0] + "\"" for r in rows]
        for table in SQLUtils.static_tables:
            table = "\"" + table + "\""
            if table in table_names:
                table_names.remove(table)
        return [t for t in table_names if not t.startswith("sqlite_")]

    def get_table_info(conn: sqlite3.Connection, table: str):
        """
        Pragmas the given connection for information on the table.
         Each row returned: (cid, name, type, notnull, dflt_value, pk)
        :param sqlite3.Connection conn:
        :param str table:
        :return list[dict[]]: list of dictionaries containing all table info from pragma
        """
        try:
            info = []
            for row in conn.execute(f"PRAGMA table_info({table});"):
                cid, name, ctype, notnull, dflt_value, pk = row
                if "Calculated" not in name:
                    info.append({
                        "cid": cid,
                        "name": "[" + name + "]",  # escape names
                        "type": ctype,
                        "notnull": notnull,
                        "dflt_value": dflt_value,
                        "pk": pk
                    })
            return info

        except sqlite3.Error as e:
            logger_setup.get_logger().critical(f'Error acquiring foreign key list: {e.sqlite_errorname}')
            logger_setup.get_logger().debug(f'SQl error: {e.__str__()}')
            raise e

    def get_foreign_key_info(conn: sqlite3.Connection, table: str):
        """
        Pragmas the given connection for information on the table.
         Each row returned: (id, seq, ref_table, from_col, to_col, on_update, on_delete, match)
        :param sqlite3.Connection conn:
        :param str table:
        :return list[dict[]]: list of dictionaries containing all table info from pragma
        """
        try:
            fks = []
            for row in conn.execute(f"PRAGMA foreign_key_list({table});"):
                fks.append({
                    "id": row[0],
                    "seq": row[1],
                    "ref_table": '\"' + row[2].replace('_old','') + '\"',
                    "from_col": "[" + row[3] + "]",
                    "to_col": "[" + row[4] + "]",
                    "on_update": row[5],
                    "on_delete": row[6],
                    "match": row[7]
                })
            return fks
        except sqlite3.Error as e:
            logger_setup.get_logger().critical(f'Error acquiring foreign key list: {e.sqlite_errorname}')
            logger_setup.get_logger().debug(f'SQl error: {e.__str__()}')
            raise e


    try:
        source_tables = get_tables(source_conn)
        incoming_tables = get_tables(incoming_conn)
    except Exception as e:
        return False

    # We assume identical sets of tables:
    common_tables = sorted(set(source_tables) & set(incoming_tables))

    # Build schema metadata
    table_schemas = {}
    for t in common_tables:
        try:
            info = get_table_info(source_conn, t)
            fks = get_foreign_key_info(source_conn, t)
        except Exception as e:
            return False

        pk_cols = [c["name"] for c in info if c["pk"] == 1]
        pk_col = pk_cols[0] if pk_cols else None

        table_schemas[t] = {
            "columns": info,
            "fks": fks,
            "primary_key": pk_col
        }

    # ----------------------------------------------------------------
    # 3. Identify which tables are "self-referential" aka Trees
    #    i.e., the table references itself in a foreign_key.
    # ----------------------------------------------------------------
    #
    # We'll also record the "parent_col" so we know which column references the PK.
    self_ref_tables = {}  # table_name -> from_col (that references itself)
    for table in SQLUtils.user_viewable_trees:
        if table in SQLUtils.static_tables:
            continue
        self_ref_tables["\"" + table + "\""] = {"parent_fk_col": "[Parent" + table[0:-1] + "ID]"}
    normal_tables = []
    mtm_tables = []
    fk_tables = []

    bridging_fks = {}

    for t in common_tables:
        schema = table_schemas[t]
        pk_col = schema["primary_key"]
        fks = schema["fks"]

        distinct_refs = set(fk["ref_table"].lower() for fk in fks)

        # Is there a foreign key that references the same table 't'?
        self_ref_fk = None
        for fk in fks:
            if fk["ref_table"].lower() == t.lower():
                # Found a self-reference
                self_ref_fk = fk
                break

        if self_ref_fk:
            self_ref_tables[t] = {
                "parent_fk_col": self_ref_fk["from_col"],  # e.g. "ParentFooID"
            }
        elif "_" in t and len(distinct_refs) == 2 and all(fk["ref_table"].lower() != t.lower() for fk in fks):
            mtm_tables.append(t)
            bridging_fks[t] = []
            for fk in fks:
                bridging_fks[t].append((fk["from_col"], fk["ref_table"]))
        elif t.replace("\"","")  in SQLUtils.foreign_key_tables:
            fk_tables.append(t)
        elif t.replace("\"","") not in SQLUtils.user_viewable_trees:
            normal_tables.append(t)

    # ----------------------------------------------------------------
    # 4. ID mapping: store old_pk -> new_pk for each table
    # ----------------------------------------------------------------
    id_map = {t: {} for t in common_tables}

    # ----------------------------------------------------------------
    # 5. Insertion function for normal (non-self-ref) tables
    # ----------------------------------------------------------------
    def merge_non_self_ref_table(table_name: str) -> bool:
        """
        Merge rows from the incoming DB to source DB, ignoring the old PK
        (letting source auto-generate) but preserving all other columns.
        :param str table_name:
        :return: True for success, False for failure
        """

        schema = table_schemas[table_name]
        pk_col = schema["primary_key"]
        col_names = [c["name"] for c in schema["columns"]]

        # SELECT all rows from incoming
        col_list_str = ", ".join(col_names)
        select_sql = f"SELECT {col_list_str} FROM {table_name};"

        try:
            incoming_rows = incoming_conn.execute(select_sql).fetchall()
        except sqlite3.Error as e:
            logger_setup.get_logger().critical(
                f'Could not select largest parent row for null parents: {e.sqlite_errorname}')
            logger_setup.get_logger().debug(f'SQL error: {e.__str__()}')
            logger_setup.get_logger().debug(f"SQL command: {select_sql}")
            return False


        # Prepare insert statement skipping pk_col
        insert_cols = [c for c in col_names if c != pk_col]
        insert_cols_str = ", ".join(insert_cols)
        placeholders_str = ", ".join("?" for _ in insert_cols)
        insert_sql = f"""INSERT INTO {table_name} ({insert_cols_str})
                         VALUES ({placeholders_str});"""

        for row in incoming_rows:
            row_dict = dict(zip(col_names, row))
            old_pk_val = row_dict[pk_col] if pk_col else None

            # We do not re-map foreign keys here. A robust approach would also
            # fix references to other tables if needed. This snippet is for
            # demonstration. (See prior code for rewriting foreign keys.)
            # Insert values minus pk
            to_insert = [row_dict[c] for c in insert_cols]

            if table_name == '"References"':
                name_index = 1
            elif table_name != '"UPbAnalyses"':
                name_index = get_name_column(table_name) - 1

            # while loop to constantly try new values to insert into the table in case
            # there are duplicate entries, such as source db and incoming db RockTypeName = "Sandstone"
            # the incoming db RockTypeName would change to append '(1)' creating "Sandstone (1).
            # todo: Change to increment rather than append, so '(1)(1)' would becoming '(2)'
            while True:
                try:
                    source_conn.execute(insert_sql, to_insert)
                    break  # success: break out of loop
                except sqlite3.Error as e:
                    if "UNIQUE constraint failed" in str(e):
                        current_value = str(to_insert[name_index])
                        to_insert[name_index] = current_value + '(1)'
                    else:
                        logger_setup.get_logger().critical(
                            f'Could not insert row into database: {e.sqlite_errorname}')
                        logger_setup.get_logger().debug(f'SQL error: {e.__str__()}')
                        logger_setup.get_logger().debug(f"SQL command: {insert_sql}")
                        logger_setup.get_logger().debug(f'SQL row: {to_insert}')
                        return False

            # Retrieve new pk
            if pk_col:
                try:
                    new_pk_val = source_conn.execute("SELECT last_insert_rowid();").fetchone()[0]
                except sqlite3.Error as e:
                    logger_setup.get_logger().critical(f'Error acquiring last insert primary key: {e.sqlite_errorname}')
                    logger_setup.get_logger().debug(f'SQl error: {e.__str__()}')
                    return False

                id_map[table_name][old_pk_val] = new_pk_val
        return True

    # ----------------------------------------------------------------
    # 6. Merge a self-referential "tree" table
    # ----------------------------------------------------------------
    def merge_self_ref_table(table_name: str) -> bool:
        """
        For a table that references itself in a parent-child relationship, we do multiple passes or a BFS approach:
          - Insert all rows with no parent (NULL or 0).
          - Then insert rows whose parent is already inserted.
          - Repeat until all are inserted.
        :param str table_name:
        :return: True for success, False for failure
        """

        schema = table_schemas[table_name]
        pk_col = schema["primary_key"]
        parent_fk_col = self_ref_tables[table_name]["parent_fk_col"]
        col_names = [c["name"] for c in schema["columns"]]

        # Read all rows from incoming
        col_list_str = ", ".join(col_names)
        select_sql = f"SELECT {col_list_str} FROM {table_name};"
        try:
            all_rows = incoming_conn.execute(select_sql).fetchall()
        except sqlite3.Error as e:
            logger_setup.get_logger().critical(f'Could not select rows from database: {e.sqlite_errorname}')
            logger_setup.get_logger().debug(f'SQL error: {e.__str__()}')
            logger_setup.get_logger().debug(f"SQL command: {select_sql}")
            return False

        # Convert to dict: old_pk -> row_dict
        incoming_dict = {}
        for row in all_rows:
            row_dict = dict(zip(col_names, row))
            old_pk = row_dict[pk_col]
            incoming_dict[old_pk] = row_dict

        # We'll track which rows are "inserted" in the source
        inserted = set()

        # Prepare the insert statement (skipping pk_col)
        insert_cols = [c for c in col_names if c != pk_col]
        insert_cols_str = ", ".join(insert_cols)
        placeholders_str = ", ".join("?" for _ in insert_cols)
        insert_sql = f"""
            INSERT INTO {table_name} ({insert_cols_str})
            VALUES ({placeholders_str});
        """

        try:
            parentrow_sql = f"SELECT MAX({insert_cols[1]}) FROM {table_name} WHERE {insert_cols[0]} is NULL;"
            largest_null_parentrow = source_conn.execute(parentrow_sql).fetchone()[0]
            if largest_null_parentrow is None:
                largest_null_parentrow = -1
        except sqlite3.Error as e:
            logger_setup.get_logger().critical(
                f'Could not select largest parent row for null parents: {e.sqlite_errorname}')
            logger_setup.get_logger().debug(f'SQL error: {e.__str__()}')
            logger_setup.get_logger().debug(f"SQL command: {parentrow_sql}")
            return False

        # Repeatedly scan all rows; insert any row whose parent is inserted or NULL
        # Keep going until no more can be inserted.
        # (Assumes no cycles, i.e., it's a true tree.)
        rows_to_insert = set(incoming_dict.keys())  # all old pks
        progress = True

        while progress and rows_to_insert:
            progress = False
            # We'll build a list of old PKs that we successfully insert in this pass
            inserted_this_round = []

            for old_pk in rows_to_insert:
                row_dict = incoming_dict[old_pk]
                parent_old_id = row_dict[parent_fk_col]

                # Condition: if parent is None (or 0) or the parent is already in 'inserted'
                # we can safely insert
                # (Adjust the condition if your schema uses a different "no parent" sentinel.)
                if parent_old_id is None or parent_old_id == 0 or parent_old_id in inserted:
                    # Let's do the insert
                    # Build the row minus the PK
                    row_for_insert = {}
                    for c in insert_cols:
                        row_for_insert[c] = row_dict[c]
                    if row_for_insert[list(row_for_insert.keys())[0]] is None:
                        row_for_insert[list(row_for_insert.keys())[1]] = largest_null_parentrow + 1
                    # Also fix the parent's PK if we have a mapping
                    if parent_old_id and parent_old_id in id_map[table_name]:
                        row_for_insert[parent_fk_col] = id_map[table_name][parent_old_id]
                    else:
                        # parent is None or we haven't inserted that parent yet
                        row_for_insert[parent_fk_col] = None if parent_old_id else None

                    # Insert
                    to_insert = [row_for_insert[c] for c in insert_cols]

                    # while loop to constantly try new values to insert into the table in case
                    # there are duplicate entries, such as source db and incoming db RockTypeName = "Sandstone"
                    # the incoming db RockTypeName would change to append '(1)' creating "Sandstone (1).
                    # todo: Change to increment rather than append, so '(1)(1)' would becoming '(2)'
                    while True:
                        try:
                            source_conn.execute(insert_sql, to_insert)
                            break  # success: break out of loop
                        except sqlite3.IntegrityError as e:
                            if "UNIQUE constraint failed" in str(e):
                                # We got a uniqueness collision, so increment or append '(1)'
                                current_value = str(to_insert[2])
                                to_insert[2] = current_value + '(1)'
                            else:
                                logger_setup.get_logger().critical(
                                    f'Could not insert row into database: {e.sqlite_errorname}')
                                logger_setup.get_logger().debug(f'SQL error: {e.__str__()}')
                                logger_setup.get_logger().debug(f"SQL command: {insert_sql}")
                                logger_setup.get_logger().debug(f'SQL row: {to_insert}')
                                return False

                    # Get new PK
                    try:
                        new_pk_val = source_conn.execute("SELECT last_insert_rowid();").fetchone()[0]
                    except sqlite3.Error as e:
                        logger_setup.get_logger().critical(
                            f'Error acquiring last insert primary key: {e.sqlite_errorname}')
                        logger_setup.get_logger().debug(f'SQl error: {e.__str__()}')
                        return False

                    id_map[table_name][old_pk] = new_pk_val

                    # Mark it inserted
                    inserted_this_round.append(old_pk)

            # After scanning all rows_to_insert, remove what we inserted
            if inserted_this_round:
                progress = True
                for pk in inserted_this_round:
                    inserted.add(pk)
                    rows_to_insert.remove(pk)
        return True

        # If rows_to_insert is still not empty, it might indicate a cycle
        # or references to a parent that doesn't exist. For a real "tree," we expect
        # everything to eventually get inserted.

    def merge_m2m_bridge_table(table_name: str) -> bool:
        """
        M2M table referencing exactly 2 other distinct tables.
        We'll read all rows from incoming, rewrite the FK columns
        to point to the new IDs from id_map, and insert them.
        If the table has its own PK, we skip it as usual so new PK is assigned.
        :param table_name:
        :return: True for success, False for failure
        """

        schema = table_schemas[table_name]
        pk_col = schema["primary_key"]
        all_cols = [c["name"] for c in schema["columns"]]

        # foreign keys
        fk_pairs = bridging_fks[table_name]
        # e.g. [ (from_col1, ref_table1), (from_col2, ref_table2) ]

        # read all from incoming
        col_list_str = ", ".join(all_cols)
        select_sql = f"SELECT {col_list_str} FROM {table_name};"
        try:
            rows = incoming_conn.execute(select_sql).fetchall()
        except sqlite3.Error as e:
            logger_setup.get_logger().critical(f'Could not select rows from database: {e.sqlite_errorname}')
            logger_setup.get_logger().debug(f'SQL error: {e.__str__()}')
            logger_setup.get_logger().debug(f"SQL command: {select_sql}")
            return False

        # We'll skip the bridging table's PK column (if any) so it re-generates
        insert_cols = [c for c in all_cols if c != pk_col]
        insert_cols_str = ", ".join(insert_cols)
        placeholders_str = ", ".join("?" for _ in insert_cols)
        insert_sql = f"""
            INSERT INTO {table_name} ({insert_cols_str})
            VALUES ({placeholders_str});
        """

        for row in rows:
            row_dict = dict(zip(all_cols, row))

            # rewrite each referencing column
            for (from_col, ref_table) in fk_pairs:
                old_fk_val = row_dict[from_col]
                if old_fk_val is not None:
                    # get the new ID from id_map
                    if old_fk_val in id_map[ref_table]:
                        row_dict[from_col] = id_map[ref_table][old_fk_val]
                    else:
                        # e.g. if it didn't exist, or wasn't inserted
                        row_dict[from_col] = None

            # Build final insert dict minus PK
            to_insert = []
            for c in insert_cols:
                to_insert.append(row_dict[c])

            try:
                source_conn.execute(insert_sql, to_insert)
            except sqlite3.Error as e:
                if "UNIQUE constraint failed" in e.__str__():
                    logger_setup.get_logger().info(f"Relationship already in table {table_name}. Skipping")
                    logger_setup.get_logger().debug(f"{to_insert}")
                elif "NOT NULL constraint failed" in e.__str__():
                    # removes 'orphaned' data
                    logger_setup.get_logger().info(f"One of the {table_name} does not exist in the original or merged database. Skipping")
                    logger_setup.get_logger().debug(f"{to_insert}")
                else:
                    logger_setup.get_logger().critical(f'Could not insert row into database: {e.sqlite_errorname}')
                    logger_setup.get_logger().debug(f'SQL error: {e.__str__()}')
                    logger_setup.get_logger().debug(f"SQL command: {insert_sql}")
                    logger_setup.get_logger().debug(f'SQL row: {to_insert}')
                    return False

            # If bridging table has a PK, update the map
            # (Often bridging tables might not need an id_map, but let's keep it consistent)
            if pk_col:
                old_pk_val = row_dict[pk_col]
                try:
                    new_pk_val = source_conn.execute("SELECT last_insert_rowid();").fetchone()[0]
                except sqlite3.Error as e:
                    logger_setup.get_logger().critical(f'Error acquiring last insert primary key: {e.sqlite_errorname}')
                    logger_setup.get_logger().debug(f'SQl error: {e.__str__()}')
                    return False

                id_map[table_name][old_pk_val] = new_pk_val
        return True

    def merge_table_with_foreign_keys(table_name: str):
        """
        Merges data from incoming -> source for table `table_name`,
        rewriting foreign keys from old IDs to new IDs using `id_map`.
        If the table has its own PK, skip that column so the source auto-generates
        a new PK, and record old_pk->new_pk in id_map.
        :param str table_name:
        """

        schema = table_schemas[table_name]
        pk_col = schema["primary_key"]
        all_cols = [c["name"] for c in schema["columns"]]
        fks = schema["fks"]

        # We'll read all rows from incoming
        col_list_str = ", ".join(all_cols)
        select_sql = f"SELECT {col_list_str} FROM {table_name};"
        try:
            incoming_rows = incoming_conn.execute(select_sql).fetchall()
        except sqlite3.Error as e:
            logger_setup.get_logger().critical(f'Could not select rows from database: {e.sqlite_errorname}')
            logger_setup.get_logger().debug(f'SQL error: {e.__str__()}')
            logger_setup.get_logger().debug(f"SQL command: {select_sql}")
            return False

        # Prepare an INSERT statement for all columns except the PK
        insert_cols = [c for c in all_cols if c != pk_col]
        insert_cols_str = ", ".join(insert_cols)
        placeholders_str = ", ".join("?" for _ in insert_cols)
        insert_sql = f"""
            INSERT INTO {table_name} ({insert_cols_str})
            VALUES ({placeholders_str});
        """

        # Merge each row
        for row in incoming_rows:
            row_dict = dict(zip(all_cols, row))
            old_pk_val = row_dict[pk_col] if pk_col else None

            # For each foreign key, rewrite the column
            for fk in fks:
                ref_table = fk["ref_table"]  # e.g. "Samples"
                if ref_table.replace('"', '') in SQLUtils.static_foreign_key_tables:
                    continue

                from_col = fk["from_col"]  # e.g. "SampleID"
                to_col = fk["to_col"]  # typically the PK of the referenced table

                old_fk_val = row_dict[from_col]
                if old_fk_val is None:
                    continue  # no reference to rewrite

                # Lookup the new ID
                # If the ref_table was already merged, we have id_map[ref_table]
                if old_fk_val in id_map[ref_table]:
                    new_fk_val = id_map[ref_table][old_fk_val]
                    row_dict[from_col] = new_fk_val
                else:
                    # Possibly the row wasn't inserted, or some special case
                    # We'll set it to None or handle differently
                    row_dict[from_col] = None

            # Build the tuple of values to insert (excluding pk)
            to_insert = []
            for c in insert_cols:
                to_insert.append(row_dict[c])

            if table_name == '"References"':
                name_index = 1
            elif table_name != '"UPbAnalyses"':
                name_index = get_name_column(table_name) - 1

            while True:
                try:
                    source_conn.execute(insert_sql, to_insert)
                    break  # success: break out of loop
                except sqlite3.IntegrityError as e:
                    if "UNIQUE constraint failed" in str(e):
                        # We got a uniqueness collision, so increment or append '(1)'
                        current_value = str(to_insert[name_index])
                        to_insert[name_index] = current_value + '(1)'
                    elif "NOT NULL constraint failed" in str(e):
                        logger_setup.get_logger().info(f'{str(e)}')
                        logger_setup.get_logger().debug(f"{to_insert}")
                        break
                    else:
                        # It's another error we don't want to handle here; re-raise
                        raise

            # If this table has a PK, record old->new in id_map
            if pk_col:
                try:
                    new_pk_val = source_conn.execute("SELECT last_insert_rowid();").fetchone()[0]
                except sqlite3.Error as e:
                    logger_setup.get_logger().critical(f'Error acquiring last insert primary key: {e.sqlite_errorname}')
                    logger_setup.get_logger().debug(f'SQl error: {e.__str__()}')
                    return False
                id_map[table_name][old_pk_val] = new_pk_val
        return True

    def merge_self_ref_table_with_foreign_keys(table_name: str) -> bool:
        """
        For a self-referencing table (i.e. table that references itself in a
        parent->child relationship), merge data from incoming -> source.

        Similar to merge_table_with_foreign_keys, but we do multiple passes (BFS)
        so that a child row is only inserted after its parent is inserted.
        Also rewrites other foreign keys the same way we do in merge_table_with_foreign_keys.

        :param table_name: e.g. '"RockTypes"'
        :return: True if success, False otherwise
        """

        schema = table_schemas[table_name]
        pk_col = schema["primary_key"]
        parent_fk_col = self_ref_tables[table_name]["parent_fk_col"]
        col_names = [c["name"] for c in schema["columns"]]
        fks = schema["fks"]

        # 1) Read all rows from incoming
        col_list_str = ", ".join(col_names)
        select_sql = f"SELECT {col_list_str} FROM {table_name};"
        try:
            all_rows = incoming_conn.execute(select_sql).fetchall()
        except sqlite3.Error as e:
            logger_setup.get_logger().critical(f'[{table_name}] Could not select rows from DB: {e.sqlite_errorname}')
            logger_setup.get_logger().debug(f'SQL error: {e}')
            logger_setup.get_logger().debug(f"SQL command: {select_sql}")
            return False

        # Convert to dict: old_pk -> row_dict
        incoming_dict = {}
        for row in all_rows:
            row_dict = dict(zip(col_names, row))
            old_pk = row_dict[pk_col]
            incoming_dict[old_pk] = row_dict

        inserted = set()  # which old PKs have been inserted
        rows_to_insert = set(incoming_dict.keys())  # all old PKs that need insertion

        # 2) Prepare the insert statement (skipping pk_col)
        insert_cols = [c for c in col_names if c != pk_col]
        insert_cols_str = ", ".join(insert_cols)
        placeholders_str = ", ".join("?" for _ in insert_cols)
        insert_sql = f"""
            INSERT INTO {table_name} ({insert_cols_str})
            VALUES ({placeholders_str});
        """

        # Helper to rewrite foreign keys for a single row_dict
        # including other foreign keys + the self-ref parent
        def rewrite_foreign_keys_for_self_ref(row_dict):
            # (a) rewrite normal foreign keys
            for fk in fks:
                ref_table = fk["ref_table"]
                if ref_table.replace('"', '') in SQLUtils.static_foreign_key_tables:
                    continue

                from_col = fk["from_col"]
                old_val = row_dict[from_col]
                if old_val is None:
                    continue
                if old_val in id_map[ref_table]:
                    row_dict[from_col] = id_map[ref_table][old_val]
                else:
                    row_dict[from_col] = None

            # (b) rewrite the self parent foreign key
            parent_old_id = row_dict[parent_fk_col]
            if parent_old_id and parent_old_id in id_map[table_name]:
                row_dict[parent_fk_col] = id_map[table_name][parent_old_id]
            else:
                # If parent's not inserted or is 0, set to None
                if not parent_old_id or parent_old_id == 0:
                    row_dict[parent_fk_col] = None

        # Attempt BFS insertion
        progress = True
        while progress and rows_to_insert:
            progress = False
            inserted_this_pass = []

            for old_pk in list(rows_to_insert):
                row_dict = incoming_dict[old_pk]
                parent_old_id = row_dict[parent_fk_col]

                # Condition: if parent is None (or 0) or parent is already inserted
                if parent_old_id is None or parent_old_id == 0 or parent_old_id in inserted:
                    # rewrite foreign keys (including the self-ref parent)
                    rewrite_foreign_keys_for_self_ref(row_dict)

                    # Build the row minus the PK
                    to_insert = [row_dict[c] for c in insert_cols]

                    # If you have a name column for collisions, find its index:
                    try:
                        name_index = get_name_column(table_name) - 1
                        # Adjust for skipping pk_col if pk_col's index < name_index
                        # but let's keep it simple if your code assumes it is the second or third column
                    except:
                        name_index = None

                    # Attempt the insert (handle collisions by appending "(1)")
                    while True:
                        try:
                            source_conn.execute(insert_sql, to_insert)
                            break
                        except sqlite3.IntegrityError as e:
                            err_str = str(e)
                            if "UNIQUE constraint failed" in err_str and name_index is not None and 0 <= name_index < len(
                                    to_insert):
                                current_value = str(to_insert[name_index])
                                to_insert[name_index] = current_value + "(1)"
                            else:
                                logger_setup.get_logger().critical(f'[{table_name}] Could not insert row: {e.sqlite_errorname}')
                                logger_setup.get_logger().debug(f'SQL error: {e}')
                                logger_setup.get_logger().debug(f"SQL command: {insert_sql}")
                                logger_setup.get_logger().debug(f"Row data: {to_insert}")
                                return False

                    # If table has a PK, fetch the new PK
                    if pk_col:
                        try:
                            new_pk_val = source_conn.execute("SELECT last_insert_rowid();").fetchone()[0]
                        except sqlite3.Error as e:
                            logger_setup.get_logger().critical(f"[{table_name}] Error acquiring last_insert_rowid: {e.sqlite_errorname}")
                            logger_setup.get_logger().debug(f"SQL error: {e}")
                            return False
                        # record old_pk->new_pk
                        id_map[table_name][old_pk] = new_pk_val

                    inserted.add(old_pk)
                    inserted_this_pass.append(old_pk)

            if inserted_this_pass:
                for pk_val in inserted_this_pass:
                    rows_to_insert.remove(pk_val)
                progress = True

        if rows_to_insert:
            # Some rows never got inserted, possibly cyclical references or a missing parent
            logger_setup.get_logger().critical(f"[{table_name}] Not all rows were inserted. Possibly a cycle. Remaining: {rows_to_insert}")

        return True

    # ----------------------------------------------------------------
    # 7. Merge logic, tables are merged in an ordered way. Tables with no related data from other tables are merged
    # first, then tables that are least to most related.
    # ----------------------------------------------------------------

    all_tables = SQLUtils.database_ordered_tables
    for t in all_tables:
        t = f'"{t}"'
        logger_setup.get_logger().info(f"Merging table {t}")
        if t == '"Aliquots"':
            if not merge_self_ref_table_with_foreign_keys(t):
                return False
            continue
        elif t in normal_tables:
            if not merge_non_self_ref_table(t):
                return False
        elif t in self_ref_tables.keys():
            if not merge_self_ref_table(t):
                return False
        elif t in fk_tables:
            if not merge_table_with_foreign_keys(t):
                return False
        elif t in mtm_tables:
            if not merge_m2m_bridge_table(t):
                return False

    # ----------------------------------------------------------------
    # 8. Commit and re-enable foreign_keys
    # ----------------------------------------------------------------

    source_conn.execute("COMMIT;")
    source_conn.execute("PRAGMA foreign_keys = ON;")

    # Close
    source_conn.close()
    incoming_conn.close()

    logger_setup.get_logger().info('Merged successfully')
    return True


if __name__ == "__main__":
    # Example usage:
    # SOURCE_DB = r"/Users/jarrodburges/Downloads/merge test/geochron.db"
    # INCOMING_DB = r"/Users/jarrodburges/Downloads/merge test/klam.db"

    SOURCE_DB = r"C:\Users\jburges\Downloads\db merge\klam2.db"
    INCOMING_DB = r"C:\Users\jburges\Downloads\db merge\klam.db"

    # SOURCE_DB = r"/Users/kametcalf/Documents/Research/GeoChron_non_git/GeoChron v.0.db"
    # INCOMING_DB = r"/Users/kametcalf/Documents/Research/GeoChronology_Code/dec_schema.db"

    merge_database(SOURCE_DB, INCOMING_DB)
import json
import re
from collections import defaultdict
from typing import List, Tuple, Dict

from Functions import SQLUtils
import logger_setup


def process_json_to_sql(json_string, scope):
    """
    Converts a structured JSON string representing a filter group to a SQL WHERE clause.
    """
    logger_setup.get_logger().debug(f'Processing with scope: {scope}: {json_string}')
    json_string = json_string.replace("'", "\"")
    group = json.loads(json_string)
    where_clause, ctes = process_group(group)

    sql = ''
    if len(ctes) > 0:
        sql += "WITH " + ",\n".join(ctes) + "\n"

    table_names = process_table_names(group)
    join = SQLUtils.get_join_from_table("", table_names)

    def extract_as_tables(join):
        as_tables = None
        select_tables = None
        where_tables = None
        if ' AS ' in join:
            pattern = r'\s+\bAS\s+(\w+)'  # regex pattern to match ' AS ' and return the table name right after it
            as_tables = re.findall(pattern, join)
        if '.[' in where_clause:
            pattern = r'\b(\w+)\.\['  # regex pattern to match the table name before '.['
            where_tables = re.findall(pattern, where_clause)
        return as_tables, select_tables, where_tables

    as_tables, select_tables, where_tables = extract_as_tables(join)
    if as_tables is not None:
        for as_table in as_tables:
            replace_table = SQLUtils.as_table_dict[as_table]
            if replace_table in where_tables:
                where_clause = where_clause.replace(replace_table, as_table)
    if not where_clause.startswith('GROUP BY') and where_clause.strip():
        where_clause = 'WHERE ' + where_clause

    if scope == 'Samples':
        sql += f"SELECT * FROM Samples {join} {where_clause};"
    elif scope == 'Aliquots':
        join = SQLUtils.get_join_from_table(join, ['Aliquots'])
        sql += f"SELECT * FROM Samples {join} {where_clause};"
    elif scope == 'Spots':
        join = SQLUtils.get_join_from_table(join, ['Spots'])
        sql += f"SELECT * FROM Samples {join} {where_clause};"
    elif scope == 'UPbAnalyses':
        join = SQLUtils.get_join_from_table(join, ['UPbAnalyses'])
        sql += f"SELECT * FROM Samples {join} {where_clause};"
    else:
        logger_setup.get_logger().critical(f"Unknown scope: {scope}")
    logger_setup.get_logger().debug(f"SQL generated successfully: {sql}")
    return sql, ctes


def process_table_names(data):
    table_names = set()

    def collect_table_names(group):
        conditions = group.get('conditions', [])
        subgroups = group.get('subgroups', [])
        for condition in conditions:
            field = condition['field']
            table_name = extract_table_name(field)
            if table_name:
                table_names.add(table_name)
        for subgroup in subgroups:
            collect_table_names(subgroup)

    collect_table_names(data)
    logger_setup.get_logger().debug(f'Collected table names: {table_names}')
    return table_names


def extract_table_name(field: str):
    """
    Helper function to extract the table name from a field string.
    :param str field: field in the format of table_name.[attribute_name]
    :return:
    """
    if '.' in field:
        parts = field.split('.')
        return parts[0]
    else:
        return None


def process_group(group: dict) -> Tuple[str, List[str]]:
    """Recursively walk the *group tree* and return (WHERE‑SQL, list‑of‑CTEs)."""

    recursive_tables_counter: Dict[str, int] = defaultdict(int)

    condition_strings, ctes = _process_group_inner(group, recursive_tables_counter)

    match group["type"].lower():
        case "match all":
            glue = " AND "
            where_sql = glue.join(condition_strings)
        case "match any":
            glue = " OR "
            where_sql = glue.join(condition_strings)
        case "match none":
            glue = " AND "
            where_sql = f"NOT {glue.join(condition_strings)}"
        case _:
            raise ValueError(f"Unknown group type: {group['type']}")

    return where_sql, ctes


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _process_group_inner(group: dict, recursive_tables: Dict[str, int]) -> Tuple[List[str], List[str]]:
    """Return (*condition list*, *cte list*) for **one** group (recursive)."""

    # 1) Split conditions: identical field → bucket; else → other list
    identical_field_buckets: Dict[str, List[str]] = defaultdict(list)
    other_conditions: List[str] = []
    ctes: List[str] = []

    for condition in group.get("conditions", []):
        sql_fragment, new_ctes, field_key = _build_single_condition(condition, recursive_tables)
        ctes.extend(new_ctes)

        if group["type"].lower() == "match all" or group["type"].lower() == "match none":
            identical_field_buckets[field_key].append(sql_fragment)
        else:
            other_conditions.append(sql_fragment)

    # 2) Collapse *identical‑field* buckets
    for field_key, conds in identical_field_buckets.items():
        if len(conds) == 1:
            other_conditions.append(conds[0])
            continue

        # --------- special handling: need **all** values on same many‑to‑many
        meta = SQLUtils.tree_tables_schema.get(field_key)
        if meta is None:
            # Non‑tree flat table – fallback to HAVING technique
            collapsed = _collapse_same_field_basic(conds, len(conds))
        else:
            # Tree table (RockTypes, etc.) – build EXISTS per value to enforce AND
            collapsed = f" {'OR' if group["type"].lower() == "match any" else 'AND'} ".join(conds)
        other_conditions.append(collapsed)

    # 3) Sub‑groups ----------------------------------------------------------
    for subgroup in group.get("subgroups", []):
        sub_conds, sub_ctes = _process_group_inner(subgroup, recursive_tables)
        if sub_conds:
            sub_sql = f" {'OR' if subgroup["type"].lower() == "match any" else 'AND'} ".join(sub_conds)
            logic = subgroup["type"].lower()
            if logic == "match all":
                other_conditions.append(f"({sub_sql})")
            elif logic == "match any":
                other_conditions.append(f"({sub_sql})")
            elif logic == "match none":
                other_conditions.append(f"NOT ({sub_sql})")
        ctes.extend(sub_ctes)

    return other_conditions, ctes

def _build_single_condition(condition: dict, recursive_tables: Dict[str, int]) -> Tuple[str, List[str], str]:
    """Return (sql_fragment, new_ctes_list, field_key)."""

    field_key: str = condition["field"].replace(" ", "")
    value = condition["value"]
    operator_raw: str = condition["operator"].lower()
    datatype: str = condition["datatype"]

    if datatype in {"relativeage", "directage", "bothage", "ages"}:
        return _build_age_condition(condition)

    operator_sql: str | List[str]
    # ---------- operator mapping (trimmed to the set used in UI) ----------
    if operator_raw in {"is", "is on"}:
        if datatype == "date":
            # build special date condition, since we only input the date, add a LIKE '2025-01-01%' so it queries right
            operator_sql = f"LIKE '{value}%'"
        else:
            operator_sql = "="
    elif operator_raw in {"is not", "is not on"}:
        if datatype == "date":
            # build special date condition, since we only input the date, add a LIKE '2025-01-01%' so it queries right
            operator_sql = f"NOT LIKE '{value}%'"
        else:
            operator_sql = "!="
    elif operator_raw == "is blank":
        operator_sql = "IS NULL"
    elif operator_raw == "is not blank":
        operator_sql = "IS NOT NULL"
    elif operator_raw == "contains":
        operator_sql = f"LIKE '%{value}%' COLLATE NOCASE"
    elif operator_raw == "does not contain":
        operator_sql = f"NOT LIKE '%{value}%' COLLATE NOCASE"
    elif operator_raw == "starts with":
        operator_sql = f"LIKE '{value}%' COLLATE NOCASE"
    elif operator_raw == "ends with":
        operator_sql = f"LIKE '%{value}' COLLATE NOCASE"
    elif operator_raw in {"is less than", "is before"}:
        operator_sql = "<"
    elif operator_raw in {"is greater than", "is after"}:
        operator_sql = ">"
    elif operator_raw == "is between" or operator_raw == "is not between":
        # Range operator – return a list of two conditions
        try:
            is_float = False
            try:
                float(value.split(',')[0])
                is_float = True
            except ValueError:
                pass
            if is_float:
                if float(value.split(',')[0]) >= float(value.split(',')[1]):
                    value_lower = value.split(',')[1]
                    value_upper = value.split(',')[0]
                else:
                    value_lower = value.split(',')[0]
                    value_upper = value.split(',')[1]
            else:
                value_lower = value.split(',')[0]
                value_upper = value.split(',')[1]
        except IndexError:
            logger_setup.get_logger().error(f"Range operator requires two numbers, got: {value}")
            raise ValueError(f"Range operator requires two numbers, got: {value}")
        if operator_raw == "is between":
            if datatype == "date":
                operator_sql = [f">= '{value_lower}'", f"<= '{value_upper}'"]
            elif datatype == "number":
                operator_sql = [f">= {value_lower}", f"<= {value_upper}"]
            else:
                logger_setup.get_logger().error(f"Range must be numeric or date, got: {datatype}")
                raise ValueError(f"Unsupported datatype for range operator: {datatype}")
        else:  # "is not between"
            if datatype == "date":
                operator_sql = [f"< '{value_lower}'", f"> '{value_upper}'"]
            elif datatype == "number":
                operator_sql = [f"< {value_lower}", f"> {value_upper}"]
            else:
                logger_setup.get_logger().error(f"Range must be numeric or date, got: {datatype}")
    else:
        # default
        operator_sql = "="

    sampleagebypass = False
    if field_key == 'SampleAges.[OldestAge]':
        field_key = 'SampleAges.[OldestAgeID]'
        value = f"(SELECT AgeID FROM Ages WHERE AgeName = '{value}' COLLATE NOCASE)"
        sampleagebypass = True

    if field_key == 'SampleAges.[YoungestAge]':
        field_key = 'SampleAges.[YoungestAgeID]'
        value = f"(SELECT AgeID FROM Ages WHERE AgeName = '{value}' COLLATE NOCASE)"
        sampleagebypass = True

    # ---------- TREE TABLE? (Regions, Ages hierarchy, etc.) ----------
    if field_key in SQLUtils.tree_tables_schema:
        meta = SQLUtils.tree_tables_schema[field_key]
        table = field_key.split(".")[0]  # e.g., "Regions", "Ages"

        # Build WHERE on the *tree table* (equal, like, etc.) for the CTE seed
        if isinstance(operator_sql, list):
            if len(operator_sql) == 2:
                # range: col >= lower AND col <= upper
                where = (
                    f"{table}.{meta['name_column']} {operator_sql[0]} "
                    f"AND {table}.{meta['name_column']} {operator_sql[1]}"
                )
            else:
                logger_setup.get_logger().error(f"Range not specified correctly: {value}")
                raise ValueError(f"Range operator requires two values, got: {value}")
        elif "NULL" in operator_sql or "LIKE" in operator_sql:
            # LIKE / IS NULL / IS NOT NULL → already has full operator
            where = f"{table}.{meta['name_column']} {operator_sql.replace('NOT ', '')}"
        elif '!=' in operator_sql:
            # "is not X" – we want the children of the matching node, so seed with "="
            where = f"{table}.{meta['name_column']} = '{value}' COLLATE NOCASE"
        else:
            # simple comparisons, case-insensitive on the name
            where = f"{table}.{meta['name_column']} {operator_sql} '{value}' COLLATE NOCASE"

        # Ensure per-field counter so CTE names stay unique per query
        recursive_tables[field_key] += 1
        cte_name = f"{meta['cte_name']}{recursive_tables[field_key]}"

        # Recursive CTE over the tree table
        cte_sql = f"""
        {cte_name} AS (
            SELECT {meta['id_column']}
              FROM {table}
             WHERE {where}
            UNION ALL
            SELECT t.{meta['id_column']}
              FROM {table} t
              JOIN {cte_name} r ON t.{meta['parent_column']} = r.{meta['id_column']}
        )""".strip()

        # ---- join condition between bridge table and CTE (which holds id_column) ----
        if field_key == 'Ages.[AgeName]':
            # Special handling: SampleAges.* uses OldestAgeID / YoungestAgeID
            col1 = "OldestAgeID"
            col2 = "YoungestAgeID"

            # rows in bridge_table are "in" the CTE if either ID hits the tree
            join_condition = (
                f"({meta['bridge_table']}.{col1} = {cte_name}.{meta['id_column']} "
                f"OR {meta['bridge_table']}.{col2} = {cte_name}.{meta['id_column']})"
            )
        else:
            # normal single-column case (Regions, RockTypes, etc.)
            join_condition = (
                f"{meta['bridge_table']}.{meta['bridge_to_column']} = "
                f"{cte_name}.{meta['id_column']}"
            )

        # ---------- correlate EXISTS to the *outer* main table ----------
        # We infer the main table from the bridge table prefix:
        #   Samples_Regions   → main_table = Samples,   pk = SampleID
        #   Aliquots_Regions  → main_table = Aliquots, pk = AliquotID
        #   Spots_Regions     → main_table = Spots,    pk = SpotID
        #   UPbAnalyses_...   → main_table = UPbAnalyses, pk = UPbAnalysisID
        main_table = meta.get("base_table", meta["bridge_table"].split("_")[0])

        default_pk_map = {
            "Samples": "SampleID",
            "Aliquots": "AliquotID",
            "Spots": "SpotID",
            "UPbAnalyses": "UPbAnalysisID",
        }
        main_pk = meta.get("base_pk", default_pk_map.get(main_table, f"{main_table.rstrip('s')}ID"))

        # correlation: bridge_table.FK_to_main = MainTable.PK
        correlation_condition = (
            f"{meta['bridge_table']}.{main_pk} = {main_table}.{main_pk}"
        )

        # ---------- Build final SQL fragment ----------
        # For UPbAnalyses we prefer a plain IN check on the *main* table
        # if main_table == "UPbAnalyses":
        #     if field_key == 'Ages.[AgeName]':
        #         # both OldestAgeID and YoungestAgeID against recursive Ages CTE
        #         in_condition = (
        #             f"({main_table}.OldestAgeID IN (SELECT {meta['id_column']} FROM {cte_name}) "
        #             f"OR {main_table}.YoungestAgeID IN (SELECT {meta['id_column']} FROM {cte_name}))"
        #         )
        #     else:
        #         in_condition = (
        #             f"{main_table}.{meta['bridge_to_column']} "
        #             f"IN (SELECT {meta['id_column']} FROM {cte_name})"
        #         )
        #
        #     prefix = "NOT " if (operator_sql == "!=" or "NOT" in str(operator_sql)) else ""
        #     exists_sql = f"{prefix}{in_condition}"
        #
        # else:
        # General case: EXISTS correlated via bridge_table → main_table
        prefix = "NOT " if (operator_sql == "!=" or "NOT" in str(operator_sql)) else ""
        exists_sql = f"""{prefix}EXISTS (
            SELECT 1
              FROM {meta['bridge_table']}
              JOIN {cte_name}
                    ON {join_condition}
             WHERE {correlation_condition}
        )"""

        return exists_sql, [cte_sql], field_key

    # ---------- Non-tree conditions ----------
    if isinstance(operator_sql, list):
        if len(operator_sql) == 2:
            if datatype == 'date':
                cond_sql = f"{field_key} {operator_sql[0]} OR {field_key} {operator_sql[1]}"
            else:
                cond_sql = f"{field_key} {operator_sql[0]} AND {field_key} {operator_sql[1]}"
        else:
            logger_setup.get_logger().error(f"Range not specified correctly: {value}")
            raise ValueError(f"Range operator requires two values, got: {value}")
    elif "NULL" in operator_sql or "LIKE" in operator_sql:
        cond_sql = f"{field_key} {operator_sql}"
    else:
        if datatype == "number":
            cond_sql = f"{field_key} {operator_sql} {value}"
        elif datatype == "boolean":
            cond_sql = f"{field_key} {operator_sql} {1 if value == 'True' else 0}"
        elif sampleagebypass:
            cond_sql = f"{field_key} {operator_sql} {value}"
        else:
            cond_sql = f"{field_key} {operator_sql} '{value}'"
            if operator_sql == "=":
                cond_sql += f" COLLATE NOCASE"

    return cond_sql, [], field_key

def _build_age_condition(condition: dict) -> Tuple[str, List[str], str]:
    """
    Build SQL for age-aware conditions on SampleAges.*, supporting:
      - SampleAges (no Direct/Relative toggle → always use CalculatedDirectAge)
      - OldestAge (Direct / Relative / Both)
      - YoungestAge (Direct / Relative / Both)

    Matches the 10 core cases in SampleAgesSqlQueries.txt:
      • SampleAges: geologic / numeric
      • OldestAge  (Direct): geologic / numeric
      • YoungestAge(Direct): geologic / numeric
      • OldestAge  (Relative): geologic / numeric
      • YoungestAge(Relative): geologic / numeric
      (Both-age mode is implemented as OR of Direct + Relative semantics.)
    """

    field_key: str = condition["field"].replace(" ", "")
    raw_value = str(condition["value"]).strip()
    operator_raw: str = condition["operator"].lower()
    mode: str = condition["datatype"]   # 'relativeage', 'directage', 'bothage', 'ages'

    table, col = field_key.split(".")
    attr = col.strip("[]")  # 'SampleAge', 'SampleAgeOldest', 'SampleAgeYoungest', etc.

    # ----------------- Column mapping -----------------
    if attr == "SampleAgeOldest":
        ageid_col = f"{table}.[OldestAgeID]"
        direct_col = f"{table}.[CalculatedOldestDirectAge]"
    elif attr == "SampleAgeYoungest":
        ageid_col = f"{table}.[YoungestAgeID]"
        direct_col = f"{table}.[CalculatedYoungestDirectAge]"
    else:
        # Generic SampleAge case (no Direct/Relative toggle – just use CalculatedDirectAge)
        ageid_col = None
        direct_col = f"{table}.[CalculatedDirectAge]"

    # ----------------- Helpers -----------------
    def is_number(text: str) -> bool:
        try:
            float(text)
            return True
        except Exception:
            return False

    def map_numeric_op(col: str, num: float) -> str:
        """
        Apply the usual numeric operators to a *direct* age column.
        Mirrors the non-age numeric operator behaviour where reasonable.
        """
        if operator_raw in {"is", "is on"}:
            return f"{col} = {num}"
        elif operator_raw in {"is not"}:
            return f"{col} != {num}"
        elif operator_raw == "is less than":
            return f"{col} < {num}"
        elif operator_raw == "is greater than":
            return f"{col} > {num}"
        elif operator_raw == "is blank":
            return f"{col} IS NULL"
        elif operator_raw == "is not blank":
            return f"{col} IS NOT NULL"
        elif operator_raw in {"is between", "is not between"}:
            parts = [p.strip() for p in raw_value.split(",")]
            if len(parts) != 2 or not all(is_number(p) for p in parts):
                raise ValueError(f"Range operator requires two numbers, got: {raw_value}")

            lower = float(parts[0])
            upper = float(parts[1])
            if lower > upper:
                lower, upper = upper, lower

            if operator_raw == "is between":
                return f"{col} >= {lower} AND {col} <= {upper}"
            else:  # "is not between"
                return f"{col} < {lower} OR {col} > {upper}"

        # Fallback: treat as equality
        return f"{col} = {num}"

    def direct_geologic_range(col: str, age_name: str) -> str:
        """
        [Calculated*DirectAge] BETWEEN Ages.YoungestAge AND Ages.OldestAge
        for a given geologic age name.
        """
        safe_name = age_name.replace("'", "''")
        return (
            f"{col} BETWEEN "
            f"(SELECT YoungestAge FROM Ages WHERE AgeName='{safe_name}' COLLATE NOCASE) "
            f"AND "
            f"(SELECT OldestAge FROM Ages WHERE AgeName='{safe_name}' COLLATE NOCASE)"
        )

    def relative_numeric_interval(ageid_column: str, num: float) -> str:
        """
        140 BETWEEN Ages.YoungestAge AND Ages.OldestAge
        where Ages.AgeID = SampleAges.OldestAgeID / YoungestAgeID.
        """
        return (
            f"{num} BETWEEN "
            f"(SELECT YoungestAge FROM Ages WHERE AgeID = {ageid_column}) "
            f"AND "
            f"(SELECT OldestAge FROM Ages WHERE AgeID = {ageid_column})"
        )

    def relative_geologic_id_match(ageid_column: str, age_name: str) -> str:
        """
        Relative + geologic entry:
          SampleAges.[OldestAgeID/YoungestAgeID] is in the subtree of the
          requested AgeName (the age itself + all descendants via ParentAgeID).
        """
        safe_name = age_name.replace("'", "''")

        return (
            f"{ageid_column} IN ("
            f"  WITH RECURSIVE AgeTree AS ("
            f"    SELECT AgeID "
            f"    FROM Ages "
            f"    WHERE AgeName = '{safe_name}' COLLATE NOCASE "
            f"    UNION ALL "
            f"    SELECT a.AgeID "
            f"    FROM Ages a "
            f"    JOIN AgeTree at ON a.ParentAgeID = at.AgeID"
            f"  ) "
            f"  SELECT AgeID FROM AgeTree"
            f")"
        )

    is_numeric = is_number(raw_value)
    clauses: List[str] = []

    # ----------------- CASE 1–2: SampleAges (mode 'ages') -----------------
    # SampleAges has no Direct/Relative toggle – always use CalculatedDirectAge
    #   Case SampleAges is geologic age entry
    #   Case SampleAges is numerical entry
    if mode == "ages" or (ageid_col is None and mode in {"directage", "relativeage", "bothage"}):
        if is_numeric:
            num = float(raw_value)
            clauses.append(map_numeric_op(direct_col, num))
        else:
            clauses.append(direct_geologic_range(direct_col, raw_value))

        cond_sql = " OR ".join(f"({c})" for c in clauses)
        return cond_sql, [], field_key

    # ----------------- DIRECT MODE -----------------
    if mode == "directage":
        # OldestAges is set to Direct, search by CalculatedOldestDirectAge
        #   geologic entry → BETWEEN (YoungestAge, OldestAge) for AgeName
        #   numeric entry  → direct numeric comparison
        #
        # YoungestAge is set to Direct, search by CalculatedYoungestDirectAge
        if is_numeric:
            num = float(raw_value)
            clauses.append(map_numeric_op(direct_col, num))
        else:
            clauses.append(direct_geologic_range(direct_col, raw_value))

        cond_sql = " OR ".join(f"({c})" for c in clauses)
        return cond_sql, [], field_key

    # ----------------- RELATIVE MODE -----------------
    if mode == "relativeage":
        # OldestAges is set to Relative
        #   geologic entry (as in spec): use CalculatedOldestDirectAge BETWEEN range
        #   numeric entry: 140 BETWEEN Ages.YoungestAge AND Ages.OldestAge
        #                  where Ages.AgeID = sa.OldestAgeID
        #
        # YoungestAge is set to Relative
        #   geologic entry: YoungestAgeID = (AgeID for AgeName)
        #   numeric entry:  140 BETWEEN Ages.YoungestAge AND Ages.OldestAge
        #                   where Ages.AgeID = sa.YoungestAgeID
        if is_numeric:
            num = float(raw_value)
            if ageid_col is not None:
                clauses.append(relative_numeric_interval(ageid_col, num))
            else:
                clauses.append(map_numeric_op(direct_col, num))
        else:
            clauses.append(relative_geologic_id_match(ageid_col, raw_value))

        cond_sql = " OR ".join(f"({c})" for c in clauses)
        return cond_sql, [], field_key

    # ----------------- BOTH MODE: combine Direct + Relative semantics -----------------
    # Not part of the original 10 examples, but implemented as:
    #   (Direct-style clause) OR (Relative-style clause)
    if mode == "bothage":
        # Direct component
        if is_numeric:
            num = float(raw_value)
            direct_clause = map_numeric_op(direct_col, num)
        else:
            direct_clause = direct_geologic_range(direct_col, raw_value)

        # Relative component
        if is_numeric and ageid_col is not None:
            rel_clause = relative_numeric_interval(ageid_col, float(raw_value))
        elif not is_numeric and ageid_col is not None:
            rel_clause = relative_geologic_id_match(ageid_col, raw_value)
        else:
            rel_clause = direct_clause

        clauses.extend([direct_clause, rel_clause])
        cond_sql = " OR ".join(f"({c})" for c in clauses)
        return cond_sql, [], field_key

    # ----------------- Fallback (should not normally hit) -----------------
    # Default to direct numeric / geologic semantics if mode is unexpected.
    if is_numeric:
        clauses.append(map_numeric_op(direct_col, float(raw_value)))
    else:
        clauses.append(direct_geologic_range(direct_col, raw_value))

    cond_sql = " OR ".join(f"({c})" for c in clauses)
    return cond_sql, [], field_key


def _collapse_same_field_basic(conds: List[str], expected_count: int) -> str:
    """Fallback for flat tables – require **all** values via COUNT‑HAVING.

    Returns a 2‑step SQL fragment:
        1. RockTypeID IN (values …)  (placed in WHERE)
        2. HAVING COUNT(DISTINCT RockTypeID) >= expected_count

    The caller is responsible for appending the HAVING part inside the
    *outermost* SELECT when this helper is used.  In GeoCORK the root SELECT is
    *always* ``Samples`` so we can inline it directly here for simplicity.
    """
    values_block = " AND ".join(conds)  # conds already like "col = 4"
    return f"GROUP BY Samples.SampleID HAVING ({values_block})"



def process_selects(group):
    """
    Recursively process a group of conditions and subgroups to create a list of fields for SELECT.
    """
    if not group.get('conditions') and not group.get('subgroups'):
        return ''

    # Process conditions in the current group
    fields = []
    for condition in group.get('conditions', []):
        field = condition['field']
        fields.append(field)

    # Process subgroups recursively
    for subgroup in group.get('subgroups', []):
        subgroup_string = process_selects(subgroup)
        if subgroup_string:
            fields.append(subgroup_string)

    return fields
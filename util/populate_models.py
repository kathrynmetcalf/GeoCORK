import time

from PyQt6 import QtWidgets, QtCore, QtSql
from PyQt6.QtCore import QSortFilterProxyModel

import util.Text_manipulations as TxM
import logger_setup
from Functions import SQLUtils
from Functions.Database_views import ViewQuery
from Functions.Settings_manager import SettingsManager
from Functions.Widget_classes import get_view_from_table, get_name_column, \
    get_headers, set_table, show_column, get_edit_column, get_name_from_id
from util.widgets.ComboBoxes.CheckableComboBox import CheckableComboBox
from util.widgets.ComboBoxes.CheckableTreeComboBox import CheckableTreeComboBox
from util.widgets.ComboBoxes.TreeComboBox import TreeComboBox
from util.widgets.models.CheckableSQLiteTableModel import CheckableSQLiteTableModel
from util.widgets.models.CheckableSqlQueryModel import CheckableSqlQueryModel
from util.widgets.models.CheckableSqlTableModel import CheckableSqlTableModel
from util.widgets.models.CheckableTreeModel import CheckableTreeModel
from util.widgets.models.DisplayRoundedModel import DisplayRoundedModel
from util.widgets.models.DisplayRoundedQueryModel import DisplayRoundedQueryModel
from util.widgets.models.LazyCheckableSqlQueryModel import LazyCheckableSqlQueryModel
from util.widgets.models.LazyCheckableSqlTableModel import LazyCheckableSqlTableModel
from util.widgets.models.LazyCheckableTreeModel import LazyCheckableTreeModel
from util.widgets.models.ReadableProxyModel import ReadableProxyModel
from util.widgets.models.SQLiteTableModel import SQLiteTableModel
from util.widgets.models.SampleAgeProxyModel import SampleAgeProxyModel
from util.widgets.models.TreeModel import TreeModel
from util.widgets.models.TreeSortFilterProxyModel import TreeSortFilterProxyModel
from util.loading_dialog_manager import show_loading_dialog, close_loading_dialog

settings = SettingsManager().settings

def populate_combo_box(comboBox: QtWidgets.QComboBox, **kwargs):
    """
    Populate a combo box with data from a database table or query. This method sets the model for the combo box based
    on the provided keyword arguments. It can handle both SQL queries and table names, and it supports displaying
    hierarchical data in a tree structure if the table is part of a user viewable tree. The method also allows specifying
    a specific column to display in the combo box. If a query is provided, it uses a DisplayRoundedQueryModel; otherwise,
    it uses a DisplayRoundedModel or a SQLiteTableModel based on the table name. If the table is part of a user viewable
    tree, it sets the model to a CheckableTreeModel or TreeModel. If the combo box is a CheckableComboBox, it uses
    CheckableSqlTableModel or CheckableSqlQueryModel to populate the combo box. The method also ensures that the
    specified column is displayed in the combo box, and it defaults to showing the name column if no specific column
    is provided.
    :param comboBox: QComboBox or subclass combo box to populate with data
    :param kwargs: keyword arguments to specify the table: str, query: str, view_query: ViewQuery, column: str, and/or live: bool
    :return:
    """
    table: str = None
    query: str = None
    view_query: ViewQuery = None
    column: str = None
    live: bool = True  # Whether live values from the database are required or SQLiteTableModel will suffice
    start_populate_combo_time = time.time()
    for key, value in kwargs.items():
        if key == 'table':
            table = TxM.remove_spaces(value)  # ensure there are no spaces in the table name
            if table == 'References':
                table = '"References"'
        elif key == 'query':
            query = value
        elif key == 'view_query':
            view_query = value
        elif key == 'column':
            column = value
        elif key == 'live':
            live = value
    if query:
        if live and not view_query:
            model = DisplayRoundedQueryModel()
            model.setQuery(query)
        else:
            model = SQLiteTableModel()
            model.setQuery(query, view_query)
        if not isinstance(model, LazyCheckableSqlTableModel):
            while model.canFetchMore():
                model.fetchMore()
        if table:
            model.set_table(table)
        if not table:
            table = model.tableName()
        if table == 'SampleAges':
            if isinstance(model, DisplayRoundedQueryModel):
                model.rounded = False
            proxy_model = SampleAgeProxyModel()
            proxy_model.setSourceModel(model)
            model = proxy_model
    elif table == 'Ages':
        model = SQLiteTableModel('SELECT * FROM Ages')
        if model.last_error:
            logger_setup.get_logger().error(f'Error setting up Ages table model')
            return
    elif table != get_view_from_table(table):
        # If the table is a view
        # Need to use a special view query
        query_args = {'show_columns': settings.value(SQLUtils.view_setting_dict[get_view_from_table(table)])}
        view_query = ViewQuery(table, edit_view=False, **query_args)
        query = view_query.table_query
        if settings.value('show_items_missing_data'):
            msg = f'Loading related data for {table}...\n\nSettings to speed up loading:\n- Hide items with missing data\n- Reduce the columns shown'
        else:
            msg = f'Loading related data for {table}...\n\nSettings to speed up loading:\n- Reduce the columns shown'
        show_loading_dialog('Loading', msg)
        if live and not view_query:
            model = DisplayRoundedQueryModel()
            model.setQuery(query)
        else:
            model = SQLiteTableModel()
            model.setQuery(query, view_query)
        while model.canFetchMore():
            model.fetchMore()
        model.set_table(table)
        close_loading_dialog('Loading', msg)
    else:
        if live:
            model = DisplayRoundedModel()
            set_table(model, table)
        else:
            model = SQLiteTableModel()
            model.setQuery(f'SELECT * FROM {table}')
    show_loading_dialog('Loading', f'Populating {model.rowCount()} {table}')
    if isinstance(comboBox, CheckableComboBox | CheckableTreeComboBox):
        if table in SQLUtils.user_viewable_trees or table == 'Ages':
            # if settings.value('lazy_loading_enabled') == 'true' and isinstance(comboBox, CheckableTreeCombobox) and table != 'Ages':
            #     tree_model = LazyCheckableTreeModel()
            if isinstance(comboBox, CheckableTreeComboBox):
                tree_model = CheckableTreeModel()
            else:
                tree_model = TreeModel()
            tree_model.setSourceModel(model)
            tree_proxy_model = TreeSortFilterProxyModel()
            tree_proxy_model.setSourceModel(tree_model)
            comboBox.setModel(tree_proxy_model)
        else:
            checkable_model = None
            proxy_model = ReadableProxyModel()
            if isinstance(comboBox, CheckableComboBox) and not query and not view_query:
                if live:
                    # If the combo box is a CheckableComboBox and the table is not a view, use CheckableSqlTableModel
                    checkable_model = CheckableSqlTableModel()
                    set_table(checkable_model, table)
                else:
                    checkable_model = CheckableSQLiteTableModel()
                    checkable_model.setQuery(f'SELECT * FROM {table}')
                if not isinstance(checkable_model, LazyCheckableSqlTableModel):
                    while checkable_model.canFetchMore():
                        checkable_model.fetchMore()
                proxy_model.setSourceModel(checkable_model)
                comboBox.setModel(proxy_model)
            elif isinstance(comboBox, CheckableComboBox) and view_query:
                checkable_model = CheckableSQLiteTableModel()
                checkable_model.setQuery(query, view_query)
                if not isinstance(checkable_model, LazyCheckableSqlQueryModel):
                    while checkable_model.canFetchMore():
                        checkable_model.fetchMore(QtCore.QModelIndex())
                checkable_model.set_table(table)
                proxy_model.setSourceModel(checkable_model)
                comboBox.setModel(proxy_model)
            elif isinstance(comboBox, CheckableComboBox) and query:
                if live:
                    checkable_model = CheckableSqlQueryModel()
                else:
                    checkable_model = CheckableSQLiteTableModel()
                checkable_model.setQuery(query)
                while checkable_model.canFetchMore():
                    checkable_model.fetchMore()
                checkable_model.set_table(table)
                proxy_model.setSourceModel(checkable_model)
                comboBox.setModel(proxy_model)
            else:
                try:
                    proxy_model.setSourceModel(checkable_model)
                    comboBox.setModel(proxy_model)
                except Exception as e:
                    logger_setup.get_logger().critical(f'Error setting model for combo box {comboBox.objectName()}')
                    logger_setup.get_logger().debug(f'Error: {e}')
                    return
            if checkable_model and not checkable_model.tableName():
                if table:
                    set_table(checkable_model, table)
                elif model.tableName():
                    set_table(checkable_model, model.tableName())
    else:
        if isinstance(comboBox, TreeComboBox):
            tree_model = TreeModel()
            tree_model.setSourceModel(model)
            proxy_model = TreeSortFilterProxyModel()
            proxy_model.setSourceModel(tree_model)
        elif isinstance(model, QSortFilterProxyModel):
            proxy_model = model
        else:
            proxy_model = ReadableProxyModel()
            proxy_model.setSourceModel(model)
        comboBox.setModel(proxy_model)
    if column:
        show_column(comboBox, column)
    else:
        if isinstance(model, SampleAgeProxyModel):
            name_col = get_headers('SampleAges')[get_name_column('SampleAges')]
        elif isinstance(comboBox, TreeComboBox):
            name_col = 0
        else:
            name_table = get_view_from_table(model.tableName())
            name_col = get_name_column(name_table)
        if name_col is not None:
            show_column(comboBox, name_col)
    close_loading_dialog('Loading', f'Populating {model.rowCount()} {table}')
    logger_setup.get_logger().debug(f'Populated combo box {comboBox.objectName()} in {time.time() - start_populate_combo_time} seconds')

def populate_model_checks(model: CheckableSqlTableModel | CheckableSqlQueryModel, item_ids: list, item_table: str=None, table_id_header: str=None):
    """
    Populate the checkable model with checks based on the item IDs and the item table, e.g. given a checkable Columns
    model and a list of Sample IDs, mark what columns are associated with those samples. This method iterates through
    the rows of the model and checks how many of the given item IDs have a specific tag in the item table. It updates
    the check state of the model's data based on the number of item IDs that have the tag. If all items have the tag,
    the check state is set to Checked; if some items have the tag, it is set to PartiallyChecked; and if no items
    have the tag, it is set to Unchecked.
    :param model: checkable model to populate with checks, data from a database table (e.g. Columns)
    :param item_ids: list of item IDs from a separate table (e.g. Sample IDs)
    :param item_table: table the list of item IDs is from. If the relationship is one-to-one or one-to-many, this may be
    a main table (e.g. Samples). If the relationship is many-to-many, this may be a junction table (e.g. SampleAges_References).
    :param table_id_header: name of the column in item_table that contains the IDs to check in the model. This may be
    different from the model table ID column (e.g. SampleColumnID column in the Samples table)
    :return: True if the model was populated successfully, False otherwise
    """
    start_populate_model_checks_time = time.time()
    while isinstance(model, QSortFilterProxyModel):
        model = model.sourceModel()
    if isinstance(model, TreeModel):
        row_count = model.source_model.rowCount()
    else:
        row_count = model.rowCount()
    show_loading_dialog('Checking model', f'Checking {row_count} {model.tableName()}...')
    if table_id_header is None:
        table_id_header = model.headerData(0, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole)
    item_id_header = get_headers(item_table)[0]
    associations = {}
    if len(item_ids) > 1:
        query_where_str = f'in {tuple(item_ids)}'
    elif len(item_ids) == 1:
        query_where_str = f'= {item_ids[0]}'
    else:
        logger_setup.get_logger().info(f'No item IDs provided to populate model checks for {model.tableName()}')
        model.blockSignals(True)
        model.clear_checks()
        model.blockSignals(False)
        close_loading_dialog('Checking model', f'Checking {row_count} {model.tableName()}...')
        return True
    # Check that the table_id_header is in the item_table headers
    table_id_header = get_edit_column(table_id_header, item_table)
    if not table_id_header:
        logger_setup.get_logger().critical(f'Error populating checks for {model.tableName()}')
        logger_setup.get_logger().debug(f'Could not find {model.tableName()} ID header in {item_table}')
        return False
    if not isinstance(model, LazyCheckableSqlTableModel | LazyCheckableSqlQueryModel):
        while model.canFetchMore(QtCore.QModelIndex()):
            model.fetchMore(QtCore.QModelIndex())
    if 'View' in item_table:
        # If the item_table is a view, we need to use the view query
        show_columns = settings.value(SQLUtils.view_setting_dict[item_table])
        where = f"WHERE {item_id_header} {query_where_str}"
        edit_view = True if 'Edit' in item_table else False
        query_args = {'show_columns': show_columns, 'where': where}
        view_query = ViewQuery(item_table, edit_view, **query_args)
        association_query_str = view_query.table_query
    elif item_table == 'References':
        association_query_str = f'SELECT {table_id_header}, {item_id_header} FROM "References" WHERE {item_id_header} {query_where_str}'
    else:
        association_query_str = f"SELECT {table_id_header}, {item_id_header} FROM {item_table} WHERE {item_id_header} {query_where_str}"
    association_query = QtSql.QSqlQuery()
    if not association_query.exec(association_query_str):
        logger_setup.get_logger().critical(f'Error getting checks for {model.tableName()}')
        logger_setup.get_logger().debug(f'Error: {association_query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {association_query_str}')
        close_loading_dialog('Checking model',
                                             f'Checking {row_count} {model.tableName()}...')
        return False
    while association_query.next():
        table_id = association_query.value(0)
        item_id = association_query.value(1)
        if table_id:
            if table_id not in associations:
                associations[table_id] = set()
            associations[table_id].add(item_id)
    all_items = set()
    some_items = set()
    for table_id, associated_item_ids in associations.items():
        if len(list(associated_item_ids)) == len(item_ids):
            all_items.add(table_id)
        elif len(list(associated_item_ids)) > 0:
            some_items.add(table_id)
    model.update_model_checks(set(all_items), set(some_items))
    if isinstance(model, LazyCheckableTreeModel):
        model.load_checked()

    close_loading_dialog('Checking model', f'Checking {row_count} {model.tableName()}...')
    logger_setup.get_logger().debug(f'Populated model checks for {model.tableName()} in {time.time() - start_populate_model_checks_time} seconds')
    return True

def populate_tree_model_checks(tree_model: CheckableTreeModel, item_ids: list, item_table: str=None, table_id_header: str=None):
    """
    Populate the tree model with checks based on the item IDs and the item table, e.g. given a checkable Units model and
    a list of Sample IDs, mark what units are associated with those samples. This method recursively iterates through
    the rows of the tree model and checks how many of the given item IDs have a specific tag in the item table. If all
    items have the tag, the check state is set to Checked; if some items have the tag, it is set to PartiallyChecked;
    and if no items have the tag, it is set to Unchecked.
    :param tree_model: checkable tree model to populate with checks, data from a database table (e.g. Units)
    :param item_ids: list of item IDs from a separate table (e.g. Sample IDs)
    :param item_table: table the list of item IDs is from. If the relationship is one-to-one or one-to-many, this may be
    a main table (e.g. Samples). If the relationship is many-to-many, this may be a junction table (e.g. SamplesUnits).
    :param table_id_header: name of the column in item_table that contains the IDs to check in the model. This may be
    different from the model table ID column in a one-to-one or one-to-many relationship.
    :return: True if the model was populated successfully, False otherwise
    """
    start_populate_tree_model_checks_time = time.time()
    associations = {}
    id_col = 1  # ID column is always placed in the second column
    if not item_ids[0]:
        tree_model.clear_checks()
        return True
    row_count = tree_model.source_model.rowCount()
    table = tree_model.table
    show_loading_dialog('Checking model', f'Checking {row_count} {table}...')
    if table_id_header is None:
        table_id_header = tree_model.headerData(id_col, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole)
        if ' ' in table_id_header:
            table_id_header = TxM.remove_spaces(table_id_header)
    # Check that the table_id_header is in the item_table headers
    table_id_header = get_edit_column(table_id_header, item_table)
    if not table_id_header:
        logger_setup.get_logger().critical(f'Error populating checks for {tree_model.tableName()}')
        logger_setup.get_logger().debug(f'Could not find {tree_model.tableName()} ID header in {item_table}')
        return False
    item_id_header = get_headers(item_table)[0]
    if len(item_ids) > 1:
        query_where_str = f'in {tuple(item_ids)}'
    elif len(item_ids) == 1:
        query_where_str = f'= {item_ids[0]}'
    else:
        logger_setup.get_logger().info(f'No item IDs provided to populate model checks for {tree_model.tableName()}')
        tree_model.blockSignals(True)
        tree_model.clear_checks()
        tree_model.blockSignals(False)
        close_loading_dialog('Checking model', f'Checking {row_count} {table}...')
        return True
    association_query_str = f"SELECT {table_id_header}, {item_id_header} FROM {item_table} WHERE {item_id_header} {query_where_str}"
    association_query = QtSql.QSqlQuery()
    if not association_query.exec(association_query_str):
        logger_setup.get_logger().critical(f'Error getting checks for {table}')
        logger_setup.get_logger().debug(f'Error: {association_query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {association_query_str}')
        close_loading_dialog('Checking model', f'Checking {row_count} {table}...')
        return False
    while association_query.next():
        table_id = association_query.value(0)
        item_id = association_query.value(1)
        if table_id:
            if table_id not in associations:
                associations[table_id] = set()
            associations[table_id].add(item_id)
    all_items = set()
    some_items = set()
    for table_id, associated_item_ids in associations.items():
        if len(associated_item_ids) == len(item_ids):
            all_items.add(table_id)
        elif len(associated_item_ids) > 0:
            some_items.add(table_id)
    tree_model.update_model_checks(set(all_items), set(some_items))
    if isinstance(tree_model, LazyCheckableTreeModel):
        tree_model.load_checked()
    close_loading_dialog('Checking model', f'Checking {row_count} {table}...')
    logger_setup.get_logger().debug(f'Populated tree model checks for {table} in {time.time() - start_populate_tree_model_checks_time} seconds')
    return True

def populate_many_model_checks(many_to_many_table: str, model: CheckableSqlTableModel | CheckableSqlQueryModel | CheckableTreeModel, first_table_ids: list):
    """
    Populate a model with checks based on a many-to-many relationship table and a list of IDs from the first table.
    This method checks how many of the given IDs have a specific tag in the many-to-many relationship table. It updates
    the check state of the model based on the number of IDs that have the tag. If all items have the tag, the check
    state is set to Checked; if some items have the tag, it is set to PartiallyChecked; and if no items have the tag,
    it is set to Unchecked. The method also handles CheckableTreeModel instances, adjusting the model and column
    indices accordingly.
    :param many_to_many_table: Many-to-many relationship table name (e.g. SampleAges_References)
    :param model: model to populate with checks, can be a CheckableSqlTableModel, CheckableSqlQueryModel, or a
    CheckableTreeModel Data must be from the second table in the many-to-many relationship (e.g. References)
    :param first_table_ids: list of IDs from the first table (e.g. Sample IDs)
    :return:
    """
    start_populate_many_checks_time = time.time()
    logger_setup.get_logger().info(f"Populating checks for {many_to_many_table}")
    if not first_table_ids or len(first_table_ids) == 0:
        logger_setup.get_logger().info("No items selected, so unchecking everything")
        model.blockSignals(True)
        model.clear_checks()
        model.blockSignals(False)
        logger_setup.get_logger().info("Unchecked everything")
        return
    if isinstance(model, TreeModel):
        row_count = model.source_model.rowCount()
    else:
        row_count = model.rowCount()
    show_loading_dialog('Checking model', f'Checking {row_count} {model.tableName()}...')
    first_table = many_to_many_table.split('_')[0]
    first_table_id_header = get_headers(first_table)[0]
    if isinstance(model, CheckableTreeModel):
        tag_id_header = model.source_model.record().fieldName(0)
    else:
        tag_id_header = model.record().fieldName(0)
    logger_setup.get_logger().info(f"Checking {many_to_many_table}")
    associations = {}
    association_query_str = f"SELECT {first_table_id_header}, {tag_id_header} FROM {many_to_many_table} WHERE {first_table_id_header} IN ({', '.join(map(str, first_table_ids))})"
    association_query = QtSql.QSqlQuery()
    if not association_query.exec(association_query_str):
        logger_setup.get_logger().critical(f'Error getting checks for {many_to_many_table}')
        logger_setup.get_logger().debug(f'Error: {association_query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {association_query_str}')
        close_loading_dialog('Checking model', f'Checking {row_count} {model.tableName()}...')
        return
    while association_query.next():
        table_id = association_query.value(0)
        tag_id = association_query.value(1)
        if tag_id:
            if tag_id not in associations:
                associations[tag_id] = set()
            associations[tag_id].add(table_id)
    all_items = set()
    some_items = set()
    for table_id, associated_item_ids in associations.items():
        if len(list(associated_item_ids)) == len(first_table_ids):
            all_items.add(table_id)
        elif len(list(associated_item_ids)) > 0:
            some_items.add(table_id)
    if model.checked_ids != all_items or model.partially_checked_ids != some_items:
        model.update_model_checks(set(all_items), set(some_items))
    close_loading_dialog('Checking model', f'Checking {row_count} {model.tableName()}...')
    logger_setup.get_logger().info(f"Populated checks for {many_to_many_table} in {time.time() - start_populate_many_checks_time} seconds")

def populate_many_combo_checks(many_to_many_table: str, combo: QtWidgets.QComboBox, first_table_ids: list):
    """
    Populate a combo box with checks based on a many-to-many relationship table and a list of IDs from the first table.
    This method checks how many of the given IDs have a specific tag in the many-to-many relationship table. It updates
    the check state of the combo box's model based on the number of IDs that have the tag. If all items have the tag,
    the check state is set to Checked; if some items have the tag, it is set to PartiallyChecked; and if no items
    have the tag, it is set to Unchecked. The method also handles both CheckableTreeCombobox and regular QComboBox
    instances, adjusting the model and column indices accordingly.
    :param many_to_many_table: Many-to-many relationship table name (e.g. SampleAges_References)
    :param combo: combo box to populate with checks, can be a CheckableTreeCombobox or a regular QComboBox. Data must be
    from the second table in the many-to-many relationship (e.g. References)
    :param first_table_ids: list of IDs from the first table (e.g. Sample IDs)
    :return:
    """
    start_populate_many_checks_time = time.time()
    logger_setup.get_logger().info(f"Populating combo checks for {many_to_many_table}")

    if isinstance(combo, CheckableTreeComboBox):
        model = combo.tree_model
        if not model:
            logger_setup.get_logger().info(f"Could not find tree model for {combo.objectName()}")
            return
    else:
        if isinstance(combo.model(), QSortFilterProxyModel):
            model = combo.model().sourceModel()
        else:
            model = combo.model()
    populate_many_model_checks(many_to_many_table, model, first_table_ids)
    if not model.checked_ids and not model.partially_checked_ids:
        # No items have these tags
        text = ""
    elif not model.partially_checked_ids:
        # All items have the same tags
        all_names = set(get_name_from_id(model.tableName(), check_id) for check_id in model.checked_ids)
        text = ', '.join(sorted(all_names))
    else:
        # items have different tags
        text = "-"
    if not text:
        text = ''
    combo.setCurrentText(text)
    logger_setup.get_logger().info(f"Populated combo checks for {many_to_many_table} in {time.time() - start_populate_many_checks_time} seconds")

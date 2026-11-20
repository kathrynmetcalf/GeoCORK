from PyQt6 import QtWidgets

import logger_setup
from Functions.Widget_classes import find_tree_model, get_selected_tree_ids
from util.widgets.views.tree_views import CheckableTreeView


class TreeContextMenu(QtWidgets.QMenu):
    """
    Custom context menu for tree views. This class extends QMenu to provide a context menu for tree views with options
    for editing, adding, expanding/collapsing items, and viewing data. It dynamically adds actions based on the selected
    items in the tree view. The context menu can handle both single and multiple selections, and it provides options
    for inserting items above or below the selected item, adding child items, and adding parent items. It also includes
    options for expanding and collapsing items, as well as viewing data related to the selected items. A tree view is
    passed with bool values to enable or disable specific actions such as delete, add, and edit. The context menu
    can be used with both checkable and non-checkable tree views, and it provides a flexible way to interact with tree
    structures in the application.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tree_view = None
        self.model = None
        self.indexes = None

    def set_view(self, tree_view: QtWidgets.QTreeView, delete_active: bool = True, add_active: bool = True,
                 edit_active: bool = True):
        """
        Set the view for the context menu. This method initializes the context menu with actions based on the selected
        items in the tree view. It retrieves the model and indexes of the selected items, and then adds actions for
        editing, adding, deleting, expanding, and collapsing items. It also adds actions for viewing data if the model
        is an Aliquots table. The actions are added based on whether the delete, add, and edit actions are active or not.
        Actions are also different depending on if single or multiple items are selected.
        :param tree_view: QTreeView that contains selected items for which the context menu is created
        :param delete_active: Adds delete action if True, otherwise does not add it
        :param add_active: Adds add actions if True, otherwise does not add it
        :param edit_active: Adds edit actions if True, otherwise does not add it
        :return:
        """
        self.tree_view = tree_view
        self.tree_view.setUniformRowHeights(True)
        self.model, self.indexes = find_tree_model(self.tree_view.model(), self.tree_view.selectedIndexes())
        if not self.model:
            logger_setup.get_logger().info(f'No checkable tree model found in {self.tree_view.objectName()}')
            return
        item_parent_dictionary = get_selected_tree_ids(self.indexes)
        if len(item_parent_dictionary.keys()) == 1:  # only one item selected
            self.add_single_tree_actions(delete_active, add_active, edit_active)
        else:
            self.add_multi_tree_actions(delete_active, add_active, edit_active)
        self.add_expand_collapse_actions()

    def add_single_tree_actions(self, delete_active: bool = True, add_active: bool = True, edit_active: bool = True):
        """
        Add actions for a single selected item in the tree view. This method adds actions for editing, adding, and deleting
        a single item in the tree view. Several hierarchical add actions are available for a single item.
        :param delete_active: Adds delete action if True, otherwise does not add it
        :param add_active: Adds add actions if True, otherwise does not add it
        :param edit_active: Adds edit action if True, otherwise does not add it
        :return:
        """
        if edit_active:
            self.addAction('Edit')
        if add_active:
            add_menu = self.addMenu('Add')
            add_menu.addAction('Insert above')
            add_menu.addAction('Insert below')
            add_menu.addAction('Add child')
            add_menu.addAction('Add parent')
            add_menu.addAction('Add to end')
        if delete_active:
            self.addAction('Delete selected')
        if edit_active and 'Aliquot' in self.model.table:
            self.add_view_data_actions()

    def add_multi_tree_actions(self, delete_active: bool = True, add_active: bool = True, edit_active: bool = True):
        """
        Add actions for multiple selected items in the tree view. This method adds actions for editing, merging, adding,
        and deleting multiple items in the tree view. No hierarchical add actions are available for multiple items.
        :param delete_active: Adds delete action if True, otherwise does not add it
        :param add_active: Adds add actions if True, otherwise does not add it
        :param edit_active: Adds edit action if True, otherwise does not add it
        :return:
        """
        if edit_active:
            self.addAction('Edit')
        if delete_active:
            self.addAction('Delete selected')
            self.addAction('Merge selected')
        if add_active:
            self.addAction('Add')
            self.addAction('Add parent')
        if edit_active and 'Aliquot' in self.model.table:
            self.add_view_data_actions()

    def add_expand_collapse_actions(self):
        """
        Add actions for expanding and collapsing items in the tree view. This method adds actions for expanding and collapsing
        children, all children, and all items in the tree view. These actions allow users to quickly expand or collapse
        the tree structure to view or hide the details of the items. The actions are grouped into Expand and Collapse menus.
        :return:
        """
        expand_menu = self.addMenu('Expand')
        expand_menu.addAction('Expand children')
        expand_menu.addAction('Expand all children')
        expand_menu.addAction('Expand all')
        collapse_menu = self.addMenu('Collapse')
        collapse_menu.addAction('Collapse children')
        collapse_menu.addAction('Collapse all children')
        collapse_menu.addAction('Collapse all')

    def add_checkable_actions(self):
        """
        Add actions for checkable tree views. This method adds actions to check all items or clear all checks in the
        checkable tree view.
        :return:
        """
        if isinstance(self.tree_view, CheckableTreeView):
            self.addAction('Clear all checks')
            self.addAction('Check all')

    def add_view_data_actions(self):
        """
        Add actions for viewing data related to the selected items in the tree view. This method adds actions to view
        spots and U-Pb analyses for the selected aliquots in separate tabs.
        :return:
        """
        view_data_menu = self.addMenu('View Data')
        view_data_menu.addAction('View Grains')
        view_data_menu.addAction('View Spots')
        view_data_menu.addAction('View U-Pb Analyses')

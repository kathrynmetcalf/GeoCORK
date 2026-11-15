from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QSortFilterProxyModel

import logger_setup
from Functions.Widget_classes import get_name_column
from util.widgets.models.CheckableSqlQueryModel import CheckableSqlQueryModel
from util.widgets.models.CheckableSqlTableModel import CheckableSqlTableModel


class CheckableTableView(QtWidgets.QTableView):
    """
    A QTableView subclass that allows for checkable items in a table structure. This class extends QTableView to allows users
    to select multiple items. The model can be set to a CheckableSqlTableModel or CheckableSqlQueryModel, which provides the data for the table.
    """
    def __init__(self):
        super().__init__()
        self.setSortingEnabled(True)
        self.setHeaderHidden(False)
        self.setUniformRowHeights(True)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.clicked.connect(self.toggle_check_state)

    def setModel(self, model: CheckableSqlTableModel | CheckableSqlQueryModel | QSortFilterProxyModel):
        """
        Set the model for the table view. This method overrides the default setModel method to ensure that the model
        is a CheckableSqlTableModel, CheckableSqlQueryModel, or a proxy model wrapping one of those models.
        :param model: CheckableSqlTableModel or CheckableSqlQueryModel to be set as the model for the table view
        :return:
        """
        if isinstance(model, QSortFilterProxyModel):
            if not isinstance(model.sourceModel(), (CheckableSqlTableModel, CheckableSqlQueryModel)):
                raise TypeError("Model must be a CheckableSqlTableModel, CheckableSqlQueryModel, or a QSortFilterProxyModel wrapping one of those models")
        super().setModel(model)

    def toggle_check_state(self, model_index: QtCore.QModelIndex):
        """
        Toggle the check state of the item at the given index. This method checks if the model is set and if the index
        is valid and user-checkable. If so, it toggles the check state of the item between Checked and Unchecked.
        :param model_index: QModelIndex to be checked or unchecked
        :return:
        """
        if self.model():
            if isinstance(self.model(), QSortFilterProxyModel):
                source_model = self.model().sourceModel()
                source_index = self.model().mapToSource(model_index)
            else:
                source_model = self.model()
                source_index = model_index
            if source_index.isValid() and QtCore.Qt.ItemFlag.ItemIsUserCheckable in source_model.flags(source_index):
                item_id = source_model.index(source_index.row(), 1).data(QtCore.Qt.ItemDataRole.DisplayRole)
                if not item_id:
                    return
                if source_model.single_click:
                    if item_id in source_model.checked_ids:
                        if source_model.not_null and len(source_model.checked_ids) == 1:
                            logger_setup.get_logger().error(
                                f'{source_model.headerData(
                                    get_name_column(source_model.tableName()), 
                                    QtCore.Qt.Orientation.Horizontal, 
                                    QtCore.Qt.ItemDataRole.DisplayRole)} cannot be blank')
                            return
                        source_model.checked_ids = set()
                    elif item_id in source_model.partially_checked_ids:
                        source_model.partially_checked_ids = set()
                        source_model.checked_ids = {item_id}
                    else:
                        source_model.checked_ids = {item_id}
                        source_model.partially_checked_ids = set()
                else:
                    if item_id in source_model.checked_ids:
                        source_model.checked_ids.remove(item_id)
                    elif item_id in source_model.partially_checked_ids:
                        source_model.partially_checked_ids.remove(item_id)
                        source_model.checked_ids.add(item_id)
                    else:
                        source_model.checked_ids.add(item_id)
                source_model.dataChanged.emit(source_index, source_index, [QtCore.Qt.ItemDataRole.CheckStateRole])
                source_model.checksChanged.emit()
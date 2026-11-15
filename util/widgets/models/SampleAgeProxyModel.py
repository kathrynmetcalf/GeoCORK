from PyQt6 import QtCore

from Functions.Widget_classes import get_name_column
from util.display_formatting import display_age


class SampleAgeProxyModel(QtCore.QSortFilterProxyModel):
    """
    Proxy model to display updated SampleAgeConverted and SampleAgeDisplay while generated columns cannot update during a transaction.
    """
    def __init__(self):
        super().__init__()
        self.edited = True

    def data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            name_col = get_name_column('SampleAges')
            if index.column() == name_col:
                from Functions.Alter_database import return_sample_age_display
                from Functions.Alter_database import return_sample_age_converted
                id = self.sourceModel().index(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole)
                if id is not None:
                    # get the updated sample age display calculated from the database
                    age_display = return_sample_age_display(id)
                    age_converted = return_sample_age_converted(id)
                    if not self.edited and age_display is not None:
                        # return the user-readable age display
                        return display_age(age_display)
                    elif self.edited and age_converted is not None:
                        # return the editable age converted
                        return display_age(age_converted)
        return super().data(index, role)


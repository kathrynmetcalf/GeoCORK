from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC

class Errors(QtW.QErrorMessage):

    def show_error(self, parent, text: str):
        error_message = QtW.QErrorMessage(parent)
        error_message.showMessage(text)
        error_message.exec()

    def duplicate_entry(self, parent, header: str, duplicates: list):
        text = f'''Each entry in {header} must be unique (case insensitive)
                    Duplicates: {duplicates}'''
        self.show_error(text)

    def blank_entry(self, parent, header: str):
        text = f'{header} cannot be blank'
        self.show_error(parent, text)
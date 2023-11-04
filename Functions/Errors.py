import sys
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC

def duplicate_entry(header, duplicates):
    strlst = ', '.join(duplicates)
    text = f'''Each entry in {header} must be unique (case insensitive)
                Duplicates: {strlst}'''
    return text

def blank_entry(header):
    text = f'{header} cannot be blank'
    return text

if __name__ == '__main__':
    # only run these commands if this script is run
    # Can't be run when used as a library for another script
    pass
import sys
from pathlib import Path

import sqlite3
from PyQt6 import QtWidgets as QtW
import ui.New_source as NS


def create_source(db_file):
    """
    Called by GeoChronMain.py
    :param db_file: database file
    :return:
    """
    # run New_source window
    conn = sqlite3.connect(db_file)
    with conn:
        c = conn.cursor()
        new_source = read_source_form(c)
        sql = '''INSERT INTO Sources ("Authors", "Year", "Title", "Source", "doi", "Short Citation")
            VALUES(?,?,?,?,?,?)'''
        c.execute(sql, new_source)


def read_source_form(c):
    if NS.rejected:
        return []
    elif NS.accepted:
        authors = NS.authors_lineEdit.text()
        year = NS.year_lineEdit.text()
        title = NS.title_lineEdit.text()
        source = NS.source_lineEdit.text()
        doi = NS.doi_lineEdit.text()
        short_citation = NS.short_lineEdit.text()
        new_source = (authors, year, title, source, doi, short_citation)
        if short_citation:
            sql = '''SELECT "Short Citation" FROM "Sources"'''
            if c.execute(sql):
                existing = c.fetchall()
                if short_citation in existing:
                    msg = QtW.QMessageBox()
                    msg.setIcon(QtW.QMessageBox.Critical)
                    msg.setText("Error")
                    msg.setInformativeText('This short citation already exists. Enter a unique short citation')
                    msg.setWindowTitle("Error")
                    msg.exec_()
            return new_source
        else:
            msg = QtW.QMessageBox()
            msg.setIcon(QtW.QMessageBox.Critical)
            msg.setText("Error")
            msg.setInformativeText('Short citation is required')
            msg.setWindowTitle("Error")
            msg.exec_()

# def create_region(self):
#     self.model.setTable('Regions')
#     new_region = self.model.record()
#     source = ('', '')
#     newRegion.setValue('Name', source[0])
#     newRegion.setValue('Description', source[1])
#     if self.model.insertRecord(-1, newRegion) is True:
#         self.model.submitAll()
#         self.display_table()
#
#
# def create_setting(self):
#     self.model.setTable('Settings')
#     newSetting = self.model.record()
#     source = ('', '')
#     newSetting.setValue('Name', source[0])
#     newSetting.setValue('Description', source[1])
#     if self.model.insertRecord(-1, newSetting) is True:
#         self.model.submitAll()
#         self.display_table()
#
#
# def create_rocktype(self):
#     self.model.setTable('Rock Types')
#     newRockType = self.model.record()
#     source = ('', '')
#     newRockType.setValue('Name', source[0])
#     newRockType.setValue('Description', source[1])
#     if self.model.insertRecord(-1, newRockType) is True:
#         self.model.submitAll()
#         self.display_table()
#
#
# def create_unit(self):
#     self.model.setTable('Units')
#     newUnit = self.model.record()
#     source = ('', '')
#     newUnit.setValue('Name', source[0])
#     newUnit.setValue('Description', source[1])
#     if self.model.insertRecord(-1, newUnit) is True:
#         self.model.submitAll()
#         self.display_table()
#
#
# def create_agesignature(self):
#     self.model.setTable('Age Signatures')
#     newAgeSignature = self.model.record()
#     source = ('', '')
#     newAgeSignature.setValue('Name', source[0])
#     newAgeSignature.setValue('Description', source[1])
#     if self.model.insertRecord(-1, newAgeSignature) is True:
#         self.model.submitAll()
#         self.display_table()

# def create_sample(self):
#     self.model.setTable('Samples')
#     newSample = self.model.record()
#     source = ('', '', '', '', '', '')
#     newSample.setValue('Authors', source[0])
#     newSample.setValue('Year', source[1])
#     newSample.setValue('Title', source[2])
#     newSample.setValue('Source', source[3])
#     newSample.setValue('doi', source[4])
#     newSample.setValue('Short Citation', source[5])
#     if self.model.insertRecord(-1, newSample) is True:
#         self.model.submitAll()
#         self.display_table()
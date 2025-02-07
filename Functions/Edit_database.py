# import sys
# from pathlib import Path
#
# import sqlite3
# from PyQt6 import QtWidgets as QtW
# import ui.New_source as NS
# import ui.New_lab_facility as NLF
# import sqlite3
#
# from PyQt6 import QtWidgets as QtW
#
# import ui.New_lab_facility as NLF
# import ui.New_source as NS
# import sys
# from pathlib import Path
#
# import sqlite3
# from PyQt6 import QtWidgets as QtW
# import ui.New_reference as NS
# import ui.New_lab_facility as NLF
#
#
# def create_source(db_file, new_source):
#     """
#     Add a new row to the Sources table
#     :param new_source: tuple of data to be added to the table in the order
#         ("Authors", "Year", "Title", "Source", "doi", "Short Citation")
#     :param db_file: database file
#     :return:
#     """
#     # run New_source window
#     conn = sqlite3.connect(db_file)
#     with conn:
#         c = conn.cursor()
#         sql = '''INSERT INTO Sources ("Authors", "Year", "Title", "Source", "doi", "Short Citation")
#             VALUES(?,?,?,?,?,?)'''
#         c.execute(sql, new_source)
#
#
# def read_source_form(c):
#     if NS.rejected:
#         return []
#     elif NS.accepted:
#         authors = NS.authors_lineEdit.text()
#         year = NS.year_lineEdit.text()
#         title = NS.title_lineEdit.text()
#         source = NS.source_lineEdit.text()
#         doi = NS.doi_lineEdit.text()
#         short_citation = NS.short_lineEdit.text()
#         new_source = (authors, year, title, source, doi, short_citation)
#         if short_citation:
#             sql = '''SELECT "Short Citation" FROM "Sources"'''
#             if c.execute(sql):
#                 existing = c.fetchall()
#                 if short_citation in existing:
#                     msg = QtW.QMessageBox()
#                     msg.setIcon(QtW.QMessageBox.Critical)
#                     msg.setText("Error")
#                     msg.setInformativeText('This short citation already exists. Enter a unique short citation')
#                     msg.setWindowTitle("Error")
#                     msg.exec_()
#             return new_source
#         else:
#             msg = QtW.QMessageBox()
#             msg.setIcon(QtW.QMessageBox.Critical)
#             msg.setText("Error")
#             msg.setInformativeText('Short citation is required')
#             msg.setWindowTitle("Error")
#             msg.exec_()
#
#
# def create_lab_facility(db_file, new_facility):
#     """
#     Add a new row to the Lab facilities table
#     :param new_facility: tuple of data to be added to the table in the order
#         ("Lab Facility Name", "Lab Facility Description")
#     :param db_file: database file
#     :return:
#     """
#     # run New_source window
#     conn = sqlite3.connect(db_file)
#     with conn:
#         c = conn.cursor()
#         sql = '''INSERT INTO "Lab Facilities" ("Lab Facility Name", "Lab Facility Description")
#             VALUES(?,?)'''
#         c.execute(sql, new_facility)
#
#
# def read_lab_facility_form(c):
#     if NLF.rejected:
#         return []
#     elif NLF.accepted:
#         name = NLF.name_lineEdit.text()
#         description = NLF.description_lineEdit.text()
#         new_lab_facility = (name, description)
#         if name:
#             sql = '''SELECT "Lab Facility Name" FROM "Lab Facilities"'''
#             if c.execute(sql):
#                 existing = c.fetchall()
#                 if name in existing:
#                     msg = QtW.QMessageBox()
#                     msg.setIcon(QtW.QMessageBox.Critical)
#                     msg.setText("Error")
#                     msg.setInformativeText('This facility name already exists. Enter a unique facility')
#                     msg.setWindowTitle("Error")
#                     msg.exec_()
#             return new_lab_facility
#         else:
#             msg = QtW.QMessageBox()
#             msg.setIcon(QtW.QMessageBox.Critical)
#             msg.setText("Error")
#             msg.setInformativeText('Facility name is required')
#             msg.setWindowTitle("Error")
#             msg.exec_()

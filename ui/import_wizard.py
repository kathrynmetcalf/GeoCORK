import sys
import os
import json
import sqlite3
import pandas as pd
import qtawesome
from difflib import get_close_matches

from PyQt6 import QtCore
from PyQt6.QtSql import QSqlDatabase, QSqlQuery, QSqlRecord, QSqlTableModel
from openpyxl import load_workbook
from openpyxl.styles import Font, Color, PatternFill

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel,
    QComboBox, QTableWidget, QTableWidgetItem, QMessageBox, QHBoxLayout,
    QLineEdit, QInputDialog, QMenu, QDialog, QFormLayout, QSplitter, QAbstractItemView, QTableView
)
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import QBrush, QColor, QFont

from Functions import SQLUtils, Database_manager
from Functions.Database_manager import SavepointManager

from Functions.Table_classes import CheckableComboBox, CheckableSqlTableModel, CheckableSampleTableView

# Updated DB schema to include lab_facilities, source, analysis_method, instrument
DATABASE_FILE = 'yrrfgs.db'

ALL_POSSIBLE_TYPES = [
    "Auto",
    "ppm",
    "ppb",
    "% Conc.",
    "% Disc.",
    "Ma",
    "ka",
]

CONFIG_FILE = 'column_mappings.json'


class ColumnMapDialog(QDialog):
    """
    Dialog that lets the user choose both a field name
    and a data type for a given column.
    """
    def __init__(self, original_header, current_field, current_dtype, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Map Column: {original_header}")

        self.selected_field = current_field
        self.selected_dtype = current_dtype

        layout = QFormLayout()

        self.combo_field = QComboBox()
        self.combo_field.addItems(["SampleID", "AliquotID"] + SQLUtils.upb_possible_input_fields)
        existing_items = [self.combo_field.itemText(i) for i in range(self.combo_field.count())]
        if current_field in existing_items:
            self.combo_field.setCurrentText(current_field)
        layout.addRow("Field:", self.combo_field)

        # self.combo_dtype = QComboBox()
        # self.combo_dtype.addItem('Auto')
        # if current_dtype in SQLUtils.upb_possible_input_fields:
        #     self.combo_dtype.setCurrentText(current_dtype)
        # layout.addRow("Data Type:", self.combo_dtype)
        # # self.combo_dtype.hide()

        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.handle_ok)
        layout.addRow(self.btn_ok)

        self.setLayout(layout)

    def handle_ok(self):
        self.selected_field = self.combo_field.currentText()
        # self.selected_dtype = self.combo_dtype.currentText()
        self.accept()

    def get_field_and_type(self):
        return self.selected_field, self.selected_dtype


class MainWindow(QWidget):
    """
    Main window of the application:
      - Left table (pinned): Sample ID, Aliquot ID, Spot ID (editable).
      - Right table (main): Excel data + 4 optional columns appended
        for Lab Facilities, Source, Analysis Method, Instrument (all editable).
      - Context menus in both tables to set selected cells to a user-defined value.
    """
    def __init__(self):
        super().__init__()
        db = QSqlDatabase.addDatabase("QSQLITE")
        db.setDatabaseName("yrrfgs.db")
        db.open()

        test = QSqlQuery()
        test.prepare(f"pragma foreign_keys = OFF")
        if not test.exec():
            QMessageBox.critical(self, "Error", "Failed to connect to database.")
            sys.exit(1)

        test = QSqlQuery()
        test.prepare(f"DELETE FROM Samples")
        if not test.exec():
            QMessageBox.critical(self, "Error", "Failed to connect to database.")
            sys.exit(1)
        test = QSqlQuery()
        test.prepare(f"DELETE FROM Aliquots")
        if not test.exec():
            QMessageBox.critical(self, "Error", "Failed to connect to database.")
            sys.exit(1)
        test = QSqlQuery()
        test.prepare(f"DELETE FROM Spots")
        if not test.exec():
            QMessageBox.critical(self, "Error", "Failed to connect to database.")
            sys.exit(1)
        test = QSqlQuery()
        test.prepare(f"DELETE FROM UPbAnalyses")
        if not test.exec():
            QMessageBox.critical(self, "Error", "Failed to connect to database.")
            sys.exit(1)

        self.setWindowTitle("UPb Importer (Left & Right Tables + Context Menus)")
        self.setGeometry(100, 100, 1500, 600)

        main_layout = QVBoxLayout(self)

        # Top bar: file selection, sheet, etc.
        top_layout = QHBoxLayout()
        self.btn_select = QPushButton("Select Excel File")
        self.btn_select.clicked.connect(self.select_file)
        top_layout.addWidget(self.btn_select)

        self.label_file = QLabel("No file selected.")
        top_layout.addWidget(self.label_file)

        self.combo_sheets = QComboBox()
        top_layout.addWidget(self.combo_sheets)

        self.btn_load_sheet = QPushButton("Load Sheet")
        self.btn_load_sheet.clicked.connect(self.load_sheet)
        top_layout.addWidget(self.btn_load_sheet)

        # Delimiter label + line edit
        delimiter_label = QLabel("Delimiter:")
        delimiter_label.setFixedWidth(80)
        self.delimiter_edit = QLineEdit()
        self.delimiter_edit.setPlaceholderText("e.g., -, etc.")
        self.delimiter_edit.setFixedSize(QSize(100, 25))
        self.delimiter_edit.textChanged.connect(self.update_left_table_on_delimiter_change)  # Connect signal
        top_layout.addWidget(delimiter_label)
        top_layout.addWidget(self.delimiter_edit)

        main_layout.addLayout(top_layout)

        combo_box_layout = QHBoxLayout()
        combo_box_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Delimiter label + line edit
        delimiter_label = QLabel("Delimiter:")
        delimiter_label.setFixedWidth(50)
        self.delimiter_edit = QLineEdit()
        self.delimiter_edit.setPlaceholderText("e.g., -, etc.")
        self.delimiter_edit.setFixedSize(QSize(100, 25))
        self.delimiter_edit.textChanged.connect(self.update_left_table_on_delimiter_change)  # Connect signal
        combo_box_layout.addWidget(delimiter_label)
        combo_box_layout.addWidget(self.delimiter_edit)

        combo_box_layout.addStretch(1)

        combo_box_layout.addWidget(QLabel("Notice: These dropdowns will overwrite all data in the tables.   "), 1, Qt.AlignmentFlag.AlignLeft)

        # ComboBox for setting Reference
        self.combo_reference_comboBox = CheckableComboBox()
        self.combo_reference_comboBox.setFixedWidth(150)
        self.combo_reference_comboBox.set_single_click(True)

        self.combo_reference = CheckableSqlTableModel()
        self.combo_reference = self.set_table(self.combo_reference, '"References"')
        self.combo_reference_comboBox.setModel(self.combo_reference)
        self.combo_reference_comboBox.closing.connect(
            lambda: self.set_all_rows("ReferenceID", self.combo_reference))
        combo_box_layout.addWidget(QLabel("Reference"))
        combo_box_layout.addWidget(self.combo_reference_comboBox)
        self.combo_reference_comboBox.set_line_edit_text(None)

        # ComboBox for setting Instrument
        self.combo_instrument_comboBox = CheckableComboBox()
        self.combo_instrument_comboBox.setFixedWidth(150)
        self.combo_instrument_comboBox.set_single_click(True)

        self.combo_instrument = CheckableSqlTableModel()
        self.combo_instrument = self.set_table(self.combo_instrument, "Instruments")
        self.combo_instrument_comboBox.setModel(self.combo_instrument)
        self.combo_instrument_comboBox.closing.connect(
            lambda: self.set_all_rows("InstrumentID", self.combo_instrument))
        combo_box_layout.addWidget(QLabel("Instrument"))
        combo_box_layout.addWidget(self.combo_instrument_comboBox)
        self.combo_instrument_comboBox.set_line_edit_text(None)

        # ComboBox for setting LabFacility
        self.combo_lab_facility_comboBox = CheckableComboBox()
        self.combo_lab_facility_comboBox.setFixedWidth(150)
        self.combo_lab_facility_comboBox.set_single_click(True)

        self.combo_lab_facility = CheckableSqlTableModel()
        self.combo_lab_facility = self.set_table(self.combo_lab_facility, "LabFacilities")
        self.combo_lab_facility_comboBox.setModel(self.combo_lab_facility)
        self.combo_lab_facility_comboBox.closing.connect(
            lambda: self.set_all_rows("LabFacilityID", self.combo_lab_facility))
        combo_box_layout.addWidget(QLabel("Lab Facility"))
        combo_box_layout.addWidget(self.combo_lab_facility_comboBox)
        self.combo_lab_facility_comboBox.set_line_edit_text(None)

        # ComboBox for setting UPbAnalysisMethod
        self.combo_upb_analysis_method_comboBox = CheckableComboBox()
        self.combo_upb_analysis_method_comboBox.setFixedWidth(150)
        self.combo_upb_analysis_method_comboBox.set_single_click(True)

        self.combo_upb_analysis_method = CheckableSqlTableModel()
        self.combo_upb_analysis_method = self.set_table(self.combo_upb_analysis_method, "UPbAnalysisMethods")
        self.combo_upb_analysis_method_comboBox.setModel(self.combo_upb_analysis_method)
        self.combo_upb_analysis_method_comboBox.closing.connect(
            lambda: self.set_all_rows("UPbAnalysisMethodID", self.combo_upb_analysis_method))
        combo_box_layout.addWidget(QLabel("UPb Analysis Method"))
        combo_box_layout.addWidget(self.combo_upb_analysis_method_comboBox)
        self.combo_upb_analysis_method_comboBox.set_line_edit_text(None)

        main_layout.addLayout(combo_box_layout)

        formats_layout = QHBoxLayout()
        formats_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.ratio_error_combobox = QComboBox()
        self.ratio_error_combobox.setFixedWidth(100)
        self.ratio_error_combobox.addItems(['1σ Absolute', '2σ Absolute', '1σ Percent', '1σ Percent'])
        formats_layout.addWidget(QLabel("Ratio Error"))
        formats_layout.addWidget(self.ratio_error_combobox)

        self.age_error_combobox = QComboBox()
        self.age_error_combobox.setFixedWidth(100)
        self.age_error_combobox.addItems(['1σ Absolute', '2σ Absolute', '1σ Percent', '1σ Percent'])
        formats_layout.addWidget(QLabel("Age Error"))
        formats_layout.addWidget(self.age_error_combobox)

        self.conc_error_combobox = QComboBox()
        self.conc_error_combobox.setFixedWidth(150)
        self.conc_error_combobox.addItems(['Concordance Ratio', 'Concordance Percent', 'Discordance Ratio', 'Discordance Percent'])
        formats_layout.addWidget(QLabel("Ratio Error"))
        formats_layout.addWidget(self.conc_error_combobox)

        main_layout.addLayout(formats_layout)


        # Splitter for left (pinned) vs right (main) tables
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left pinned table: 3 columns for SampleID, AliquotID, SpotID
        self.left_table = QTableWidget()
        self.left_table.setColumnCount(3)
        self.left_table.setHorizontalHeaderLabels(["SampleID", "AliquotID", "SpotID"])
        self.left_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.left_table.customContextMenuRequested.connect(self.show_left_table_context_menu)

        # Right table for the actual Excel data
        self.right_table = QTableWidget()
        self.right_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.right_table.customContextMenuRequested.connect(self.show_right_table_context_menu)

        # Connect the header double-click signal to the handler
        header = self.right_table.horizontalHeader()
        header.sectionDoubleClicked.connect(self.handle_header_double_clicked)

        # Scroll synchronization (vertical)
        self.left_table.verticalScrollBar().valueChanged.connect(
            self.right_table.verticalScrollBar().setValue
        )
        self.right_table.verticalScrollBar().valueChanged.connect(
            self.left_table.verticalScrollBar().setValue
        )

        splitter.addWidget(self.left_table)
        splitter.addWidget(self.right_table)
        splitter.setStretchFactor(0, 0)  # left narrower
        splitter.setStretchFactor(1, 1)  # right expands

        main_layout.addWidget(splitter)

        # Bottom bar: mapping + import
        bottom_layout = QHBoxLayout()
        self.btn_save_mapping = QPushButton("Save Mapping")
        self.btn_save_mapping.clicked.connect(self.save_mapping)
        bottom_layout.addWidget(self.btn_save_mapping)

        self.btn_load_mapping = QPushButton("Load Mapping")
        self.btn_load_mapping.clicked.connect(self.load_mapping)
        bottom_layout.addWidget(self.btn_load_mapping)

        self.btn_import = QPushButton("Import to Database")
        self.btn_import.clicked.connect(self.check_and_import)
        bottom_layout.addWidget(self.btn_import)

        self.btn_add_column = QPushButton("Add Column")
        self.btn_add_column.clicked.connect(self.add_column)
        bottom_layout.addWidget(self.btn_add_column)

        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

        # DataFrame for the right table
        self.df = None
        # Mappings for right table columns
        self.column_mappings = {}
        # Rejected rows
        self.rejected_rows = set()

        # openpyxl workbook
        self.wb = None
        self.current_sheet_name = None

        # Icons for accepted/rejected
        self.rejected_icon = qtawesome.icon('fa5s.minus-circle', color='red', scale_factor=1.0)
        self.accepted_icon = qtawesome.icon('fa5s.check', color='green', scale_factor=1.0)

        # Flash fill connections
        self.left_table.cellChanged.connect(self.handle_cell_change)
        self.right_table.cellChanged.connect(self.handle_cell_change)

        self.right_table.cellClicked.connect(self.handle_cell_click)

    def closeEvent(self, a0):
        self.combo_reference_comboBox.disconnect()
        self.combo_instrument_comboBox.disconnect()
        self.combo_lab_facility_comboBox.disconnect()
        self.combo_upb_analysis_method_comboBox.disconnect()
        super().closeEvent(a0)

    def set_table(self, model, table: str):
        model.setTable(table)
        model.select()
        return model


    # ---------------------------
    #    Context Menu Methods
    # ---------------------------

    def handle_cell_click(self, row, column):
        """
        Handle cell clicks for specific columns and show a popup with a QSqlTableModel.
        Args:
            row (int): Row index of the clicked cell.
            column (int): Column index of the clicked cell.
        """
        # Determine the clicked column's header
        header_item = self.right_table.horizontalHeaderItem(column)
        if not header_item:
            return

        column_name = header_item.text()

        # Map column names to database tables
        column_to_table = {
            "ReferenceID": "References",
            "InstrumentID": "Instruments",
            "LabFacilityID": "LabFacilities",
            "UPbAnalysisMethodID": "UPbAnalysisMethods",
        }

        if column_name in column_to_table:
            table_name = column_to_table[column_name]
            self.show_table_popup(table_name, row, column)

    def show_table_popup(self, table_name, row, column):
        """
        Show a popup with a QSqlTableModel for the specified table.
        Args:
            table_name (str): Name of the database table to display.
        """

        # Create a QSqlTableModel and set the table
        model = CheckableSqlTableModel()
        model = self.set_table(model, table_name)

        # Create a QTableView to display the model
        combobox = CheckableComboBox()
        combobox.setModel(model)

        combobox.setGeometry(self.right_table.visualItemRect(self.right_table.item(row, column)))

        combobox.show()
        combobox.setFocus()

        # Close the ComboBox when it loses focus
        combobox.focusOutEvent = lambda event: self.cleanup_combobox(combobox, event)

    def add_column(self):
        """
        Add a new column to the table based on user input from the Column Map Dialog.
        """
        # Open the Column Map Dialog to let the user select a column name and data type
        dialog = ColumnMapDialog("New Column", "None", "Auto", self)
        if dialog.exec():
            selected_field, selected_dtype = dialog.get_field_and_type()

            # Ensure the user selected a valid field
            if selected_field == "None":
                QMessageBox.warning(self, "Invalid Selection", "Please select a valid column field.")
                return

            for col_idx in range(self.right_table.columnCount()):
                header = self.right_table.horizontalHeaderItem(col_idx)
                if header and header.text().startswith(selected_field):
                    QMessageBox.warning(self, "Duplicate Column", f"Column '{selected_field}' already exists.")
                    return

            # Insert the new column at the end of the table
            col_index = self.right_table.columnCount()
            self.right_table.insertColumn(col_index)

            # Set the column header
            header_text = f"{selected_field}"
            header_item = QTableWidgetItem(header_text)
            header_item.setBackground(QBrush(QColor("#ffffcc")))  # Light yellow background for new column
            self.right_table.setHorizontalHeaderItem(col_index, header_item)

            # Add the new column to the column mappings
            self.column_mappings[col_index] = (selected_field, selected_dtype)

            self.right_table.blockSignals(True)
            # Initialize the column cells with empty values
            for row in range(self.right_table.rowCount()):
                self.right_table.setItem(row, col_index, QTableWidgetItem(""))
            self.right_table.blockSignals(False)

            # Notify the user
            QMessageBox.information(self, "Column Added", f"Column '{header_text}' added successfully.")

    def show_left_table_context_menu(self, pos: QPoint):
        """
        Context menu for the left table (Sample ID, Aliquot ID, Spot ID).
        Allows setting all selected cells to a user-defined value.
        """
        menu = QMenu(self)
        set_value_action = menu.addAction("Set Selected Cells to Value...")

        action = menu.exec(self.left_table.mapToGlobal(pos))
        if action == set_value_action:
            new_value, ok = QInputDialog.getText(self, "Set Value", "Enter new value:")
            if ok:
                for item in self.left_table.selectedItems():
                    item.setText(new_value)

    def show_right_table_context_menu(self, pos: QPoint):
        """
        Context menu for the right table.
        Includes remove rows, mark rows rejected, unmark,
        and set selected cells to a user-defined value.
        """
        menu = QMenu(self)
        remove_action = menu.addAction("Remove Selected Rows")
        reject_action = menu.addAction("Mark Selected Rows as Rejected")
        accept_action = menu.addAction("Mark Selected Rows as Accepted")
        set_value_action = menu.addAction("Set Selected Cells to Value...")
        remove_column = menu.addAction('Remove Selected Column')

        action = menu.exec(self.right_table.mapToGlobal(pos))
        if action == remove_action:
            self.remove_selected_rows()
        elif action == reject_action:
            self.mark_selected_rows_rejected(True)
        elif action == accept_action:
            self.mark_selected_rows_rejected(False)
        elif action == set_value_action:
            new_value, ok = QInputDialog.getText(self, "Set Value", "Enter new value:")
            if ok:
                for item in self.right_table.selectedItems():
                    item.setText(new_value)
        elif action == remove_column:
            self.remove_selected_columns()

        self.repaint()

    # ---------------------------
    #     File & Sheet Loading
    # ---------------------------

    def handle_cell_change(self, row, column):
        """
        Handle cell value changes. Ask the user if they want to flash fill downward.
        """

        if self.sender() == self.left_table:
            target_table = self.left_table
        elif self.sender() == self.right_table:
            target_table = self.right_table
        else:
            return

        # Get the current value of the cell
        current_value = target_table.item(row, column).text().strip()

        # If the value is empty or invalid, ignore
        if not current_value:
            return

        # Check if the user wants to flash fill
        reply = QMessageBox.question(
            self, "Flash Fill Downward",
            "Do you want to auto-fill downward with this value for blank cells?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.flash_fill_downward(target_table, row, column, current_value)

    def flash_fill_downward(self, target_table, start_row, column, value):
        """
        Flash fill a column downward starting from a given row.
        """

        self.left_table.blockSignals(True)
        self.right_table.blockSignals(True)
        # Start from the next row and go downward
        for row in range(start_row + 1, target_table.rowCount()):
            item = target_table.item(row, column)

            # If the cell is blank, fill it with the given value
            if item is None or not item.text().strip():
                # If the cell doesn't exist, create it
                if item is None:
                    item = QTableWidgetItem()
                    target_table.setItem(row, column, item)

                # Set the value
                item.setText(value)
            else:
                # Stop when a non-blank value is encountered
                break
        self.left_table.blockSignals(False)
        self.right_table.blockSignals(False)

    def select_file(self):
        dlg = QFileDialog(self)
        path, _ = dlg.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
        if path:
            self.selected_file_path = path
            self.label_file.setText(f"Selected File: {os.path.basename(path)}")
            try:
                self.wb = load_workbook(path, data_only=True)
                self.combo_sheets.clear()
                self.combo_sheets.addItems(self.wb.sheetnames)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read Excel file:\n{e}")

    def load_sheet(self):
        if not hasattr(self, 'selected_file_path') or not self.selected_file_path:
            QMessageBox.warning(self, "No File", "Please select an Excel file first.")
            return
        sheet_name = self.combo_sheets.currentText()
        if not sheet_name:
            QMessageBox.warning(self, "No Sheet", "Please select a sheet.")
            return

        try:
            self.df = pd.read_excel(self.selected_file_path, sheet_name=sheet_name, engine="openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to parse sheet with pandas:\n{e}")
            return

        # Remove initial blank rows
        while not self.df.empty and self.df.iloc[0].isna().all():
            self.df = self.df.iloc[1:].reset_index(drop=True)

        # Reset mapping & rejections
        self.column_mappings.clear()
        self.rejected_rows.clear()

        # Display data on the right table
        self.display_right_table_with_styles(sheet_name)

        # Build the left table rows
        self.sync_left_table_rows()

        # Auto-guess column names
        # self.auto_guess_column_names()

    def display_right_table_with_styles(self, sheet_name):
        """
        Display the right table with openpyxl-based formatting
        + add 4 extra columns for Lab Facilities, Source, Analysis Method, Instrument (editable).
        """
        sheet = self.wb[sheet_name]
        self.right_table.clear()
        self.right_table.setRowCount(0)
        self.right_table.setColumnCount(0)

        rows, cols = self.df.shape
        # We'll add 4 extra columns for Lab Facilities, Source, Analysis Method, Instrument
        # extra_cols = 4
        self.right_table.setRowCount(rows)
        self.right_table.setColumnCount(cols)

        # Set column headers for the loaded data columns
        for c in range(cols):
            col_name = str(self.df.columns[c])
            hdr_item = QTableWidgetItem(col_name)
            self.right_table.setHorizontalHeaderItem(c, hdr_item)

        # Populate cells for the loaded data
        self.left_table.blockSignals(True)
        self.right_table.blockSignals(True)
        for r in range(rows):
            row_rejected = False
            for c in range(cols):
                cell = sheet.cell(row=r+1, column=c+1)
                value = self.df.iat[r, c]
                disp_val = "NULL" if pd.isna(value) or value == "" else str(value)

                item = QTableWidgetItem(disp_val)
                font = cell.font
                fill = cell.fill

                # Foreground
                if font.color and hasattr(font.color, "rgb") and isinstance(font.color.rgb, str):
                    hex_col = "#" + font.color.rgb[-6:]
                    item.setForeground(QBrush(QColor(hex_col)))
                    if hex_col.lower() == "#ff0000":
                        row_rejected = True
                # else:
                #     item.setForeground(QBrush(Qt.GlobalColor.black))

                qfont = QFont()
                qfont.setBold(font.bold if font.bold else False)
                qfont.setItalic(font.italic if font.italic else False)
                qfont.setStrikeOut(font.strike if font.strike else False)
                item.setFont(qfont)

                if font.strike:
                    row_rejected = True

                # Background
                if isinstance(fill, PatternFill) and fill.fgColor and fill.fgColor.rgb:
                    bg_hex = "#" + fill.fgColor.rgb[-6:]
                    if fill.fill_type and fill.fill_type != "none":
                        item.setBackground(QBrush(QColor(bg_hex)))

                self.right_table.setItem(r, c, item)

            if row_rejected:
                self.rejected_rows.add(r)

        self.left_table.blockSignals(False)
        self.right_table.blockSignals(False)
        # Setup vertical header icons
        for r in range(rows):
            self.update_row_icon(r, (r in self.rejected_rows))

        self.right_table.resizeColumnsToContents()

    def sync_left_table_rows(self):
        """
        Make the left table have the same row count as the right table
        and add editable cells for Sample ID, Aliquot ID, Spot ID.
        """
        self.left_table.blockSignals(True)
        row_count = self.right_table.rowCount()
        self.left_table.setRowCount(row_count)
        for r in range(row_count):
            for c in range(3):
                if not self.left_table.item(r, c):
                    self.left_table.setItem(r, c, QTableWidgetItem(""))
        self.left_table.blockSignals(False)

        self.left_table.resizeColumnsToContents()

    def auto_guess_column_names(self):
        """
        Use difflib to guess the best match from SQLUtils.upb_possible_input_fields for the right table columns
        (excluding the 4 appended columns).
        """
        import difflib
        cutoff = 0.5

        total_cols = self.right_table.columnCount()
        # Exclude appended columns for Lab, Source, Method, Instrument
        # main_cols = total_cols - 4 if (total_cols > 4 and self.lab_col is not None) else total_cols
        main_cols = total_cols
        for col_idx in range(main_cols):
            original_header = self.right_table.horizontalHeaderItem(col_idx).text()
            best = difflib.get_close_matches(original_header, SQLUtils.upb_possible_input_fields, n=1, cutoff=cutoff)
            if best:
                field = best[0]
                self.column_mappings[col_idx] = (field, "Auto")
                item = self.right_table.horizontalHeaderItem(col_idx)
                item.setText(f"{field}")
                item.setBackground(QBrush(QColor("#ffffcc")))
            else:
                self.column_mappings[col_idx] = ("None", "Auto")

    # ---------------------------
    #     Context Menu Logic
    # ---------------------------

    def set_all_rows(self, field, model):
        """
        Set all rows in the specified column to the given value.
        Args:
            field (str): The field name (e.g., 'Reference', 'Instrument').
            value (str): The value to set.
        """
        if model.tableName() == '"References"':
            name_col = 6
        else:
            name_col = 1
        # Determine the column index for the field

        for row in range(model.rowCount()):
            name_index = model.index(row, name_col)
            id_index = model.index(row, 0)

            if model.data(name_index, QtCore.Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked:
                checked_item_name = model.data(name_index, Qt.ItemDataRole.DisplayRole)
                checked_item_id = model.data(id_index, Qt.ItemDataRole.DisplayRole)


        field_to_column = {
            "ReferenceID": self.get_column_index("ReferenceID"),
            "Reference Display": self.get_column_index("Reference Display"),
            "InstrumentID": self.get_column_index("InstrumentID"),
            "Instrument Name": self.get_column_index("Instrument Name"),
            "LabFacilityID": self.get_column_index("LabFacilityID"),
            "Lab Facility Name": self.get_column_index("Lab Facility Name"),
            "UPbAnalysisMethodID": self.get_column_index("UPbAnalysisMethodID"),
            "UPb Analysis Method Name": self.get_column_index("UPb Analysis Method Name"),
        }

        column = field_to_column.get(field)
        if column is None:
            # msg = f"Column for '{field}' not found. Add missing columns to the import?"
            # reply = QMessageBox.question(self, 'Missing Columns', msg,
            #                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            #                              QMessageBox.StandardButton.Yes)
            #
            # if reply == QMessageBox.StandardButton.No:
            #     return

            # ADD ID Column to the tablewidget
            # Insert the new column at the end of the table
            col_index = self.right_table.columnCount()
            self.right_table.insertColumn(col_index)

            # Set the column header
            header_text = f"{field}"
            header_item = QTableWidgetItem(header_text)
            header_item.setBackground(QBrush(QColor("#ffffcc")))  # Light yellow background for new column
            self.right_table.setHorizontalHeaderItem(col_index, header_item)

            # Add the new column to the column mappings
            self.column_mappings[col_index] = (field, "Auto")

            self.right_table.blockSignals(True)
            # Initialize the column cells with empty values
            for row in range(self.right_table.rowCount()):
                self.right_table.setItem(row, col_index, QTableWidgetItem(str(checked_item_id)))
            self.right_table.blockSignals(False)
            self.right_table.hideColumn(col_index)

            # ADD Display Column to the tablewidget
            # Insert the new column at the end of the table
            col_index = self.right_table.columnCount()
            self.right_table.insertColumn(col_index)

            if field == "ReferenceID":
                display_column_name = "Reference Display"
            elif field == "InstrumentID":
                display_column_name = "Instrument Name"
            elif field == "LabFacilityID":
                display_column_name = "Lab Facility Name"
            elif field == "UPbAnalysisMethodID":
                display_column_name = "UPb Analysis Method Name"

            # Set the column header
            header_text = f"{display_column_name}"
            header_item = QTableWidgetItem(header_text)
            header_item.setBackground(QBrush(QColor("#ffffcc")))  # Light yellow background for new column
            self.right_table.setHorizontalHeaderItem(col_index, header_item)

            # Add the new column to the column mappings
            self.column_mappings[col_index] = (field, "Auto")

            self.right_table.blockSignals(True)
            # Initialize the column cells with empty values
            for row in range(self.right_table.rowCount()):
                self.right_table.setItem(row, col_index, QTableWidgetItem(checked_item_name))
            self.right_table.blockSignals(False)
        else:

            # Update all rows in the column
            self.right_table.blockSignals(True)

            field_to_column = {
                "ReferenceID": self.get_column_index("ReferenceID"),
                "Reference Display": self.get_column_index("Reference Display"),
                "InstrumentID": self.get_column_index("InstrumentID"),
                "Instrument Name": self.get_column_index("Instrument Name"),
                "LabFacilityID": self.get_column_index("LabFacilityID"),
                "Lab Facility Name": self.get_column_index("Lab Facility Name"),
                "UPbAnalysisMethodID": self.get_column_index("UPbAnalysisMethodID"),
                "UPb Analysis Method Name": self.get_column_index("UPb Analysis Method Name"),
            }

            if field == "ReferenceID":
                display_column_name = "Reference Display"
            elif field == "InstrumentID":
                display_column_name = "Instrument Name"
            elif field == "LabFacilityID":
                display_column_name = "Lab Facility Name"
            elif field == "UPbAnalysisMethodID":
                display_column_name = "UPb Analysis Method Name"
            id_column = field_to_column.get(field)
            name_column = field_to_column.get(display_column_name)
            self.right_table.blockSignals(True)
            for row in range(self.right_table.rowCount()):
                item = self.right_table.item(row, id_column)
                if item is None:
                    item = QTableWidgetItem()
                    self.right_table.setItem(row, id_column, item)
                item.setText(str(checked_item_id))

                item = self.right_table.item(row, name_column)
                if item is None:
                    item = QTableWidgetItem()
                    self.right_table.setItem(row, name_column, item)
                item.setText(str(checked_item_name))
            self.right_table.blockSignals(False)

        QMessageBox.information(self, "Success", f"All rows updated with '{str(checked_item_name)}' for {field}.")

    def get_column_index(self, header_name):
        """
        Get the column index of a header by its name.
        Args:
            header_name (str): The name of the header.
        Returns:
            int: The column index, or None if not found.
        """
        for col in range(self.right_table.columnCount()):
            header_item = self.right_table.horizontalHeaderItem(col)
            if header_item and header_item.text().startswith(header_name):
                return col
        return None

    def update_row_icon(self, row_idx, rejected):
        header_item = QTableWidgetItem()
        header_item.setText(str(row_idx + 1))
        if rejected:
            header_item.setIcon(self.rejected_icon)
        else:
            header_item.setIcon(self.accepted_icon)
        self.right_table.setVerticalHeaderItem(row_idx, header_item)

    # Existing logic for removing rows, marking them rejected, etc.

    def remove_selected_rows(self):
        selected_rows = {i.row() for i in self.right_table.selectedItems()}
        if not selected_rows:
            return

        sr = sorted(selected_rows, reverse=True)
        if self.df is not None and len(self.df) > 0:
            self.df.drop(self.df.index[sr], inplace=True)
            self.df.reset_index(drop=True, inplace=True)

        for r in sr:
            self.right_table.removeRow(r)
            self.left_table.removeRow(r)
            self.rejected_rows.discard(r)
        self.update_vertical_headers()

    def remove_selected_columns(self):
        """
        Remove selected columns from the right table, the column mappings,
        and associated data structures.
        """
        selected_columns = {i.column() for i in self.right_table.selectedItems()}
        if not selected_columns:
            return

        # Sort selected columns in descending order to remove from the rightmost column
        sc = sorted(selected_columns, reverse=True)

        for col in sc:
            # Remove the column from the right table
            self.right_table.removeColumn(col)

            # Update column mappings to reflect the removed column
            if col in self.column_mappings:
                del self.column_mappings[col]

            # Shift column mappings for columns after the removed one
            self.column_mappings = {
                (idx - 1 if idx > col else idx): value
                for idx, value in self.column_mappings.items()
            }

        # Notify the user
        QMessageBox.information(self, "Columns Removed", "Selected columns have been successfully removed.")

    def update_vertical_headers(self):
        """
        Update the vertical headers to ensure they match the current row indices.
        """
        row_count = self.right_table.rowCount()
        for row_idx in range(row_count):
            header_item = QTableWidgetItem(str(row_idx + 1))  # Update row numbers
            # Check if the row is rejected and set the appropriate icon
            if row_idx in self.rejected_rows:
                header_item.setIcon(self.rejected_icon)
            else:
                header_item.setIcon(self.accepted_icon)
            self.right_table.setVerticalHeaderItem(row_idx, header_item)

    def mark_selected_rows_rejected(self, rejected: bool):
        selected_rows = {i.row() for i in self.right_table.selectedItems()}
        if not selected_rows:
            return

        for r in selected_rows:
            if rejected:
                self.rejected_rows.add(r)
            else:
                self.rejected_rows.discard(r)
            self.update_row_icon(r, rejected)

    # ---------------------------
    #     Header Double Click
    # ---------------------------

    def handle_header_double_clicked(self, logical_index):
        """
        Double-click on a right table header => open mapping dialog.
        """
        item = self.right_table.horizontalHeaderItem(logical_index)
        if not item:
            return
        original_header_text = item.text()
        curr_map = self.column_mappings.get(logical_index, ("None", "Auto"))
        dialog = ColumnMapDialog(original_header_text, curr_map[0], curr_map[1], self)
        if dialog.exec():
            new_field, new_dtype = dialog.get_field_and_type()
            if new_field == "None":
                if logical_index in self.column_mappings:
                    del self.column_mappings[logical_index]
                item.setText(original_header_text)
                item.setBackground(QBrush(Qt.GlobalColor.White))
            else:
                self.column_mappings[logical_index] = (new_field, new_dtype)
                item.setText(f"{new_field} ({new_dtype})")
                item.setBackground(QBrush(Qt.GlobalColor.green))

                # If it’s Sample ID / Aliquot ID / Spot ID, auto-populate left table
                if new_field == "SpotID":
                    self.auto_split_sample_spot(logical_index)

    def update_left_table_on_delimiter_change(self):
        """
        Update the left table's Sample ID and Spot ID columns whenever the delimiter value changes.
        """
        # Find the right table column mapped to "Spot ID"
        spot_id_column = None
        for col_idx, (field_name, _) in self.column_mappings.items():
            if field_name == "SpotID":
                spot_id_column = col_idx
                break

        if spot_id_column is not None:
            self.auto_split_sample_spot(spot_id_column)

    def auto_split_sample_spot(self, col_idx):
        """
        Split the right table's Spot ID column values into Sample ID and Spot ID
        using the delimiter, and populate the left table accordingly.
        """
        delimiter = self.delimiter_edit.text().strip()
        # if not delimiter:
        #     # QMessageBox.warning(self, "No Delimiter", "Please specify a delimiter to split Spot IDs.")
        #     return

        row_count = self.right_table.rowCount()

        for r in range(row_count):
            cell_item = self.right_table.item(r, col_idx)
            if not cell_item:
                continue

            spot_id_value = cell_item.text().strip()

            if delimiter in spot_id_value and delimiter:
                # Split based on the delimiter
                sample_id, spot_id = spot_id_value.split(delimiter, 1)
            else:
                # No delimiter found, treat the entire value as Spot ID
                sample_id = ""
                spot_id = spot_id_value

            # Update the left table
            self.left_table.blockSignals(True)
            self.left_table.setItem(r, 0, QTableWidgetItem(sample_id))  # Sample ID
            self.left_table.setItem(r, 2, QTableWidgetItem(spot_id))  # Spot ID
            self.left_table.blockSignals(False)

    def save_mapping(self):
        if not self.column_mappings:
            QMessageBox.warning(self, "No Mapping", "No columns have been mapped yet.")
            return

        name, ok = QInputDialog.getText(self, "Save Mapping", "Enter a name for this mapping:")
        if ok and name:
            try:
                if os.path.exists(CONFIG_FILE):
                    with open(CONFIG_FILE, 'r') as f:
                        configs = json.load(f)
                else:
                    configs = {}

                jmap = {str(k): {"field": v[0], "type": v[1]} for k, v in self.column_mappings.items()}
                configs[name] = jmap
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(configs, f, indent=4)
                QMessageBox.information(self, "Saved", f"Mapping '{name}' saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save mapping:\n{e}")

    def load_mapping(self):
        if not os.path.exists(CONFIG_FILE):
            QMessageBox.warning(self, "No Config", "No configuration file found.")
            return

        try:
            with open(CONFIG_FILE, 'r') as f:
                configs = json.load(f)
            if not configs:
                QMessageBox.warning(self, "No Mappings", "No mappings found in configuration.")
                return

            items = list(configs.keys())
            name, ok = QInputDialog.getItem(self, "Load Mapping", "Select a mapping to load:", items, 0, False)
            if ok and name:
                loaded = configs[name]
                self.column_mappings.clear()
                for k_str, v in loaded.items():
                    idx = int(k_str)
                    self.column_mappings[idx] = (v["field"], v["type"])

                total_cols = self.right_table.columnCount()
                for col_idx in range(total_cols):
                    hdr_item = self.right_table.horizontalHeaderItem(col_idx)
                    if not hdr_item:
                        continue
                    if col_idx in self.column_mappings:
                        f_name, f_type = self.column_mappings[col_idx]
                        hdr_item.setText(f"{f_name} ({f_type})")
                        hdr_item.setBackground(QBrush(QColor("#ffffcc")))
                    else:
                        hdr_item.setBackground(QBrush(Qt.GlobalColor.White))

                QMessageBox.information(self, "Loaded", f"Mapping '{name}' loaded successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load mapping:\n{e}")

    def check_empty_cells_in_left_table(self):
        empty_cells = []
        for row in range(self.left_table.rowCount()):
            for col in range(3):  # Columns for Sample ID, Aliquot ID, Spot ID
                cell = self.left_table.item(row, col)
                if cell is None or cell.text().strip() == "":
                    empty_cells.append((row, col))
        return empty_cells

    def ask_to_use_default_values(self, empty_cells):
        """
        Prompt the user to confirm whether to use autogenerated default values for empty cells.
        """
        missing_count = len(empty_cells)
        msg = f"{missing_count} cells are empty. Would you like to use autogenerated default values?"
        reply = QMessageBox.question(self, 'Missing Values', msg,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.Yes)

        if reply == QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

    def fill_empty_cells_with_defaults(self, empty_cells):
        """
        Fill the empty cells in the left table with default values.
        """
        self.left_table.blockSignals(True)

        # Initialize variables for tracking SampleID and counter
        current_sample_id = None
        aliquot_counter = 0

        for row, col in empty_cells:
            if col == 0:  # Sample ID
                # If Sample ID is missing, set a default value
                if not self.left_table.item(row, col) or not self.left_table.item(row, col).text().strip():
                    self.left_table.setItem(row, col, QTableWidgetItem("DefaultSample"))
                current_sample_id = self.left_table.item(row, col).text().strip()  # Update current SampleID
                aliquot_counter = 0  # Reset counter for new SampleID

            elif col == 1:  # Aliquot ID
                # If SampleID exists, create AliquotID with the counter
                sample_id_item = self.left_table.item(row, col - 1)
                if sample_id_item and sample_id_item.text().strip():
                    sample_id = sample_id_item.text().strip()
                    if sample_id != current_sample_id:
                        current_sample_id = sample_id
                        aliquot_counter = 0  # Reset counter for new SampleID
                    aliquot_counter += 1
                    self.left_table.setItem(row, col, QTableWidgetItem(f"{sample_id}-{aliquot_counter}"))

            elif col == 2:  # Spot ID
                # Set a default value for Spot ID
                if not self.left_table.item(row, col) or not self.left_table.item(row, col).text().strip():
                    self.left_table.setItem(row, col, QTableWidgetItem("DefaultSpot"))

            # Highlight the updated cell
            self.left_table.item(row, col).setBackground(Qt.GlobalColor.yellow)

        self.left_table.blockSignals(False)

    def check_and_import(self):
        # Step 1: Check for empty cells in the left table
        empty_cells = self.check_empty_cells_in_left_table()

        if empty_cells:
            # Step 2: Show dialog to ask if the user wants to use default values
            use_defaults = self.ask_to_use_default_values(empty_cells)

            if use_defaults:
                # Step 3: Fill empty cells with default values
                self.fill_empty_cells_with_defaults(empty_cells)

                # Optional: Give user a chance to review and adjust the values
                QMessageBox.information(self, "Review",
                                        "The empty cells have been filled with default values. Please review before clicking import again.")
        else:
            # Step 4: Proceed with import
            self.import_to_db()

    # ---------------------------
    #      Import to DB
    # ---------------------------

    def import_to_db(self):
        row_count = self.right_table.rowCount()
        if row_count == 0:
            QMessageBox.warning(self, "No Data", "There are no rows to import.")
            return

        # savepoint_manager = SavepointManager.get_instance()
        # Database_manager.create_savepoint('before_upb_import')

        inserted_count = 0

        try:
            for row_idx in range(row_count):
                # Build a record dict with every key initialized to None
                record = {field: None for field in SQLUtils.upb_possible_input_fields}
                if row_idx in self.rejected_rows:
                    record['Rejected'] = True
                else:
                    record['Rejected'] = False

                record['RatioErrorTypeID'] = self.ratio_error_combobox.currentIndex()
                record['AgeErrorTypeID'] = self.age_error_combobox.currentIndex()
                record['ConcordanceTypeID'] = self.conc_error_combobox.currentIndex()


                # Populate the left-table items (sample_id, aliquot_id, spot_id)
                sample_id_item = self.left_table.item(row_idx, 0)
                aliquot_id_item = self.left_table.item(row_idx, 1)
                spot_id_item = self.left_table.item(row_idx, 2)


                record["SampleID"] = sample_id_item.text().strip() if sample_id_item else None
                record["AliquotID"] = aliquot_id_item.text().strip() if aliquot_id_item else None
                record["SpotID"] = spot_id_item.text().strip() if spot_id_item else None

                # Find matching SampleID or create new
                sample_query = QSqlQuery()
                sample_query.prepare(f"SELECT SampleID FROM Samples WHERE SampleName=:name COLLATE NOCASE")
                sample_query.bindValue(":name", record["SampleID"])

                if sample_query.exec():
                    if sample_query.next():
                        # found matching samplename in database, will use that sample ID
                        record["SampleID"] = sample_query.value(0)
                    else:
                        # no matching samplename in database, will create new one.
                        create_sample = QSqlQuery()
                        create_sample.prepare('INSERT INTO Samples (SampleName) VALUES (:name)')
                        create_sample.bindValue(":name", record["SampleID"])

                        if not create_sample.exec():
                            print("Failed to execute query:", create_sample.lastError().text())
                        else:
                            record["SampleID"] = create_sample.lastInsertId()
                else:
                    print("Failed to execute query:", sample_query.lastError().text())


                # Find matching AliquotID or create new
                aliquot_query = QSqlQuery()
                aliquot_query.prepare('SELECT AliquotID FROM Aliquots WHERE AliquotName=:name COLLATE NOCASE AND SampleID=:sample_id')
                aliquot_query.bindValue(":name", record["AliquotID"])
                aliquot_query.bindValue(":sample_id", record["SampleID"])

                if aliquot_query.exec():
                    if aliquot_query.next():
                        # found matching samplename in database, will use that sample ID
                        record["AliquotID"] = aliquot_query.value(0)
                    else:
                        # no matching samplename in database, will create new one.
                        create_aliquot = QSqlQuery()
                        create_aliquot.prepare('INSERT INTO Aliquots (AliquotName, SampleID) VALUES (:name, :sample_id)')
                        create_aliquot.bindValue(":name", record["AliquotID"])
                        create_aliquot.bindValue(":sample_id", record["SampleID"])

                        if not create_aliquot.exec():
                            print("Failed to create_aliquot execute query:", create_aliquot.lastError().text())
                        else:
                            record["AliquotID"] = create_aliquot.lastInsertId()
                else:
                    print("Failed to select_aliquot execute query:", aliquot_query.lastError().text())

                # Find matching SpotID or create new
                spot_query = QSqlQuery()
                spot_query.prepare(
                    'SELECT SpotID FROM Spots WHERE SpotName=:name COLLATE NOCASE AND AliquotID=:aliquot_id')
                spot_query.bindValue(":name", record["SpotID"])
                spot_query.bindValue(":aliquot_id", record["AliquotID"])

                if spot_query.exec():
                    if spot_query.next():
                        # found matching samplename in database, will use that sample ID
                        record["SpotID"] = spot_query.value(0)
                    else:
                        # no matching samplename in database, will create new one.
                        create_spot = QSqlQuery()

                        create_spot.prepare(
                            'INSERT INTO Spots (SpotName, AliquotID) VALUES (:name, :aliquot_id)')
                        create_spot.bindValue(":name", record["SpotID"])
                        create_spot.bindValue(":aliquot_id", record["AliquotID"])

                        if not create_spot.exec():
                            print("Failed to execute query:", create_spot.lastError().text())
                        else:
                            record["SpotID"] = create_spot.lastInsertId()
                else:
                    print("Failed to execute query:", spot_query.lastError().text())

                # by this point a valid Sample, Aliquot, and Spot should be created.

                # Process the main columns from the mapping.
                # In your code, you might reduce main_cols by 4 if these appended columns
                # are always the last 4 columns. Adjust logic as needed.
                main_cols = self.right_table.columnCount()
                for col_idx in range(main_cols):
                    if col_idx not in self.column_mappings:
                        continue

                    field_name, data_type = self.column_mappings[col_idx]
                    if field_name == "None" or field_name in ('SampleID', 'AliquotID', 'SpotID'):
                        continue

                    cell_item = self.right_table.item(row_idx, col_idx)
                    if not cell_item:
                        continue

                    cell_text = cell_item.text().strip()
                    if cell_text.upper() == "NULL":
                        record[field_name] = None
                    else:
                        record[field_name] = cell_text

                field_names = ", ".join([f'[{field}]' for field in SQLUtils.upb_possible_input_fields])
                placeholders = ', '.join(
                    [f':{field.replace('/', '').replace('*', '')}' for field in SQLUtils.upb_possible_input_fields])
                insert_sql = f"""
                            INSERT INTO UPbAnalyses (
                                {field_names}
                            )
                            VALUES (
                                {placeholders}
                            )
                        """
                print(insert_sql)

                # Finally insert the row
                insert_query = QSqlQuery()

                if not insert_query.prepare(insert_sql):
                    print("Failed to execute prepare:", insert_query.lastError().text())
                    sys.exit(1)
                record_count = 0
                print("Keys in Record:", list(record.keys()))
                for key, value in record.items():
                    if key == "SampleID" or key == "AliquotID":
                        continue #.replace('/', '_').replace('*', '_')
                    print(f"Binding: {key} | :{key.replace('/', '').replace('*', '')}  -> {value}")
                    insert_query.bindValue(f":{key.replace('/', '').replace('*', '')}", value)
                    record_count += 1
                print('binded record count:', record_count)
                if not insert_query.exec():

                    print(f"Error executing query: {insert_query.lastError().text()}")
                    print(insert_query.executedQuery())
                    for value in insert_query.boundValues():
                        print(value)

                inserted_count += 1

            # Database_manager.release_savepoint('before_upb_import')
            QMessageBox.information(self, "Success", f"Imported {inserted_count} rows into the database.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import data:\n{e}")
            # Database_manager.rollback_savepoint('before_upb_import')
        QSqlDatabase().commit()


if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
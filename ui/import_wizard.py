import sys
import os
import json
import sqlite3
import pandas as pd
import qtawesome
from difflib import get_close_matches

from openpyxl import load_workbook
from openpyxl.styles import Font, Color, PatternFill

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel,
    QComboBox, QTableWidget, QTableWidgetItem, QMessageBox, QHBoxLayout,
    QLineEdit, QInputDialog, QMenu, QDialog, QFormLayout, QSplitter, QAbstractItemView
)
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import QBrush, QColor, QFont

# Name of the local SQLite database file
DATABASE_FILE = 'upb_data.db'

# Fields the user can map columns to (some can be blank/None)
ALL_POSSIBLE_FIELDS = [
    "Pb204cps", "Pb206cps", "Pb207cps", "Pb208cps", "Pb*cps",
    "Th232cps", "U235cps", "U238cps", "Uppm", "Thppm",
    "CalculatedU/Th", "CalculatedTh/U", "Calculated206Pb/207Pb",
    "Calculated207Pb/206Pb", "Calculated207Pb/235U", "Calculated235U/207Pb",
    "Calculated206Pb/238U", "Calculated238U/206Pb", "Calculated208Pb/232Th",
    "Calculated232Th/208Pb", "Calculated238U/232Th", "Calculated232Th/238U",
    "Calculated204Pb/238U", "Calculated238U/204Pb", "Calculated206Pb/204Pb",
    "Calculated204Pb/206Pb", "Calculated207Pb/204Pb", "Calculated204Pb/207Pb",
    "Calculated208Pb/204Pb", "Calculated204Pb/208Pb", "Concordance", "Rejected",
    "UPbAnalysisCreated", "UPbAnalysisModified", "Calculated207Pb/206PbAge",
    "Calculated206Pb/238UAge", "Calculated207Pb/235UAge", "Calculated208Pb/232ThAge",
    "CalculatedSpotSize", "Calculated207Pb/206PbAgeError", "Calculated207Pb/235UAgeError",
    "Calculated206Pb/238UAgeError", "Calculated208Pb/232ThAgeError", "BestAge",
    "CalculatedBestAgeError", "Calculated206Pb/207PbError", "Calculated207Pb/206PbError",
    "Calculated207Pb/235UError", "Calculated235U/207PbError", "Calculated206Pb/238UError",
    "Calculated238U/206PbError", "Calculated208Pb/232ThError", "Calculated232Th/208PbError",
    "Calculated238U/232ThError", "Calculated232Th/238UError", "Calculated204Pb/238UError",
    "Calculated238U/204PbError", "Calculated206Pb/204PbError", "Calculated204Pb/206PbError",
    "Calculated207Pb/204PbError", "Calculated204Pb/207PbError", "Calculated208Pb/204PbError",
    "Calculated204Pb/208PbError"
]

# Some typical data types we might assign (ppm, %, Ma, etc.)
ALL_POSSIBLE_TYPES = [
    "Auto",
    "ppm",
    "ppb",
    "% Conc.",
    "% Disc.",
    "Ma",
    "ka",
    "text"
]

# Configuration file to store column mappings
CONFIG_FILE = 'column_mappings.json'

def init_db():
    """
    Initialize the SQLite database and create the upb_samples table if it does not exist.
    Returns a sqlite3.Connection object.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS upb_samples(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id TEXT,
            aliquot_id TEXT,
            spot_id TEXT,
            u REAL,
            pb REAL,
            age REAL,
            rejected BOOLEAN DEFAULT 0
        )
    """)
    conn.commit()
    return conn


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
        self.combo_field.addItems(ALL_POSSIBLE_FIELDS + ["Sample ID", "Aliquot ID", "Spot ID"])
        if current_field in [self.combo_field.itemText(i) for i in range(self.combo_field.count())]:
            self.combo_field.setCurrentText(current_field)
        layout.addRow("Field:", self.combo_field)

        self.combo_dtype = QComboBox()
        self.combo_dtype.addItems(ALL_POSSIBLE_TYPES)
        if current_dtype in ALL_POSSIBLE_TYPES:
            self.combo_dtype.setCurrentText(current_dtype)
        layout.addRow("Data Type:", self.combo_dtype)

        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.handle_ok)
        layout.addRow(self.btn_ok)

        self.setLayout(layout)

    def handle_ok(self):
        self.selected_field = self.combo_field.currentText()
        self.selected_dtype = self.combo_dtype.currentText()
        self.accept()

    def get_field_and_type(self):
        return self.selected_field, self.selected_dtype


class MainWindow(QWidget):
    """
    Main window of the application with:
      - Left pinned table: 3 columns for Sample ID, Aliquot ID, Spot ID
      - Right table: actual data from Excel
      - Delimiter handling for "Sample ID" mapping (auto-split into Sample ID + Spot ID)
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UPb Importer (Pinned Left Table + Auto ID Sync)")
        self.setGeometry(100, 100, 1500, 600)

        self.conn = init_db()

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
        self.delimiter_edit.setPlaceholderText("(e.g., '-')")
        self.delimiter_edit.setFixedSize(QSize(50, 20))
        self.delimiter_edit.textChanged.connect(self.update_left_table_on_delimiter_change)  # Connect signal
        top_layout.addWidget(delimiter_label)
        top_layout.addWidget(self.delimiter_edit)

        main_layout.addLayout(top_layout)

        # Splitter for left (pinned) vs right (main) tables
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left pinned table: 3 columns for SampleID, AliquotID, SpotID
        self.left_table = QTableWidget()
        self.left_table.setColumnCount(3)
        self.left_table.setHorizontalHeaderLabels(["Sample ID", "Aliquot ID", "Spot ID"])
        self.left_table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)

        # Right table for the actual Excel data
        self.right_table = QTableWidget()
        self.right_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.right_table.customContextMenuRequested.connect(self.show_table_context_menu)

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
        self.btn_import.clicked.connect(self.import_to_db)
        bottom_layout.addWidget(self.btn_import)

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

    def select_file(self):
        """
        Open file dialog, load workbook
        """
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
        """
        Load the chosen sheet into a DataFrame, skip blank rows,
        display in right_table with styles, create matching rows in left_table.
        """
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
        self.auto_guess_column_names()

    def display_right_table_with_styles(self, sheet_name):
        """
        Display the right table with openpyxl-based formatting
        and auto-detect if row is rejected.
        """
        sheet = self.wb[sheet_name]
        self.right_table.clear()
        self.right_table.setRowCount(0)
        self.right_table.setColumnCount(0)

        rows, cols = self.df.shape
        self.right_table.setRowCount(rows)
        self.right_table.setColumnCount(cols)

        # Set column headers
        for c in range(cols):
            col_name = str(self.df.columns[c])
            hdr_item = QTableWidgetItem(col_name)
            self.right_table.setHorizontalHeaderItem(c, hdr_item)

        # Populate cells
        for r in range(rows):
            row_rejected = False
            for c in range(cols):
                cell = sheet.cell(row=r+1, column=c+1)
                value = self.df.iat[r, c]
                disp_val = "NULL" if pd.isna(value) or value == "" else str(value)

                item = QTableWidgetItem(disp_val)

                # Font/color
                font = cell.font
                fill = cell.fill

                # Foreground
                if font.color and hasattr(font.color, "rgb") and isinstance(font.color.rgb, str):
                    hex_col = "#" + font.color.rgb[-6:]
                    item.setForeground(QBrush(QColor(hex_col)))
                    # If pure red, mark row rejected
                    if hex_col.lower() == "#ff0000":
                        row_rejected = True
                else:
                    item.setForeground(QBrush(Qt.GlobalColor.black))

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

        # Setup vertical header icons
        for r in range(rows):
            self.update_row_icon(r, (r in self.rejected_rows))

        self.right_table.resizeColumnsToContents()

    def sync_left_table_rows(self):
        """
        Make the left table have the same row count as the right table
        and add editable cells for Sample ID, Aliquot ID, Spot ID.
        """
        row_count = self.right_table.rowCount()
        self.left_table.setRowCount(row_count)
        for r in range(row_count):
            # If there's already an item, keep it, otherwise create new
            for c in range(3):
                if not self.left_table.item(r, c):
                    self.left_table.setItem(r, c, QTableWidgetItem(""))

        self.left_table.resizeColumnsToContents()

    def auto_guess_column_names(self):
        """
        Use difflib to guess the best match from ALL_POSSIBLE_FIELDS for the right table columns.
        """
        import difflib
        cutoff = 0.5
        for col_idx in range(self.right_table.columnCount()):
            original_header = self.right_table.horizontalHeaderItem(col_idx).text()
            best = difflib.get_close_matches(original_header, ALL_POSSIBLE_FIELDS, n=1, cutoff=cutoff)
            if best:
                field = best[0]
                self.column_mappings[col_idx] = (field, "Auto")
                # Update the header
                item = self.right_table.horizontalHeaderItem(col_idx)
                item.setText(f"{field} (Auto)")
                item.setBackground(QBrush(QColor("#ffffcc")))
            else:
                self.column_mappings[col_idx] = ("None", "Auto")

    def update_row_icon(self, row_idx, rejected):
        """
        Update the vertical header icon for the right table to show accepted/rejected.
        """
        header_item = QTableWidgetItem()
        header_item.setText(str(row_idx + 1))
        if rejected:
            header_item.setIcon(self.rejected_icon)
        else:
            header_item.setIcon(self.accepted_icon)
        self.right_table.setVerticalHeaderItem(row_idx, header_item)

    def show_table_context_menu(self, pos: QPoint):
        """
        Context menu for removing rows or marking them Rejected/Accepted.
        """
        menu = QMenu(self)
        remove_action = menu.addAction("Remove Selected Rows")
        reject_action = menu.addAction("Mark Selected Rows as Rejected")
        accept_action = menu.addAction("Unmark Selected Rows as Rejected")

        action = menu.exec(self.right_table.mapToGlobal(pos))
        if action == remove_action:
            self.remove_selected_rows()
        elif action == reject_action:
            self.mark_selected_rows_rejected(True)
        elif action == accept_action:
            self.mark_selected_rows_rejected(False)

    def remove_selected_rows(self):
        """
        Remove selected rows from both tables and from df.
        """
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

        for r in sr:
            self.rejected_rows.discard(r)

    def mark_selected_rows_rejected(self, rejected: bool):
        """
        Mark or unmark selected rows as Rejected in the right table.
        """
        selected_rows = {i.row() for i in self.right_table.selectedItems()}
        if not selected_rows:
            return

        for r in selected_rows:
            if rejected:
                self.rejected_rows.add(r)
            else:
                self.rejected_rows.discard(r)
            self.update_row_icon(r, rejected)

    def handle_header_double_clicked(self, logical_index):
        """
        Double-click on a right table header => open mapping dialog.
        If user sets "Sample ID", "Aliquot ID", or "Spot ID",
        auto-fill the left table from that column.
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
                item.setBackground(QBrush(QColor("#ffffcc")))

                # If it’s Sample ID / Aliquot ID / Spot ID, auto-populate left table
                if new_field == "Spot ID":
                    self.auto_split_sample_spot(logical_index)

    def update_left_table_on_delimiter_change(self):
        """
        Update the left table's Sample ID and Spot ID columns whenever the delimiter value changes.
        """
        # Find the right table column mapped to "Spot ID"
        spot_id_column = None
        for col_idx, (field_name, _) in self.column_mappings.items():
            if field_name == "Spot ID":
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
            self.left_table.setItem(r, 0, QTableWidgetItem(sample_id))  # Sample ID
            self.left_table.setItem(r, 2, QTableWidgetItem(spot_id))  # Spot ID

    def save_mapping(self):
        """
        Save the column mappings to a JSON file.
        """
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
        """
        Load a column mapping from JSON and apply to the right table.
        Then also auto-fill the pinned columns if they're mapped to Sample/Aliquot/Spot.
        """
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

                # Apply to header
                for col_idx in range(self.right_table.columnCount()):
                    hdr_item = self.right_table.horizontalHeaderItem(col_idx)
                    if not hdr_item:
                        continue
                    if col_idx in self.column_mappings:
                        f_name, f_type = self.column_mappings[col_idx]
                        hdr_item.setText(f"{f_name} ({f_type})")
                        hdr_item.setBackground(QBrush(QColor("#ffffcc")))
                    else:
                        hdr_item.setBackground(QBrush(Qt.GlobalColor.White))

                # Also auto-fill pinned columns for Sample/Aliquot/Spot
                for col_idx, (f_name, f_type) in self.column_mappings.items():
                    if f_name in ("Sample ID", "Aliquot ID", "Spot ID"):
                        self.auto_fill_pinned_ids(f_name, col_idx)

                QMessageBox.information(self, "Loaded", f"Mapping '{name}' loaded successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load mapping:\n{e}")

    def import_to_db(self):
        """
        Insert rows into the DB:
         - We read "Sample ID", "Aliquot ID", "Spot ID" from left_table
         - We read mapped columns from right_table
         - 'rejected' from self.rejected_rows
        """
        row_count = self.right_table.rowCount()
        if row_count == 0:
            QMessageBox.warning(self, "No Data", "There are no rows to import.")
            return
        if not self.column_mappings:
            QMessageBox.warning(self, "No Mapping", "Please map columns before importing.")
            return

        cursor = self.conn.cursor()
        inserted_count = 0

        try:
            for row_idx in range(row_count):
                # Left table: Sample ID, Aliquot ID, Spot ID
                sample_id_item = self.left_table.item(row_idx, 0)
                aliquot_id_item = self.left_table.item(row_idx, 1)
                spot_id_item = self.left_table.item(row_idx, 2)

                record = {
                    "sample_id": sample_id_item.text().strip() if sample_id_item else None,
                    "aliquot_id": aliquot_id_item.text().strip() if aliquot_id_item else None,
                    "spot_id": spot_id_item.text().strip() if spot_id_item else None,
                    "u": None,
                    "pb": None,
                    "age": None,
                    "rejected": 1 if (row_idx in self.rejected_rows) else 0
                }

                # Populate from right table columns
                for col_idx in range(self.right_table.columnCount()):
                    if col_idx not in self.column_mappings:
                        continue
                    field_name, data_type = self.column_mappings[col_idx]
                    if field_name == "None":
                        continue
                    db_field = field_name.lower().replace(' ', '_')

                    cell_text = self.right_table.item(row_idx, col_idx).text().strip()
                    if cell_text.upper() == "NULL":
                        record[db_field] = None
                    else:
                        if data_type in ("ppm", "% Conc.", "% Disc.", "Ma", "ka", "ppb"):
                            try:
                                record[db_field] = float(cell_text)
                            except ValueError:
                                record[db_field] = None
                        elif data_type == "Auto":
                            try:
                                record[db_field] = float(cell_text)
                            except ValueError:
                                record[db_field] = cell_text
                        else:
                            record[db_field] = cell_text

                cursor.execute("""
                    INSERT INTO upb_samples (
                        sample_id, aliquot_id, spot_id, u, pb, age, rejected
                    )
                    VALUES (:sample_id, :aliquot_id, :spot_id, :u, :pb, :age, :rejected)
                """, record)
                inserted_count += 1

            self.conn.commit()
            QMessageBox.information(self, "Success", f"Imported {inserted_count} rows into the database.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import data:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

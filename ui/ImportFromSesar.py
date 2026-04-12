# ImportFromSesar.py
# this file handles importing sample data from sesar using igsn numbers
# needs error handling logic but it does the basic stuff
# error handling logic added but needs to be tested fully

# ImportFromSesar.py
# this file handles importing sample data from sesar using igsn numbers
# needs error handling logic but it does the basic stuff
# error handling logic added but needs to be tested fully

import json
import requests
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QTextEdit, QMessageBox, 
                             QFileDialog, QComboBox, QWidget, QSplitter, QTreeWidget, QTreeWidgetItem, QMenu,
                             QApplication)  #added QApplication here
from PyQt6.QtGui import QTextCursor, QAction
import pandas as pd


class CheckableTreeWidgetItem(QTreeWidgetItem):
    #tree item with checkbox functionality
    
    def __init__(self, text):
        super().__init__()
        self.setText(0, text)
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.setCheckState(0, Qt.CheckState.Unchecked)


class SampleHierarchyWidget(QWidget):
    #widget for exploring igsn relationships
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_igsn = None
        self.sibling_data = {}  #store fetched data to avoid repeated api calls
        self.setup_ui()
    
    def setup_ui(self):
        #setup the user interface
        layout = QVBoxLayout()
        
        #label to show current igsn
        self.current_label = QLabel("No sample selected")
        layout.addWidget(self.current_label)
        
        #horizontal layout for download buttons
        button_layout = QHBoxLayout()
        
        #download selected button
        self.download_selected_button = QPushButton("Download Selected IGSNs")
        self.download_selected_button.clicked.connect(self.download_selected)
        self.download_selected_button.setEnabled(False)
        button_layout.addWidget(self.download_selected_button)
        
        #select all button maybe we shouldnt have this because it could lead to downloading a lot of data by accident but it is convenient for users who do want to download everything
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all)
        button_layout.addWidget(self.select_all_button)
        
        #clear all button
        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.clicked.connect(self.clear_all)
        button_layout.addWidget(self.clear_all_button)
        
        layout.addLayout(button_layout)
        
        #tree widget for hierarchical display
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Sample Hierarchy")
        self.tree.itemExpanded.connect(self.on_item_expanded)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemChanged.connect(self.on_item_checked)
        layout.addWidget(self.tree)
        
        #text area to display table info
        self.table_text = QTextEdit()
        self.table_text.setReadOnly(True)
        layout.addWidget(self.table_text)
        
        self.setLayout(layout)
    
    #collect all checked IGSNs from the tree
    def get_checked_igsns(self):
        checked_igsns = []
        
        def collect_checked(parent_item):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                igsn = child.text(0)
                if igsn != "No children found":
                    if child.checkState(0) == Qt.CheckState.Checked:
                        checked_igsns.append(igsn)
                    collect_checked(child)
        
        #start from root items
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            igsn = item.text(0)
            if item.checkState(0) == Qt.CheckState.Checked:
                checked_igsns.append(igsn)
            collect_checked(item)
        
        return checked_igsns
    
    #show confirmation dialog before downloading
    def download_selected(self):
        checked_igsns = self.get_checked_igsns()
        if not checked_igsns:
            QMessageBox.warning(self, "No Selection", "No IGSNs selected for download")
            return
        
        #create confirmation dialog
        confirm_dialog = QMessageBox(self)
        confirm_dialog.setWindowTitle("Confirm Download")
        confirm_dialog.setIcon(QMessageBox.Icon.Question)
        confirm_dialog.setText(f"You are about to download {len(checked_igsns)} IGSN(s)")
        
        #show the list of IGSNs to be downloaded limit to first 10 for readability but we can make a scrollable dialog if needed in the future
        if len(checked_igsns) <= 10:
            igsn_list = "\n".join(checked_igsns)
            confirm_dialog.setInformativeText(f"The following IGSNs will be downloaded:\n\n{igsn_list}")
        else:
            igsn_list = "\n".join(checked_igsns[:10])
            confirm_dialog.setInformativeText(f"The following IGSNs will be downloaded (showing first 10 of {len(checked_igsns)}):\n\n{igsn_list}\n\n...and {len(checked_igsns) - 10} more")
        
        confirm_dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm_dialog.setDefaultButton(QMessageBox.StandardButton.No)
        
        reply = confirm_dialog.exec()
        
        if reply == QMessageBox.StandardButton.Yes:
            self.perform_download(checked_igsns)
    
    #perform the actual download after confirmation
    def perform_download(self, checked_igsns):
        success_count = 0
        fail_count = 0
        failed_igsns = []
        
        #create a progress dialog
        progress = QMessageBox(self)
        progress.setWindowTitle("Downloading")
        progress.setText(f"Downloading 0 of {len(checked_igsns)} IGSNs...")
        progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress.setIcon(QMessageBox.Icon.Information)
        progress.show()
        
        for i, igsn in enumerate(checked_igsns):
            progress.setText(f"Downloading {i+1} of {len(checked_igsns)} IGSNs...\nCurrent: {igsn}")
            QApplication.processEvents()  #keep the UI responsive
            
            if self.save_sample_data(igsn, show_message=False):
                success_count += 1
            else:
                fail_count += 1
                failed_igsns.append(igsn)
        
        progress.accept()
        
        #show results
        result_msg = f"Download Complete!\n\nSuccessfully downloaded: {success_count}\nFailed: {fail_count}"
        if failed_igsns and len(failed_igsns) <= 10:
            result_msg += f"\n\nFailed IGSNs:\n" + "\n".join(failed_igsns)
        elif failed_igsns:
            result_msg += f"\n\nFailed IGSNs (showing first 10 of {len(failed_igsns)}):\n" + "\n".join(failed_igsns[:10])
        
        QMessageBox.information(self, "Download Results", result_msg)
    
    #select all IGSNs in the tree
    def select_all(self):
        def select_all_items(parent_item):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                igsn = child.text(0)
                if igsn != "No children found":
                    child.setCheckState(0, Qt.CheckState.Checked)
                    select_all_items(child)
        
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setCheckState(0, Qt.CheckState.Checked)
            select_all_items(item)
        
        self.download_selected_button.setEnabled(True)
    
    #clear all checkboxes in the tree
    def clear_all(self):
        def clear_all_items(parent_item):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                igsn = child.text(0)
                if igsn != "No children found":
                    child.setCheckState(0, Qt.CheckState.Unchecked)
                    clear_all_items(child)
        
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setCheckState(0, Qt.CheckState.Unchecked)
            clear_all_items(item)
        
        self.download_selected_button.setEnabled(False)
    
    #when an item is checked/unchecked
    def on_item_checked(self, item, column):
        #enable download button if any items are checked
        checked = self.get_checked_igsns()
        self.download_selected_button.setEnabled(len(checked) > 0)
    
    #this function contacts the sesar website to get sample information
    def fetch_sample_data(self, igsn):
        if igsn in self.sibling_data:
            return self.sibling_data[igsn]
        
        url = "https://app.geosamples.org/webservices/display.php"
        params = {"igsn": igsn}
        headers = {"Accept": "application/json"}
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            self.sibling_data[igsn] = data
            return data
        except:
            return None
    
    #save sample data to a json file
    def save_sample_data(self, igsn, show_message=True):
        data = self.fetch_sample_data(igsn)
        if not data:
            if show_message:
                QMessageBox.warning(self, "Download Failed", f"Could not fetch data for {igsn}")
            return False
        
        safe_igsn = igsn.replace("/", "_")
        filename = f"sesar_{safe_igsn}.json"
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            if show_message:
                QMessageBox.information(self, "Download Complete", f"Data saved to {filename}")
            return True
        except IOError as e:
            if show_message:
                QMessageBox.critical(self, "Save Failed", f"Could not save file: {e}")
            return False
    
    #show context menu on right click so users can download the chosen igsn
    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return
        
        igsn = item.text(0)
        #dont allow downloading the "No children found" placeholder
        if igsn == "No children found":
            return
        
        menu = QMenu()
        download_action = QAction("Download IGSN Data", self)
        download_action.triggered.connect(lambda: self.save_sample_data(igsn))
        menu.addAction(download_action)
        
        #add checkbox toggle options
        menu.addSeparator()
        check_action = QAction("Check this item", self)
        check_action.triggered.connect(lambda: item.setCheckState(0, Qt.CheckState.Checked))
        menu.addAction(check_action)
        
        uncheck_action = QAction("Uncheck this item", self)
        uncheck_action.triggered.connect(lambda: item.setCheckState(0, Qt.CheckState.Unchecked))
        menu.addAction(uncheck_action)
        
        menu.exec(self.tree.viewport().mapToGlobal(position))
    
    #this pulls out all siblings from a sample's data
    #siblings are samples that share the same parent
    def get_siblings_table(self, data):
        rows = []
        
        try:
            parent_igsn = data.get("sample", {}).get("parent_igsn", None)
            sibling_info = data.get("sample", {}).get("siblings", {})
            samples = sibling_info.get("samples", {})
            sibling_data = samples.get("sample", [])
            
            #if there is only one sibling it comes as a dictionary not a list
            #this converts it to a list so the code can loop through it
            if not isinstance(sibling_data, list):
                sibling_data = [sibling_data] if sibling_data else []
            
            for index, sibling in enumerate(sibling_data):
                if isinstance(sibling, dict) and "igsn" in sibling:
                    rows.append({
                        "ItemID": sibling["igsn"],
                        "ParentID": parent_igsn,
                        "ParentRow": index
                    })
        except:
            pass
        
        return rows
    
    #this adds the current sample to the beginning of the siblings list
    def add_current_sample_to_table(self, rows, current_igsn, parent_igsn):
        current_row = [{
            "ItemID": current_igsn,
            "ParentID": parent_igsn,
            "ParentRow": None
        }]
        return current_row + rows
    
    #this pulls out all children from a sample data
    def get_children_table(self, data):
        rows = []
        
        try:
            current_igsn = data.get("sample", {}).get("igsn")
            children_info = data.get("sample", {}).get("children", {})
            samples = children_info.get("samples", {})
            children_data = samples.get("sample", [])
            
            #if there is only one child it comes as a dictionary not a list
            #this converts it to a list so the code can loop through it
            if not isinstance(children_data, list):
                children_data = [children_data] if children_data else []
            
            for index, child in enumerate(children_data):
                if isinstance(child, dict) and "igsn" in child:
                    rows.append({
                        "ItemID": child["igsn"],
                        "ParentID": current_igsn,
                        "ParentRow": index
                    })
        except:
            pass
        
        return rows
    
    #this prints a table to the screen with row numbers on the left
    #the user uses these row numbers to make selections
    def display_table_text(self, rows, title):
        if not rows:
            self.table_text.append(f"\nNo {title.lower()} found")
            return
        
        df = pd.DataFrame(rows)
        
        text = f"\n{'='*60}\n"
        text += f"{title}\n"
        text += f"{'='*60}\n"
        text += f"\nTotal rows: {len(df)}\n"
        text += "\nIdx | ItemID                          | ParentID                      | ParentRow\n"
        text += "-"*90 + "\n"
        
        for idx, row in df.iterrows():
            item_id = row["ItemID"]
            parent_id = row["ParentID"] if row["ParentID"] else "None"
            parent_row = row["ParentRow"] if pd.notna(row["ParentRow"]) else "None"
            
            text += f"{idx:<3} | {item_id:<30} | {parent_id:<30} | {parent_row}\n"
        
        self.table_text.append(text)
    
    #load children for a tree item when expanded
    def load_children_into_tree(self, parent_item, igsn):
        data = self.fetch_sample_data(igsn)
        if not data:
            return
        
        children = self.get_children_table(data)
        
        #remove the dummy child first
        parent_item.takeChildren()
        
        if not children:
            #add a child item that says no children
            no_child_item = QTreeWidgetItem(parent_item)
            no_child_item.setText(0, "No children found")
            #display message in text area
            self.table_text.append(f"\nNo children found for {igsn}")
        else:
            #add real children with checkboxes
            for child in children:
                child_item = CheckableTreeWidgetItem(child["ItemID"])
                parent_item.addChild(child_item)
                child_item.setData(0, Qt.ItemDataRole.UserRole, child)
                #add a dummy child to make expand arrow appear
                #actual children will be loaded when expanded
                dummy = QTreeWidgetItem()
                dummy.setText(0, "")
                child_item.addChild(dummy)
            
            #display children table in text area
            self.display_table_text(children, f"CHILDREN OF {igsn}")
    
    #when user expands a tree item /clicks the expand arrow
    def on_item_expanded(self, item):
        #check if this item has a dummy child meaning children not loaded yet
        if item.childCount() > 0 and item.child(0).text(0) == "":
            #load real children or no children message
            igsn = item.text(0)
            self.load_children_into_tree(item, igsn)
    
    #load and display siblings for the given igsn
    def load_siblings(self, igsn):
        self.current_igsn = igsn
        self.current_label.setText(f"Current Sample: {igsn}")
        self.table_text.clear()
        self.tree.clear()
        
        data = self.fetch_sample_data(igsn)
        if not data:
            self.table_text.append("Failed to fetch data")
            return
        
        parent_igsn = data.get("sample", {}).get("parent_igsn", None)
        siblings = self.get_siblings_table(data)
        
        #add current sample plus all siblings as top level items
        siblings_with_current = self.add_current_sample_to_table(siblings, igsn, parent_igsn)
        
        if not siblings_with_current:
            self.table_text.append("No siblings found")
            return
        
        self.display_table_text(siblings_with_current, f"SIBLINGS TABLE (Current: {igsn})")
        
        #populate the tree with checkable items
        for row in siblings_with_current:
            item = CheckableTreeWidgetItem(row["ItemID"])
            self.tree.addTopLevelItem(item)
            item.setData(0, Qt.ItemDataRole.UserRole, row)
            #add a dummy child to make expand arrow appear
            #actual children will be loaded when expanded
            dummy = QTreeWidgetItem()
            dummy.setText(0, "")
            item.addChild(dummy)


class ImportFromSesar(QDialog):
    # main window for importing from sesar
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import from SESAR (IGSN)")
        self.setMinimumSize(800, 600)
        
        # main vertical layout
        layout = QVBoxLayout()
        
        # title label at the top of the window
        title_label = QLabel("Import Sample Data from SESAR")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        #create splitter for two sections
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        #top section - original import functionality
        import_widget = QWidget()
        import_layout = QVBoxLayout()
        
        # horizontal layout for the igsn input field
        igsn_layout = QHBoxLayout()
        igsn_label = QLabel("IGSN:")
        # text input where user types the igsn
        self.igsn_input = QLineEdit()
        # shows an example of what to type
        self.igsn_input.setPlaceholderText("e.g., 10.58052/IENWUC821")
        igsn_layout.addWidget(igsn_label)
        igsn_layout.addWidget(self.igsn_input)
        import_layout.addLayout(igsn_layout)
        
        # horizontal layout for the buttons
        button_layout = QHBoxLayout()
        # button that starts the fetch process
        self.fetch_button = QPushButton("Fetch and Save Data")
        # connect the button click to the function that does the work
        self.fetch_button.clicked.connect(self.fetch_and_save)
        button_layout.addWidget(self.fetch_button)
        
        #button to open sibling explorer
        self.explore_button = QPushButton("Explore")
        self.explore_button.clicked.connect(self.open_explorer)
        button_layout.addWidget(self.explore_button)
        
        # button to close the window
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        import_layout.addLayout(button_layout)
        
        # text area where results will be shown
        self.results_text = QTextEdit()
        # user can only read the text not edit
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Results will appear here...")
        import_layout.addWidget(self.results_text)
        
        import_widget.setLayout(import_layout)
        splitter.addWidget(import_widget)
        
        #bottom section - sibling explorer (initially hidden)
        self.explorer_widget = SampleHierarchyWidget()
        self.explorer_widget.setVisible(False)
        splitter.addWidget(self.explorer_widget)
        
        layout.addWidget(splitter)
        self.setLayout(layout)
    
    def open_explorer(self):
        #open the sibling explorer with the entered igsn
        igsn = self.igsn_input.text().strip()
        if not igsn:
            QMessageBox.warning(self, "Missing IGSN", "Please enter an IGSN first.")
            return
        
        self.explorer_widget.setVisible(True)
        self.explorer_widget.load_siblings(igsn)
    
    def fetch_and_save(self):
        # fetch data from sesar and save to a json file
        
        # get the igsn from the input field and remove any spaces
        igsn = self.igsn_input.text().strip()
        
        # check if the user typed something
        if not igsn:
            # show a warning if no igsn was entered
            QMessageBox.warning(self, "Missing IGSN", "Please enter an IGSN.")
            return
        
        #####################################################################
        # ERROR HANDLING SECTION FOR API RETRIEVAL PROCESS        
        try:
            # clear any previous results from the text area
            self.results_text.clear()
            self.results_text.append(f"Fetching data for IGSN: {igsn}...")
            # disable the fetch button so user cannot click multiple times
            self.fetch_button.setEnabled(False)
            
            # the sesar api endpoint
            url = "https://app.geosamples.org/webservices/display.php"
            
            # parameters for the get request
            params = {
                "igsn": igsn
            }
            
            # tell sesar json data is wanted
            headers = {
                "Accept": "application/json"
            }
            
            # send the request to sesar with timeout to prevent hanging
            self.results_text.append("Connecting to SESAR API...")
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            # check if the request was successful
            response.raise_for_status()
            
            # check if we got a valid response (not empty)
            if not response.text:
                raise ValueError("Received empty response from SESAR API")
            
            # convert the response to json with error handling
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                self.results_text.append(f"Failed to parse JSON response: {e}")
                self.results_text.append(f"Response preview: {response.text[:200]}...")
                QMessageBox.critical(self, "Error", 
                                   f"Failed to parse API response as JSON.\n\nError: {e}\n\nThis might indicate the IGSN was not found or the API returned an error.")
                return
            
            # check if the response indicates an error or no data
            if not data:
                self.results_text.append("No data found for this IGSN")
                QMessageBox.warning(self, "No Data", 
                                  f"No sample data found for IGSN: {igsn}\n\nPlease check the IGSN and try again.")
                return
            
            # check for API error messages in the response
            if 'error' in data:
                self.results_text.append(f"API Error: {data['error']}")
                QMessageBox.critical(self, "API Error", 
                                   f"The SESAR API returned an error:\n{data['error']}")
                return
            
            # make a safe filename by replacing slashes with underscores
            safe_igsn = igsn.replace("/", "_")
            # create the filename
            filename = f"sesar_{safe_igsn}.json"
            
            # save the data to a json file with error handling
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    # indent=2 makes the json file pretty and readable
                    json.dump(data, f, indent=2)
            except IOError as e:
                self.results_text.append(f"Failed to save file: {e}")
                QMessageBox.critical(self, "File Error", 
                                   f"Failed to save data to file:\n{filename}\n\nError: {e}")
                return
            
            # show success message in the text area
            self.results_text.append(f"✓ Successfully saved data to: {filename}")
            self.results_text.append("\n--- Sample Information ---")
            
            # extract and display the important sample information
            if 'data' in data:
                sample = data['data']
                # show the igsn
                if 'igsn' in sample:
                    self.results_text.append(f"IGSN: {sample['igsn']}")
                # show the sample name if available
                if 'sample_primary_name' in sample:
                    self.results_text.append(f"Sample Name: {sample['sample_primary_name']}")
                # show the sample type if available
                if 'sample_type' in sample:
                    self.results_text.append(f"Sample Type: {sample['sample_type']}")
                # show the description if available
                if 'sample_description' in sample:
                    self.results_text.append(f"Description: {sample['sample_description']}")
                # show the location if coordinates are available
                if 'sample_latitude' in sample and 'sample_longitude' in sample:
                    self.results_text.append(f"Location: {sample['sample_latitude']}, {sample['sample_longitude']}")
            else:
                self.results_text.append("No sample data found in the response")
            
            # show the raw json data
            self.results_text.append("\n--- Raw JSON Data ---")
            formatted_data = json.dumps(data, indent=2)
            self.results_text.append(formatted_data)
            
            # show a popup telling the user the operation worked
            QMessageBox.information(self, "Success", 
                                   f"Data successfully saved to:\n{filename}")
            
        except requests.exceptions.Timeout:
            # handle timeout errors specifically
            self.results_text.append("Connection timeout: The API took too long to respond")
            QMessageBox.critical(self, "Timeout Error", 
                               "The request to SESAR API timed out.\n\nPlease check your internet connection and try again.")
        except requests.exceptions.ConnectionError:
            # handle connection errors
            self.results_text.append("Connection error: Could not connect to SESAR API")
            QMessageBox.critical(self, "Connection Error", 
                               "Failed to connect to SESAR API.\n\nPlease check your internet connection and try again.")
        except requests.exceptions.HTTPError as e:
            # handle HTTP errors (404, 500, etc.)
            if response.status_code == 404:
                self.results_text.append(f"IGSN not found: {igsn}")
                QMessageBox.warning(self, "Not Found", 
                                   f"No sample found with IGSN: {igsn}\n\nPlease verify the IGSN and try again.")
            elif response.status_code == 429:
                self.results_text.append("Too many requests: Rate limit exceeded")
                QMessageBox.warning(self, "Rate Limit", 
                                   "Too many requests to the SESAR API.\n\nPlease wait a moment and try again.")
            elif response.status_code >= 500:
                self.results_text.append(f"Server error: {e}")
                QMessageBox.critical(self, "Server Error", 
                                   f"SESAR server error (HTTP {response.status_code}).\n\nPlease try again later.")
            else:
                self.results_text.append(f"HTTP Error: {e}")
                QMessageBox.critical(self, "HTTP Error", f"HTTP error occurred:\n{e}")
        except requests.exceptions.RequestException as e:
            # handle any other network errors
            self.results_text.append(f"Network error: {e}")
            QMessageBox.critical(self, "Network Error", f"Failed to fetch data:\n{e}")
        except ValueError as e:
            # handle value errors (like empty response)
            self.results_text.append(f"Error: {e}")
            QMessageBox.critical(self, "Error", f"{e}")
        except Exception as e:
            # handle any other errors
            self.results_text.append(f"Unexpected error: {e}")
            QMessageBox.critical(self, "Unexpected Error", 
                               f"An unexpected error occurred:\n{e}\n\nPlease try again.")
        finally:
            # always re-enable the button when done
            self.fetch_button.setEnabled(True)
        
        #####################################################################


















#Saving old code just in case.
# # ImportFromSesar.py
# # this file handles importing sample data from sesar using igsn numbers
# # needs error handling logic but it does the basic stuff
# # error handling logic added but needs to be tested fully


# import json
# import requests
# from PyQt6.QtCore import Qt
# from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
#                              QPushButton, QLineEdit, QTextEdit, QMessageBox, 
#                              QFileDialog)


# class ImportFromSesar(QDialog):
#     # main window for importing from sesar
    
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Import from SESAR (IGSN)")
#         self.setMinimumSize(600, 500)
        
#         # main vertical layout
#         layout = QVBoxLayout()
        
#         # title label at the top of the window
#         title_label = QLabel("Import Sample Data from SESAR")
#         title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
#         layout.addWidget(title_label)
        
#         # horizontal layout for the igsn input field
#         igsn_layout = QHBoxLayout()
#         igsn_label = QLabel("IGSN:")
#         # text input where user types the igsn
#         self.igsn_input = QLineEdit()
#         # shows an example of what to type
#         self.igsn_input.setPlaceholderText("e.g., 10.58052/IENWUC821")
#         igsn_layout.addWidget(igsn_label)
#         igsn_layout.addWidget(self.igsn_input)
#         layout.addLayout(igsn_layout)
        
#         # horizontal layout for the buttons
#         button_layout = QHBoxLayout()
#         # button that starts the fetch process
#         self.fetch_button = QPushButton("Fetch and Save Data")
#         # connect the button click to the function that does the work
#         self.fetch_button.clicked.connect(self.fetch_and_save)
#         button_layout.addWidget(self.fetch_button)
        
#         # button to close the window
#         self.close_button = QPushButton("Close")
#         self.close_button.clicked.connect(self.accept)
#         button_layout.addWidget(self.close_button)
#         layout.addLayout(button_layout)
        
#         # text area where results will be shown
#         self.results_text = QTextEdit()
#         # user can only read the text not edit
#         self.results_text.setReadOnly(True)
#         self.results_text.setPlaceholderText("Results will appear here...")
#         layout.addWidget(self.results_text)
        
#         # apply the layout to the window
#         self.setLayout(layout)
        
#     def fetch_and_save(self):
#         # fetch data from sesar and save to a json file
        
#         # get the igsn from the input field and remove any spaces
#         igsn = self.igsn_input.text().strip()
        
#         # check if the user typed something
#         if not igsn:
#             # show a warning if no igsn was entered
#             QMessageBox.warning(self, "Missing IGSN", "Please enter an IGSN.")
#             return
        
#         #####################################################################
#          # ERROR HANDLING SECTION FOR API RETRIEVAL PROCESS        
#         try:
#             # clear any previous results from the text area
#             self.results_text.clear()
#             self.results_text.append(f"Fetching data for IGSN: {igsn}...")
#             # disable the fetch button so user cannot click multiple times
#             self.fetch_button.setEnabled(False)
            
#             # the sesar api endpoint
#             url = "https://app.geosamples.org/webservices/display.php"
            
#             # parameters for the get request
#             params = {
#                 "igsn": igsn
#             }
            
#             # tell sesar json data is wanted
#             headers = {
#                 "Accept": "application/json"
#             }
            
#             # send the request to sesar with timeout to prevent hanging
#             self.results_text.append("Connecting to SESAR API...")
#             response = requests.get(url, params=params, headers=headers, timeout=30)
            
#             # check if the request was successful
#             response.raise_for_status()
            
#             # check if we got a valid response (not empty)
#             if not response.text:
#                 raise ValueError("Received empty response from SESAR API")
            
#             # convert the response to json with error handling
#             try:
#                 data = response.json()
#             except json.JSONDecodeError as e:
#                 self.results_text.append(f"Failed to parse JSON response: {e}")
#                 self.results_text.append(f"Response preview: {response.text[:200]}...")
#                 QMessageBox.critical(self, "Error", 
#                                    f"Failed to parse API response as JSON.\n\nError: {e}\n\nThis might indicate the IGSN was not found or the API returned an error.")
#                 return
            
#             # check if the response indicates an error or no data
#             if not data:
#                 self.results_text.append("No data found for this IGSN")
#                 QMessageBox.warning(self, "No Data", 
#                                   f"No sample data found for IGSN: {igsn}\n\nPlease check the IGSN and try again.")
#                 return
            
#             # check for API error messages in the response
#             if 'error' in data:
#                 self.results_text.append(f"API Error: {data['error']}")
#                 QMessageBox.critical(self, "API Error", 
#                                    f"The SESAR API returned an error:\n{data['error']}")
#                 return
            
#             # make a safe filename by replacing slashes with underscores
#             safe_igsn = igsn.replace("/", "_")
#             # create the filename
#             filename = f"sesar_{safe_igsn}.json"
            
#             # save the data to a json file with error handling
#             try:
#                 with open(filename, "w", encoding="utf-8") as f:
#                     # indent=2 makes the json file pretty and readable
#                     json.dump(data, f, indent=2)
#             except IOError as e:
#                 self.results_text.append(f"Failed to save file: {e}")
#                 QMessageBox.critical(self, "File Error", 
#                                    f"Failed to save data to file:\n{filename}\n\nError: {e}")
#                 return
            
#             # show success message in the text area
#             self.results_text.append(f"✓ Successfully saved data to: {filename}")
#             self.results_text.append("\n--- Sample Information ---")
            
#             # extract and display the important sample information
#             if 'data' in data:
#                 sample = data['data']
#                 # show the igsn
#                 if 'igsn' in sample:
#                     self.results_text.append(f"IGSN: {sample['igsn']}")
#                 # show the sample name if available
#                 if 'sample_primary_name' in sample:
#                     self.results_text.append(f"Sample Name: {sample['sample_primary_name']}")
#                 # show the sample type if available
#                 if 'sample_type' in sample:
#                     self.results_text.append(f"Sample Type: {sample['sample_type']}")
#                 # show the description if available
#                 if 'sample_description' in sample:
#                     self.results_text.append(f"Description: {sample['sample_description']}")
#                 # show the location if coordinates are available
#                 if 'sample_latitude' in sample and 'sample_longitude' in sample:
#                     self.results_text.append(f"Location: {sample['sample_latitude']}, {sample['sample_longitude']}")
#             else:
#                 self.results_text.append("No sample data found in the response")
            
#             # show the raw json data
#             self.results_text.append("\n--- Raw JSON Data ---")
#             formatted_data = json.dumps(data, indent=2)
#             self.results_text.append(formatted_data)
            
#             # show a popup telling the user the operation worked
#             QMessageBox.information(self, "Success", 
#                                    f"Data successfully saved to:\n{filename}")
            
#         except requests.exceptions.Timeout:
#             # handle timeout errors specifically
#             self.results_text.append("Connection timeout: The API took too long to respond")
#             QMessageBox.critical(self, "Timeout Error", 
#                                "The request to SESAR API timed out.\n\nPlease check your internet connection and try again.")
#         except requests.exceptions.ConnectionError:
#             # handle connection errors
#             self.results_text.append("Connection error: Could not connect to SESAR API")
#             QMessageBox.critical(self, "Connection Error", 
#                                "Failed to connect to SESAR API.\n\nPlease check your internet connection and try again.")
#         except requests.exceptions.HTTPError as e:
#             # handle HTTP errors (404, 500, etc.)
#             if response.status_code == 404:
#                 self.results_text.append(f"IGSN not found: {igsn}")
#                 QMessageBox.warning(self, "Not Found", 
#                                    f"No sample found with IGSN: {igsn}\n\nPlease verify the IGSN and try again.")
#             elif response.status_code == 429:
#                 self.results_text.append("Too many requests: Rate limit exceeded")
#                 QMessageBox.warning(self, "Rate Limit", 
#                                    "Too many requests to the SESAR API.\n\nPlease wait a moment and try again.")
#             elif response.status_code >= 500:
#                 self.results_text.append(f"Server error: {e}")
#                 QMessageBox.critical(self, "Server Error", 
#                                    f"SESAR server error (HTTP {response.status_code}).\n\nPlease try again later.")
#             else:
#                 self.results_text.append(f"HTTP Error: {e}")
#                 QMessageBox.critical(self, "HTTP Error", f"HTTP error occurred:\n{e}")
#         except requests.exceptions.RequestException as e:
#             # handle any other network errors
#             self.results_text.append(f"Network error: {e}")
#             QMessageBox.critical(self, "Network Error", f"Failed to fetch data:\n{e}")
#         except ValueError as e:
#             # handle value errors (like empty response)
#             self.results_text.append(f"Error: {e}")
#             QMessageBox.critical(self, "Error", f"{e}")
#         except Exception as e:
#             # handle any other errors
#             self.results_text.append(f"Unexpected error: {e}")
#             QMessageBox.critical(self, "Unexpected Error", 
#                                f"An unexpected error occurred:\n{e}\n\nPlease try again.")
#         finally:
#             # always re-enable the button when done
#             self.fetch_button.setEnabled(True)
        
#         #####################################################################
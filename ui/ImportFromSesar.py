# ImportFromSesar.py
# this file handles importing sample data from sesar using igsn numbers
# needs error handling logic but it does the basic stuff
# error handling logic added but needs to be tested fully


import json
import requests
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QTextEdit, QMessageBox, 
                             QFileDialog)


class ImportFromSesar(QDialog):
    # main window for importing from sesar
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import from SESAR (IGSN)")
        self.setMinimumSize(600, 500)
        
        # main vertical layout
        layout = QVBoxLayout()
        
        # title label at the top of the window
        title_label = QLabel("Import Sample Data from SESAR")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # horizontal layout for the igsn input field
        igsn_layout = QHBoxLayout()
        igsn_label = QLabel("IGSN:")
        # text input where user types the igsn
        self.igsn_input = QLineEdit()
        # shows an example of what to type
        self.igsn_input.setPlaceholderText("e.g., 10.58052/IENWUC821")
        igsn_layout.addWidget(igsn_label)
        igsn_layout.addWidget(self.igsn_input)
        layout.addLayout(igsn_layout)
        
        # horizontal layout for the buttons
        button_layout = QHBoxLayout()
        # button that starts the fetch process
        self.fetch_button = QPushButton("Fetch and Save Data")
        # connect the button click to the function that does the work
        self.fetch_button.clicked.connect(self.fetch_and_save)
        button_layout.addWidget(self.fetch_button)
        
        # button to close the window
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)
        
        # text area where results will be shown
        self.results_text = QTextEdit()
        # user can only read the text not edit
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Results will appear here...")
        layout.addWidget(self.results_text)
        
        # apply the layout to the window
        self.setLayout(layout)
        
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
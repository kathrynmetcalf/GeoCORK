## Tests
This is a non-exhaustive list of variuous functionality to test to ensure all aspects of geocork are working correctly.

### Importer
### Data Tables
* Table comboBox switcher successfully swaps between tables
  * Displays Tables, Trees, Views as expected
* Edit pushbutton works
  * Shows Tables, Trees, Views as expected
* Refresh buttons works
* Search correctly searches all columns upon return pressed
  * Test on Tables, Trees, Views
* Next/Prev button works
* Show per page combobox correctly loads from settings
* Show per page combobox updates offset/limit in query upon changing
* show per page label correct shows
* go to record shows correct name, completer populates, and works
  * Only for tables or table views
### View Data Table
* Open view data table from right click on samples
  * Aliquots, Spots, UPbAnalyses
* Edit table view from view data works 
### Edit Tables
### Edit Trees
### Edit Views
### Filters
### Data Viewer
* Properly loads when filter is loaded
* Does not open if no filters returns no ids
* Switcher between scope on data table works
* Selection on data table updates data filtered table properly
* Data filtered table changes when selection stays same but combobox for table switches
* Edit Views on data table works
* Edit Tables/Trees/Views on data filtered table works
* Search correctly searches all columns upon return pressed
  * Test on Tables, Trees, Views
* Next/Prev button works
* Show per page combobox correctly loads from settings
* Show per page combobox updates offset/limit in query upon changing
* show per page label correct shows
* go to record shows correct name, completer populates, and works
  * Only for tables or table views
### Exporter
### Settings
* Restore from defaults
* Changing view column order and checked
* Updating database About table
* Changing settings reflects throughout GeoCORK
### Create Backup
* Properly stores backup to folder location
### Restore Backup
* Properly copies over backup data to current database
### Merge
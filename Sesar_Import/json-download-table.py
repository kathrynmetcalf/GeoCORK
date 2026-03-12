import requests
import json
import pandas as pd
import time  # added this to use the sleep function for adding delays between API calls

# this script asks the user for one IGSN, then builds a table showing how that sample and all related samples are connected.
# the pandas library helps create and display tables of data.

#I think the issue with too many API calls happens in the function build_hierarchy_table 
# because it is fetching data for each child sample to find its children
#  but some of those child samples may have already been fetched when we climbed up the parent chain
# there has to be a more optimized way to build the table without fetching the same sample multiple times

################################################################################
#Functions
################################################################################

#fetch_sample_data is the function that contacts the SESAR website to get information about one specific sample.
def fetch_sample_data(igsn):
    """
    This function contacts the SESAR website to get information about one specific sample.
    The function needs the IGSN of the sample to look up.
    The function returns the sample information as a collection of key-value pairs/dictionary.
    If something goes wrong, the function returns None (which means "nothing").
    """
    
    #this is the web address where the SESAR website expects requests for sample info
    url = "https://app.geosamples.org/webservices/display.php"
    
    #this is the information we need to send to the website to ask for the sample data
    # SESAR2 expects the IGSN to be sent as a parameter called "igsn"
    params = {"igsn": igsn}
    
    # this tells the website to please send the information back to me in JSON format.
    headers = {"Accept": "application/json"}
    
    try:
        # this line actually sends the request to the website and waits for the response
        response = requests.get(url, params=params, headers=headers)
        
        # this checks if the website was able to fulfill the request.
        # If something went wrong (like the IGSN doesn't exist), this will trigger an error.
        response.raise_for_status()
        
        # the website sends back text that is formatted as JSON
        # this line converts that text into a Python dictionary/key-value pairs so we can work with it easy
        data = response.json()
        
        # print a message to let the user know the fetch was successful and what IGSN was fetched (maybe remove this later)
        print(f"  Fetched {igsn}")
        
        # return the data we got from the website so it can be used by other parts of the program
        return data
        
    except requests.exceptions.RequestException as error:
        # if anything went wrong with the website request this runs instead of crashing 
        # print an error message showing what went wrong and which IGSN caused the problem
        print(f"  Error fetching {igsn}: {error}")
        
        # return None to let user know the fetch failed and the program can keep running w/o crashing
        return None

#check_for_parent is the function that looks at a sample's data to see if it has a parent sample
def check_for_parent(data):
    """
    This function looks at a sample's data to see if it has a parent sample.
    The function needs one piece of information: the sample data dictionary that we got from using fetch_sample_data.
    The function returns the parent's IGSN if one exists, or None if there is no parent.
    """
    
    try:
        # the sample data has a section called "sample" that contains all the main information
        # inside that section, there is a field called "parent_igsn" that directly tells us the parent
        # we check if both "sample" and "parent_igsn" exist in the data to avoid errors if they are missing
        if "sample" in data and "parent_igsn" in data["sample"]:
            parent_igsn = data["sample"]["parent_igsn"] #this sets parent_igsn to the value of the parent_igsn field if it exists
            
            # check if the parent_igsn field actually contains something.
            # an empty string or None means there is no parent.
            if parent_igsn:
                return parent_igsn

    # except is how we catch errors that might happen if the data doesn't have the structure we expect      
    except (AttributeError, KeyError, TypeError):
        # if any of the nested data structures don't exist or are the wrong type,
        # this catches the error and ignores it 
        # #the function will just return None maybe add a error message here later if we want to know when this happens
        pass
    
    # if no parent was found, return None
    return None

# #get_siblings_with_details looks at the sample data to find any siblings of the sample and their position among siblings
# def get_siblings_with_details(data):
#     """
#     This function finds all siblings of a sample that share the same parent as this sample.
    
#     The function needs one piece of information the sample data dictionary which we got from using fetch_sample_data.
#     It returns a list of dictionaries. Each dictionary contains:
#         - "igsn": the IGSN of a sibling sample
#         - "parent_row": the position of that sibling among all children of the parent (0, 1, 2, etc.)
#     If there are no siblings, it returns an empty list.
#     """
    
#     siblings = [] #this will hold sibling information
    
#     try:
#         #navigate through the JSON structure to find sibling information.
#         #the path is: sample -> siblings -> samples -> sample
#         #this means we look inside the "sample" section, then inside "siblings", then inside "samples", and finally at the "sample" field 
#         # which contains the sibling data.
        
#         sibling_info = data.get("sample", {}).get("siblings", {})
        
#         # check if sibling information exists and contains sample data
#         #if sibling_info exists and has a "samples" field, we can look for siblings
#         # set sample to sibling_info["samples"] to make it easier to work with
#         if sibling_info and "samples" in sibling_info:
#             samples = sibling_info["samples"]
            
#             # the "sample" field likely will contain one sibling or a list of siblings
#             #if the "sample" field exists in the samples data, we can look for siblings there
#             if "sample" in samples:
#                 sibling_data = samples["sample"]
                
#                 # ff sibling_data is a list, that means there are multiple siblings
#                 # the position in the list likely indicates the order among siblings
#                 #so we loop through the list and add each sibling's IGSN and its index in the list as the parent_row
#                 if isinstance(sibling_data, list):
#                     for index, sibling in enumerate(sibling_data):
#                         if isinstance(sibling, dict) and "igsn" in sibling:
#                             siblings.append({
#                                 "igsn": sibling["igsn"],
#                                 "parent_row": index
#                             })
                
#                 # If sibling_data is a dictionary, that means there is exactly one sibling.
#                 elif isinstance(sibling_data, dict) and "igsn" in sibling_data:
#                     siblings.append({
#                         "igsn": sibling_data["igsn"],
#                         "parent_row": 0
#                     })
                    
#     except (AttributeError, KeyError, TypeError):
#         # ff any part of the nested structure doesn't exist, just return an empty list.
#         pass
    
#     return siblings

#find_top_parent is the function that climbs up the parent chain until it finds the highest-level sample
def find_top_parent(start_igsn):
    """
    This function climbs up the parent chain until it finds the highest-level sample.
    
    Starting from the IGSN the user provided, this function repeatedly:
        1. Looks at the current sample to find its parent.
        2. Fetches that parent sample data.
        3. Makes the parent the new current sample.
        4. Repeats until a sample with no parent is found.
    
    This is Step 1 of the hierarchy building process.
    
    The function returns three things:
        1. The IGSN of the top parent
        2. The data dictionary of the top parent
        3. A dictionary containing all sample data that was fetched along the way
           (keys are IGSNs, values are the corresponding data dictionaries)
    
    If anything fails, it returns None for all three values.
    """
    
    print("\n" + "="*60)
    print("STEP 1: FINDING TOP PARENT")
    print("="*60)
    
    #start with the IGSN the user provided.
    current_igsn = start_igsn
    
    #fetch the data for the starting sample.
    current_data = fetch_sample_data(current_igsn) 
    
    # if the fetch failed we cannot continue return None for all three values to indicate failure
    if not current_data:
        return None, None, {}
    
    # create a dictionary to store all the data we fetch along the way starting w/ the initial igsn 
    # this prevents us from having to fetch the same sample twice later when we build the table
    fetched_data = {current_igsn: current_data}
    
    # this loop continues until we find a sample with no parent
    while True:
        # check if the current sample has a parent.
        parent_igsn = check_for_parent(current_data)
        
        # if there is no parent, we have reached the top.
        if not parent_igsn:
            print(f"  {current_igsn} has no parent. This is the top parent. Yay!")
            break
        
        # print the relationship we found
        print(f"  {current_igsn} has parent: {parent_igsn}")
        
        # fetch the parent sample data
        parent_data = fetch_sample_data(parent_igsn)
        
        # if the fetch failed break the loop and return what we have so far
        if not parent_data:
            print(f"  Failed to fetch parent {parent_igsn}")
            break
        
        # store the parent data for later use
        fetched_data[parent_igsn] = parent_data
        
        # move up one level: the parent becomes the current sample for the next iteration
        current_igsn = parent_igsn
        current_data = parent_data
    
    # after the loop ends the current sample is the top parent
    top_igsn = current_igsn
    top_data = current_data
    print(f"\nTOP PARENT FOUND: {top_igsn}")
    
    return top_igsn, top_data, fetched_data

# get_children_directly_from_parent
# this function extracts children directly from a parent's "children" section
def get_children_directly_from_parent(parent_data):
    """
    This function extracts all children directly from a parent sample's "children" section.
    
    Parameters:
        parent_data: The data dictionary of the parent sample
    
    Returns a list of dictionaries. Each dictionary contains:
        - "igsn": the IGSN of a child sample
        - "parent_row": the position of that child in the list (0, 1, 2, etc.)
    """
    
    children = []
    
    try:
        # navigate to the children section in the JSON
        # path is sample -> children -> samples -> sample
        children_info = parent_data.get("sample", {}).get("children", {})
        
        #check if children information exists and contains sample data
        #if children_info exists and has a "samples" field then samples = children_info["samples"] (the section that contains the children data)
        if children_info and "samples" in children_info:
            samples = children_info["samples"]
            
            # if the sample field contains the list of children then children_data = samples["sample"] (the section that contains the actual child samples)
            if "sample" in samples:
                children_data = samples["sample"]
                
                # if children_data is a list, that means there are multiple children
                # the position in the list indicates the order
                #if children_data is a list, we loop through it and add each child's IGSN and its index in the list as the parent_row
                if isinstance(children_data, list):
                    for index, child in enumerate(children_data):
                        if isinstance(child, dict) and "igsn" in child:
                            children.append({
                                "igsn": child["igsn"],
                                "parent_row": index
                            })
                
                #if children_data is a dictionary, that means there is exactly one child
                elif isinstance(children_data, dict) and "igsn" in children_data:
                    children.append({
                        "igsn": children_data["igsn"],
                        "parent_row": 0
                    })
                    
    except (AttributeError, KeyError, TypeError):
        # If any part of the nested structure doesn't exist, just return an empty list
        pass
    
    return children

# build_hierarchy_table
# this function builds the table using the simple children-based approach
# this this function is making too many unnessisary api calls to begin with
# i am setting a timer to slow it down so we don't get errors but we should really rethink the logic to avoid fetching the same sample multiple times
def build_hierarchy_table(top_igsn, top_data, fetched_data):
    """
    This function builds the complete hierarchy table starting from the top parent.
    
    The logic:
        1. Add the top parent to the table
        2. Look in the parent's "children" section to find all its children
        3. Add each child to the table with its position as parent_row
        4. For each child, fetch its data and repeat steps 2-4
    
    Parameters:
        top_igsn: The IGSN of the top parent
        top_data: The data dictionary for the top parent
        fetched_data: Dictionary containing data for all fetched samples
    
    Returns a list of dictionaries, where each dictionary represents one row in the final table.
    """
    
    print("\n" + "="*60) #this prints a line of equal signs to visually separate this section in the output
    print("BUILDING HIERARCHY TABLE FROM CHILDREN SECTIONS") #this prints a message to indicate that we are now building the hierarchy table using the new approach based on children sections
    print("="*60)#this prints another line of equal signs to complete the visual separation in the output
    
    # this list will hold all the rows for our table
    all_rows = []
    
    # this set tracks which IGSNs have already been added to the table
    added_samples = set()
    
    # step 1: Add the top parent
    print(f"\nAdding top parent: {top_igsn}")
    all_rows.append({
        "ItemID": top_igsn,
        "ParentID": None,
        "ParentRow": None
    })
    added_samples.add(top_igsn)
    
    # this queue will hold parents we need to process to find their children
    # start with the top parent
    parents_to_process = [(top_igsn, top_data)]
    
    # process each parent in the queue
    while parents_to_process:
        current_parent_igsn, current_parent_data = parents_to_process.pop(0)
        print(f"\nProcessing parent: {current_parent_igsn}")
        
        #get all children directly from the parent's children section
        children = get_children_directly_from_parent(current_parent_data)
        
        if not children:
            print(f"  No children found for {current_parent_igsn}")
            continue
        
        print(f"  Found {len(children)} children")
        
        # add each child to the table and fetch their data
        for child in children:
            child_igsn = child["igsn"]
            child_row = child["parent_row"]
            
            # add the child to the table if not already added
            if child_igsn not in added_samples:
                all_rows.append({
                    "ItemID": child_igsn,
                    "ParentID": current_parent_igsn,
                    "ParentRow": child_row
                })
                added_samples.add(child_igsn)
                print(f"    Added child {child_igsn} at position {child_row}")
                
                # fetch the child's data to find ITS children later 
                if child_igsn not in fetched_data:
                    # adding a 1 second delay before each API call to avoid hitting the rate limit and getting 429 errors
                    # this is a temporary fix we should optimize the logic later to reduce the number of calls
                    print(f"      Waiting 1 seconds before fetching {child_igsn} to be nice to the SESAR server...")
                    time.sleep(1.0)  # 1 second delay between each API call to avoid rate limiting
                    
                    child_data = fetch_sample_data(child_igsn)
                    if child_data:
                        fetched_data[child_igsn] = child_data
                        # add this child to the queue to process itS children
                        parents_to_process.append((child_igsn, child_data))
    
    return all_rows


################################################################################
# Main Program
################################################################################

def main():
    """    
    Main does the following in order:
        1. Asks the user for an IGSN
        2. Finds the top parent by climbing up the parent chain
        3. Builds the complete hierarchy table
        4. Displays the table
        5. Offers to save the table to a CSV file
    """
    
    # ask the user to type an IGSN
    # the input function displays the prompt and waits for the user to type something and press Enter
    # the .strip() removes any extra spaces at the beginning or end of what the user typed
    igsn = input("Please enter an IGSN (e.g., 10.58052/IENWUC821): ").strip()
    
    # check if the user actually typed something
    # If they just pressed Enter without typing then the string will be empty
    if not igsn:
        print("IGSN cannot be empty. Exiting.")
        return
    
    # Step 1: Find the top parent
    # this function fetches data as it climbs up the parent chain
    top_igsn, top_data, fetched_data = find_top_parent(igsn) #it uses the IGSN the user provided to start climbing up the parent chain and returns the top parent's IGSN, its data, and all the data fetched along the way
    
    # ff find_top_parent couldn't find a top parent we cannot continue
    if not top_igsn:
        print("Failed to find top parent. Exiting.")
        return
    
    # display how many samples were fetched during the process
    print(f"\nTotal samples fetched so far: {len(fetched_data)}")
    
    #build the complete hierarchy table using the children-based approach
    hierarchy_rows = build_hierarchy_table(top_igsn, top_data, fetched_data)
    
    # convert the list of rows into a pandas DataFrame/ table-like structure that makes it easy to display and save data
    data_frame = pd.DataFrame(hierarchy_rows)
    
    # display the final table to the user.
    print("\n" + "="*60)
    print("FINAL HIERARCHY TABLE")
    print("="*60)
    print(f"\nTotal rows in table: {len(data_frame)}")
    print(f"Total samples fetched overall: {len(fetched_data)}")
    print("\nItemID                          ParentID                      ParentRow")
    print("-"*90)
    
    # loop through each row in the DataFrame and print it in a formatted way
    for _, row in data_frame.iterrows():
        # get the values from the row.
        item_id = row["ItemID"]
        
        # for ParentID, if it's None, display "None" instead
        parent_id = row["ParentID"] if row["ParentID"] else "None"
        
        # for ParentRow, pandas uses NaN Not a Number for empty values
        # pd.notna checks if the value is not NaN
        parent_row = row["ParentRow"] if pd.notna(row["ParentRow"]) else "None"
        
        # print the row with consistent spacing
        # the :<30 fir left-align this field in a space 30 characters wide
        print(f"{item_id:<30} {parent_id:<30} {parent_row}")
    
    # ask the user if they want to save the table to a file (this is so i can double check the result by hand ;A; )
    save_choice = input("\nSave hierarchy table to CSV? (yes/no): ").strip().lower()
    
    # check if the user said yes accepting 'yes', 'y', 'yeah', etc
    if save_choice in ['yes', 'y']:
        #create a safe filename by replacing any slashes in the IGSN with underscores
        # slashes are not allowed in filenames on some operating systems
        safe_igsn = igsn.replace("/", "_")
        filename = f"hierarchy_table_{safe_igsn}.csv"
        
        # save the DataFrame to a CSV file
        # index=false so we don't save the row numbers as a separate column
        data_frame.to_csv(filename, index=False)
        
        print(f"Table saved to {filename}")
    
    print("\nProcess complete.")


if __name__ == "__main__":
    main()

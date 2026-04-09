import requests
import pandas as pd

#this function contacts the sesar website to get sample information
def fetch_sample_data(igsn):
    url = "https://app.geosamples.org/webservices/display.php"
    params = {"igsn": igsn}
    headers = {"Accept": "application/json"}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except:
        return None

#this pulls out all siblings from a sample's data
#siblings are samples that share the same parent (does not include the sample itself)
def get_siblings_table(data):
    rows = []
    
    try:
        parent_igsn = data.get("sample", {}).get("parent_igsn", None)
        sibling_info = data.get("sample", {}).get("siblings", {})
        samples = sibling_info.get("samples", {})
        sibling_data = samples.get("sample", [])
        
        #if there is only one sibling, it comes as a dictionary not a list
        #this converts it to a list so we can loop through it
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
def add_current_sample_to_table(rows, current_igsn, parent_igsn):
    current_row = [{
        "ItemID": current_igsn,
        "ParentID": parent_igsn,
        "ParentRow": None
    }]
    return current_row + rows

#this pulls out all children from a sample's data
#children are samples that have this sample as their parent
def get_children_table(data):
    rows = []
    
    try:
        current_igsn = data.get("sample", {}).get("igsn")
        children_info = data.get("sample", {}).get("children", {})
        samples = children_info.get("samples", {})
        children_data = samples.get("sample", [])
        
        #if there is only one child, it comes as a dictionary not a list
        #this converts it to a list so we can loop through it
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
def display_table(rows, title):
    if not rows:
        print(f"\nNo {title.lower()} found")
        return None
    
    df = pd.DataFrame(rows)
    
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"\nTotal rows: {len(df)}")
    print("\nIdx | ItemID                          | ParentID                      | ParentRow")
    print("-"*90)
    
    for idx, row in df.iterrows():
        item_id = row["ItemID"]
        parent_id = row["ParentID"] if row["ParentID"] else "None"
        parent_row = row["ParentRow"] if pd.notna(row["ParentRow"]) else "None"
        
        print(f"{idx:<3} | {item_id:<30} | {parent_id:<30} | {parent_row}")
    
    return df

#main program starts here
start_igsn = input("Enter starting IGSN: ").strip()
current_igsn = start_igsn
first_round = True

#this loop continues until the user quits
while True:
    #get the data for the current sample
    data = fetch_sample_data(current_igsn)
    if not data:
        print("Failed to fetch data")
        break
    
    #get the parent igsn for display purposes
    parent_igsn = data.get("sample", {}).get("parent_igsn", None)
    
    #get the siblings table (does not include current sample)
    siblings = get_siblings_table(data)
    
    #only add the current sample to the table on the first round
    if first_round:
        siblings_with_current = add_current_sample_to_table(siblings, current_igsn, parent_igsn)
        first_round = False
    else:
        siblings_with_current = siblings
    
    if not siblings_with_current:
        print("No siblings found. Exiting.")
        break
    
    display_table(siblings_with_current, f"SIBLINGS TABLE (Current: {current_igsn})")
    
    #let the user pick any sample from the table to explore
    while True:
        try:
            choice = input(f"\nSelect a row index to see its children (or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                print("Goodbye.")
                exit()
            
            idx = int(choice)
            if 0 <= idx < len(siblings_with_current):
                selected_igsn = siblings_with_current[idx]["ItemID"]
                print(f"\nShowing children of {selected_igsn}...")
                
                #get the data for the selected sample
                selected_data = fetch_sample_data(selected_igsn)
                if selected_data:
                    #show the children of the selected sample
                    children = get_children_table(selected_data)
                    
                    #if no children, create a table with just the selected sample
                    if not children:
                        print(f"\nNo children found for {selected_igsn}")
                        single_row = [{
                            "ItemID": selected_igsn,
                            "ParentID": None,
                            "ParentRow": None
                        }]
                        display_table(single_row, f"CHILDREN OF {selected_igsn}")
                        children = single_row
                    else:
                        display_table(children, f"CHILDREN OF {selected_igsn}")
                    
                    #let the user pick a child to go deeper
                    while True:
                        try:
                            child_choice = input(f"\nSelect a child index to see its children (or 'b' to go back to siblings, 'q' to quit): ").strip()
                            if child_choice.lower() == 'q':
                                print("Goodbye.")
                                exit()
                            if child_choice.lower() == 'b':
                                break
                            
                            child_idx = int(child_choice)
                            if 0 <= child_idx < len(children):
                                current_igsn = children[child_idx]["ItemID"]
                                print(f"\nMoving to {current_igsn}")
                                break
                            else:
                                print(f"Invalid index. Please enter 0-{len(children)-1}, 'b', or 'q'")
                        except ValueError:
                            print("Please enter a valid number, 'b', or 'q'")
                    
                    #if the user picked a child, break out to the main loop
                    if child_choice.lower() != 'b':
                        break
                else:
                    print("Failed to fetch selected sample")
                    break
            else:
                print(f"Invalid index. Please enter 0-{len(siblings_with_current)-1}")
        except ValueError:
            print("Please enter a valid number or 'q'")
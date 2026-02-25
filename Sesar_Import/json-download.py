import requests # import the requests module to handle HTTP requests
import json # import the json module to handle JSON data

# set url variable to the SESAR web service endpoint for retrieving sample data
url = "https://app.geosamples.org/webservices/display.php"

# prompt user for an IGSN and save it to the variable igsn, stripping any leading/trailing whitespace
igsn = input("Please enter an IGSN :) (e.g., 10.58052/IENWUC821): ").strip()

# check if the user input is empty, if it is then raise a ValueError with the message "IGSN cannot be empty."
if not igsn:
    raise ValueError("IGSN cannot be empty. Exiting the program.") 
# make this so user can retry if they want to without closing the program 
# or choose to exit the program if they are done


# set up the parameters for the GET request to the SESAR web service, including the user-provided IGSN
params = {
    "igsn": igsn
}

# set up the headers for the GET request to specify that we want the response in JSON format
headers = {
    "Accept": "application/json"
}

# send GET request to the SESAR web service
response = requests.get(url, params=params, headers=headers)
# check if the request was successful if not then raise an HTTPError with the appropriate message
response.raise_for_status()

# save the JSON response from the SESAR web service to the variable data
data = response.json() # 

# create a filename based on the IGSN 
safe_igsn = igsn.replace("/", "_") # replace any slashes in the IGSN with underscores to create a safe filename
# create filename variable that combines the prefix sesar_ the safe IGSN and  .json to create a unique filename for each IGSN
filename = f"sesar_{safe_igsn}.json"

# save the retrieved data to a JSON file
with open(filename, "w", encoding="utf-8") as f: # open a new file called f with filename in w/write mode with UTF-8 encoding
    json.dump(data, f, indent=2) # dump the JSON data into the file with an indentation of 2 spaces for readability

print(f"Saved SESAR data to {filename}")  # confirmation that data was successfully saved to json with filename
import requests
import json

# This script retrieves sample data from the SESAR web service and saves it as a JSON file.
url = "https://app.geosamples.org/webservices/display.php" # SESAR web service website
params = {
    "igsn": "10.58052/IENWUC821"
} # Sample IGSN for testing; change so user can input their own IGSN if desired

headers = {
    "Accept": "application/json"
} # Request JSON format from the SESAR web service

# Send GET request to the SESAR web service with the specified parameters and headers
response = requests.get(url, params=params, headers=headers)
# Check if the request was successful; if not, raise an HTTPError with the appropriate message 
response.raise_for_status()

data = response.json() # Parse the JSON response from the SESAR web service and store it in the 'data' variable

# Save the retrieved data to a JSON file named 'sesar_sample.json' with UTF-8 encoding w/ indentation of 2 spaces
with open("sesar_sample.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("Saved SESAR data to sesar_sample.json") # Print a confirmation message indicating that the data has been successfully saved to the specified JSON file.

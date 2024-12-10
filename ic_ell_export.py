
"""
Title: Infinite Campus DC export
File Name: ic_dc_export.py
Purpose: Pull the grades from Infinite Campus at the end of the quarter for report cards, system reconciliation
Dependencies: navigator.py, ic_file_mover_headers.py
Description: This file extracts the data viewer reports from Infininte Campus in html format and deposits them into the icampus_downloads directory.
Notes:
 - If the scripts encounters errors on the iframe functions, the frame names may have changed in Infinite Campus.
 - At which time iframe_names will need to be updated in both iframe functions.
 - To determine the location of th iframe for each function:
    - run a report from the DataView in Infinite Campus
    - use the inspect tool to find the target frame for the report list and the settings
    - run the script called [TODO: ADD name of script with function:]
  - insert new frame names into list for variable "iframe_names"
"""
# Rename key variables based on repoart name and copied xpath from Infinite campus
base_file_name = "ell_export"
report_xpath = '//*[@id="row86935"]/td[3]'

# Import required libraries
import os
import glob
import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as EC
from navigator import go_to_reports_id, go_to_settings, get_chrome_options, enable_download_headless

print("Current working directory:", os.getcwd())
# Record the start time
start_time = time.time()

# Open JSON file with credentials & save credentials as variables
print("Retrieving credentials...")
config_file_path = os.path.join("/home/KIPPNashvilleData/", "credentials_all.json")
with open(config_file_path) as config_file:
    data = json.load(config_file)
config = json.load(open(config_file_path))["infinitecampus"]
username = config["username"]
password = config["password"]
site = config["ic_url"]
reports_frame = config["reports_url"]

print("Credentials retrieved")
print("Starting Chromedriver set up...")
download_dir = "/home/KIPPNashvilleData/icampus_downloads/"
chrome_options = get_chrome_options(download_dir)
driver = webdriver.Chrome(options=chrome_options)
enable_download_headless(driver, download_dir)
# Print Chrome options for debugging
print("Chrome Options:")
for option in chrome_options.arguments:
    print(option)
print("Chromedriver set up and initialized")

# Opening browser in headless mode. Go to site. Check site name for accuracy"
print("Opening Chromedriver and navigating to IC site")
driver.get(site)
print("Site Name:" + driver.title)
print("Site Open.")

# Infinite Campus Login Sequence
print("Logging in to Site")
WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "password"))).send_keys(password)
time.sleep(10)
driver.find_element(By.ID, "signinbtn").click()
time.sleep(15)
print("Logged in to IC")
print("Site Name:" + driver.title)

print("Clicking Link to Data Viewer Frame")
driver.get(reports_frame)
print("Site Name:" + driver.title)

go_to_reports_id(driver)
# Find the specific row id for the report
report = driver.find_element(By.XPATH, report_xpath)
report.click()
print("Report Clicked")

# Set the report options
print("Starting Options...")
# Call function to navigate to the frame with the settings
go_to_settings(driver)
# Set the report type to html
format_drop = driver.find_element(By.ID, "mode")
htmlop = Select(format_drop)
htmlop.select_by_value("html")
# Select All schools in the list
school_list = driver.find_element(By.ID, "calendarID")
select = Select(school_list)
school_options = ["3891", "3892", "3894", "3896", "3898"]
for value in school_options:
    select.select_by_value(value)
print("Options set")

""""
####  Ensuring the file downloads before closing the browser   ####
  1. Create a variable to hold the List of names of browsers open - (only 1 at this time)
      -example: initial_window_handle = driver.window_handles
  2. Create a variable that calculated the length of that list ex:
      -example: handle_length = len(initial_window_handles)
  3. Click on the Report
  4. User WebDriverWait until the driver.window_handles>handle_length
"""
# Create variables for inequality expression
initial_window_handles = driver.window_handles
handle_length = len(initial_window_handles)

# Click on the Generate report button to download
print("Generating report...")
# Click on Generate Report Button
generate_button = driver.find_element(By.ID, "next")
generate_button.click()

# Wait for the number of window handles to change (indicating the popup)
WebDriverWait(driver, 180).until(lambda driver: len(driver.window_handles) > handle_length)
print("Report window opened")

time.sleep(60)
driver.close()
print("Driver Closed")
# Find the most recent "extract.html" file

html_files = glob.glob(os.path.join(download_dir, 'extract.html'))

# Sort the files by modification time (newest first)
html_files.sort(key=os.path.getmtime, reverse=True)

# Check if any HTML files were found
if html_files:
    most_recent_html = html_files[0]

    # Get the modification time of the file
    file_mtime = os.path.getmtime(most_recent_html)

    # Get the current time
    current_time = time.time()

    # Check if the file was downloaded in the last 10 minutes
    if current_time - file_mtime <= 600:  # 600 seconds = 10 minutes
        # Rename the file to "base_file_name.html"
        os.rename(most_recent_html, os.path.join(download_dir, f"{base_file_name}.html"))
        print(f"Renamed extract.html to '{base_file_name}.html'")

        # Read the HTML file into a pandas DataFrame
        df = pd.read_html(os.path.join(download_dir, f"{base_file_name}.html"), header=1)[0]
        # dfs = pd.read_html(table_html, header=0)
        # Remove rows where the first column contains "All records"
        # df = df.iloc[1:]
        df = df[df.iloc[:, 0] != "All Records"]

        # Save the cleaned DataFrame to a new CSV file
        cleaned_csv_path = os.path.join(download_dir, f"{base_file_name}.csv")
        df.to_csv(cleaned_csv_path, index=False)
        print(f"Cleaned data saved to '{cleaned_csv_path}'")
    else:
        print("The file is older than 10 minutes.")
else:
    print("No 'extract.html' file found in the directory.")

end_time = time.time()

# Calculate the elapsed time
elapsed_time = end_time - start_time

# Print the elapsed time in seconds
print(f"Script execution time: {elapsed_time} seconds")
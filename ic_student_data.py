"""
Title: Infinite Campus Student Data
File Name: ic_student_data.py
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

import os
import glob
import time
import json
import logging
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as EC
from navigator import go_to_reports_id, go_to_settings, get_chrome_options, enable_download_headless

# Configure logging
logging.basicConfig(
    filename='/home/KIPPNashvilleData/infinite_campus/icampus_reports.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# Set up Google Sheets credentials and client
def setup_google_sheets(spreadsheet_name, sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('/home/KIPPNashvilleData/creds.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(spreadsheet_name).worksheet(sheet_name)
    return sheet

# Log to Google Sheets
def log_to_google_sheets(sheet, message):
    sheet.append_row([time.strftime("%Y-%m-%d %H:%M:%S"), message])

# Function to retrieve credentials and report configurations from JSON file
def get_config():
    config_file_path = os.path.join("/home/KIPPNashvilleData/", "credentials_all.json")
    with open(config_file_path) as config_file:
        data = json.load(config_file)
    infinitecampus = data["infinitecampus"]
    icampus_reports = data["icampus_reports"]
    return infinitecampus["username"], infinitecampus["password"], infinitecampus["ic_url"], infinitecampus["reports_url"], icampus_reports

# Function to initialize Chrome driver
def initialize_driver(download_dir):
    chrome_options = get_chrome_options(download_dir)
    driver = webdriver.Chrome(options=chrome_options)
    enable_download_headless(driver, download_dir)
    return driver

# Function to generate report
def generate_report(driver, report_xpath, download_dir, base_file_name, sheet):
    try:
        report = driver.find_element(By.XPATH, report_xpath)
        report.click()
        logging.info(f"Report clicked for {base_file_name}")
        log_to_google_sheets(sheet, f"INFO: Report clicked for {base_file_name}")

        # Set report options
        go_to_settings(driver)
        format_drop = driver.find_element(By.ID, "mode")
        htmlop = Select(format_drop)
        htmlop.select_by_value("html")
        school_list = driver.find_element(By.ID, "calendarID")
        select = Select(school_list)
        school_options = ["4163", "4164", "4165", "4166", "4166"]
        for value in school_options:
            select.select_by_value(value)
        logging.info(f"Options set for {base_file_name}")
        log_to_google_sheets(sheet, f"INFO: Options set for {base_file_name}")

        # Generate report
        generate_button = driver.find_element(By.ID, "next")
        generate_button.click()
        logging.info(f"Report generation initiated for {base_file_name}")
        log_to_google_sheets(sheet, f"INFO: Generate report button clicked for {base_file_name}.")

        # Wait for report to download
        time.sleep(60)
        return process_download(download_dir, base_file_name, sheet)

    except Exception as e:
        logging.error(f"Error generating report for {base_file_name}: {e}")
        log_to_google_sheets(sheet, f"ERROR: Unable to generate report for {base_file_name}: {e}")
        return False

# Function to process downloaded report
def process_download(download_dir, base_file_name, sheet):
    try:
        html_files = glob.glob(os.path.join(download_dir, 'extract.html'))
        if html_files:
            most_recent_html = html_files[0]
            with open(most_recent_html, 'r') as file:
                html_content = file.read()
                num_records = html_content.count('<tr>')
                if num_records > 2:  # Check if there are more than 2 records
                    os.rename(most_recent_html, os.path.join(download_dir, f"{base_file_name}.html"))
                    logging.info(f"Renamed extract.html to '{base_file_name}.html'")
                    log_to_google_sheets(sheet, f"INFO: Renamed extract.html to '{base_file_name}.html'")
                    df = pd.read_html(os.path.join(download_dir, f"{base_file_name}.html"), header=1)[0]
                    df = df[df.iloc[:, 0] != "All Records"]
                    cleaned_csv_path = os.path.join(download_dir, f"{base_file_name}.csv")
                    df.to_csv(cleaned_csv_path, index=False)
                    logging.info(f"Updated file saved to '{cleaned_csv_path}'")
                    log_to_google_sheets(sheet, f"INFO: Updated file saved to '{cleaned_csv_path}'")
                    return True
                else:
                    os.remove(most_recent_html)
                    logging.info(f"Deleted '{most_recent_html}' as it has 2 or fewer records.")
                    log_to_google_sheets(sheet, f"INFO: Deleted '{most_recent_html}' as it has 2 or fewer records.")
                    return False
        else:
            logging.warning("No 'extract.html' file found in the directory.")
            log_to_google_sheets(sheet, "WARNING: No 'extract.html' file found in the directory.")
            return False
    except Exception as e:
        logging.error(f"Error processing download for {base_file_name}: {e}")
        log_to_google_sheets(sheet, f"ERROR: Unable to process a download for {base_file_name}: {e}")
        return False

# Main function
def main():
    # Record the start time
    start_time = time.time()
    download_dir = "/home/KIPPNashvilleData/icampus_downloads/"

    # Retrieve credentials and report configurations
    logging.info("Retrieving credentials and report configurations")
    username, password, ic_url, reports_url, reports = get_config()
    logging.info("Credentials and configurations retrieved")

    # Set up Google Sheets
    spreadsheet_name = 'PythonAnywhereLogs'  # Name of your Google Sheets workbook
    sheet_name = 'ic_student_data'  # Name of the sheet within the workbook
    sheet = setup_google_sheets(spreadsheet_name, sheet_name)
    log_to_google_sheets(sheet, "INFO: Starting process to access Infinite Campus.")

    # Initialize Chrome driver
    logging.info("Starting Chromedriver set up...")
    driver = initialize_driver(download_dir)
    logging.info("Chromedriver set up and initialized")

    # Open IC site and login
    logging.info("Opening Chromedriver and navigating to IC site")
    driver.get(ic_url)
    logging.info(f"Site opened: {driver.title}")
    try:
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "password"))).send_keys(password)
        time.sleep(10)
        driver.find_element(By.ID, "signinbtn").click()
        time.sleep(15)

        # Check if login was successful
        expected_title = "Infinite Campus"
        if driver.title != expected_title:
            raise Exception("Login failed: Site title does not match 'Infinite Campus'")

        logging.info(f"Logged in to IC: {driver.title}")
        log_to_google_sheets(sheet, f"INFO: Logged in to IC: {driver.title}")

    except Exception as e:
        logging.error(f"Error logging in to IC: {e}")
        log_to_google_sheets(sheet, f"EROR: Unable to log in to IC: {e}")
        driver.quit()
        return

    # Navigate to reports frame
    logging.info("Clicking Link to Data Viewer Frame")
    driver.get(reports_url)
    logging.info(f"Site opened: {driver.title}")
    log_to_google_sheets(sheet, f"INFO: Site opened: {driver.title}")

    # Generate the specific report
    base_file_name = "student_data"
    report_xpath = '//*[@id="row84446"]/td[3]' # student_data

    # report_xpath = '//*[@id="row84450"]/td[3]' # attendance_codes
    # base_file_name = "attendance_codes"


    # Go to reports and generate report
    go_to_reports_id(driver)
    report_generated = generate_report(driver, report_xpath, download_dir, base_file_name, sheet)
    if report_generated:
        logging.info(f"Report generation and processing completed successfully for {base_file_name}")
        log_to_google_sheets(sheet, f"INFO: Report generation and processing completed successfully for {base_file_name}")
    else:
        logging.warning(f"Failed to generate or process the report for {base_file_name}")
        log_to_google_sheets(sheet, f"WARNING: Did not generate or process the report for {base_file_name}")

    # Close Chrome driver
    driver.quit()
    logging.info("Reports generation and processing completed")
    logging.info(f"Elapsed time: {time.time() - start_time} seconds")
    log_to_google_sheets(sheet, "INFO: Reports generation and processing completed")

    # Calculate and log the elapsed time
    elapsed_time = time.time() - start_time
    logging.info(f"Script executed in {elapsed_time:.2f} seconds.")
    log_to_google_sheets(sheet, f"INFO: Script executed in {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    main()


# import os
# import glob
# import time
# import json
# import logging
# import pandas as pd
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support.select import Select
# from selenium.webdriver.support import expected_conditions as EC
# from navigator import go_to_reports_id, go_to_settings, get_chrome_options, enable_download_headless

# # Configure logging
# logging.basicConfig(
#     filename='/home/KIPPNashvilleData/infinite_campus/icampus_reports.log',
#     level=logging.INFO,
#     format='%(asctime)s:%(levelname)s:%(message)s'
# )

# # Set up Google Sheets credentials and client
# def setup_google_sheets(spreadsheet_name, sheet_name):
#     scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#     creds = ServiceAccountCredentials.from_json_keyfile_name('/home/KIPPNashvilleData/creds.json', scope)
#     client = gspread.authorize(creds)
#     sheet = client.open(spreadsheet_name).worksheet(sheet_name)
#     return sheet

# # Log to Google Sheets
# def log_to_google_sheets(sheet, message):
#     sheet.append_row([time.strftime("%Y-%m-%d %H:%M:%S"), message])

# # Function to retrieve credentials and report configurations from JSON file
# def get_config():
#     config_file_path = os.path.join("/home/KIPPNashvilleData/", "credentials_all.json")
#     with open(config_file_path) as config_file:
#         data = json.load(config_file)
#     infinitecampus = data["infinitecampus"]
#     icampus_reports = data["icampus_reports"]
#     return infinitecampus["username"], infinitecampus["password"], infinitecampus["ic_url"], infinitecampus["reports_url"], icampus_reports

# # Function to initialize Chrome driver
# def initialize_driver(download_dir):
#     chrome_options = get_chrome_options(download_dir)
#     driver = webdriver.Chrome(options=chrome_options)
#     enable_download_headless(driver, download_dir)
#     return driver

# # Function to generate report
# def generate_report(driver, report_xpath, download_dir, base_file_name, sheet):
#     try:
#         report = driver.find_element(By.XPATH, report_xpath)
#         report.click()
#         logging.info(f"Report clicked for {base_file_name}")
#         log_to_google_sheets(sheet, f"Report clicked for {base_file_name}")

#         # Set report options
#         go_to_settings(driver)
#         format_drop = driver.find_element(By.ID, "mode")
#         htmlop = Select(format_drop)
#         htmlop.select_by_value("html")
#         school_list = driver.find_element(By.ID, "calendarID")
#         select = Select(school_list)
#         school_options = ["4163", "4164", "4165", "4166", "4166"]
#         for value in school_options:
#             select.select_by_value(value)
#         logging.info(f"Options set for {base_file_name}")
#         log_to_google_sheets(sheet, f"Options set for {base_file_name}")

#         # Generate report
#         generate_button = driver.find_element(By.ID, "next")
#         generate_button.click()
#         logging.info(f"Report generation initiated for {base_file_name}")
#         log_to_google_sheets(sheet, f"Report generation initiated for {base_file_name}")

#         # Wait for report to download
#         time.sleep(60)
#         return process_download(download_dir, base_file_name, sheet)

#     except Exception as e:
#         logging.error(f"Error generating report for {base_file_name}: {e}")
#         log_to_google_sheets(sheet, f"Error generating report for {base_file_name}: {e}")
#         return False

# # Function to process downloaded report
# def process_download(download_dir, base_file_name, sheet):
#     try:
#         html_files = glob.glob(os.path.join(download_dir, 'extract.html'))
#         if html_files:
#             most_recent_html = html_files[0]
#             with open(most_recent_html, 'r') as file:
#                 html_content = file.read()
#                 num_records = html_content.count('<tr>')
#                 if num_records > 2:  # Check if there are more than 2 records
#                     os.rename(most_recent_html, os.path.join(download_dir, f"{base_file_name}.html"))
#                     logging.info(f"Renamed extract.html to '{base_file_name}.html'")
#                     log_to_google_sheets(sheet, f"Renamed extract.html to '{base_file_name}.html'")
#                     df = pd.read_html(os.path.join(download_dir, f"{base_file_name}.html"), header=1)[0]
#                     df = df[df.iloc[:, 0] != "All Records"]
#                     cleaned_csv_path = os.path.join(download_dir, f"{base_file_name}.csv")
#                     df.to_csv(cleaned_csv_path, index=False)
#                     logging.info(f"Cleaned data saved to '{cleaned_csv_path}'")
#                     log_to_google_sheets(sheet, f"Cleaned data saved to '{cleaned_csv_path}'")
#                     return True
#                 else:
#                     os.remove(most_recent_html)
#                     logging.info(f"Deleted '{most_recent_html}' as it has 2 or fewer records.")
#                     log_to_google_sheets(sheet, f"Deleted '{most_recent_html}' as it has 2 or fewer records.")
#                     return False
#         else:
#             logging.warning("No 'extract.html' file found in the directory.")
#             log_to_google_sheets(sheet, "No 'extract.html' file found in the directory.")
#             return False
#     except Exception as e:
#         logging.error(f"Error processing download for {base_file_name}: {e}")
#         log_to_google_sheets(sheet, f"Error processing download for {base_file_name}: {e}")
#         return False

# # Main function
# def main():
#     # Record the start time
#     start_time = time.time()
#     download_dir = "/home/KIPPNashvilleData/icampus_downloads/"

#     # Retrieve credentials and report configurations
#     logging.info("Retrieving credentials and report configurations")
#     username, password, ic_url, reports_url, reports = get_config()
#     logging.info("Credentials and configurations retrieved")

#     # Set up Google Sheets
#     spreadsheet_name = 'PythonAnywhereLogs'  # Name of your Google Sheets workbook
#     sheet_name = 'ic_student_data'  # Name of the sheet within the workbook
#     sheet = setup_google_sheets(spreadsheet_name, sheet_name)
#     log_to_google_sheets(sheet, "Started processing reports")

#     # Initialize Chrome driver
#     logging.info("Starting Chromedriver set up...")
#     driver = initialize_driver(download_dir)
#     logging.info("Chromedriver set up and initialized")

#     # Open IC site and login
#     logging.info("Opening Chromedriver and navigating to IC site")
#     driver.get(ic_url)
#     logging.info(f"Site opened: {driver.title}")
#     try:
#         WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
#         WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "password"))).send_keys(password)
#         time.sleep(10)
#         driver.find_element(By.ID, "signinbtn").click()
#         time.sleep(15)
#         logging.info(f"Logged in to IC: {driver.title}")
#         log_to_google_sheets(sheet, f"Logged in to IC: {driver.title}")
#     except Exception as e:
#         logging.error(f"Error logging in to IC: {e}")
#         log_to_google_sheets(sheet, f"Error logging in to IC: {e}")
#         driver.quit()
#         return

#     # Navigate to reports frame
#     logging.info("Clicking Link to Data Viewer Frame")
#     driver.get(reports_url)
#     logging.info(f"Site opened: {driver.title}")
#     log_to_google_sheets(sheet, f"Site opened: {driver.title}")

#     # Generate the specific report
#     base_file_name = "student_data"
#     report_xpath = '//*[@id="row84446"]/td[3]'

#     # Go to reports and generate report
#     go_to_reports_id(driver)
#     report_generated = generate_report(driver, report_xpath, download_dir, base_file_name, sheet)
#     if report_generated:
#         logging.info(f"Report generation and processing completed successfully for {base_file_name}")
#         log_to_google_sheets(sheet, f"Report generation and processing completed successfully for {base_file_name}")
#     else:
#         logging.warning(f"Failed to generate or process the report for {base_file_name}")
#         log_to_google_sheets(sheet, f"Failed to generate or process the report for {base_file_name}")

#     # Close Chrome driver
#     driver.quit()
#     logging.info("Reports generation and processing completed")
#     logging.info(f"Elapsed time: {time.time() - start_time} seconds")
#     log_to_google_sheets(sheet, "Reports generation and processing completed")


# if __name__ == "__main__":
#     main()


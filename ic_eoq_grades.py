# import os
import sys
import time
import json
# import logging
# from datetime import datetime, timedelta
# import pandas as pd
from kipp import *

# Constants and configurations
BASE_FILE_NAME = "eoq_grades"
REPORT_XPATH = '//*[@id="row84445"]/td[3]'  # student_data
DOWNLOAD_DIR = "/home/KIPPNashvilleData/icampus_downloads/"
LOG_FILE = "/home/KIPPNashvilleData/icampus/icampus_reports.log"
SPREADSHEET_NAME = 'PythonAnywhereLogs'  # Name of your Google Sheets workbook
SHEET_NAME = 'eoq_grades'  # Name of the sheet within the workbook
aws_folder = 'icampus'
CONFIG_FILE_PATH = "/home/KIPPNashvilleData/credentials_all.json"  # Path to the configuration file
cleaning_method = "base"  # Specify the desired cleaning method

# Set up logging
setup_logging(LOG_FILE)

# Function to retrieve credentials and report configurations from JSON file
def get_config():
    config_file_path = CONFIG_FILE_PATH
    with open(config_file_path) as config_file:
        data = json.load(config_file)
    infinitecampus = data["infinitecampus"]
    icampus_reports = data["icampus_reports"]
    return infinitecampus["username"], infinitecampus["password"], infinitecampus["ic_url"], infinitecampus["reports_url"], icampus_reports, data["awss3"]

# Main function
def main():
    # Set up Google Sheets
    sheet = setup_google_sheets(SPREADSHEET_NAME, SHEET_NAME)

    # Record the start time
    start_time = time.time()
    log_message(sheet, f'INFO: Script Started at {start_time}')
    log_message(sheet, "INFO: Starting process to access Infinite Campus.")

    # Retrieve credentials and report configurations
    log_message(sheet, "INFO: Retrieving credentials and report configurations")
    username, password, ic_url, reports_url, reports, aws_config = get_config()
    log_message(sheet, "INFO: Credentials and configurations retrieved")

    # Set up Chromedriver
    log_message(sheet, "INFO: Starting Chromedriver Set up.")
    driver = setup_chromedriver(DOWNLOAD_DIR)
    log_message(sheet, "Chromedriver Set up.")

    # Open Browser & Navigate to Infinite Campus
    log_message(sheet, "INFO: Opening Chromedriver and navigating to IC site")
    driver.get(ic_url)
    log_message(sheet, f"INFO: Site opened - {driver.title}")

    # Try to log in
    if not login_to_icampus(driver, username, password, sheet):
        log_message(sheet, "ERROR: Unable to log in to IC.")
        driver.quit()
        return

    # Navigate to reports frame
    log_message(sheet, "INFO: Clicking Link to Data Viewer Frame")
    driver.get(reports_url)
    log_message(sheet, f"INFO: Site opened: {driver.title}")

    # Go to reports and generate report
    go_to_reports_id(driver, sheet)
    report_generated = generate_report(driver, REPORT_XPATH, DOWNLOAD_DIR, BASE_FILE_NAME, sheet)
    if report_generated:
        log_message(sheet, f"INFO: Report generation and processing completed successfully for {BASE_FILE_NAME}")
    else:
        log_message(sheet, f"WARNING: Did not generate or process the report for {BASE_FILE_NAME}")

    # Close Chrome driver
    driver.quit()
    log_message(sheet, "INFO: Reports generation and processing completed")

    # Calculate and log the elapsed time
    elapsed_time = time.time() - start_time
    log_message(sheet, f"INFO: Script executed in {elapsed_time:.2f} seconds.")

    # Define CSV file path and cleaning method
    csv_file = f"{BASE_FILE_NAME}.csv"
    directory_path = DOWNLOAD_DIR

    # Process CSV File and upload to S3
    process_csv_file(CONFIG_FILE_PATH, csv_file, directory_path, aws_folder, cleaning_method, sheet)
    log_message(sheet, "INFO: File cleaned and transferred to AWS S3 bucket")

    log_message(sheet, f"INFO: Elapsed time = {time.time() - start_time} seconds")

if __name__ == "__main__":
    try:
        main()
        sys.exit(0)  # Successful execution
    except Exception as e:
        # log_message(sheet, f"ERROR: {str(e)}")
        sys.exit(1)  # Error occurred

# import os
# import time
# import json
# from kipp import *

# # Constants and configurations
# BASE_FILE_NAME = "eoq_grades"
# REPORT_XPATH = '//*[@id="row84445"]/td[3]'  # student_data
# DOWNLOAD_DIR = "/home/KIPPNashvilleData/icampus_downloads/"
# LOG_FILE = "/home/KIPPNashvilleData/icampus/icampus_reports.log"
# SPREADSHEET_NAME = 'PythonAnywhereLogs'  # Name of your Google Sheets workbook
# SHEET_NAME = 'eoq_grades'  # Name of the sheet within the workbook
# aws_folder = 'icampus'


# # Set up logging
# setup_logging(LOG_FILE)

# # Function to retrieve credentials and report configurations from JSON file
# def get_config():
#     config_file_path = os.path.join("/home/KIPPNashvilleData/", "credentials_all.json")
#     with open(config_file_path) as config_file:
#         data = json.load(config_file)
#     infinitecampus = data["infinitecampus"]
#     icampus_reports = data["icampus_reports"]
#     return infinitecampus["username"], infinitecampus["password"], infinitecampus["ic_url"], infinitecampus["reports_url"], icampus_reports

# # Main function
# def main():
#     # Set up Google Sheets
#     sheet = setup_google_sheets(SPREADSHEET_NAME, SHEET_NAME)

#     # Record the start time
#     start_time = time.time()
#     log_message(sheet, f'INFO: Script Started at {start_time}')
#     log_message(sheet, "INFO: Starting process to access Infinite Campus.")

#     # Retrieve credentials and report configurations
#     log_message(sheet, "INFO: Retrieving credentials and report configurations")
#     username, password, ic_url, reports_url, reports = get_config()
#     log_message(sheet, "INFO: Credentials and configurations retrieved")

#     # Set up Chromedriver
#     log_message(sheet, "INFO: Starting Chromedriver Set up.")
#     driver = setup_chromedriver(DOWNLOAD_DIR)
#     log_message(sheet, "Chromedriver Set up.")

#     # Open Browser & Navigate to Infinite Campus
#     log_message(sheet, "INFO: Opening Chromedriver and navigating to IC site")
#     driver.get(ic_url)
#     log_message(sheet, f"INFO: Site opened - {driver.title}")

#     # Try to log in
#     if not login_to_icampus(driver, username, password):
#         log_message(sheet, "ERROR: Unable to log in to IC.")
#         driver.quit()
#         return

#     # Navigate to reports frame
#     log_message(sheet, "INFO: Clicking Link to Data Viewer Frame")
#     driver.get(reports_url)
#     log_message(sheet, f"INFO: Site opened: {driver.title}")

#     # Go to reports and generate report
#     go_to_reports_id(driver)
#     report_generated = generate_report(driver, REPORT_XPATH, DOWNLOAD_DIR, BASE_FILE_NAME, sheet)
#     if report_generated:
#         log_message(sheet, f"INFO: Report generation and processing completed successfully for {BASE_FILE_NAME}")
#     else:
#         log_message(sheet, f"WARNING: Did not generate or process the report for {BASE_FILE_NAME}")

#     # Close Chrome driver
#     driver.quit()
#     log_message(sheet, "INFO: Reports generation and processing completed")


#     # Calculate and log the elapsed time
#     elapsed_time = time.time() - start_time
#     log_message(sheet, f"INFO: Script executed in {elapsed_time:.2f} seconds.")

#     #Process CSV File
#     process_csv_file(CONFIG_FILE_PATH, csv_file, directory_path, aws_folder, cleaning_method)
#     log_message(sheet, "INFO: File cleaned and transfered to AWS S3 bucket")

#     log_message(sheet, f"Info: Elapsed time = {time.time() - start_time} seconds")

# if __name__ == "__main__":
#     try:
#         main()
#         sys.exit(0)  # Successful execution
#     except Exception as e:
#         log_message(sheet, f"ERROR: {str(e)}")
#         sys.exit(1)  # Error occurred
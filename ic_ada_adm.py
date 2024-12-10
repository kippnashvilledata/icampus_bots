import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from navigator import setup_chromedriver

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
DOWNLOAD_DIR = "/home/KIPPNashvilleData/icampus_downloads/"
CONFIG_FILE_PATH = "/home/KIPPNashvilleData/credentials_all.json"
FILE_PATH = os.path.join(DOWNLOAD_DIR, 'ADM_ADA_Detail_Report.csv')
CLEANED_CSV_PATH = os.path.join(DOWNLOAD_DIR, 'adm_ada.csv')
MAX_ATTEMPTS = 5
WAIT_TIME = 300  # 5 minutes in seconds

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

# Function to get yesterday's date
def get_yesterday_date():
    current_datetime = datetime.now()
    previous_day = current_datetime - timedelta(days=1)
    return previous_day.strftime("%m/%d/%Y")

# Function to load credentials from a JSON file
def load_credentials(config_path):
    with open(config_path) as config_file:
        data = json.load(config_file)
    config = data["infinitecampus"]
    return config["username"], config["password"], config["ic_url"], config["ada_adm_url"]

# Function to wait for a file to be created
def wait_for_file(file_path, max_attempts, wait_time, sheet):
    attempt = 0
    while attempt < max_attempts:
        if os.path.exists(file_path):
            logging.info(f'FOUND: {file_path}. Proceeding with the script.')
            log_to_google_sheets(sheet, f"INFO: FOUND: {file_path}. Proceeding with the script.")
            return True
        else:
            logging.warning(f'DID NOT FIND: {file_path}. Attempt {attempt + 1} of {max_attempts}. Retrying in 5 minutes.')
            log_to_google_sheets(sheet, f"WARNING: DID NOT FIND: {file_path}. Attempt {attempt + 1} of {max_attempts}. Retrying in 5 minutes.")
            attempt += 1
            time.sleep(wait_time)
    return False

# Main function
def main():
    # Set up Google Sheets
    spreadsheet_name = 'PythonAnywhereLogs'  # Name of your Google Sheets workbook
    sheet_name = 'ic_ada_adm'  # Name of the sheet within the workbook
    sheet = setup_google_sheets(spreadsheet_name, sheet_name)

    # Change to the current first day of school
    first_day = '08/06/2024'
    yesterday = get_yesterday_date()

    # Start time to calculate script run time.
    start_time = time.time()

    log_to_google_sheets(sheet, f"INFO: Script started. First day = {first_day}, Yesterday = {yesterday}")

    """ CHANGEABLE VARIABLES """
    # HTML elements: Update if Infinite Campus code is changed.
    html_elements = {
        "end_date": "endDate",
        "detail_button": 'input[type="radio"][title="summary information + data for each student"]',
        "calc_button": '//*[@id="reportOptions"]/table/tbody/tr[4]/td[1]/table/tbody/tr[10]/td/label[2]',
        "dropdown_element": "format",
        "school_list": "calendarID",
        "generate_button": "sbutton"
    }

    # Site names for WebDriverWait: Update if Page Names are changed
    home_page = "Infinite Campus"
    report_page = "ADM & ADA Report Options"

    # Infinite Campus School Numbers: If the method for selecting them in report options changes, update here.
    school_options = ["4163", "4164", "4165", "4166", "4166"]

    logging.info(f"Set variables 'first_day' = {first_day} & 'yesterday' = {yesterday}")
    log_to_google_sheets(sheet, f"INFO: Set variables 'first_day' = {first_day} & 'yesterday' = {yesterday}")

    logging.info("Retrieving credentials...")
    username, password, site, reports = load_credentials(CONFIG_FILE_PATH)
    logging.info("Credentials retrieved")
    log_to_google_sheets(sheet, "INFO: Credentials retrieved")

    logging.info("Starting Chromedriver setup")
    driver = setup_chromedriver(DOWNLOAD_DIR)
    logging.info("Chromedriver set up and initialized")
    log_to_google_sheets(sheet, "INFO: Chromedriver set up and initialized")

    logging.info("Opening Chromedriver and navigating to IC site")
    driver.get(site)
    logging.info(f"Site Name: {driver.title}")
    logging.info("Site Open")
    log_to_google_sheets(sheet, f"INFO: Site opened: {driver.title}")

    logging.info("Logging in to site")
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "password"))).send_keys(password)
    time.sleep(10)
    driver.find_element(By.ID, "signinbtn").click()
    time.sleep(15)

    WebDriverWait(driver, 60).until(EC.title_is(home_page))
    driver.get(reports)
    logging.info(f"Site Name: {driver.title}")
    log_to_google_sheets(sheet, f"INFO: Site name after login: {driver.title}")

    WebDriverWait(driver, 60).until(EC.title_is(report_page))

    logging.info("Entering report options")
    end_date = driver.find_element(By.ID, html_elements["end_date"])
    end_date.send_keys(Keys.CONTROL + "a")
    end_date.send_keys(Keys.DELETE)
    end_date.send_keys(first_day)

    end_date = driver.find_element(By.ID, html_elements["end_date"])
    end_date.send_keys(Keys.CONTROL + "a")
    end_date.send_keys(Keys.DELETE)
    end_date.send_keys(yesterday)

    detail_button = driver.find_element(By.CSS_SELECTOR, html_elements["detail_button"])
    detail_button.click()

    calc_button = driver.find_element(By.XPATH, html_elements["calc_button"])
    calc_button.click()

    dropdown_element = driver.find_element(By.ID, html_elements["dropdown_element"])
    format_drop = Select(dropdown_element)
    format_drop.select_by_value('csv')

    school_list = driver.find_element(By.ID, html_elements["school_list"])
    select = Select(school_list)
    for value in school_options:
        select.select_by_value(value)
    logging.info("Options set")
    log_to_google_sheets(sheet, "INFO: Report options set")

    initial_window_handles = driver.window_handles
    handle_length = len(initial_window_handles)

    generate_button = driver.find_element(By.ID, html_elements["generate_button"])
    generate_button.click()

    WebDriverWait(driver, 180).until(lambda driver: len(driver.window_handles) > handle_length)
    logging.info("Report window opened")
    log_to_google_sheets(sheet, "INFO: Report window opened")
    time.sleep(60)

    if not wait_for_file(FILE_PATH, MAX_ATTEMPTS, WAIT_TIME, sheet):
        logging.error(f'DID NOT FIND: {FILE_PATH} after {MAX_ATTEMPTS} attempts. Closing browser and exiting script.')
        log_to_google_sheets(sheet, f"ERROR: DID NOT FIND: {FILE_PATH} after {MAX_ATTEMPTS} attempts. Exiting script.")
        driver.close()
        sys.exit()

    driver.close()
    logging.info("Driver Closed")
    log_to_google_sheets(sheet, "INFO: Driver closed")

    df = pd.read_csv(FILE_PATH, skiprows=range(1, 36), header=0, index_col=False, engine='python')
    num_rows = df.shape[0]
    num_cols = df.shape[1]
    logging.info(f"Columns: {num_cols}")
    logging.info(f"Rows: {num_rows}")
    logging.info(df.head(10))
    log_to_google_sheets(sheet, f"INFO: CSV Columns: {num_cols}, Rows: {num_rows}")

    df = df.drop('Student Count', axis=1)
    logging.info("\nDataFrame after dropping 'Student Count':")
    logging.info(df)

    df.to_csv(CLEANED_CSV_PATH, index=False)
    logging.info(f"Cleaned file saved to {CLEANED_CSV_PATH}")
    log_to_google_sheets(sheet, f"INFO: Cleaned file saved to {CLEANED_CSV_PATH}")

    end_time = time.time()
    elapsed_time = end_time - start_time
    logging.info(f"Script finished in {elapsed_time:.2f} seconds.")
    log_to_google_sheets(sheet, f"INFO: Script finished in {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    main()

# import os
# import sys
# import time
# import json
# import logging
# from datetime import datetime, timedelta
# import pandas as pd
# # from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.select import Select
# from navigator import setup_chromedriver

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# # Constants
# DOWNLOAD_DIR = "/home/KIPPNashvilleData/icampus_downloads/"
# CONFIG_FILE_PATH = "/home/KIPPNashvilleData/credentials_all.json"
# FILE_PATH = os.path.join(DOWNLOAD_DIR, 'ADM_ADA_Detail_Report.csv')
# CLEANED_CSV_PATH = os.path.join(DOWNLOAD_DIR, 'adm_ada.csv')
# MAX_ATTEMPTS = 5
# WAIT_TIME = 300  # 5 minutes in seconds

# def get_yesterday_date():
#     current_datetime = datetime.now()
#     previous_day = current_datetime - timedelta(days=1)
#     return previous_day.strftime("%m/%d/%Y")

# def load_credentials(config_path):
#     with open(config_path) as config_file:
#         data = json.load(config_file)
#     config = data["infinitecampus"]
#     return config["username"], config["password"], config["ic_url"], config["ada_adm_url"]

# def wait_for_file(file_path, max_attempts, wait_time):
#     attempt = 0
#     while attempt < max_attempts:
#         if os.path.exists(file_path):
#             logging.info(f'FOUND: {file_path}. Proceeding with the script.')
#             return True
#         else:
#             logging.warning(f'DID NOT FIND: {file_path}. Attempt {attempt + 1} of {max_attempts}. Retrying in 5 minutes.')
#             attempt += 1
#             time.sleep(wait_time)
#     return False

# def main():
#     # Change to the current first day of school
#     first_day = '08/06/2024'
#     yesterday = get_yesterday_date()

#     #Start time to calculate script run time.
#     start_time = time.time()

#     """ CHANGEABLE VARIABLES """
#     # HTML elements: Update if Infinite Campus code is changed.
#     html_elements = {
#         "end_date": "endDate",
#         "detail_button": 'input[type="radio"][title="summary information + data for each student"]',
#         "calc_button": '//*[@id="reportOptions"]/table/tbody/tr[4]/td[1]/table/tbody/tr[10]/td/label[2]',
#         "dropdown_element": "format",
#         "school_list": "calendarID",
#         "generate_button": "sbutton"
#     }

#     # Site names for WebDriverWait: Update if Page Names are changed
#     home_page = "Infinite Campus"
#     report_page = "ADM & ADA Report Options"

#     # Infinite Campus School Numbers: If the method for selecting them in report options changes, update here.
#     school_options = ["4163", "4164", "4165", "4166", "4166"]


#     """ Start of Active Script """
#     logging.info(f"Set variables 'first_day' = {first_day} & 'yesterday' = {yesterday}")
#     logging.info("Retrieving credentials...")
#     username, password, site, reports = load_credentials(CONFIG_FILE_PATH)
#     logging.info("Credentials retrieved")

#     logging.info("Starting Chromedriver setup")
#     driver = setup_chromedriver(DOWNLOAD_DIR)
#     logging.info("Chromedriver set up and initialized")

#     logging.info("Opening Chromedriver and navigating to IC site")
#     driver.get(site)
#     logging.info(f"Site Name: {driver.title}")
#     logging.info("Site Open")

#     logging.info("Logging in to site")
#     WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
#     WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "password"))).send_keys(password)
#     time.sleep(10)
#     driver.find_element(By.ID, "signinbtn").click()
#     time.sleep(15)

#     WebDriverWait(driver, 60).until(EC.title_is(home_page))
#     driver.get(reports)
#     logging.info(f"Site Name: {driver.title}")

#     WebDriverWait(driver, 60).until(EC.title_is(report_page))

#     logging.info("Entering report options")
#     end_date = driver.find_element(By.ID, html_elements["end_date"])
#     end_date.send_keys(Keys.CONTROL + "a")
#     end_date.send_keys(Keys.DELETE)
#     end_date.send_keys(first_day)

#     end_date = driver.find_element(By.ID, html_elements["end_date"])
#     end_date.send_keys(Keys.CONTROL + "a")
#     end_date.send_keys(Keys.DELETE)
#     end_date.send_keys(yesterday)

#     detail_button = driver.find_element(By.CSS_SELECTOR, html_elements["detail_button"])
#     detail_button.click()

#     calc_button = driver.find_element(By.XPATH, html_elements["calc_button"])
#     calc_button.click()

#     dropdown_element = driver.find_element(By.ID, html_elements["dropdown_element"])
#     format_drop = Select(dropdown_element)
#     format_drop.select_by_value('csv')

#     school_list = driver.find_element(By.ID, html_elements["school_list"])
#     select = Select(school_list)
#     for value in school_options:
#         select.select_by_value(value)
#     logging.info("Options set")

#     initial_window_handles = driver.window_handles
#     handle_length = len(initial_window_handles)

#     generate_button = driver.find_element(By.ID, html_elements["generate_button"])
#     generate_button.click()

#     WebDriverWait(driver, 180).until(lambda driver: len(driver.window_handles) > handle_length)
#     logging.info("Report window opened")
#     time.sleep(60)

#     if not wait_for_file(FILE_PATH, MAX_ATTEMPTS, WAIT_TIME):
#         logging.error(f'DID NOT FIND: {FILE_PATH} after {MAX_ATTEMPTS} attempts. Closing browser and exiting script.')
#         driver.close()
#         sys.exit()

#     driver.close()
#     logging.info("Driver Closed")

#     df = pd.read_csv(FILE_PATH, skiprows=range(1, 36), header=0, index_col=False, engine='python')
#     num_rows = df.shape[0]
#     num_cols = df.shape[1]
#     logging.info(f"Columns: {num_cols}")
#     logging.info(f"Rows: {num_rows}")
#     logging.info(df.head(10))

#     df = df.drop('Student Count', axis=1)
#     logging.info("\nDataFrame after dropping 'Student Count':")
#     logging.info(df)

#     df.to_csv(CLEANED_CSV_PATH, index=False)
#     logging.info(f"Cleaned file saved to {CLEANED_CSV_PATH}")

#     if os.path.exists(FILE_PATH):
#         os.remove(FILE_PATH)
#         logging.info(f'{FILE_PATH} has been deleted.')
#     else:
#         logging.warning(f'{FILE_PATH} does not exist.')

#     logging.info("Original file deleted from directory.")

#     end_time = time.time()
#     elapsed_time = end_time - start_time
#     logging.info(f"Script execution time: {elapsed_time} seconds")

# if __name__ == "__main__":
#     main()
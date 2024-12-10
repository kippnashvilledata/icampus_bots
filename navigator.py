import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException



def get_chrome_options(download_dir):
    """ Sets the chrome drive options """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-infobars")
    # chrome_options.add_argument("--disable-extensions")
    # chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-popup-blocking")
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False, # added for testing remove if problems
        "download.directory_upgrade": True, # added for testing remove if problems
        "w3c": True,
        "safebrowsing.enabled": True
        }
    chrome_options.add_experimental_option('prefs', prefs)
    return chrome_options

def enable_download_headless(browser,download_dir):
    # """ Enable and define how files ar downloaded """
     browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
     params = {'cmd':'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
     browser.execute("send_command", params)


def enable_download_headless1(browser, download_dir):
    # Enable and define how files are downloaded with file name time stamped
    browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    timestamp = time.strftime("%Y%m%d_%H%M%S")  # Get current timestamp
    filename = f"{timestamp}_extract.html"  # Construct filename with timestamp
    download_path = os.path.join(download_dir, filename)  # Combine download directory with filename
    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
    browser.execute("send_command", params)
    print(f"Downloads enabled. Files will be saved to: {download_path}")
    return filename

def setup_chromedriver(download_dir):
    chrome_options = get_chrome_options(download_dir)
    driver = webdriver.Chrome(options=chrome_options)
    enable_download_headless(driver, download_dir)
    return driver



# Maintaining the functions needed navigate Infinite Campus
"""
 - If the any IC report scraping file encounters errors on the iframe functions, the frame names may have changed in Infinite Campus.
 - At which time iframe_names will need to be updated in both iframe functions.
 - To determine the location of th iframe for each function:
    - run a report from the DataView in Infinite Campus
    - use the inspect tool to find the target frame for the report list and the settings
    - run the script called [TODO: ADD name of script with function:]
 - TODO finish instructions for running the iframe FILE * FUNCTIONS and getting frame name
 - insert new frame names into list for variable "iframe_names"
"""

def go_to_reports(driver):
    """ Move to the browser to the reports iframe. """
    driver.switch_to.default_content()
    iframe_names = ["frameWorkspace", "frameWorkspaceWrapper", "frameWorkspaceDetail", "reportList"]
    #iframe_names = ["frameWorkspaceWrapper", "frameWorkspaceDetail", "reportList"]
    for iframe_name in iframe_names:
        try:
            # Wait for the iframe to be present before switching to it
            iframe = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, iframe_name)))
            driver.switch_to.frame(iframe)
            print(f"Switched to iframe: {iframe_name}")
        except:
            print(f"Timeout: {iframe_name} iframe not found")

def go_to_reports_id(driver):
    """ Move to the browser to the reports iframe. """
    driver.switch_to.default_content()
    iframe_ids = ["frameWorkspace", "frameWorkspaceWrapper", "frameWorkspaceDetail", "reportList"]
    #iframe_names = ["frameWorkspaceWrapper", "frameWorkspaceDetail", "reportList"]
    for iframe_id in iframe_ids:
        try:
            # Wait for the iframe to be present before switching to it
            iframe = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, iframe_id)))
            driver.switch_to.frame(iframe)
            print(f"Switched to iframe: {iframe_id}")
        except:
            print(f"Timeout: {iframe_id} iframe not found")

# def go_to_reports(driver):

#     driver.switch_to.default_content()
#     iframe_names = ["frameWorkspace", "frameWorkspaceWrapper", "frameWorkspaceDetail", "reportList"]
#     for iframe_name in iframe_names:
#         driver.switch_to.frame(iframe_name)
#         print(f"Switched to iframe: {iframe_name}")

def go_to_settings(driver):
    """ Move the browser to the iframe with the report settings. """
    driver.switch_to.default_content()
    iframe_names = ["frameWorkspace", "frameWorkspaceWrapper", "frameWorkspaceDetail"]
    for iframe_name in iframe_names:
        try:
            # Wait for the iframe to be present before switching to it
            iframe = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, iframe_name)))
            driver.switch_to.frame(iframe)
            print(f"Switched to iframe: {iframe_name}")
        except TimeoutException:
            print(f"Timeout: {iframe_name} iframe not found")


def traverse_iframes_by_index(driver):
    """ Use to find the names of the iframes in the infinite campus site page """
    def print_iframe_details(index, iframe_name):
        print(f"Switched to iframe with index {index}: {iframe_name}")

    def traverse_iframes_recursive(driver, iframes, index=0):
        if index < len(iframes):
            iframe_element = iframes[index]
            driver.switch_to.frame(iframe_element)
            iframe_name = driver.execute_script("return window.name;")
            print_iframe_details(index, iframe_name)
            nested_iframes = driver.find_elements(By.TAG_NAME, "iframe")
            traverse_iframes_recursive(driver, nested_iframes)
            driver.switch_to.parent_frame()
            traverse_iframes_recursive(driver, iframes, index+1)

if __name__ == "__main__":
    print("This code is being run directly.")
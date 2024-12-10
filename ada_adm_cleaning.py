import os
import re
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
DOWNLOAD_DIR = "/home/KIPPNashvilleData/ic_downloads/"
FILE_PATH = os.path.join(DOWNLOAD_DIR, 'ADM_ADA_Detail_Report.csv')
CLEANED_CSV_PATH = os.path.join(DOWNLOAD_DIR, 'adm_ada_cleaned.csv')

def clean_headers(header):
    clean_header = header.lower().replace(' ', '_')
    clean_header = re.sub(r'[^\w_]', '_', clean_header)
    return clean_header

def process_headers(headers):
    cleaned_headers = []
    for header in headers:
        cleaned_headers.append(clean_headers(header))
    return cleaned_headers

# Function to load, clean, and save the CSV
def clean_csv():
    # Load the CSV, skipping rows and setting headers as necessary
    df = pd.read_csv(FILE_PATH, skiprows=range(1, 36), header=0, index_col=False, engine='python')

    # Log details about the loaded data
    logging.info(f"Loaded CSV with {df.shape[0]} rows and {df.shape[1]} columns.")
    logging.info(f"Preview:\n{df.head(10)}")

    # Drop the 'Student Count' column if it exists
    if 'Student Count' in df.columns:
        df = df.drop('Student Count', axis=1)
        logging.info("Dropped 'Student Count' column.")

    logging.info(f"Preview after dropped column:\n{df.head(10)}")

    df.columns = process_headers(df.columns)

    logging.info(f"Preview after cleaning headers:\n{df.head(10)}")

    # Save the cleaned CSV
    df.to_csv(CLEANED_CSV_PATH, index=False)
    logging.info(f"Cleaned file saved to {CLEANED_CSV_PATH}")


if __name__ == "__main__":
    clean_csv()
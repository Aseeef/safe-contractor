from dateutil.parser import parse

import re
import os
import requests
import time

def parse_float(value):
    """Convert string to float, handling currency symbols, empty strings, and invalid values."""
    try:
        value = normalize_text(value)

        if not value or not value.strip():
            return None

        # Remove currency symbols like 'EUR', 'USD', 'Dollar', etc.
        cleaned_value = re.sub(r'(?i)\b(eur|usd|dollar)\b', '', value)

        # Remove any non-numeric characters except for periods, commas, or minus signs
        cleaned_value = re.sub(r'[^\d.,-]', '', cleaned_value)

        # Handle commas in European number formats (e.g., 1.000,50 -> 1000.50)
        if ',' in cleaned_value and '.' not in cleaned_value:
            cleaned_value = cleaned_value.replace(',', '.')
        elif ',' in cleaned_value and '.' in cleaned_value:
            cleaned_value = cleaned_value.replace(',', '')

        return float(cleaned_value.strip())
    except ValueError:
        return None

def parse_int(value):
    """Convert string to int, handling empty strings and invalid values."""
    try:
        value = normalize_text(value)
        return int(value) if value.strip() else None
    except ValueError:
        return None


from datetime import datetime


def parse_date(date_str):
    """Attempt to parse a date string using multiple common formats and normalize it."""

    date_str = normalize_text(date_str)

    if date_str == "" or date_str == None:
        return None

    try:
        parsed_date = parse(date_str)
    except ValueError:
        print(date_str)
        exit(1)
        return None
    except OverflowError:
        return None

    normalized_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")

    return normalized_date

def normalize_text(text):
    """Normalize text by stripping whitespace and converting to lowercase."""
    return text.strip().lower() if text else None

def download_csv(url, save_path):
    """Download a large CSV file from Boston's data portal and save it locally if it's older than 1 hour"""

    # Check if the file exists and is recent (less than 1 hour old)
    if os.path.exists(save_path):
        last_modified_time = os.path.getmtime(save_path)
        current_time = time.time()

        # Skip download if file was modified in the last 3600 seconds (1 hour)
        if current_time - last_modified_time < 3600:
            print("File is already downloaded and up-to-date (less than 1 hour old).")
            return save_path

    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()  # Raise an error for bad status codes

            # Open a file to write the downloaded content
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1 MB chunks
                    if chunk:  # Skip empty chunks
                        f.write(chunk)
        print("File downloaded successfully.")
        return save_path  # Return the path to the saved file

    except requests.RequestException as ex:
        print(f"Error downloading CSV: {ex}")
        return None

    except requests.RequestException as ex:
        print(f"Error downloading CSV: {ex}")
        return None
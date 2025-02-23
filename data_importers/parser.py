from dateutil.parser import parse

import re

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
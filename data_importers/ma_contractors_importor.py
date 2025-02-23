import requests
from bs4 import BeautifulSoup
from time import sleep

import database

from data_importers.utils import normalize_text, parse_date
from datetime import datetime
from database import get_or_create_address, add_or_update_contractor, get_session

# Initial setup
url = "https://services.oca.state.ma.us/hic/licenseelist.aspx"
session = requests.Session()


# New function to extract all hidden fields at once
def extract_hidden_fields(soup):
    fields = {}
    for field in ["__VIEWSTATE", "__EVENTVALIDATION", "__VIEWSTATEGENERATOR"]:
        element = soup.find("input", {"name": field})
        fields[field] = element["value"] if element else None
    return fields


# Updated function to scrape a single page with refreshed hidden fields
def scrape_page(state_code, page_number=1, hidden_fields=None):
    # For first page, do a GET request to obtain hidden fields
    if page_number == 1 or hidden_fields is None:
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        hidden_fields = extract_hidden_fields(soup)
    # Prepare form data for postback
    post_data = {
        "__EVENTTARGET": "ctl00$pagecontentplaceholder$gvLicenseeList" if page_number > 1 else "ctl00$pagecontentplaceholder$btnSubmit",
        "__EVENTARGUMENT": f"Page${page_number}" if page_number > 1 else "",
        "__VIEWSTATE": hidden_fields.get("__VIEWSTATE"),
        "__VIEWSTATEGENERATOR": hidden_fields.get("__VIEWSTATEGENERATOR"),
        "__EVENTVALIDATION": hidden_fields.get("__EVENTVALIDATION"),
        "ctl00$pagecontentplaceholder$txtSearchState": state_code,
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    # Send the POST request
    response = session.post(url, data=post_data, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Refresh hidden fields from the latest page
    hidden_fields = extract_hidden_fields(soup)

    # If __VIEWSTATE is missing, likely we've reached the end
    if not hidden_fields.get("__VIEWSTATE"):
        return [], hidden_fields

    # Debug: print the current page HTML if needed
    # print(soup)

    # Extract the results
    results = soup.find_all("tr")
    page_data = []
    for row in results:
        columns = row.find_all("td")
        if columns:
            # Replace <br> tags with a comma and space
            for col in columns:
                for br in col.find_all("br"):
                    br.replace_with(", ")
            row_data = [col.text.strip() for col in columns]
            # Only add rows that match the expected 6 fields
            if len(row_data) == 6:
                page_data.append(row_data)

    return page_data, hidden_fields


def update_contractor_table_task():
    print(f"MA Contractors Import Task started at {datetime.now()}")

    # Step 1: Scrape multiple pages
    all_data = []
    page_number = 1
    has_more_pages = True

    # Initial hidden fields (None so that first page GET is triggered)
    hidden_fields = None

    while has_more_pages:
        print(f"Scraping contractors Page {page_number}")
        page_data, hidden_fields = scrape_page(
            state_code="MA",
            page_number=page_number,
            hidden_fields=hidden_fields
        )

        # If no data returned or critical hidden field missing, stop pagination
        if not page_data or not hidden_fields.get("__VIEWSTATE"):
            print(f"No more pages available. Stopping at Page {page_number}.")
            has_more_pages = False
        else:
            all_data.extend(page_data)
            # Process each contractor from the current page
            for contractor_data in page_data:
                company = normalize_text(contractor_data[0])
                contractor_name = normalize_text(contractor_data[1])
                # Name is in "last, first" format; we convert it to "first last"
                if contractor_name is not None:
                    contractor_name = " ".join(contractor_name.split(", ")[::-1])
                registration_no = normalize_text(contractor_data[2])
                address = normalize_text(contractor_data[3])
                expire_date = parse_date(contractor_data[4])
                status = normalize_text(contractor_data[5])

                if address is not None:
                    # Example format: "529 main street, suite p200, charlestown, ma 02129"
                    address_parts = address.split(",")
                    street_parts = address_parts[0].split(" ")
                    street_number = street_parts[0].strip()
                    street_name = " ".join(street_parts[1:]).strip()
                    has_unit_no = len(address_parts) > 3
                    if has_unit_no:
                        unit_no = address_parts[1].strip()
                    else:
                        unit_no = None
                    city = address_parts[2 if has_unit_no else 1].strip()
                    state_zip_parts = address_parts[3 if has_unit_no else 2].split(" ")
                    state = state_zip_parts[0].strip()
                    zip = state_zip_parts[1].strip()
                else:
                    unit_no = None
                    street_number = None
                    street_name = None
                    city = None
                    zip = None
                    state = None

                # Insert into contractor table
                with get_session() as session:
                    print(f"Adding contractor: {contractor_name} with registration_no: {registration_no}")
                    add_or_update_contractor(
                        session=session,
                        license_id=registration_no,
                        name=contractor_name,
                        address_id=None,
                        company=company
                    )
            session.commit()
            # Adjust page_number if needed. The current logic forces page_number to 16 if less.
            page_number += 1

        # Optionally, include a short delay to be polite to the server
        # sleep(0.1)

    # Optionally, process or store all_data as needed
    for row in all_data:
        print(row)

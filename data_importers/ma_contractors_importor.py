import requests
from bs4 import BeautifulSoup
from time import sleep

import database
from data_importers.parser import normalize_text, parse_date
from datetime import datetime
from database import get_or_create_address, add_or_update_contractor, get_session

# Initial setup
url = "https://services.oca.state.ma.us/hic/licenseelist.aspx"
session = requests.Session()

# Function to extract hidden fields
def extract_hidden_field(soup, field_name):
    element = soup.find("input", {"name": field_name})
    return element["value"] if element else None

# Function to scrape a single page
def scrape_page(state_code, page_number=1, viewstate=None, eventvalidation=None, viewstategenerator=None):
    response = session.get(url) if page_number == 1 else None
    soup = BeautifulSoup(response.text, "html.parser") if response else None

    # Extract hidden fields for the first request
    if page_number == 1:
        viewstate = extract_hidden_field(soup, "__VIEWSTATE")
        eventvalidation = extract_hidden_field(soup, "__EVENTVALIDATION")
        viewstategenerator = extract_hidden_field(soup, "__VIEWSTATEGENERATOR")

    # Prepare form data for postback
    post_data = {
        "__EVENTTARGET": "ctl00$pagecontentplaceholder$gvLicenseeList" if page_number > 1 else "ctl00$pagecontentplaceholder$btnSubmit",
        "__EVENTARGUMENT": f"Page${page_number}" if page_number > 1 else "",
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": viewstategenerator,
        "__EVENTVALIDATION": eventvalidation,
        "ctl00$pagecontentplaceholder$txtSearchState": state_code,
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # Send the POST request
    response = session.post(url, data=post_data, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Update hidden fields for the next request
    viewstate = extract_hidden_field(soup, "__VIEWSTATE")
    eventvalidation = extract_hidden_field(soup, "__EVENTVALIDATION")
    viewstategenerator = extract_hidden_field(soup, "__VIEWSTATEGENERATOR")

    # Extract the results
    results = soup.find_all("tr")
    page_data = []
    for row in results:
        columns = row.find_all("td")
        if columns:
            for col in columns:
                for br in col.find_all("br"):
                    br.replace_with(", ")
            row_data = [col.text.strip() for col in columns]
            # contractor list as exactly 6 fields
            if len(row_data) == 6:
                page_data.append(row_data)

    return page_data, viewstate, eventvalidation, viewstategenerator


def update_contractor_table_task():
    print(f"MA Contractors Import Task started at {datetime.now()}")

    # Step 1: Scrape multiple pages
    all_data = []
    page_number = 1
    has_more_pages = True

    # Initial state
    viewstate, eventvalidation, viewstategenerator = None, None, None

    print(1)
    while has_more_pages:
        print(f"Scraping contractors Page {page_number}")
        page_data, viewstate, eventvalidation, viewstategenerator = scrape_page(
            state_code="MA",
            page_number=page_number,
            viewstate=viewstate,
            eventvalidation=eventvalidation,
            viewstategenerator=viewstategenerator,
        )

        if not page_data:
            has_more_pages = False  # No more data means no more pages
        else:
            for contractor_data in page_data:
                company = normalize_text(contractor_data[0])

                contractor_name = normalize_text(contractor_data[1])
                # name is in format last, first
                # we need first last
                if contractor_name is not None:
                    contractor_name = " ".join(contractor_name.split(", ")[::-1])

                registration_no = normalize_text(contractor_data[2])
                address = normalize_text(contractor_data[3])
                expire_date = parse_date(contractor_data[4])
                status = normalize_text(contractor_data[5])

                if address is not None:
                    # example format: 529 main street, suite p200, charlestown, ma 02129
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

                # insert into address table
                with get_session() as session:
                    if address is not None:
                        address_id, created = get_or_create_address(
                            session=session,
                            street_number=street_number,
                            street_name=street_name,
                            city=city,
                            state=state,
                            zipcode=zip,
                            # unit_no=unit_no, #NOTE: ignore unit number. TBH contractors address is not important - not worth added complexity
                        )
                    else:
                        address_id = None

                    #print(f"Adding contractor: {contractor_name}"\
                    #        f" with registration_no: {registration_no}"\
                    #        f" and address_id: {address_id}")


                    # insert into contractor table
                    add_or_update_contractor(
                        session=session,
                        license_id=registration_no,
                        name=contractor_name,
                        address_id=address_id,
                        company=company
                    )

            session.commit()
            page_number += 1

        #sleep(0.1)  # small delay to not ddos mass.gov lol
        # not needed because processing the data itself takes a bit

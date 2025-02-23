from data_importers.parser import normalize_text

import csv
import os
import time
from io import StringIO
import requests
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from apscheduler.schedulers.background import BackgroundScheduler

# Import your models
from database import Address, Contractor, ApprovedPermit, get_session, get_or_create_address
from .parser import parse_date, parse_float, parse_int



IMPORT_URL = "https://data.boston.gov/dataset/cd1ec3ff-6ebf-4a65-af68-8329eceab740/resource/6ddcd912-32a0-43df-9908-63574f8c7e77/download/tmpfpuiefir.csv"

def download_csv(save_path="data.csv"):
    """Download a large CSV file from Boston's data portal and save it locally if it's older than 1 hour"""
    url = IMPORT_URL

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


def import_csv_to_db(csv_file_path, db_session):
    print("Importing data from Boston Permits...")
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            try:
                normalized_address = normalize_text(row['address'])
                normalized_city = normalize_text(row['city'])
                normalized_state = normalize_text(row['state'])
                normalized_zip = normalize_text(row['zip'])
                normalized_occupancy = normalize_text(row['occupancytype'])

                normalized_address = None if normalized_address == '' else normalized_address
                normalized_city = None if normalized_city == '' else normalized_city
                normalized_state = None if normalized_state == '' else normalized_state
                normalized_zip = None if normalized_zip == '' else normalized_zip
                normalized_occupancy = None if normalized_occupancy == '' else normalized_occupancy

                if normalized_address is None:
                    street_number = None
                    street_name = None
                else:
                    raw_address_parts = normalized_address.split(' ')
                    street_number = raw_address_parts[0]
                    street_name = " ".join(raw_address_parts[1:])

                # First, create or get the address
                address_id, created = get_or_create_address(
                    session=db_session,
                    street_number=street_number,
                    street_name=street_name,
                    city=normalized_city,
                    state=normalized_state,
                    zipcode=normalized_zip,
                    occupancy_type=normalized_occupancy,
                    latitude=parse_float(row['y_latitude']),
                    longitude=parse_float(row['x_longitude'])
                )

                # normalize fields
                permit_id = normalize_text(row['permitnumber'])
                permit_id = None if permit_id == '' else permit_id
                issue_date = parse_date(row['issued_date'])
                issue_date = None if issue_date == '' else issue_date
                project_amount = parse_float(row['declared_valuation'])
                project_amount = None if project_amount == '' else project_amount
                project_status = normalize_text(row['status'])
                project_status = None if project_status == '' else project_status
                contractor_name = normalize_text(row['applicant'])
                contractor_name = None if contractor_name == '' else contractor_name
                project_description = normalize_text(row['description'])
                project_description = None if project_description == '' else project_description

                try:
                    # Attempt to insert the permit
                    permit = ApprovedPermit(
                        permit_id=permit_id,
                        date_started=issue_date,
                        project_address_id=address_id,
                        project_amount=project_amount,
                        project_status=project_status,
                        owner_name=None,  # No owner name in CSV
                        contractor_name=contractor_name,
                        project_description=project_description,
                        project_comments=row['comments']
                    )

                    db_session.add(permit)
                    db_session.commit()

                except IntegrityError:
                    db_session.rollback()  # Roll back the failed insert

                    # Permit already exists, update instead
                    existing_permit = db_session.query(ApprovedPermit).filter_by(permit_id=permit_id).first()

                    if existing_permit:
                        # Update all fields except project_id and permit_id
                        existing_permit.date_started = issue_date
                        existing_permit.project_address_id = address_id
                        existing_permit.project_amount = project_amount
                        existing_permit.project_status = project_status
                        existing_permit.contractor_name = contractor_name
                        existing_permit.project_description = project_description
                        existing_permit.project_comments = row['comments']

                        db_session.commit()

            except IntegrityError as e:
                print(f"Error processing row: {permit_id}")
                print(f"Error details: {str(e)}")
                db_session.rollback()
            except Exception as e:
                print(f"Unexpected error processing row: {permit_id}")
                print(f"Error details: {str(e)}")
                db_session.rollback()

def update_database_task():
    """Scheduled task to update the database and record the update timestamp."""
    print(f"Boston Permit Import Task started at {datetime.now()}")

    try:
        with get_session() as session:
            # Step 1: Download the CSV
            csv_file_path = download_csv()

            if csv_file_path:
                # Step 2: Import data into the database
                import_csv_to_db(csv_file_path, session)

                # Step 3: Update the state table
                state = session.query(State).first()  # Assuming there's only one row
                if not state:
                    state = State()  # Create a new state row if none exists
                    session.add(state)

                state.boston_permits_update_ts = datetime.utcnow()
                session.commit()

                print(f"Boston Permit Import Task completed successfully at {datetime.now()}")

    except Exception as e:
        print(f"Error during scheduled task: {e}")
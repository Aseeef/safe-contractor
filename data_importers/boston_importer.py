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

# Import your models
from database import Address, Contractor, ApprovedPermit, get_session
from parser import parse_date, parse_float, parse_int



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
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            try:
                normalized_address = normalize_text(row['address'])
                normalized_city = normalize_text(row['city'])
                normalized_state = normalize_text(row['state'])
                normalized_zip = normalize_text(row['zip'])

                normalized_address = None if normalized_address == '' else normalized_address
                normalized_city = None if normalized_city == '' else normalized_city
                normalized_state = None if normalized_state == '' else normalized_state
                normalized_zip = None if normalized_zip == '' else normalized_zip

                if normalized_address is None:
                    street_number = None
                    street_name = None
                else:
                    raw_address_parts = normalized_address.split(' ')
                    street_number = raw_address_parts[0]
                    street_name = " ".join(raw_address_parts[1:])

                # First, create or get the address
                address = Address(
                    street_number=street_number,
                    street_name=street_name,
                    city=normalize_text(row['city']),
                    state=normalize_text(row['state']),
                    zipcode=normalize_text(row['zip']),
                    occupancy_type=normalize_text(row['occupancytype']),
                    latitude=parse_float(row['y_latitude']),
                    longitude=parse_float(row['x_longitude'])
                )

                db_session.add(address)
                db_session.flush()  # This will assign an ID to the address

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


                # Create the permit record
                permit = ApprovedPermit(
                    permit_id=permit_id,
                    date_started=issue_date,
                    project_address_id=address.id,
                    project_amount=project_amount,
                    project_status=project_status,
                    owner_name=None,  # CSV doesn't have owner name
                    contractor_name=contractor_name,
                    project_description=project_description,
                    project_comments=row['comments']
                )

                db_session.add(permit)

                # Commit in batches (optional)
                db_session.commit()

            except IntegrityError as e:
                print(f"Error processing row: {row['permitnumber']}")
                print(f"Error details: {str(e)}")
                db_session.rollback()
            except Exception as e:
                print(f"Unexpected error processing row: {row['permitnumber']}")
                print(f"Error details: {str(e)}")
                db_session.rollback()

def update_database_task():
    """Scheduled task to update the database and record the update timestamp."""
    print(f"Task started at {datetime.now()}")

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

                print(f"Task completed successfully at {datetime.now()}")

    except Exception as e:
        print(f"Error during scheduled task: {e}")


def start_scheduled_updates():
    """Starts the scheduler with a 5-hour interval."""
    scheduler.add_job(update_database_task, 'interval', hours=5)
    scheduler.start()
    print("Scheduler started! Task will run every 5 hours.")

if __name__ == '__main__':
    main()
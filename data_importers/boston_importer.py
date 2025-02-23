from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from fastapi import FastAPI
from datetime import datetime
import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import your helper functions and models
from data_importers.utils import download_csv, normalize_text, parse_date, parse_float
from database import Address, Contractor, ApprovedPermit, State, get_session, add_or_update_address

# ---------------------------
# Parallel Processing Helpers
# ---------------------------
def process_csv_row(row, line_number):
    """
    Process a single CSV row.
    Each invocation creates its own DB session (sessions aren't thread-safe).
    """
    session = get_session()
    try:
        # Normalize address fields
        normalized_address = normalize_text(row['address'])
        normalized_city = normalize_text(row['city'])
        normalized_state = normalize_text(row['state'])
        normalized_zip = normalize_text(row['zip'])
        normalized_occupancy = normalize_text(row['occupancytype'])

        normalized_address = normalized_address if normalized_address.strip() else None
        normalized_city = normalized_city if normalized_city.strip() else None
        normalized_state = normalized_state if normalized_state.strip() else None
        normalized_zip = normalized_zip if normalized_zip.strip() else None
        normalized_occupancy = normalized_occupancy if normalized_occupancy.strip() else None

        if normalized_address:
            raw_address_parts = normalized_address.split(' ')
            street_number = raw_address_parts[0]
            street_name = " ".join(raw_address_parts[1:])
        else:
            street_number = None
            street_name = None

        # Add or update address (assumes add_or_update_address returns (address_id, created))
        address_id, created = add_or_update_address(
            session=session,
            street_number=street_number,
            street_name=street_name,
            city=normalized_city,
            state=normalized_state,
            zipcode=normalized_zip,
            occupancy_type=normalized_occupancy,
            latitude=parse_float(row['y_latitude']),
            longitude=parse_float(row['x_longitude'])
        )

        # Normalize permit fields
        permit_id = normalize_text(row['permitnumber'])
        permit_id = permit_id if permit_id.strip() else None
        issue_date = parse_date(row['issued_date'])
        issue_date = issue_date if issue_date.strip() else None
        project_amount = parse_float(row['declared_valuation'])
        project_amount = project_amount if project_amount is not None else None
        project_status = normalize_text(row['status'])
        project_status = project_status if project_status.strip() else None
        contractor_name = normalize_text(row['applicant'])
        contractor_name = contractor_name if contractor_name.strip() else None
        project_description = normalize_text(row['description'])
        project_description = project_description if project_description.strip() else None

        try:
            # Try inserting the new permit
            permit = ApprovedPermit(
                permit_id=permit_id,
                date_started=issue_date,
                project_address_id=address_id,
                project_amount=project_amount,
                project_status=project_status,
                owner_name=None,  # No owner name provided
                contractor_name=contractor_name,
                project_description=project_description,
                project_comments=row['comments'][:1000]  # Trim if needed
            )
            session.add(permit)
            session.commit()
            print(f"Added permit: {permit_id} on line {line_number}")
        except Exception as e:
            session.rollback()
            # If permit exists, update instead
            existing_permit = session.query(ApprovedPermit).filter_by(permit_id=permit_id).first()
            if existing_permit:
                existing_permit.date_started = issue_date
                existing_permit.project_address_id = address_id
                existing_permit.project_amount = project_amount
                existing_permit.project_status = project_status
                existing_permit.contractor_name = contractor_name
                existing_permit.project_description = project_description
                existing_permit.project_comments = row['comments']
                session.commit()
                print(f"Updated permit: {permit_id} on line {line_number}")
            else:
                print(f"Error processing row {line_number} for permit {permit_id}: {e}")
    except Exception as exc:
        print(f"Unexpected error on line {line_number} for permit {permit_id}: {exc}")
        session.rollback()
    finally:
        session.close()


def import_csv_to_db(csv_file_path):
    """
    Reads the CSV and processes each row in parallel using a thread pool.
    """
    print("Importing data from Boston Permits...")
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        rows = list(csv_reader)

    # Using 10 worker threads; adjust max_workers as needed.
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_csv_row, row, idx+2): idx for idx, row in enumerate(rows)}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Row processing generated an exception: {e}")


# ---------------------------
# Scheduled Task
# ---------------------------
def update_permits_table_task():
    """Scheduled task to update the permits table and record the update timestamp."""
    print(f"Boston Permit Import Task started at {datetime.now()}")
    # Download CSV (download_csv should accept a URL and a save path)
    csv_file_path = download_csv("https://data.boston.gov/dataset/cd1ec3ff-6ebf-4a65-af68-8329eceab740/resource/6ddcd912-32a0-43df-9908-63574f8c7e77/download/tmpfpuiefir.csv", "permits.csv")
    if csv_file_path:
        # Process CSV rows concurrently
        import_csv_to_db(csv_file_path)
        # Update state table timestamp
        with get_session() as session:
            state = session.query(State).first()
            if not state:
                state = State()
                session.add(state)
            state.boston_permits_update_ts = datetime.utcnow()
            session.commit()
        print(f"Boston Permit Import Task completed successfully at {datetime.now()}")
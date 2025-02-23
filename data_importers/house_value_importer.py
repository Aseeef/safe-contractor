from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd
import csv
from typing import Dict, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'vps0.aseef.dev',
    'port': 3306,
    'user': 'civic_hacks',
    'password': '6ycrmb*L99%gQM',
    'database': '2025_civic_hackathon'
}

# Required fields that cannot be NULL
REQUIRED_FIELDS = {'city'}

def create_db_engine():
    """Create and return a database engine."""
    connection_string = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    return create_engine(connection_string, pool_size=5, max_overflow=10)

def parse_float_value(value) -> Optional[float]:
    """Parse string to float, handling comma-separated numbers."""
    if pd.isna(value):
        return None
    try:
        # Remove commas and convert to float
        return float(str(value).replace(',', ''))
    except (ValueError, TypeError):
        return None

def process_address_row(row: Dict) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Process a row from the CSV and return formatted data matching the database schema.
    Returns (data_dict, error_message) tuple. If error_message is not None, data_dict will be None.
    """
    try:
        # Extract city first as it's required
        city = str(row.get('CITY', '')).strip().lower() if pd.notna(row.get('CITY')) else None
        if not city:
            return None, "Missing required field: city"

        # Parse the house value first to catch any parsing errors
        house_value = parse_float_value(row.get('TOTAL_VALUE'))
        
        data = {
            'street_number': str(row.get('ST_NUM', '')).strip() if pd.notna(row.get('ST_NUM')) else None,
            'street_name': str(row.get('ST_NAME', '')).strip().lower() if pd.notna(row.get('ST_NAME')) else None,
            'city': city,
            'state': 'ma',  # Default to MA as per sample
            'zipcode': str(row.get('ZIPCODE', '')).strip() if pd.notna(row.get('ZIPCODE')) else None,
            'longitude': parse_float_value(row.get('LONGITUDE')),
            'latitude': parse_float_value(row.get('LATITUDE')),
            'occupancy_type': str(row.get('OCCUPANCY_TYPE', '')).strip().lower() if pd.notna(row.get('OCCUPANCY_TYPE')) else None,
            'address_owner': None,  # Set to NULL as per sample
            'house_value': house_value
        }
        return data, None

    except Exception as e:
        return None, f"Error processing row values: {str(e)}"

def update_or_create_address(session, data: Dict) -> Tuple[bool, Optional[str]]:
    """
    Update existing address or create new one.
    Returns (success, error_message) tuple.
    """
    try:
        # Check if address exists based on street name and number
        query = text("""
            SELECT id 
            FROM addresses 
            WHERE street_name = :street_name 
            AND street_number = :street_number
            AND city = :city
            LIMIT 1
        """)
        
        result = session.execute(query, data)
        existing_address = result.fetchone()

        if existing_address:
            # Update only house_value for existing address
            update_query = text("""
                UPDATE addresses 
                SET house_value = :house_value
                WHERE id = :id
            """)
            session.execute(update_query, {'id': existing_address[0], 'house_value': data['house_value']})
            return True, None
        else:
            # Insert new record with all fields
            insert_query = text("""
                INSERT INTO addresses (
                    street_number, street_name, city, state, zipcode,
                    longitude, latitude, occupancy_type, address_owner, house_value
                ) VALUES (
                    :street_number, :street_name, :city, :state, :zipcode,
                    :longitude, :latitude, :occupancy_type, :address_owner, :house_value
                )
            """)
            session.execute(insert_query, data)
            return True, None

    except Exception as e:
        return False, str(e)

def import_csv_to_database(csv_path: str, batch_size: int = 1000, start_from: int = 0) -> None:
    """Import CSV data to database with batch processing."""
    engine = create_db_engine()
    Session = sessionmaker(bind=engine)
    
    stats = {
        'total_processed': 0,
        'successful': 0,
        'skipped': 0,
        'errors': 0
    }
    
    try:
        with open(csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            batch = []
            
            # Skip rows if starting from middle
            for _ in range(start_from):
                next(reader, None)
            
            for row_num, row in enumerate(reader, start_from + 1):
                try:
                    # Process the row
                    data, error = process_address_row(row)
                    stats['total_processed'] += 1
                    
                    if error:
                        stats['skipped'] += 1
                        logger.warning(f"Skipping row {row_num}: {error}")
                        continue
                    
                    batch.append(data)
                    
                    # Process in batches
                    if len(batch) >= batch_size:
                        session = Session()
                        try:
                            for data in batch:
                                success, error = update_or_create_address(session, data)
                                if success:
                                    stats['successful'] += 1
                                else:
                                    stats['errors'] += 1
                                    logger.error(f"Error processing address: {error}")
                            session.commit()
                            logger.info(f"Processed batch. Progress: {stats['total_processed']} rows")
                        except Exception as e:
                            session.rollback()
                            logger.error(f"Error processing batch at row {row_num}: {str(e)}")
                            raise
                        finally:
                            session.close()
                        batch = []
                except Exception as e:
                    logger.error(f"Error processing row {row_num}: {str(e)}")
                    raise
            
            # Process remaining records
            if batch:
                session = Session()
                try:
                    for data in batch:
                        success, error = update_or_create_address(session, data)
                        if success:
                            stats['successful'] += 1
                        else:
                            stats['errors'] += 1
                            logger.error(f"Error processing address: {error}")
                    session.commit()
                except Exception as e:
                    session.rollback()
                    raise
                finally:
                    session.close()
                
        # Log final statistics
        logger.info("Import completed. Statistics:")
        logger.info(f"Total rows processed: {stats['total_processed']}")
        logger.info(f"Successfully processed: {stats['successful']}")
        logger.info(f"Skipped (missing required fields): {stats['skipped']}")
        logger.info(f"Errors during processing: {stats['errors']}")
                
    except Exception as e:
        logger.error(f"Fatal error during import: {str(e)}")
        raise

if __name__ == "__main__":
    csv_path = "../housing_data.csv"  # Replace with your CSV file path
    try:
        # Start from row 70000 (adjust this number based on what was actually processed)
        import_csv_to_database(csv_path, batch_size=500, start_from=50000)
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Contractor, Address, ApprovedPermit
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import database
import os
import requests
from bs4 import BeautifulSoup
from data_importers import update_permits_table_task, update_contractor_table_task

def get_bool_env_var(key, default=False):
    return os.environ.get(key, str(default)).lower() in ('true', '1', 'yes')

# Load environment variables from .env
load_dotenv()

# Read database credentials from environment variables
SQL_HOST = os.getenv("SQL_HOST")
SQL_PORT = os.getenv("SQL_PORT", 3306)  # Default to 3306 if not specified
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_ALCHEMY_DEBUG = get_bool_env_var("SQL_ALCHEMY_DEBUG", False)

# Construct the MariaDB connection URL
DATABASE_URL = (
    f"mysql+pymysql://{SQL_USER}:{SQL_PASSWORD}@{SQL_HOST}:{SQL_PORT}/{SQL_DATABASE}"
)

# Get DB Engine
engine = create_engine(DATABASE_URL, echo=SQL_ALCHEMY_DEBUG)

# Create all tables based on our models
database.init(engine)

# Create a session factory
SessionLocal = sessionmaker(bind=engine)

def get_session():
    return SessionLocal()


# Initialize Scheduler
scheduler = AsyncIOScheduler()


# Lifespan context for handling startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    scheduler.add_job(update_contractor_table_task, trigger="interval", hours=5, next_run_time=datetime.now())
    scheduler.add_job(update_permits_table_task, trigger="interval", hours=5, next_run_time=datetime.now())
    scheduler.start()
    print("Scheduler started with FastAPI lifespan event.")

    yield  # Allows FastAPI to continue running while the scheduler is active

    # Shutdown actions
    scheduler.shutdown()
    print("Scheduler shut down gracefully.")

# Get FastAPI
app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def root():
    return 200

@app.get("/search-contractor")
async def search_contractor(contractor_name: str = None, license_id: str = None):
    """
    Search for a contractor and their associated data using either name or license ID.
    Returns contractor details, previous works, and address information.
    """
    with get_session() as session:
        # Build the query based on provided parameters
        query = session.query(Contractor)
        if license_id:
            contractor = query.filter_by(license_id=license_id).first()
        elif contractor_name:
            contractor = query.filter_by(name=contractor_name).first()
        else:
            raise HTTPException(status_code=400, detail="Either contractor_name or license_id must be provided")

        if not contractor:
            raise HTTPException(status_code=404, detail="Contractor not found")

        # Retrieve previous works from ApprovedPermit table
        previous_works = session.query(ApprovedPermit).filter_by(contractor_name=contractor.name).all()

        # Retrieve address details from Address table
        address_details = session.query(Address).filter_by(id=contractor.address_id).first()

        # Prepare the response
        response = {
            "contractor": {
                "license_id": contractor.license_id,
                "name": contractor.name,
                "address_id": contractor.address_id
            },
            "previous_works": [
                {
                    "project_id": work.project_id,
                    "permit_id": work.permit_id,
                    "project_amount": work.project_amount,
                    "project_status": work.project_status,
                    "owner_name": work.owner_name,
                    "project_description": work.project_description
                } for work in previous_works
            ],
            "address_details": {
                "street_number": address_details.street_number,
                "street_name": address_details.street_name,
                "city": address_details.city,
                "state": address_details.state,
                "zipcode": address_details.zipcode,
                "longitude": address_details.longitude,
                "latitude": address_details.latitude,
                "occupancy_type": address_details.occupancy_type,
                "address_owner": address_details.address_owner
            } if address_details else None
        }
    
    return response

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
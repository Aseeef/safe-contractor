from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import database
import os
from database import Contractor, Address, ApprovedPermit
import requests
from bs4 import BeautifulSoup

# Load environment variables from .env
load_dotenv()

# Read database credentials from environment variables
SQL_HOST = os.getenv("SQL_HOST")
SQL_PORT = os.getenv("SQL_PORT", 3306)  # Default to 3306 if not specified
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
SQL_DATABASE = os.getenv("SQL_DATABASE")

# Construct the MariaDB connection URL
DATABASE_URL = (
    f"mysql+pymysql://{SQL_USER}:{SQL_PASSWORD}@{SQL_HOST}:{SQL_PORT}/{SQL_DATABASE}"
)

# Get FastAPI
app = FastAPI()
# Get DB Engine
engine = create_engine(DATABASE_URL, echo=True)

# Create all tables based on our models
database.init(engine)

# Create a session factory
SessionLocal = sessionmaker(bind=engine)

def get_session():
    return SessionLocal()

@app.get("/health")
async def root():
    return 200

@app.get("/search-contractor")
async def search_contractor(contractor_name: str = None, radius: int = None, license_id: str = None):
    scraped_data = scrape_contractor_data(contractor_name, radius, license_id)
    
    with get_session() as session:
        contractor = session.query(Contractor).filter_by(license_id=scraped_data["license_id"]).first()
        if not contractor:
            contractor = Contractor(
                license_id=scraped_data["license_id"],
                name=scraped_data["name"],
                address_id=scraped_data["address_id"]
            )
            session.add(contractor)
            session.commit()

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

# if __name__ == '__main__':
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)


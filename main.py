from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Contractor, Address, ApprovedPermit, Base
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# Create the database engine - this will create a new SQLite database file
engine = create_engine('sqlite:///database.db', echo=True)  # echo=True shows SQL commands

# Create all tables based on our models
Base.metadata.create_all(engine)

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


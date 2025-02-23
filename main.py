from dotenv import load_dotenv
# Load environment variables from .env
load_dotenv()

from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Contractor, Address, ApprovedPermit
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from contextlib import asynccontextmanager
import database
import api
import os
import requests
from bs4 import BeautifulSoup
from data_importers import update_permits_table_task, update_contractor_table_task

def get_bool_env_var(key, default=False):
    return os.environ.get(key, str(default)).lower() in ('true', '1', 'yes')

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
    scheduler.add_job(update_contractor_table_task, trigger="interval", hours=12)
    scheduler.add_job(update_permits_table_task, trigger="interval", hours=12)
    scheduler.start()
    print("Scheduler started with FastAPI lifespan event.")

    yield  # Allows FastAPI to continue running while the scheduler is active

    # Shutdown actions
    scheduler.shutdown()
    print("Scheduler shut down gracefully.")

# Get FastAPI
app = FastAPI(lifespan=lifespan)
app.include_router(api.router, prefix="/api")

@app.get("/health")
async def health():
    return 200

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
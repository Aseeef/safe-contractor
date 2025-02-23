import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, Double, DateTime, UniqueConstraint, Engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

Base = declarative_base()

# Define the valid project statuses
PROJECT_STATUSES = ['cancelled', 'ongoing', 'completed']


class Address(Base):
    __tablename__ = 'addresses'

    id = Column(Integer, primary_key=True)
    street_number = Column(String(255))
    street_name = Column(String(1024))
    city = Column(String(1024), nullable=False)
    state = Column(String(64), nullable=False)
    zipcode = Column(String(64))
    longitude = Column(Double)
    latitude = Column(Double)
    occupancy_type = Column(String(255))
    address_owner = Column(String(1024))

    # Relationships
    contractors = relationship("Contractor", back_populates="address")
    permits = relationship("ApprovedPermit", back_populates="project_address")

    __table_args__ = (
        UniqueConstraint(
            'street_number', 'street_name', 'city', 'state', 'zipcode',
            name='unique_address'
        ),
    )


class Contractor(Base):
    __tablename__ = 'contractors'

    id = Column(Integer, primary_key=True)
    license_id = Column(String(255), unique=True)
    name = Column(String(1024), nullable=False)
    address_id = Column(Integer, ForeignKey('addresses.id'))

    # Relationship
    address = relationship("Address", back_populates="contractors")


class ApprovedPermit(Base):
    __tablename__ = 'approved_permits'

    project_id = Column(Integer, primary_key=True)
    date_started = Column(String(1024))
    permit_id = Column(String(1024), unique=True)
    project_address_id = Column(Integer, ForeignKey('addresses.id'))
    project_amount = Column(Double)
    project_status = Column(String(1024))  # Will store 'cancelled', 'ongoing', or 'completed'
    owner_name = Column(String(1024))
    contractor_name = Column(String(1024))
    project_description = Column(String(1024))
    project_comments = Column(String(1024))

    # Relationship
    project_address = relationship("Address", back_populates="permits")


class State(Base):
    __tablename__ = 'state'

    id = Column(Integer, primary_key=True, default=1)  # Singleton ID always set to 1
    boston_permits_update_ts = Column(DateTime, default=datetime.datetime.min, nullable=False)
    boston_property_update_ts = Column(DateTime, default=datetime.datetime.min, nullable=False)
    mass_contractor_update_ts = Column(DateTime, default=datetime.datetime.min, nullable=False)

    # Enforce a single row constraint
    __table_args__ = {'sqlite_autoincrement': True}

engine = None
session_creator = None
# Create all tables based on our models
def init(engine_ref: Engine):
    global engine
    global session_creator
    engine = engine_ref
    session_creator = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    initialize_or_get_state()

def get_session():
    return session_creator()

def initialize_or_get_state() -> State:
    """Ensure a single State record exists and return it."""
    with get_session() as session:
        state = session.query(State).filter_by(id=1).first()  # Ensure only ID 1 exists
        if not state:
            # Insert the single row if it doesn't exist
            state = State(
                id=1,
                boston_permits_update_ts=datetime.datetime.min,
                boston_property_update_ts=datetime.datetime.min,
                mass_contractor_update_ts=datetime.datetime.min
            )
            session.add(state)
            session.commit()
            print("Initialized the State table with a single entry.")
        return state

    return None

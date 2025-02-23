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
    #unit_number = Column(String(255)) not worth added complexity especially because permits db doesnt care about this
    unit_number = None
    city = Column(String(1024), nullable=False)
    state = Column(String(64), nullable=False)
    zipcode = Column(String(64))
    longitude = Column(Double)
    latitude = Column(Double)
    occupancy_type = Column(String(255))
    address_owner = Column(String(1024))
    house_value = Column(Double)

    # Relationshipsf
    contractors = relationship("Contractor", back_populates="address")
    permits = relationship("ApprovedPermit", back_populates="project_address")

    # Updated Unique Constraint to include unit_number
    __table_args__ = (
        UniqueConstraint(
            'street_number', 'street_name', 'city', 'state', 'zipcode', # 'unit_number',
            name='unique_address'
        ),
    )

    @property
    def full_address(self):
        if self.unit_number:
            return f"{self.street_number} {self.street_name}, {self.unit_number}, {self.city}, {self.state} {self.zipcode}"
        else:
            return f"{self.street_number} {self.street_name}, {self.city}, {self.state} {self.zipcode}"

class Contractor(Base):
    __tablename__ = 'contractors'

    id = Column(Integer, primary_key=True)
    license_id = Column(String(255), unique=True)
    company = Column(String(1024))
    name = Column(String(1024), nullable=False)
    address_id = Column(Integer, ForeignKey('addresses.id'))
    license_status = Column(String(1024))
    expire_date = Column(DateTime)

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

def add_or_update_address(session, street_number, street_name, city, state, zipcode, **kwargs):
    # Step 1: Check if the address already exists
    existing_address = session.query(Address).filter_by(
        street_number=street_number,
        street_name=street_name,
        city=city,
        state=state,
        zipcode=zipcode
    ).first()

    if existing_address:
        # If the address exists, return the existing ID
        return existing_address.id, False  # False -> Not newly created

    # Step 2: Create and flush a new address
    new_address = Address(
        street_number=street_number,
        street_name=street_name,
        city=city,
        state=state,
        zipcode=zipcode,
        **kwargs
    )
    session.add(new_address)
    session.flush()  # Assigns an ID without committing yet
    session.commit()

    return new_address.id, True  # True -> Newly created

def add_or_update_contractor(session, license_id, name, address_id, company=None, license_status=None, expire_date=None):
    if license_id is None or name is None:
        return None

    # Step 1: Check if the contractor already exists
    existing_contractor = session.query(Contractor).filter_by(license_id=license_id).first()

    if existing_contractor:
        # If the contractor exists, update the name and address ID
        existing_contractor.name = name
        existing_contractor.address_id = address_id
        existing_contractor.company = company
        existing_contractor.license_status = license_status
        existing_contractor.expire_date = expire_date
        session.commit()
        return existing_contractor.id, False  # False -> Not newly created

    # Step 2: Create and flush a new contractor
    new_contractor = Contractor(
        license_id=license_id,
        name=name,
        address_id=address_id,
        company=company,
        license_status=license_status,
        expire_date=expire_date
    )
    session.add(new_contractor)
    session.flush()  # Assigns an ID without committing yet
    session.commit()

    print("adding", new_contractor.id)

    return new_contractor.id, True  # True -> Newly created

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

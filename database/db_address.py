from sqlalchemy import Column, Integer, String, ForeignKey, Double, UniqueConstraint
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
    street_number = Column(String)
    street_name = Column(String)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zipcode = Column(String)
    longitude = Column(Double)
    latitude = Column(Double)
    occupancy_type = Column(String)
    address_owner = Column(String)

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
    license_id = Column(String, unique=True)
    name = Column(String, nullable=False)
    address_id = Column(Integer, ForeignKey('addresses.id'))

    # Relationship
    address = relationship("Address", back_populates="contractors")


class ApprovedPermit(Base):
    __tablename__ = 'approved_permits'

    project_id = Column(Integer, primary_key=True)
    date_started = Column(String)
    permit_id = Column(String, unique=True)
    project_address_id = Column(Integer, ForeignKey('addresses.id'))
    project_amount = Column(Double)
    project_status = Column(String)  # Will store 'cancelled', 'ongoing', or 'completed'
    owner_name = Column(String)
    contractor_name = Column(String)
    project_description = Column(String)
    project_comments = Column(String)

    # Relationship
    project_address = relationship("Address", back_populates="permits")

# Create the database engine - this will create a new SQLite database file
engine = create_engine('sqlite:///database.db', echo=True)  # echo=True shows SQL commands

# Create all tables based on our models
Base.metadata.create_all(engine)

# Create a session factory
SessionLocal = sessionmaker(bind=engine)

def get_session():
    return SessionLocal()

if __name__ == '__main__':
    with get_session() as session:
        session.add(Contractor(
            license_id="CTR123456",
            name="Acme Construction",
            address_id=None
        ))
        session.commit()
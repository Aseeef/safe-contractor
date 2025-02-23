from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Copy your DB_CONFIG from the original code
DB_CONFIG = {
    'host': 'vps0.aseef.dev',
    'port': 3306,
    'user': 'civic_hacks',
    'password': '6ycrmb*L99%gQM',
    'database': '2025_civic_hackathon'
}

def clear_transaction():
    connection_string = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    engine = create_engine(connection_string)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        session.rollback()
        print("Transaction rolled back successfully")
    finally:
        session.close()
        print("Session closed")

if __name__ == "__main__":
    clear_transaction()
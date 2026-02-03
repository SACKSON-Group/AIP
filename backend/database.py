from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Use aip_platform.db as the default database
db_path = os.path.join(os.path.dirname(__file__), 'aip_platform.db')
default_db_url = f"sqlite:///{db_path}"
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL", default_db_url)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
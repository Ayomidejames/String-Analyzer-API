# models.py
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()
SessionLocal = None  # will be set in init_db()

class StoredString(Base):
    __tablename__ = "strings"
    id = Column(String, primary_key=True, index=True)   # sha256 hex
    value = Column(Text, nullable=False, unique=True)
    properties = Column(Text, nullable=False)  # JSON string of properties
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

def init_db(database_url: str = "sqlite:///strings.db"):
    """
    Initialize DB. Call once on app startup.
    """
    global SessionLocal
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

def get_session():
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return SessionLocal()

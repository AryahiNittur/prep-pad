from sqlmodel import SQLModel, create_engine, Session
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - you can change this to your preferred database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./prep_pad.db")

# Create engine
engine = create_engine(DATABASE_URL, echo=True)

def create_db():
    """Create all tables"""
    SQLModel.metadata.create_all(engine)

def get_db():
    """Dependency to get database session"""
    with Session(engine) as session:
        yield session
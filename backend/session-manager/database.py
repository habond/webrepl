from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, text
from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as DBSession
import json
from datetime import datetime
import os
import time

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/sessions.db")

# Create engine (with fallback retry logic for robustness)
def create_db_engine():
    retries = 3  # Reduced retries since SQLite is more reliable
    while retries > 0:
        try:
            # Configure engine based on database type
            if DATABASE_URL.startswith('sqlite'):
                engine = create_engine(
                    DATABASE_URL,
                    echo=False,
                    # SQLite specific settings
                    connect_args={"check_same_thread": False}
                )
            else:
                # For other databases (if needed)
                engine = create_engine(
                    DATABASE_URL,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    echo=False
                )
            
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return engine
        except Exception as e:
            print(f"Database connection failed, retrying... ({retries} attempts left)")
            print(f"Error: {e}")
            retries -= 1
            if retries > 0:
                time.sleep(1)  # Shorter sleep for SQLite
    raise Exception("Failed to connect to database after multiple attempts")

# Create the engine
engine = create_db_engine()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base model
Base = declarative_base()

# Custom JSON type that handles datetime serialization
class JSONEncodedDict(TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""
    impl = TEXT
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            # Custom serialization that handles datetime objects
            def json_serial(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")
            return json.dumps(value, default=json_serial)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value

# Session model
class SessionModel(Base):
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    language = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    execution_count = Column(Integer, default=0, nullable=False)
    history = Column(JSONEncodedDict, default=list, nullable=False)
    environment_data = Column(Text, nullable=True)  # Base64 encoded serialized environment
    environment_language = Column(String(50), nullable=True)
    environment_updated = Column(DateTime, nullable=True)

# Create tables
def init_db():
    """Initialize the database, creating tables if they don't exist"""
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
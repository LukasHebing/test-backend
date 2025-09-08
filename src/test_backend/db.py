import os
from datetime import datetime, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve database credentials from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Construct the database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create a SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Example function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    email_verified = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    email_verifications = relationship("EmailVerification", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")

class UserSession(Base):
    __tablename__ = 'user_sessions'
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    expires_at = Column(DateTime, nullable=False, default=lambda: func.current_timestamp() + timedelta(hours=24))
    revoked_at = Column(DateTime, nullable=True)
    user_agent = Column(String(255), nullable=True)
    ip = Column(String(45), nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="sessions")

class EmailVerification(Base):
    __tablename__ = 'email_verifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    
    # Relationship
    user = relationship("User", back_populates="email_verifications")

class PasswordReset(Base):
    __tablename__ = 'password_resets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    
    # Relationship
    user = relationship("User", back_populates="password_resets")


def execute_raw_query(query: str):
    """Execute a raw SQL query and return the results."""
    with engine.connect() as connection:
        result = connection.execute(text(query))
        if result.returns_rows:
            return result.fetchall()
        return None
    
def create_tables():
    """create the tables from the models. delete all data if tables exist."""
   # Drop all tables
    Base.metadata.drop_all(bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    # Test the database connection
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * from information_schema.tables;"))
            print("Database connection successful:", result.fetchone())
    except Exception as e:
        print("Database connection failed:", e)
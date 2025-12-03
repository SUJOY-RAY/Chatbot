from datetime import datetime
from sqlalchemy import JSON, DateTime, Float, ForeignKey, create_engine, Column, Integer, String, func
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

# Database URL (SQLite in this case)
DATABASE_URL = "sqlite:///./users.db"

# Create SQLAlchemy engine
# `check_same_thread=False` is required for SQLite to allow access from multiple threads
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create a session factory for interacting with the database
# autocommit=False -> we manually control commits
# autoflush=False -> avoid automatic flushing of changes
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


class User(Base):
    """
    SQLAlchemy model for the 'users' table.
    
    Fields:
        - id: Primary key
        - username: Unique username
        - session_token: Unique token for user sessions
        - ip_address: Optional IP address
        - created_at: Timestamp of creation (defaults to current time)
        - queries: Relationship to Query objects
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)  # Primary key
    username = Column(String(150), unique=True, nullable=False, index=True)  # Unique username
    session_token = Column(String(150), unique=True, index=True)  # Unique session token
    ip_address = Column(String(50))  # Optional IP address of user
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Timestamp

    # One-to-many relationship: a user can have multiple queries
    # 'cascade="all, delete-orphan"' ensures queries are deleted if user is deleted
    queries = relationship("Query", back_populates="user", cascade="all, delete-orphan")


class Query(Base):
    """
    SQLAlchemy model for the 'queries' table.
    
    Fields:
        - id: Primary key
        - text: User query text
        - sentiment: Sentiment label
        - score: Compound sentiment score (float)
        - details: JSON field containing detailed sentiment analysis
        - time: Timestamp of query (defaults to current time)
        - user_id: Foreign key to User table
        - user: Relationship back to User
        - ip_address: IP address of user when query was made
        - latitude, longitude, city, region, country: Optional geolocation info
        - confidence: Confidence of sentiment analysis (optional)
    """
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(500), nullable=False)  # Query text
    sentiment = Column(String(50), nullable=False)  # Sentiment label
    score = Column(Float, nullable=False)  # Compound sentiment score
    details = Column(JSON)  # JSON details of sentiment

    # Timestamp when query was created
    time = Column(DateTime(timezone=True), server_default=func.now())

    # Relation to User table
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="queries")  # Back-reference

    # Metadata
    ip_address = Column(String(50))  # IP address of user

    # Optional location info derived from IP
    latitude = Column(Float)
    longitude = Column(Float)
    city = Column(String(120))
    region = Column(String(120))
    country = Column(String(120))
    confidence = Column(Float, nullable=True)  # Confidence of sentiment score


def init_db():
    """
    Initialize the database.
    Creates all tables defined in the Base metadata.
    """
    Base.metadata.create_all(bind=engine)

from datetime import datetime
from sqlalchemy import JSON, DateTime, Float, ForeignKey, create_engine, Column, Integer, String, func
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./users.db"

# Database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # required for SQLite
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarative class
Base = declarative_base()


# -------------------------------
# User Model
# -------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=False, index=True)
    session_token = Column(String(150), unique=True, index=True)
    ip_address = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to queries
    queries = relationship("Query", back_populates="user", cascade="all, delete-orphan")


# -------------------------------
# Query Model
# -------------------------------
class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(500), nullable=False)
    sentiment = Column(String(50), nullable=False)
    score = Column(Float, nullable=False)
    details = Column(JSON)

    time = Column(DateTime(timezone=True), server_default=func.now())

    # Relation to user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="queries")

    # Metadata
    ip_address = Column(String(50))

    # Location data
    latitude = Column(Float)
    longitude = Column(Float)
    city = Column(String(120))
    region = Column(String(120))
    country = Column(String(120))
    confidence = Column(Float, nullable=True)  # <-- ADD THIS



# -------------------------------
# Initialize DB
# -------------------------------
def init_db():
    Base.metadata.create_all(bind=engine)

import datetime
from sqlalchemy import DateTime, ForeignKey, create_engine, Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./users.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    session_token = Column(String, unique=True, index=True)
    queries = relationship("Query", back_populates="user")
    ip_address = Column(String)  
    time = Column(DateTime)

class Query(Base):
    __tablename__ = "queries"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    sentiment = Column(String)
    score = Column(String)
    time = Column(DateTime, default=datetime.UTC)
    user_id = Column(Integer, ForeignKey("users.id"))
    ip_address = Column(String)  
    user = relationship("User", back_populates="queries")

def init_db():
    Base.metadata.create_all(bind=engine)

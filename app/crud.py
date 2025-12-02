from sqlalchemy.orm import Session
from database import User, Query
import uuid
from datetime import datetime, timezone
from ipconverter import ip_to_location

def create_user(db: Session, username: str, ip_address: str):
    token = str(uuid.uuid4())
    
    user = User(
        username=username,
        session_token=token,
        ip_address=ip_address,
        time=datetime.now()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_token(db: Session, token: str):
    return db.query(User).filter(User.session_token == token).first()

def save_query(db, user, text, sentiment, score, ip_address):
    loc = ip_to_location(ip_address)
    db_query = Query(
        text=text,
        sentiment=sentiment,
        score=str(score),
        time=datetime.now(timezone.utc),
        
        user=user,
        ip_address=ip_address,
        
        latitude=loc["lat"] if loc else None,
        longitude=loc["lon"] if loc else None,
        country=loc["country"] if loc else None,
        city=loc["city"] if loc else None,
        zip=loc["zip"] if loc else None
    )
    db.add(db_query)
    db.commit()
    db.refresh(db_query)
    return db_query


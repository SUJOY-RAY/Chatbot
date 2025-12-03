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
        created_at=datetime.now()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_token(db: Session, token: str):
    return db.query(User).filter(User.session_token == token).first()

def save_query(db, user, text, sentiment, score, ip_address, confidence, details):
    loc = ip_to_location(ip_address)

    db_query = Query(
        text=text,
        sentiment=sentiment,
        score=score,  # store as float, not string
        time=datetime.now(timezone.utc),
        confidence=confidence,  # make sure Query model has a Float column for this
        details=details,
        user=user,
        ip_address=ip_address,

        latitude=loc.get("lat") if loc else None,
        longitude=loc.get("lon") if loc else None,
        country=loc.get("country") if loc else None,
        city=loc.get("city") if loc else None,
        region=loc.get("region") if loc else None,  # optional
    )

    db.add(db_query)
    db.commit()
    db.refresh(db_query)

    return db_query

def chat_history(db:Session, token):
    data = db.query(Query).filter(User.session_token == token)
    print(data)
    return data

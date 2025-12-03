from sqlalchemy.orm import Session
from database import User, Query  # SQLAlchemy models
import uuid
from datetime import datetime, timezone
from ipconverter import ip_to_location  # utility to convert IP to geolocation


def create_user(db: Session, username: str, ip_address: str):
    """
    Create a new user in the database with a unique session token.
    
    Args:
        db (Session): SQLAlchemy database session.
        username (str): Desired username for the new user.
        ip_address (str): IP address of the user (for logging or geolocation).
        
    Returns:
        User: Newly created User object with session_token assigned.
    """
    # Generate a unique session token for this user
    token = str(uuid.uuid4())
    
    # Create a new User object
    user = User(
        username=username,
        session_token=token,
        ip_address=ip_address,
        created_at=datetime.now()  # timestamp for creation
    )
    
    # Add user to the database
    db.add(user)
    db.commit()  # save changes
    db.refresh(user)  # refresh the instance with DB-generated fields (like ID)
    
    return user


def get_user_by_token(db: Session, token: str):
    """
    Retrieve a user from the database by their session token.
    
    Args:
        db (Session): SQLAlchemy database session.
        token (str): User's session token.
        
    Returns:
        User or None: The User object if found, else None.
    """
    return db.query(User).filter(User.session_token == token).first()


def save_query(db, user, text, sentiment, score, ip_address, confidence, details):
    """
    Save a user's query and its sentiment analysis results to the database.
    
    Args:
        db (Session): SQLAlchemy database session.
        user (User): The user object who made the query.
        text (str): Original query text.
        sentiment (str): Sentiment label (e.g., Positive, Negative).
        score (float): Compound sentiment score.
        ip_address (str): IP address of the user when making the query.
        confidence (float): Confidence in sentiment classification.
        details (dict): Detailed sentiment breakdown (pos, neg, neu, compound).
        
    Returns:
        Query: The saved Query object.
    """
    # Convert IP address to geolocation (may return None if lookup fails)
    loc = ip_to_location(ip_address)

    # Create a Query object to store in the database
    db_query = Query(
        text=text,
        sentiment=sentiment,
        score=score,  # store as a float
        time=datetime.now(timezone.utc),  # UTC timestamp
        confidence=confidence,  # float value
        details=details,  # store the sentiment breakdown
        user=user,  # associate query with user
        ip_address=ip_address,

        # Geolocation information
        latitude=loc.get("lat") if loc else None,
        longitude=loc.get("lon") if loc else None,
        country=loc.get("country") if loc else None,
        city=loc.get("city") if loc else None,
        region=loc.get("region") if loc else None,  # optional
    )

    # Add query to database and commit changes
    db.add(db_query)
    db.commit()
    db.refresh(db_query)  # refresh instance to get DB-generated fields (like ID)

    return db_query


def chat_history(db: Session, token: str):
    """
    Retrieve all queries associated with a user session token.
    
    Args:
        db (Session): SQLAlchemy database session.
        token (str): User's session token.
        
    Returns:
        Query: SQLAlchemy query object (can be iterated to get results).
    """
    # Attempt to get queries for user by joining User and Query via token
    data = db.query(Query).join(User).filter(User.session_token == token).all()
    
    # # Print for debugging (optional)
    # print(data)
    
    return data

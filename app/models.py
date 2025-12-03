from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str

class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    sentiment: str
    score: float

class IPLocation:
    lat: Optional[float] = None       # Latitude
    lon: Optional[float] = None       # Longitude
    country: Optional[str] = None     # Country name
    city: Optional[str] = None        # City name
    zip: Optional[str] = None         # ZIP code


class SentimentQueryOut(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None
    sentiment: str
    score: float
    city: str
    country: str
    text: str
    uid: Optional[int] = None  

    class Config:
        from_attributes = True  

class UserOut(BaseModel):
    username: str
    session_token: str

    class Config:
        from_attributes = True


class QueryHistoryOut(BaseModel):
    id: int
    text: str
    sentiment: str
    score: float
    time: datetime
    city: Optional[str] = None
    country: Optional[str] = None
    confidence: Optional[float] = None

    class Config:
        from_attributes = True

class HistoryListOut(BaseModel):
    username: str
    queries: List[QueryHistoryOut]


class SentimentAnalysisOut(BaseModel):
    text: str
    sentiment: str
    score: float
    confidence: float
    details: Dict
    
    class Config:
        from_attributes = True

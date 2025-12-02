from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str

class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    sentiment: str
    score: float


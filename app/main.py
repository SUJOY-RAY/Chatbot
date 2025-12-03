from fastapi import FastAPI, Depends, File, Request, Form, UploadFile, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ipconverter import ip_to_location
from database import Query, SessionLocal, init_db
from crud import create_user, get_user_by_token, save_query
from sentiment import analyze_sentiment
import os

init_db()
app = FastAPI()
templates = Jinja2Templates(directory="templates")
INACTIVITY_TIMEOUT = 2.0

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Register ----------

@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register", response_class=HTMLResponse)
def register_user(request: Request, username: str = Form(...), db: Session = Depends(get_db)):
    client_host = request.client.host  # get IP address
    db_user = create_user(db, username, ip_address=client_host)
    return templates.TemplateResponse("welcome.html", {
        "request": request,
        "username": db_user.username,
        "session_token": db_user.session_token
    })

# ---------- Sentiment ----------

@app.get("/sentiment-form", response_class=HTMLResponse)
def sentiment_form(request: Request):
    return templates.TemplateResponse("sentiment_form.html", {
        "request": request,
        "text": "",
        "sentiment": None,
        "score": None,
        "error": None
    })

@app.post("/sentiment", response_class=HTMLResponse)
def sentiment_analysis(request: Request, text: str = Form(...), token: str = Form(...), db: Session = Depends(get_db)):
    user = get_user_by_token(db, token)
    client_host = request.client.host  # get IP address
    if not user:
        return templates.TemplateResponse("sentiment_form.html", {
            "request": request,
            "text": text,
            "sentiment": None,
            "score": None,
            "error": 'Invalid session token. <a href="/register">Register here</a>'
        })
    result = analyze_sentiment(text)
    save_query(db, user, text, result["sentiment"], result["score"], client_host)

    return templates.TemplateResponse("sentiment_form.html", {
        "request": request,
        "text": text,
        "sentiment": result['sentiment'],
        "score": result['score'],
        "error": None
    })

@app.post("/sentiment", response_class=HTMLResponse)
def sentiment_analysis(
    request: Request,
    text: str = Form(...),
    token: str = Form(...),
    db: Session = Depends(get_db)
):
    # Authenticate
    user = get_user_by_token(db, token)
    client_ip = request.client.host

    if not user:
        return templates.TemplateResponse("sentiment_form.html", {
            "request": request,
            "text": text,
            "sentiment": None,
            "score": None,
            "error": 'Invalid session token. <a href="/register">Register here</a>'
        })

    # Analyze sentiment (your existing function)
    result = analyze_sentiment(text)
    sentiment = result["sentiment"]
    score = result["score"]

    # Geolocation
    loc = ip_to_location(client_ip)

    # Save query to database
    query = Query(
        text=text,
        sentiment=sentiment,
        score=score,
        user_id=user.id,
        ip_address=client_ip,
        latitude=loc["lat"] if loc else None,
        longitude=loc["lon"] if loc else None,
        country=loc["country"] if loc else None,
        city=loc["city"] if loc else None
    )

    db.add(query)
    db.commit()

    # Return results
    return templates.TemplateResponse("sentiment_form.html", {
        "request": request,
        "text": text,
        "sentiment": sentiment,
        "score": score,
        "error": None
    })

@app.get("/map")
def map_page(request: Request):
    return templates.TemplateResponse("sentiment_map.html", {"request": request})


@app.get("/sentiment-map")
def sentiment_map(db: Session = Depends(get_db)):
    data = db.query(Query).all()

    result = []
    for q in data:
        result.append({
            "lat": q.latitude,
            "lng": q.longitude,
            "sentiment": q.sentiment if q.sentiment else "Unknown",
            "score": float(q.score) if q.score is not None else 0.0,
            "city": q.city if q.city else "Unknown City",
            "country": q.country if q.country else "Unknown Country",
            "text": q.text if q.text else "No text",
            "uid": q.user_id
        })

    return result


# ---------- Home ----------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})

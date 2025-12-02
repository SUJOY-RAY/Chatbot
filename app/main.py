from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from requests import request
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from crud import create_user, get_user_by_token, save_query
from sentiment import analyze_sentiment

init_db()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

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

@app.get("/sentiment_form", response_class=HTMLResponse)
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

# ---------- Home ----------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})

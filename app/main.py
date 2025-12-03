from fastapi import FastAPI, Depends, File, Request, Form, UploadFile, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import Query, SessionLocal, init_db
from crud import create_user, get_user_by_token, save_query, chat_history
from sentiment import analyze_sentiment
import os

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
    return templates.TemplateResponse("auth/register.html", {"request": request})

@app.post("/register", response_class=HTMLResponse)
def register_user(request: Request, username: str = Form(...), db: Session = Depends(get_db)):
    client_host = request.client.host
    db_user = create_user(db, username, ip_address=client_host)
    return templates.TemplateResponse("welcome.html", {
        "request": request,
        "username": db_user.username,
        "session_token": db_user.session_token
    })

@app.get("/sentiment-form", response_class=HTMLResponse)
def sentiment_form(request: Request):
    return templates.TemplateResponse("/sentiment/sentiment_form.html", {
        "request": request,
        "text": "",
        "sentiment": None,
        "score": None,
        "error": None
    })


def render_error(request: Request, message: str):
    return templates.TemplateResponse("component/error.html", {
        "request": request,
        "error": message
    })

def verify_user(request: Request, db: Session, token: str):
    user = get_user_by_token(db, token)
    if not user:
        return render_error(request, 'Invalid session token. <a href="/register">Register here</a>')
    return user

@app.post("/sentiment", response_class=HTMLResponse)
def sentiment_analysis(request: Request, text: str = Form(...), token: str = Form(...), db: Session = Depends(get_db)):
    ip_address = request.client.host  # get IP address
    user = verify_user(db=db, token=token, request=request)
    result = analyze_sentiment(text)
    save_query(db, user, text, result["sentiment"], result["score"], ip_address, result["confidence"], result["details"])

    data = {
        "request": request,
        "text": text,
        "sentiment": result['sentiment'],
        "score": result['score'],
        "result": result["details"],
        "error": None
    }
    print(data)
    return templates.TemplateResponse("sentiment/sentiment_form.html", data)

@app.get("/map")
def map_page(request: Request):
    return templates.TemplateResponse("sentiment/sentiment_map.html", {"request": request})


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

@app.get("/about", response_class=HTMLResponse)
def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/history", response_class=HTMLResponse)
def history(request: Request, token: str | None = None, db: Session = Depends(get_db)):
    if token is None:
        return templates.TemplateResponse("/components/error.html", {
            "request": request,
            "error": "Missing session token."
        })

    user = get_user_by_token(db, token)
    if not user:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Invalid session token."
        })

    queries = (
        db.query(Query)
        .filter(Query.user_id == user.id)
        .order_by(Query.time.desc())
        .all()
    )

    return templates.TemplateResponse("history.html", {
        "request": request,
        "queries": queries,
        "username": user.username
    })

@app.delete("/delete-query/{query_id}")
def delete_query(query_id: int, token: str, db: Session = Depends(get_db)):
    user = get_user_by_token(db, token)
    if not user:
        return {"error": "Invalid session token."}

    query = db.query(Query).filter(Query.id == query_id, Query.user_id == user.id).first()
    if not query:
        return {"error": "Query not found."}

    db.delete(query)
    db.commit()
    return {"success": True}

# ---------- Home ----------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})

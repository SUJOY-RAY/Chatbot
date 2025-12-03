import io
from fastapi import FastAPI, Depends, File, Request, Form, UploadFile, WebSocket
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import Query, SessionLocal, User, init_db
from crud import create_user, get_user_by_token, save_query, chat_history
from sentiment import analyze_sentiment
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# ---------- Initialize database and FastAPI ----------

init_db()  # Create all tables if they don't exist
app = FastAPI()
templates = Jinja2Templates(directory="templates")  # Directory for Jinja2 HTML templates

# ---------- Dependency: database session ----------

def get_db():
    """
    Dependency that provides a SQLAlchemy database session for each request.
    Ensures proper closing of the session after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Registration Endpoints ----------

@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    """
    Display the registration form page.
    """
    return templates.TemplateResponse("auth/register.html", {"request": request})

@app.post("/register", response_class=HTMLResponse)
def register_user(request: Request, username: str = Form(...), db: Session = Depends(get_db)):
    """
    Handle user registration:
    - Create a new user with a unique session token.
    - Capture the user's IP address.
    - Return a welcome page with username and token.
    """
    client_host = request.client.host  # Get client IP
    db_user = create_user(db, username, ip_address=client_host)
    return templates.TemplateResponse("welcome.html", {
        "request": request,
        "username": db_user.username,
        "session_token": db_user.session_token
    })

# ---------- Sentiment Form ----------

@app.get("/sentiment-form", response_class=HTMLResponse)
def sentiment_form(request: Request):
    """
    Render the sentiment analysis form page with empty default values.
    """
    return templates.TemplateResponse("/sentiment/sentiment_form.html", {
        "request": request,
        "text": "",
        "sentiment": None,
        "score": None,
        "error": None
    })

# ---------- Utility functions ----------

def render_error(request: Request, message: str):
    """
    Render a reusable error template with a custom message.
    """
    return templates.TemplateResponse("/components/error.html", {
        "request": request,
        "error": message
    })

def verify_user(request: Request, db: Session, token: str):
    """
    Verify that a session token belongs to a valid user.
    Returns the User object if valid, otherwise renders an error.
    """
    user = get_user_by_token(db, token)
    if not user:
        return render_error(request, 'Invalid session token. <a href="/register">Register here</a>')
    return user

# ---------- Sentiment Analysis Endpoint ----------

@app.post("/sentiment", response_class=HTMLResponse)
def sentiment_analysis(request: Request, text: str = Form(...), token: str = Form(...), db: Session = Depends(get_db)):
    """
    Process a text for sentiment analysis:
    - Verify user token.
    - Analyze sentiment using VADER.
    - Save query to database.
    - Render the form page again with results.
    """
    ip_address = request.client.host  # Capture user's IP
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
    return templates.TemplateResponse("sentiment/sentiment_form.html", data)

# ---------- Map Page ----------

@app.get("/map")
def map_page(request: Request):
    """
    Render a page showing a map of sentiment locations.
    """
    return templates.TemplateResponse("sentiment/sentiment_map.html", {"request": request})

@app.get("/sentiment-map")
def sentiment_map(db: Session = Depends(get_db)):
    """
    Return JSON data of all queries with location and sentiment info.
    Used to populate a frontend map.
    """
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

# ---------- About Page ----------

@app.get("/about", response_class=HTMLResponse)
def about_page(request: Request):
    """
    Render an About page.
    """
    return templates.TemplateResponse("about.html", {"request": request})

# ---------- History Page ----------

@app.get("/history", response_class=HTMLResponse)
def history(request: Request, token: str | None = None, db: Session = Depends(get_db)):
    """
    Show the query history for a user identified by session token.
    """
    if token is None:
        return render_error(request, "Missing session token.")

    user = get_user_by_token(db, token)
    if not user:
        return render_error(request, "Invalid session token.")

    queries = db.query(Query).filter(Query.user_id == user.id).order_by(Query.time.desc()).all()
    return templates.TemplateResponse("history.html", {
        "request": request,
        "queries": queries,
        "username": user.username
    })

# ---------- Delete Query ----------

@app.delete("/delete-query/{query_id}")
def delete_query(query_id: int, token: str, db: Session = Depends(get_db)):
    """
    Delete a specific query by ID for a user.
    Returns JSON success or error.
    """
    user = get_user_by_token(db, token)
    if not user:
        return {"error": "Invalid session token."}

    query = db.query(Query).filter(Query.id == query_id, Query.user_id == user.id).first()
    if not query:
        return {"error": "Query not found."}

    db.delete(query)
    db.commit()
    return {"success": True}

# ---------- Trend Page ----------

@app.get("/trend_page", response_class=HTMLResponse)
def trend_page(request: Request):
    """
    Render a page for showing sentiment trend over time.
    """
    return templates.TemplateResponse("trend.html", {"request": request})

@app.get("/trend")
def trend(token: str, db: Session = Depends(get_db)):
    """
    Generate a sentiment trend plot for a user over time:
    - Fetch user's queries.
    - Plot scores over time with points colored by location.
    - Return as a PNG image.
    """
    history = db.query(Query).join(User).filter(User.session_token == token).order_by(Query.time.asc()).all()
    if not history:
        return {"error": "No history found"}

    times = [q.time for q in history]
    scores = [q.score for q in history]
    locations = [f"{q.country or 'Unknown'} - {q.city or 'Unknown'}" for q in history]

    unique_locations = list(set(locations))
    cmap = cm.get_cmap("tab10", len(unique_locations))
    color_map = {loc: cmap(i) for i, loc in enumerate(unique_locations)}

    plt.figure(figsize=(12, 6))
    plt.title("Sentiment Trend Colored by Location")
    plt.xlabel("Time")
    plt.ylabel("Sentiment Score (Compound)")
    plt.grid(True)

    for i, q in enumerate(history):
        plt.scatter(
            q.time,
            q.score,
            color=color_map[locations[i]],
            s=60,
            label=locations[i] if i == locations.index(locations[i]) else ""
        )

    plt.plot(times, scores, linestyle="--", color="gray", alpha=0.4)
    plt.legend(title="Country - City", fontsize=8)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    plt.close()

    return StreamingResponse(buf, media_type="image/png")

# ---------- Home Page ----------

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    Render the main welcome/home page.
    """
    return templates.TemplateResponse("welcome.html", {"request": request})

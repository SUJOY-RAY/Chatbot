# from nltk.sentiment.vader import SentimentIntensityAnalyzer
# import nltk

# nltk.download('vader_lexicon')

# sia = SentimentIntensityAnalyzer()

# def analyze_sentiment(text: str):
#     score = sia.polarity_scores(text)['compound']
#     if score >= 0.6:
#         sentiment = "Very Positive"
#     elif score >= 0.05:
#         sentiment = "Positive"
#     elif score > -0.05 and score < 0.05:
#         sentiment = "Neutral"
#     elif score <= -0.05 and score > -0.6:
#         sentiment = "Negative"
#     else:
#         sentiment = "Very Negative"
#     return {"sentiment": sentiment, "score": score}


import re
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

nltk.download("vader_lexicon")

sia = SentimentIntensityAnalyzer()

def clean_text(text: str) -> str:
    """Normalize text for more reliable VADER output."""
    text = text.strip()

    # Remove URLs
    text = re.sub(r"http\S+|www\S+", "", text)

    # Remove excessive punctuation
    text = re.sub(r"([!?.,])\1{2,}", r"\1\1", text)

    # Fix stretched words: "soooo happy" → "soo happy"
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)

    return text


def classify_sentiment(score: float) -> str:
    """Use softened, data-backed thresholds for more accuracy."""
    if score >= 0.7:
        return "Very Positive"
    elif score >= 0.25:
        return "Positive"
    elif score > -0.25 and score < 0.25:
        return "Neutral"
    elif score <= -0.25 and score > -0.7:
        return "Negative"
    else:
        return "Very Negative"


def analyze_sentiment(text: str):
    """Improved sentiment logic for real-world, noisy inputs."""
    cleaned = clean_text(text)
    raw_scores = sia.polarity_scores(cleaned)
    compound = raw_scores["compound"]

    sentiment = classify_sentiment(compound)

    # Confidence estimate based on distance from 0
    confidence = round(abs(compound), 3)

    return {
        "text": text,
        "cleaned_text": cleaned,
        "sentiment": sentiment,
        "score": round(compound, 4),
        "confidence": confidence,
        "details": raw_scores  
    }

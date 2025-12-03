import re
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# Download the VADER lexicon for sentiment analysis (only needed once)
nltk.download("vader_lexicon")

# Initialize the VADER sentiment analyzer
sia = SentimentIntensityAnalyzer()

def clean_text(text: str) -> str:
    """
    Normalize text for more reliable VADER sentiment analysis.
    
    Steps:
    1. Strip leading/trailing whitespace.
    2. Remove URLs (both http(s) and www formats).
    3. Reduce excessive punctuation (like "!!!" → "!!").
    4. Reduce stretched words (like "soooo happy" → "soo happy").
    
    Args:
        text (str): Raw input text.
        
    Returns:
        str: Cleaned and normalized text.
    """
    text = text.strip()

    # Remove URLs
    text = re.sub(r"http\S+|www\S+", "", text)

    # Remove excessive punctuation (limit repeated punctuations to 2)
    text = re.sub(r"([!?.,])\1{2,}", r"\1\1", text)

    # Fix stretched words (e.g., "soooo" → "soo")
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)

    return text


def classify_sentiment(score: float) -> str:
    """
    Classify sentiment based on VADER compound score using softened thresholds.
    
    Args:
        score (float): Compound sentiment score from VADER (-1 to 1).
        
    Returns:
        str: Sentiment category: Very Positive, Positive, Neutral, Negative, Very Negative.
    """
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
    """
    Analyze sentiment of a text string with preprocessing, scoring, and confidence estimation.
    
    Steps:
    1. Clean the text using `clean_text` for better accuracy on noisy inputs.
    2. Get sentiment scores from VADER.
    3. Classify sentiment category based on compound score.
    4. Estimate confidence as the absolute value of the compound score.
    
    Args:
        text (str): Input text to analyze.
        
    Returns:
        dict: Contains original and cleaned text, sentiment label, compound score, 
              confidence, and detailed VADER scores.
    """
    # Clean text for more reliable sentiment scoring
    cleaned = clean_text(text)

    # Get raw sentiment scores from VADER
    raw_scores = sia.polarity_scores(cleaned)
    compound = raw_scores["compound"]  # overall sentiment score

    # Classify sentiment category
    sentiment = classify_sentiment(compound)

    # Confidence estimate based on how far the score is from 0
    confidence = round(abs(compound), 3)

    return {
        "text": text,  # original text
        "cleaned_text": cleaned,  # cleaned/normalized text
        "sentiment": sentiment,  # classified sentiment label
        "score": round(compound, 4),  # compound score rounded to 4 decimals
        "confidence": confidence,  # confidence in sentiment classification
        "details": raw_scores  # detailed VADER scores (pos, neg, neu, compound)
    }

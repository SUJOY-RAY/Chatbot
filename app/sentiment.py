from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import torch.nn.functional as F

nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()

def analyze_sentiment(text: str):
    score = sia.polarity_scores(text)['compound']
    if score >= 0.6:
        sentiment = "Very Positive"
    elif score >= 0.05:
        sentiment = "Positive"
    elif score > -0.05 and score < 0.05:
        sentiment = "Neutral"
    elif score <= -0.05 and score > -0.6:
        sentiment = "Negative"
    else:
        sentiment = "Very Negative"
    return {"sentiment": sentiment, "score": score}
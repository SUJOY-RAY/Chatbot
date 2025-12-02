from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
import torch, librosa, numpy as np
import torch.nn.functional as F
import pyaudio

nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()
extractor = AutoFeatureExtractor.from_pretrained("superb/wav2vec2-base-superb-er")
model = AutoModelForAudioClassification.from_pretrained("superb/wav2vec2-base-superb-er")

CHUNK = 16000         # 1 second of audio (16kHz)
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 16000

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


# def analyse_voice_emotion(audio_file):
#     # Load audio
#     audio, sr = librosa.load(audio_file, sr=16000, mono=True)

#     # Preprocess for model
#     inputs = extractor(
#         audio,
#         sampling_rate=16000,
#         return_tensors="pt",
#         padding=True,
#         truncation=True
#     )

#     inputs = {k: v.to(torch.device) for k, v in inputs.items()}

#     # Forward pass
#     with torch.no_grad():
#         logits = model(**inputs).logits

#     # Softmax for probability
#     probs = F.softmax(logits, dim=-1).cpu().numpy()[0]

#     # Highest probability
#     emotion_id = int(np.argmax(probs))
#     label = model.config.id2label[emotion_id]
#     score = float(probs[emotion_id])

#     return {
#         "emotion": label,
#         "confidence": score,
#         "probabilities": {
#             model.config.id2label[i]: float(probs[i]) for i in range(len(probs))
#         }
#     }

def safe_rms(audio):
    # 1. Convert NaNs / infs to 0
    audio = np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)

    # 2. Normalize audio to [-1, 1] to prevent overflow
    max_val = np.max(np.abs(audio)) + 1e-9  # avoid divide by zero
    audio = audio / max_val

    # 3. Compute RMS
    rms = float(np.sqrt(np.mean(np.square(audio))))
    return rms


def get_intensity(audio):
    rms = safe_rms(audio)
    return float(rms)

def analyze_audio(audio_np):
    inputs = extractor(audio_np, sampling_rate=16000, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)[0]

    emotion_id = int(torch.argmax(probs))
    emotion = model.config.id2label[emotion_id]
    confidence = float(probs[emotion_id])

    intensity = get_intensity(audio_np)

    return {"emotion": emotion, "confidence": confidence, "intensity": intensity}


import os
import json
import pandas as pd
from dotenv import load_dotenv
from google import genai
# ── load environment variables from .env file ──────────────────
load_dotenv()
from config import Config
from gemini_client import GeminiClient
from prompts import Prompts
from data_preprocessor import DataPreprocessor
from sentiment_analyzer import SentimentAnalyzer
from predictor import MoodPredictor


# ── set up Gemini client ───────────────────────────────────────
gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
client        = GeminiClient(gemini_client, Config.GEMINI_MODEL)


# ══════════════════════════════════════════════════════════════
# Step 1 — DATA GENERATION & CLEANING
# ══════════════════════════════════════════════════════════════
print("Step 1: DATA CLEANING")
print("\n")

raw_mock = client.ask_json(Prompts.MOCK_DATA, "Generate the data now.")
mock_df  = pd.DataFrame(raw_mock)

preprocessor = DataPreprocessor(client)
result       = preprocessor.clean(mock_df)

print(f"\nStats: {result['stats']}")
print(f"\nUsable ({len(result['usable'])}):")
for row in result['usable']:
    print(f"   {row['date']} | score={row.get('mood_score')} | "
          f"{str(row.get('journal_text',''))[:40]} | {row.get('clean_notes','')}")

if result['discarded']:
    print(f"\nDiscarded ({len(result['discarded'])}):")
    for row in result['discarded']:
        print(f"   {row['date']} | {row.get('clean_notes','')}")

# build clean DataFrame
clean_df = pd.DataFrame(result['usable'])
clean_df['date']       = pd.to_datetime(clean_df['date'])
clean_df['mood_score'] = pd.to_numeric(clean_df['mood_score'], errors='coerce')
clean_df = clean_df.dropna(subset=['mood_score'])
clean_df = clean_df.sort_values('date').reset_index(drop=True)


# ══════════════════════════════════════════════════════════════
# Step 2 — SENTIMENT ANALYSIS
# ══════════════════════════════════════════════════════════════
print("\n")
print("Step 2: SENTIMENT ANALYSIS (local, no AI)")
print("\n")

sa = SentimentAnalyzer()
clean_df['sentiment_label'] = clean_df['journal_text'].apply(
    lambda t: sa.analyze(str(t)).label)
clean_df['sentiment_note']  = clean_df['journal_text'].apply(
    lambda t: sa.analyze(str(t)).brief_note)
clean_df['sentiment_flags'] = clean_df['journal_text'].apply(
    lambda t: sa.analyze(str(t)).flags)

print(f"\nSentiment distribution:")
print(clean_df['sentiment_label'].value_counts().to_string())

flagged = clean_df[clean_df['sentiment_flags'].apply(len) > 0]
if len(flagged) > 0:
    print(f"\nFlagged entries ({len(flagged)}):")
    for _, row in flagged.iterrows():
        print(f"   {row['date'].strftime('%Y-%m-%d')} | "
              f"{row['sentiment_flags']} | "
              f"{str(row['journal_text'])[:50]}")


# ══════════════════════════════════════════════════════════════
# Step 3 — PATTERN ANALYSIS (AI)
# ══════════════════════════════════════════════════════════════
print("\n")
print("Step 3: PATTERN ANALYSIS (AI)")
print("\n")

last_14 = clean_df.tail(14)
mood_data_for_analysis = [
    {
        "score":      int(row['mood_score']),
        "day":        row['date'].strftime('%a'),
        "brief_note": row['sentiment_note']
    }
    for _, row in last_14.iterrows()
]

analysis = client.ask_json(Prompts.PATTERN_ANALYSIS, json.dumps(mood_data_for_analysis))
print(f"\n{json.dumps(analysis, indent=2, ensure_ascii=False)}")


# ══════════════════════════════════════════════════════════════
# Step 4 — ESCALATION CHECK
# ══════════════════════════════════════════════════════════════
print("\n")
print("Step 4: ESCALATION CHECK")
print("\n")

recent_scores    = clean_df['mood_score'].tail(5).astype(int).tolist()
all_flags        = [f for flags in clean_df['sentiment_flags'].tail(5) for f in flags]
needs_escalation = sa.should_escalate(recent_scores, all_flags)

print(f"\nRecent 5 scores: {recent_scores}")
print(f"Flags: {all_flags}")
print(f"Escalation needed: {needs_escalation}")

if needs_escalation:
    esc = client.ask_json(
        Prompts.ESCALATION,
        json.dumps({"last_5_scores": recent_scores, "sentiment_flags": all_flags})
    )
    print(f"Risk level: {esc['risk_level']}")
    print(f"Action: {esc['suggested_action']}")
    if esc.get('resource_link'):
        print(f"Resource: {esc['resource_link']}")
else:
    print("No escalation needed.")


# ══════════════════════════════════════════════════════════════
# Step 5 — REFLECTION PROMPT (AI)
# ══════════════════════════════════════════════════════════════
print("\n")
print("Step 5: REFLECTION PROMPT (AI)")
print("\n")

last_row   = clean_df.iloc[-1]
reflection = client.ask(
    Prompts.REFLECTION,
    f"Mood score: {int(last_row['mood_score'])}/5\n"
    f"Time of day: {last_row.get('time_of_day', 'evening')}\n"
    f"Day of week: {last_row['date'].strftime('%A')}"
)
print(f"\n💬 {reflection}")


# ══════════════════════════════════════════════════════════════
# Step 6 — LSTM PREDICTION
# ══════════════════════════════════════════════════════════════
print("\n")
print("Step 6: MOOD PREDICTION (LSTM)")
print("\n")

scores = clean_df['mood_score'].tolist()
dates  = clean_df['date'].tolist()

print(f"\nTraining data: {len(scores)} days")
print(f"Range: {dates[0].strftime('%Y-%m-%d')} ~ {dates[-1].strftime('%Y-%m-%d')}")

print("\nTraining LSTM...")
predictor     = MoodPredictor(window_size=3, hidden_size=32, epochs=300, lr=0.01)
predictor.train(scores)

PREDICT_DAYS  = 7
future_scores = predictor.predict(scores, days=PREDICT_DAYS)
print(f"\nPredicted next {PREDICT_DAYS} days: {future_scores}")

predictor.plot(
    dates, scores, future_scores,
    title="Campus Mental Health — Mood Trend & 7-Day Prediction"
)

print("ALL DONE")
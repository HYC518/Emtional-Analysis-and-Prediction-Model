# server.py

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import json
import threading
import pandas as pd
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from google import genai

from config import Config
from gemini_client import GeminiClient
from prompts import Prompts
from data_preprocessor import DataPreprocessor
from sentiment_analyzer import SentimentAnalyzer
from predictor import MoodPredictor

app = Flask(__name__)
CORS(app, origins=Config.CLIENT_ORIGIN)

# ── shared clients ─────────────────────────────────────────────
gemini_connection = genai.Client(api_key=Config.GEMINI_API_KEY)
client = GeminiClient(gemini_connection, Config.GEMINI_MODEL)
sa     = SentimentAnalyzer()

# ── in-memory storage ──────────────────────────────────────────
entries = []

# ── prediction cache ───────────────────────────────────────────
prediction_cache  = {}
prediction_status = {"status": "idle"}


# ══════════════════════════════════════════════════════════════
# PAGE
# ══════════════════════════════════════════════════════════════
@app.route('/')
def index():
    return render_template('index.html')


# ══════════════════════════════════════════════════════════════
# API — submit a journal entry
# ══════════════════════════════════════════════════════════════
@app.route('/api/submit', methods=['POST'])
def submit():
    data        = request.json
    journal     = data.get('journal_text', '')
    mood_score  = int(data.get('mood_score', 3))
    date        = data.get('date', '')
    time_of_day = data.get('time_of_day', 'evening')

    # sentiment analysis (local, instant)
    result = sa.analyze(journal)

    # reflection prompt from Gemini
    from datetime import datetime
    try:
        day_of_week = datetime.strptime(date, '%Y-%m-%d').strftime('%A')
    except Exception:
        day_of_week = 'Monday'

    reflection = client.ask(
        Prompts.REFLECTION,
        f"Mood score: {mood_score}/5\n"
        f"Time of day: {time_of_day}\n"
        f"Day of week: {day_of_week}"
    )

    # store entry
    entry = {
        'date':            date,
        'mood_score':      mood_score,
        'journal_text':    journal,
        'time_of_day':     time_of_day,
        'sentiment_label': result.label,
        'sentiment_note':  result.brief_note,
        'sentiment_flags': result.flags,
        'sentiment_score': result.score,
    }
    entries.append(entry)

    # reset prediction cache when new data comes in
    prediction_status["status"] = "idle"
    prediction_cache.clear()

    # escalation check
    recent_scores = [e['mood_score'] for e in entries[-5:]]
    all_flags     = [f for e in entries[-5:] for f in e['sentiment_flags']]
    needs_esc     = sa.should_escalate(recent_scores, all_flags)

    escalation = None
    if needs_esc:
        escalation = client.ask_json(
            Prompts.ESCALATION,
            json.dumps({"last_5_scores": recent_scores, "sentiment_flags": all_flags})
        )

    return jsonify({
        'sentiment': {
            'label':      result.label,
            'score':      result.score,
            'brief_note': result.brief_note,
            'flags':      result.flags,
        },
        'reflection':    reflection,
        'escalation':    escalation,
        'total_entries': len(entries),
    })


# ══════════════════════════════════════════════════════════════
# API — get all entries
# ══════════════════════════════════════════════════════════════
@app.route('/api/entries', methods=['GET'])
def get_entries():
    return jsonify(entries)


# ══════════════════════════════════════════════════════════════
# API — pattern analysis (needs 7+ entries)
# ══════════════════════════════════════════════════════════════
@app.route('/api/patterns', methods=['GET'])
def patterns():
    if len(entries) < 7:
        return jsonify({
            'error': f'Need at least 7 entries. You have {len(entries)} so far.'
        }), 400

    last_14   = entries[-14:]
    mood_data = [
        {
            'score':      e['mood_score'],
            'day':        pd.to_datetime(e['date']).strftime('%a'),
            'brief_note': e['sentiment_note'],
        }
        for e in last_14
    ]
    analysis = client.ask_json(Prompts.PATTERN_ANALYSIS, json.dumps(mood_data))
    return jsonify(analysis)


# ══════════════════════════════════════════════════════════════
# API — LSTM prediction (runs in background thread)
# ══════════════════════════════════════════════════════════════
@app.route('/api/predict', methods=['GET'])
def predict():
    if len(entries) < 4:
        return jsonify({
            'error': f'Need at least 4 entries. You have {len(entries)} so far.'
        }), 400

    # already have a cached result
    if prediction_status["status"] == "done":
        return jsonify(prediction_cache)

    # already training
    if prediction_status["status"] == "training":
        return jsonify({
            'status':  'training',
            'message': 'Still training, check back soon...'
        })

    # start training in background thread
    # Flask stays free to handle other requests while this runs
    prediction_status["status"] = "training"

    def train_and_predict():
        try:
            scores = [e['mood_score'] for e in entries]
            dates  = [e['date'] for e in entries]

            # epochs=50 and hidden_size=16 instead of 300 and 32
            # the model architecture is IDENTICAL — same LSTM, same logic
            # only fewer training rounds and fewer detectors
            # for small datasets (4-30 points) this is faster and avoids overfitting
            predictor = MoodPredictor(
                window_size=3,
                hidden_size=16,
                epochs=50,
                lr=0.01
            )
            predictor.train(scores)
            future_scores = predictor.predict(scores, days=7)

            from datetime import datetime, timedelta
            last_date    = datetime.strptime(dates[-1], '%Y-%m-%d')
            future_dates = [
                (last_date + timedelta(days=i+1)).strftime('%Y-%m-%d')
                for i in range(7)
            ]

            prediction_cache.update({
                'status':            'done',
                'historical_dates':  dates,
                'historical_scores': scores,
                'predicted_dates':   future_dates,
                'predicted_scores':  future_scores,
            })
            prediction_status["status"] = "done"
            print("LSTM training complete.")

        except Exception as e:
            prediction_status["status"] = "error"
            prediction_cache.update({'status': 'error', 'error': str(e)})
            print(f"LSTM error: {e}")

    thread        = threading.Thread(target=train_and_predict)
    thread.daemon = True
    thread.start()

    return jsonify({
        'status':  'training',
        'message': 'Training started! Check back in about 10 seconds.'
    })


# ══════════════════════════════════════════════════════════════
# API — poll prediction status
# ══════════════════════════════════════════════════════════════
@app.route('/api/predict/status', methods=['GET'])
def predict_status():
    if prediction_status["status"] == "done":
        return jsonify(prediction_cache)
    return jsonify({'status': prediction_status["status"]})


# ══════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print(f"Server starting on http://localhost:{Config.PORT}")
    app.run(port=Config.PORT, debug=False)

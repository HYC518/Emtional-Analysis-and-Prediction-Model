# Mood Journal 🌿
### AI-Powered Mental Health Journaling for College Students
**HackWashU Spring 2026** · Built with Python, Flask, and Google Gemini

---

## What It Does

Mood Journal is a daily check-in app that helps college students track their emotional wellbeing over time. Users write a short journal entry each day, rate their mood from 1 to 5, and receive personalized AI-generated feedback. Over time, the app identifies mood patterns, predicts the next 7 days, and automatically alerts close friends if a user's mood stays critically low.

---

## Features

| Feature | Description |
|---|---|
| 📓 Daily Journal | Write freely and rate your mood 1–5 |
| 🤖 AI Reflection | Gemini reads your entry and responds like a caring friend |
| 💬 Sentiment Analysis | Local NLP detects emotional tone with negation handling |
| ⚠️ Crisis Detection | Flags concerning phrases and links to WashU Counseling |
| 📈 Pattern Analysis | Gemini identifies mood trends after 7+ entries |
| 🔮 7-Day Forecast | Trend-aware mood predictor for the next week |
| 👥 Friend Alerts | Notifies close friends after 5 consecutive low-mood days |
| 💬 Real-Time Chat | Message friends directly from the app |
| 🔐 Multi-User Auth | Token-based login with friend request system |

---

## Tech Stack

**Backend:** Python 3.12, Flask, Google Gemini API  
**ML/NLP:** PyTorch LSTM, Custom Sentiment Analyzer  
**Frontend:** HTML, CSS, JavaScript, Chart.js  
**Data:** Pandas, Matplotlib  
**Auth:** SHA256 password hashing, Bearer token sessions  
**Storage:** In-memory (per-user), JSON for accounts  

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/HYC518/MoodJournal.git
cd MoodJournal
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create `.env` file
```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
PORT=3002
```

### 5. Run the server
```bash
python server.py
```

Open [http://localhost:3002](http://localhost:3002) in your browser.

---

## Default Accounts

| Username | Password |
|---|---|
| alice | alice123 |
| bob | bob123 |

Or register a new account from the login page.

---

## Project Structure

```
MoodJournal/
├── server.py              # Flask web server + all API routes
├── auth.py                # Login, register, token auth, friend system
├── config.py              # Environment config
├── gemini_client.py       # Google Gemini API wrapper
├── prompts.py             # All AI prompt templates
├── sentiment_analyzer.py  # Local NLP with negation handling
├── predictor.py           # Mood prediction model
├── data_preprocessor.py   # Data cleaning pipeline
├── data_loader.py         # CSV/Excel loader
├── main.py                # Terminal pipeline (standalone)
├── users.json             # User accounts + friend relationships
├── requirements.txt
└── templates/
    ├── index.html         # Main calendar app
    ├── friend.html        # Friend inbox + chat
    └── login.html         # Login / register
```

---

## How It Works

```
1. User writes a journal entry and selects mood score (1–5)
2. Local sentiment analyzer detects emotional tone instantly
3. Gemini reads the entry and generates a warm, personalized response
4. Escalation check runs — flags crisis language or sustained low scores
5. After 7+ entries → Gemini analyzes mood patterns across the week
6. After 4+ entries → Predictor forecasts next 7 days
7. After 5 consecutive low-mood days → Close friends receive an alert
```

---

## AI Pipeline

```
Journal Entry
     │
     ├─► Sentiment Analysis (local, instant)
     │        └─► negation handling, crisis phrase detection
     │
     ├─► Gemini Reflection (AI)
     │        └─► reads actual entry, responds like a friend
     │
     ├─► Safety Escalation (AI)
     │        └─► risk assessment → WashU Counseling link
     │
     ├─► Pattern Analysis (AI, 7+ entries)
     │        └─► weekly trends, concrete suggestions
     │
     └─► Mood Prediction (4+ entries)
              └─► 7-day forecast on calendar
```

---

## Notes

- Journal data is stored in memory — restarting the server clears entries
- Passwords are hashed with SHA256
- Gemini API processes journal text — no data sold to third parties
- Minimum 4 entries for mood prediction, 7 for pattern analysis

---

## Built At

**HackWashU AI Hackathon · Spring 2026 · St. Louis, MO**

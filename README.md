# Mood Journal — Emotional Analysis & Prediction Model

A mental health journaling app for college students that combines AI, sentiment analysis, and deep learning to track and predict mood patterns.

## Features

- **Daily Journal** — write entries and rate your mood (1-5)
- **Sentiment Analysis** — automatically detects positive, negative and concerning language
- **Reflection Prompts** — Gemini AI generates warm, personalised journaling questions
- **Escalation Check** — flags concerning phrases and sustained low mood
- **Pattern Analysis** — Gemini finds mood trends across the last 14 days
- **7-Day Prediction** — LSTM neural network predicts future mood scores
- **Web Interface** — clean Flask web app with chart visualisation

## Tech Stack

- **AI** — Google Gemini API
- **ML** — PyTorch LSTM neural network
- **Backend** — Python, Flask
- **Data** — Pandas, Matplotlib
- **Frontend** — HTML, CSS, JavaScript, Chart.js

## Setup

### 1. Clone the repo
```
git clone https://github.com/HYC518/Emtional-Analysis-and-Prediction-Model.git
cd Emtional-Analysis-and-Prediction-Model
```

### 2. Create virtual environment
```
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Create .env file
```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### 5. Run the web app
```
python server.py
```

Then open http://localhost:3001 in your browser.

### 6. Or run the terminal pipeline
```
python main.py
```

## Project Structure
```
mood-journal/
├── config.py              # environment settings
├── gemini_client.py       # Gemini AI wrapper
├── data_loader.py         # data loading and cleaning
├── prompts.py             # all Gemini prompt templates
├── data_preprocessor.py   # two-stage data cleaning pipeline
├── sentiment_analyzer.py  # local sentiment analysis
├── predictor.py           # LSTM mood prediction model
├── server.py              # Flask web server
├── main.py                # terminal pipeline
├── requirements.txt       # dependencies
└── templates/
    └── index.html         # web frontend
```

## How it Works

1. Student writes a daily journal entry and rates their mood (1-5)
2. System runs local sentiment analysis on the journal text
3. Gemini generates a warm personalised reflection prompt
4. Escalation check runs on last 5 entries — flags concerning phrases
5. After 7+ entries — Gemini analyses mood patterns and gives suggestions
6. After 4+ entries — LSTM model predicts next 7 days of mood scores

## Notes

- All data is stored in memory — restarting the server clears entries
- Minimum 4 entries needed for mood prediction
- Minimum 7 entries needed for pattern analysis

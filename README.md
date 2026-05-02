# Wikipedia Racer

An autonomous Wikipedia speedrun bot vs. human race game.

## Prerequisites
- Python 3.10+
- Node.js & npm

## Setup & Running

### 1. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m backend.app.main
```
The backend will run on `http://localhost:8000`.

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
The frontend will run on `http://localhost:5173`.

## Features
- **Autonomous Bot:** Uses `all-mpnet-base-v2` embeddings for semantic navigation.
- **Real-time Tracking:** WebSockets broadcast the bot's path live.
- **Wikipedia Proxy:** Tracks human clicks by rewriting Wikipedia links through the backend.
- **Caching:** SQLite stores page links and embeddings to speed up repetitive topics.
# Wikipedia-Racer

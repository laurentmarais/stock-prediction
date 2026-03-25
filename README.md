# Stock Prediction

This repository contains a lightweight stock scenario application with:

- a FastAPI backend,
- a React frontend,
- free data sources by default,
- modular provider adapters so paid data sources can be added later,
- and a replay-friendly architecture so forecasts can be generated from a past date using only information available at that time.

## Structure

- `backend/`: API, forecast service, replay logic, and provider adapters
- `frontend/`: chart-first UI built with React and Lightweight Charts
- `architecture_predict.txt`: product and system architecture
- `brainstorm_predict.txt`: modeling and product ideation

## Default free providers

- Market data: Yahoo Finance
- Fundamentals: Yahoo Finance
- Macro: FRED via public endpoints
- Events: public calendar data exposed through Yahoo Finance

## Provider switching

Providers are selected through environment variables in the backend:

- `MARKET_DATA_PROVIDER`
- `FUNDAMENTALS_PROVIDER`
- `MACRO_DATA_PROVIDER`
- `EVENT_DATA_PROVIDER`

The code is structured so a future paid provider only needs a new adapter module plus one registry entry.

## Replay concept

Replay mode should let the user select a past timestamp and:

- load chart history only up to that point,
- run the forecast using point-in-time data only,
- render the forecast forward from that date,
- and compare the simulated scenarios with what actually happened afterward.

## Local run

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Docker

```bash
docker compose up --build
```

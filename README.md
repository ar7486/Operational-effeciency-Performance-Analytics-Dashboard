# Operational Efficiency & Performance Analytics Dashboard

An interactive Streamlit dashboard for inspecting operational performance, isolating anomalies, and reviewing localized statistics from tabular business data.

## What it does

The app loads CSV or Excel data, filters it, summarizes it, spots anomalies, plots trends, and lets you download the filtered slice.

## Requirements

- Python 3.12 is recommended for this project.
- pip

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Project structure

- `app.py` contains the dashboard.
- `requirements.txt` lists the dependencies.
- `PREREQUISITE.txt` explains the theory and core topics.

## Deployment

Quick options to publish this app:

- Streamlit Community Cloud (fastest): push this repo to GitHub, then go to https://streamlit.io/cloud, connect your GitHub account, pick this repository and branch, and deploy. Streamlit Cloud uses `requirements.txt` and runs `streamlit run app.py` automatically.

- Docker (portable): build and run the included `Dockerfile`:

```bash
docker build -t operational-dashboard:latest .
docker run -p 8501:8501 operational-dashboard:latest
```

- Render / Heroku / Railway: use the provided `Procfile` or `Dockerfile`. These platforms detect `Procfile` or allow Docker-based deploys.

Notes:
- Do NOT commit your virtual environment (`.venv/`) — `.gitignore` is included.
- If you want me to initialize git and push to GitHub from this machine, tell me the GitHub repository URL or grant `gh` CLI access.


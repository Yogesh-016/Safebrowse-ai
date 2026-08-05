# 🛡️ SafeBrowse AI

An AI-powered web analysis tool that summarizes any webpage, lets you chat with its content, and flags basic phishing/scam risk indicators before you trust a link.

🔗 **Live Demo**: [safebrowse-ai.onrender.com](https://safebrowse-ai.onrender.com)

> Note: hosted on Render's free tier — the app spins down after 15 minutes of inactivity, so the first request may take 30–60 seconds while it spins back up.

## Features

- **URL Summarizer** — scrapes a webpage (via Playwright) and generates a quick summary, key points, and takeaways using an LLM (Groq `llama-3.3-70b-versatile`)
- **Chat With Website** — ask follow-up questions answered strictly from the scraped page content (no hallucinated facts from outside the page)
- **Risk / Trust Score** — a lightweight heuristic score (HTTPS check, URL length, suspicious keyword matching) that flags potentially risky links
- **Frontend** — single-page vanilla HTML/CSS/JS UI with a glassmorphism / cyberpunk aesthetic

## Tech Stack

- **Backend**: FastAPI + Uvicorn
- **Scraping**: Playwright (headless Chromium)
- **LLM**: Groq API (`llama-3.3-70b-versatile`)
- **Frontend**: HTML/CSS/JS (no framework)

## Project Structure

```
.
├── app.py              # FastAPI server: serves frontend + /api/analyze, /api/chat
├── url.py              # Core logic: scraping, risk scoring, summarization, chat
├── SafeBrowse-AI.html  # Frontend UI
├── requirements.txt
├── Dockerfile
├── .dockerignore
└── render.yaml         # Render deployment blueprint
```

## Setup (Local)

1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. Set your Groq API key as an environment variable (get one free at [console.groq.com](https://console.groq.com)):
   ```bash
   export GROQ_API_KEY=your_key_here      # Windows: set GROQ_API_KEY=your_key_here
   ```

3. Run the server:
   ```bash
   uvicorn app:app --reload
   ```

4. Open `http://127.0.0.1:8000` in your browser.

## Deployment (Render)

This repo ships with a `Dockerfile` and `render.yaml` for one-click deployment:

1. Push this repo to GitHub.
2. On [Render](https://render.com): **New → Blueprint**, connect the repo.
3. Render reads `render.yaml` automatically and prompts you to paste in `GROQ_API_KEY` as a secret.
4. First build takes a few minutes (downloading the Chromium base image). After that you'll get a live public URL.

> **Note**: on Render's free tier, the service spins down after 15 minutes of inactivity. The first request after idling can take 30–50 seconds while headless Chromium cold-starts — this is expected, not a bug.

## API Endpoints

| Endpoint       | Method | Description                                      |
|----------------|--------|---------------------------------------------------|
| `/`            | GET    | Serves the frontend                               |
| `/api/analyze` | POST   | `{ "url": "..." }` → summary, risk score, insights |
| `/api/chat`    | POST   | `{ "question": "...", "pageContent": "..." }` → answer |

## Security Notes

- The Groq API key is loaded from the `GROQ_API_KEY` environment variable — **never** hardcode it in source or commit it to the repo.
- CORS is currently open (`allow_origins=["*"]`) for ease of local testing; tighten this to your actual frontend origin before any production use.

## Disclaimer

The risk score is a basic heuristic (HTTPS presence, URL length, suspicious keywords) and is **not** a substitute for a real security/anti-phishing scanner. Treat it as an informational signal only.

import os
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from url import Groq, API_KEY, MODEL, client, extract_website, risk_check, summarize_page

app = FastAPI(title="SafeBrowse AI Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/favicon.ico")
async def favicon():
    return PlainTextResponse("", status_code=204)

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    html_path = os.path.join(os.path.dirname(__file__), "SafeBrowse-AI.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Frontend file not found")

@app.post("/api/analyze")
async def analyze_url(request: Request):
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    url = (payload.get("url") or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    original_url = url
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url

    content = await run_in_threadpool(extract_website, url)
    if isinstance(content, str) and content.startswith("ERROR"):
        if url.startswith("https://"):
            stripped = original_url
            for prefix in ("https://", "http://"):
                if stripped.startswith(prefix):
                    stripped = stripped[len(prefix):]
                    break
            fallback_url = "http://" + stripped
            content = await run_in_threadpool(extract_website, fallback_url)
            if not (isinstance(content, str) and content.startswith("ERROR")):
                url = fallback_url

    if isinstance(content, str) and content.startswith("ERROR"):
        raise HTTPException(status_code=400, detail=content)

    score, level_text, reasons = await run_in_threadpool(risk_check, url)
    parsed = urlparse(url)
    host = parsed.hostname or url
    level_lower = level_text.split()[0].lower()
    category = "General"
    if "wikipedia" in host:
        category = "Reference & Knowledge"
    elif "github" in host:
        category = "Technology"
    elif "google" in host or "search" in host:
        category = "Technology"

    summary = await run_in_threadpool(summarize_page, content)
    insights = [
        f"Analyzed content from {host}",
        "HTTPS detected" if parsed.scheme == "https" else "No HTTPS detected",
        "Suspicious keywords found" if reasons else "No suspicious keywords detected",
    ]
    takeaways = [
        f"Security level: {level_text}",
        f"URL length: {len(url)} characters",
        "Use strong caution if you enter credentials on this site" if level_lower != "low" else "No major risk indicators detected in this scan",
    ]
    facts_list = [
        f"Domain: {host}",
        f"Protocol: {parsed.scheme.upper()}",
        f"Risk score: {score}/100",
        f"Risk level: {level_text}",
    ]

    return {
        "url": url,
        "host": host,
        "content": content[:15000],
        "summary": summary,
        "score": score,
        "level": level_text,
        "reasons": reasons,
        "trust": score,
        "safety": score,
        "riskLevel": level_lower,
        "category": category,
        "isHttps": parsed.scheme == "https",
        "knownSafe": "wikipedia" in host or "github" in host,
        "insights": insights,
        "takeaways": takeaways,
        "factsList": facts_list,
        "readingTime": max(1, len(summary.split()) // 180),
        "complexity": min(100, 30 + len(reasons) * 20),
        "sentiment": "Cautionary" if level_lower != "low" else "Informative",
        "facts": len(facts_list),
        "scamProbability": max(0, min(100, 100 - score)),
    }

@app.post("/api/chat")
async def chat_with_page(request: Request):
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    question = (payload.get("question") or "").strip()
    page_content = (payload.get("pageContent") or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    if not page_content:
        raise HTTPException(status_code=400, detail="Page content is required")

    prompt = f"Answer the user question using only the website content below.\n\nWebsite content:\n{page_content[:12000]}\n\nQuestion: {question}"
    response = await run_in_threadpool(
        client.chat.completions.create,
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a safe browsing assistant. Answer using only the page content provided."
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.3,
        max_tokens=500,
    )
    answer = response.choices[0].message.content
    return {"answer": answer}

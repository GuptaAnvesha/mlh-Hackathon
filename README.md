# 🛡️ Veritas — Grounded Fact-Checking, Powered by Gemini

> Paste any article, tweet, or claim. Veritas breaks it into atomic claims, verifies
> **each one against the live web** using Gemini's Google Search grounding, and returns
> a per-claim verdict with **real citations** plus an overall credibility score.

Built for the **MLH "Best Use of the Google Gemini API"** challenge.

---

## Why this is different

Most LLM fact-checkers just ask the model "is this true?" and trust its memory — which
hallucinates and goes stale. Veritas uses Gemini's **native Google Search grounding tool**,
so every verdict is backed by sources the model actually retrieved at query time.

| Judging criterion | How Veritas delivers |
|---|---|
| **Creativity** | Grounded claim-decomposition pipeline, not a wrapper chatbot |
| **Technical execution** | Structured output + Google Search grounding + citation extraction + parallel verification |
| **Gemini API use** | Uses Gemini's *distinctive* features (grounding + typed JSON), not generic LLM calls |
| **Impact** | Directly targets misinformation — a real, resonant problem |
| **Presentation** | One-tap mobile demo: paste spicy text → live scored teardown |

---

## Architecture

```
🌐 Web UI (web/index.html)  ──HTTP──►  🐍 FastAPI backend  ──►  Gemini API
   served at  /                          veritas/                (grounding + structured output)
```

The FastAPI backend both runs the pipeline **and serves the web UI** at `/`, so
there's a single thing to launch and demo. The API key lives **only** in the
backend — never in the frontend. (A React Native / Expo client also lives in
`mobile/` for a phone demo — optional; needs ~1 GB of npm packages.)

**Pipeline** (`veritas/pipeline.py`):
1. `claims.py` — decompose text into atomic claims via Gemini **structured output**
2. `verify.py` — ground each claim against the web via the **Google Search tool**, in parallel
3. Aggregate a confidence-weighted **credibility score** (0–100)

---

## Grounding, models & the free tier

- **Model:** defaults to `gemini-flash-lite-latest`, which has the most generous
  free-tier quota. Override with `VERITAS_*_MODEL` in `.env`.
- **Grounding:** Google Search grounding requires a **billing-enabled** key. On the
  free tier the Search tool returns HTTP 429, so Veritas **degrades gracefully** —
  it verifies each claim from the model's own knowledge (via structured output),
  marks the result `grounded: false`, and says so in the UI. Enable billing and
  live grounding + citations activate automatically, no code changes needed.
- **Quota:** the free tier caps daily requests; each claim is one request. If you
  hit the cap, the API returns a clean `429` and the UI shows a friendly message.

## Quick start (web app — the main demo)

```bash
pip install -r requirements.txt
cp .env.example .env          # then paste your key (https://aistudio.google.com/apikey)

uvicorn veritas.api:app --host 0.0.0.0 --port 8000
```

Then open **http://localhost:8000** in your browser, paste some text, and hit
**Check the facts**. That's the whole demo.

Prefer the terminal? `python -m veritas.cli "Honey never spoils and the Great Wall is visible from space."`

### Optional: React Native phone app

```bash
cd mobile
npm install        # ~1 GB; needs free disk space
npm start          # scan the QR code with Expo Go
```

Point `API_BASE_URL` in `mobile/config.js` at your computer's LAN IP
(e.g. `http://192.168.1.42:8000`) so the phone can reach the backend.

---

## API

`POST /analyze`

```json
{ "text": "The text to fact-check." }
```

Returns a `Report`: `credibility_score`, `summary`, and a `results[]` array of
`{ claim, verdict, confidence, explanation, citations[] }`.

Verdicts: `SUPPORTED · DISPUTED · MISLEADING · UNSUPPORTED · OPINION`.

---

## Demo script (for the judges)

1. Paste a paragraph mixing true, false, and misleading claims.
2. Hit **Check the facts**.
3. Watch it flag "visible from space" as **Disputed** with a citation, confirm
   "honey never spoils" as **Supported**, and land an overall score.

---

## Project layout

```
veritas/          Python backend
  schemas.py      Pydantic models (claims, verdicts, report)
  claims.py       Step 1 — structured claim extraction
  verify.py       Step 2 — grounded verification (+ ungrounded fallback)
  pipeline.py     Orchestration + credibility scoring
  api.py          FastAPI service (also serves the web UI)
  cli.py          Terminal demo
web/index.html    Single-file web UI (served at /)
mobile/           Optional React Native (Expo) app
tests/            Offline unit tests for the scoring logic
```

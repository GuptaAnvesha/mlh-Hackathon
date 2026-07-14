"""FastAPI service exposing Veritas to the React Native app.

Run:  uvicorn veritas.api:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from google.genai import errors as genai_errors
from pydantic import BaseModel, Field

from .pipeline import analyze
from .schemas import Report

_WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(
    title="Veritas API",
    description="Grounded misinformation & claim-checker powered by the Gemini API.",
    version="0.1.0",
)

# Open CORS so the Expo app (any LAN IP / tunnel) can call the backend during the demo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, description="The text to fact-check.")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(_WEB_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze", response_model=Report)
def analyze_endpoint(req: AnalyzeRequest) -> Report:
    try:
        return analyze(req.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except genai_errors.ClientError as exc:
        if getattr(exc, "code", None) == 429:
            raise HTTPException(
                status_code=429,
                detail="Gemini free-tier quota exhausted. Wait for the daily reset "
                "or enable API billing, then try again.",
            ) from exc
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except RuntimeError as exc:  # e.g. missing API key
        raise HTTPException(status_code=500, detail=str(exc)) from exc

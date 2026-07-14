"""BioQuest FastAPI application: REST + WebSocket.

Endpoints are fleshed out in later build steps; this module wires the app,
CORS, and a health check so the scaffold is runnable from step one.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__

app = FastAPI(title="BioQuest", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "bioquest", "version": __version__}

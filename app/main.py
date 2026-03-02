"""
Application entry point.

Creates the FastAPI application with:
    - Lifespan-managed MongoDB connection
    - CORS middleware (open for local dev / ngrok tunneling)
    - Structured logging
    - Profile-saving router
"""

from __future__ import annotations

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import lifespan
from app.routes import router as profile_router

# ── Logging ──────────────────────────────────────────────────────


def _configure_logging() -> None:
    """Set up structured console logging for the entire application."""
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d — %(message)s"
    )
    logging.basicConfig(
        level=settings.log_level.upper(),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


_configure_logging()
logger = logging.getLogger(__name__)

# ── App factory ──────────────────────────────────────────────────

app = FastAPI(
    title="ElevenLabs Child Profile API",
    description=(
        "Receives structured child profile data from the ElevenLabs Agent "
        "save_child_profile server tool and stores it in a local MongoDB instance."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────

app.include_router(profile_router)


# ── Health check ─────────────────────────────────────────────────


@app.get("/health", tags=["ops"])
async def health_check() -> dict[str, str]:
    """Simple liveness probe."""
    return {"status": "healthy"}

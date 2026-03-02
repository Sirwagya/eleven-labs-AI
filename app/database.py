"""
Async MongoDB connection management via Motor.

Exposes:
    - ``lifespan``     – FastAPI lifespan context manager (startup / shutdown).
    - ``get_database`` – dependency that yields the database handle.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import FastAPI

from app.config import settings

logger = logging.getLogger(__name__)

# Module-level state – populated on startup, cleared on shutdown.
_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: connect to MongoDB on startup, close on shutdown."""
    global _client, _database

    logger.info("Connecting to MongoDB at %s …", settings.mongodb_url)
    _client = AsyncIOMotorClient(
        settings.mongodb_url,
        serverSelectionTimeoutMS=5000,
    )

    # Verify the connection is alive
    try:
        await _client.admin.command("ping")
        logger.info("✅  MongoDB connection established.")
    except Exception as exc:
        logger.error("❌  MongoDB ping failed: %s", exc)
        raise

    _database = _client[settings.database_name]

    # Create indexes on the profiles collection (idempotent)
    profiles = _database["profiles"]
    await profiles.create_index("name")
    await profiles.create_index("created_at")
    logger.info("Indexes ensured on 'profiles' collection.")

    yield  # ← application runs here

    # Shutdown
    if _client is not None:
        _client.close()
        logger.info("MongoDB connection closed.")


async def get_database() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """FastAPI dependency – yields the active database handle."""
    if _database is None:
        raise RuntimeError("Database not initialised. Is the lifespan running?")
    yield _database

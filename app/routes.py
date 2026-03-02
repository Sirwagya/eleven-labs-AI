"""
API route for saving child profiles from ElevenLabs Agent tool calls.

POST /api/save-profile
    - Validates the ChildProfile JSON body.
    - Inserts into MongoDB with a created_at timestamp.
    - Returns success response with the inserted document ID.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.models import ChildProfile, SaveProfileResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["profiles"])


# ── Endpoint ─────────────────────────────────────────────────────


@router.post(
    "/save-profile",
    response_model=SaveProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Save child profile from ElevenLabs Agent",
    description=(
        "Receives a structured child profile from the ElevenLabs Agent "
        "save_child_profile tool and persists it in MongoDB."
    ),
)
async def save_profile(
    profile: ChildProfile,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> SaveProfileResponse:
    """Validate, enrich, and store a child profile."""
    logger.info("Received profile for: %s (age %d)", profile.name, profile.age)

    try:
        doc = profile.to_mongo_dict()
        result = await db["profiles"].insert_one(doc)

        logger.info(
            "✅  Saved profile %s for %s", result.inserted_id, profile.name
        )

        return SaveProfileResponse(
            status="success",
            id=str(result.inserted_id),
        )

    except Exception as exc:
        logger.exception("❌  Failed to save profile for %s", profile.name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save profile: {exc}",
        ) from exc

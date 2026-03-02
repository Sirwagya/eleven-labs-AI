"""
Pydantic models for request validation and MongoDB document schema.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Incoming request body ────────────────────────────────────────


class ChildProfile(BaseModel):
    """
    Structured child profile sent by the ElevenLabs Agent
    via the save_child_profile server tool.
    """

    model_config = {"extra": "forbid"}

    name: str = Field(..., min_length=1, description="Child's name")
    age: int = Field(..., gt=0, description="Child's age (must be positive)")
    gender: Literal["boy", "girl"] = Field(..., description="Boy or Girl")
    interests: list[str] = Field(
        default_factory=list,
        description="List of interests / hobbies",
    )

    def to_mongo_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict with a UTC created_at timestamp."""
        data = self.model_dump()
        data["created_at"] = datetime.now(timezone.utc)
        return data


# ── API response schema ──────────────────────────────────────────


class SaveProfileResponse(BaseModel):
    """Response returned after successfully saving a profile."""

    status: str = "success"
    id: str

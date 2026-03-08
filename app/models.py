"""
Pydantic models for request validation and MongoDB document schema.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Order ID generator ───────────────────────────────────────────


def generate_order_id() -> str:
    """Generate a unique order ID with prefix 'OUM' + 8 random digits."""
    digits = random.randint(10_000_000, 99_999_999)
    return f"OUM{digits}"


# ── Incoming request body ────────────────────────────────────────


class ChildProfile(BaseModel):
    """
    Structured child profile sent by the ElevenLabs Agent
    via the save_child_profile server tool.
    """

    model_config = {"extra": "forbid"}

    name: str = Field(..., min_length=1, max_length=100, description="Child's name")
    age: int = Field(..., gt=0, le=18, description="Child's age (1–18)")
    gender: Literal["boy", "girl"] = Field(..., description="Boy or Girl")
    order_type: Literal["story book", "movie"] = Field(
        ..., description="Type of order: 'story book' or 'movie'"
    )
    interests: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="List of interests / hobbies (max 10)",
    )

    def to_mongo_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict with order_id and created_at timestamp."""
        data = self.model_dump()
        data["order_id"] = generate_order_id()
        data["created_at"] = datetime.now(timezone.utc)
        return data


# ── API response schema ──────────────────────────────────────────


class SaveProfileResponse(BaseModel):
    """Response returned after successfully saving a profile."""

    status: str = "success"
    order_id: str = Field(..., description="Custom order ID (e.g. OUM12345678)")


# ── Order / Profile Lookup ───────────────────────────────────────


class OrderDetailsResponse(BaseModel):
    """A single profile/order document returned to the caller."""

    order_id: str = Field(..., description="Custom order ID (e.g. OUM12345678)")
    name: str
    age: int
    gender: str
    order_type: str = Field(..., description="Type of order: story book or movie")
    interests: list[str] = []
    created_at: str = Field(
        ..., description="UTC timestamp when the profile was created"
    )


class OrderLookupResponse(BaseModel):
    """Wrapper returned by the GET order-details endpoint."""

    status: str = "success"
    result: OrderDetailsResponse | None = None


# ── Update / Cancel ──────────────────────────────────────────────


class UpdateProfileRequest(BaseModel):
    """
    Partial-update body for an existing profile.
    Only the fields that are provided will be updated.
    """

    model_config = {"extra": "forbid"}

    order_id: str = Field(..., description="Custom order ID (e.g. OUM12345678)")
    name: str | None = Field(None, min_length=1, max_length=100, description="New child name")
    age: int | None = Field(None, gt=0, le=18, description="New age (1–18)")
    gender: Literal["boy", "girl"] | None = Field(None, description="New gender")
    order_type: Literal["story book", "movie"] | None = Field(
        None, description="New order type"
    )
    interests: list[str] | None = Field(None, max_length=10, description="New interests list (max 10)")


class UpdateProfileResponse(BaseModel):
    """Response after successfully updating a profile."""

    status: str = "success"
    message: str
    updated_fields: list[str] = Field(
        default_factory=list,
        description="List of field names that were updated",
    )


class CancelOrderResponse(BaseModel):
    """Response after successfully cancelling (deleting) an order."""

    status: str = "success"
    message: str

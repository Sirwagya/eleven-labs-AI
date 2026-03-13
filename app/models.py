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


class Address(BaseModel):
    """Delivery address of the user."""

    pincode: str = Field(..., description="Postal code or pincode")
    Country: str = Field(..., description="Country")
    State: str = Field(..., description="State or province")
    city: str = Field(..., description="City")
    locality: str = Field(..., description="Locality, street, or neighborhood")


class ChildProfile(BaseModel):
    """
    Structured child profile sent by the ElevenLabs Agent
    via the save_child_profile server tool.
    """

    model_config = {"extra": "forbid"}

    parent_name: str = Field(..., min_length=1, max_length=100, description="Parent's name")
    phone_number: str = Field(..., description="Phone number (important)")
    email: str | None = Field(None, description="Email address (optional)")
    address: Address = Field(..., description="User's delivery address")

    name: str = Field(..., min_length=1, max_length=100, description="Child's name")
    age: int = Field(..., gt=0, le=18, description="Child's age (1–18)")
    gender: Literal["boy", "girl"] = Field(..., description="Boy or Girl")
    order_type: Literal["story book", "movie", "combo story book + animated movie"] = Field(
        ..., description="Type of order: 'story book', 'movie', or 'combo story book + animated movie'"
    )
    interests: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="List of interests / hobbies (max 10)",
    )
    character: str | None = Field(None, description="Child's character qualities (e.g., brave, kind)")
    
    extra_message: str | None = Field(None, description="Extra message (optional)")
    status: str = Field("pending", description="Order status")

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
    parent_name: str
    phone_number: str | None = None
    email: str | None = None
    address: Address | None = None

    name: str
    age: int
    gender: str
    order_type: str = Field(..., description="Type of order: story book, movie, or combo story book + animated movie")
    interests: list[str] = []
    character: str | None = None

    extra_message: str | None = None
    status: str = "pending"
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
    parent_name: str | None = Field(None, min_length=1, max_length=100, description="New parent name")
    phone_number: str | None = Field(None, description="New phone number")
    email: str | None = Field(None, description="New email address")
    address: Address | None = Field(None, description="New delivery address")

    name: str | None = Field(None, min_length=1, max_length=100, description="New child name")
    age: int | None = Field(None, gt=0, le=18, description="New age (1–18)")
    gender: Literal["boy", "girl"] | None = Field(None, description="New gender")
    order_type: Literal["story book", "movie", "combo story book + animated movie"] | None = Field(
        None, description="New order type"
    )
    interests: list[str] | None = Field(None, max_length=10, description="New interests list (max 10)")
    character: str | None = Field(None, description="New character qualities")

    extra_message: str | None = Field(None, description="New extra message")
    status: str | None = Field(None, description="New order status")


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

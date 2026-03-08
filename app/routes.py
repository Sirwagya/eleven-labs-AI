"""
API routes for managing child profiles via ElevenLabs Agent tool calls.

POST   /api/save-profile       – Create a new child profile.
GET    /api/get-order-details   – Look up a profile by order_id only.
PUT    /api/update-order        – Update fields on an existing profile.
DELETE /api/cancel-order        – Delete a profile (cancel the order).
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.models import (
    CancelOrderResponse,
    ChildProfile,
    OrderDetailsResponse,
    OrderLookupResponse,
    SaveProfileResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["profiles"])


# ── Helpers ──────────────────────────────────────────────────────


def _doc_to_response(doc: dict) -> OrderDetailsResponse:
    """Convert a raw MongoDB document to an OrderDetailsResponse."""
    return OrderDetailsResponse(
        order_id=doc.get("order_id", ""),
        name=doc.get("name", ""),
        age=doc.get("age", 0),
        gender=doc.get("gender", ""),
        order_type=doc.get("order_type", ""),
        interests=doc.get("interests", []),
        created_at=doc["created_at"].isoformat() if doc.get("created_at") else "",
    )


def _validate_order_id(order_id: str) -> str:
    """Validate that the order_id matches the OUM + 8 digit format."""
    if not order_id or not order_id.startswith("OUM") or len(order_id) != 11:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid order_id format: '{order_id}'. Expected format: OUM followed by 8 digits (e.g. OUM12345678).",
        )
    return order_id


# ── POST: Save Profile ──────────────────────────────────────────


@router.post(
    "/save-profile",
    response_model=SaveProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save child profile from ElevenLabs Agent",
    description=(
        "Receives a structured child profile from the ElevenLabs Agent "
        "save_child_profile tool and persists it in MongoDB. "
        "Returns a custom order ID (OUM + 8 digits)."
    ),
)
async def save_profile(
    profile: ChildProfile,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> SaveProfileResponse:
    """Validate, enrich, and store a child profile."""
    logger.info("Received profile for: %s (age %d)", profile.name, profile.age)

    try:
        collection = db["profiles"]

        # ── Duplicate check (case-insensitive name + age + gender + order_type)
        pattern = re.compile(f"^{re.escape(profile.name)}$", re.IGNORECASE)
        existing = await collection.find_one({
            "name": pattern,
            "age": profile.age,
            "gender": profile.gender,
            "order_type": profile.order_type,
        })

        if existing:
            logger.info(
                "⚠️  Duplicate profile detected for %s — returning existing order_id %s",
                profile.name, existing.get("order_id"),
            )
            return SaveProfileResponse(
                status="already_exists",
                order_id=existing.get("order_id", ""),
            )

        doc = profile.to_mongo_dict()

        # Ensure unique order_id (retry on collision)
        for _ in range(5):
            if not await collection.find_one({"order_id": doc["order_id"]}):
                break
            from app.models import generate_order_id
            doc["order_id"] = generate_order_id()

        result = await collection.insert_one(doc)

        logger.info(
            "✅  Saved profile %s (order_id=%s) for %s",
            result.inserted_id, doc["order_id"], profile.name,
        )

        return SaveProfileResponse(
            status="success",
            order_id=doc["order_id"],
        )

    except Exception as exc:
        logger.exception("❌  Failed to save profile for %s", profile.name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred. Please try again later.",
        ) from exc


# ── GET: Order Lookup (by order_id only) ─────────────────────────


@router.get(
    "/get-order-details",
    response_model=OrderLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Get order/profile details by order ID",
    description=(
        "Retrieves a saved child profile from MongoDB by its order ID "
        "(format: OUM + 8 digits). Name-based lookup is not supported."
    ),
)
async def get_order_details(
    order_id: str = Query(
        ..., description="Custom order ID (e.g. OUM12345678)"
    ),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> OrderLookupResponse:
    """Look up order/profile details by order_id."""

    _validate_order_id(order_id)

    collection = db["profiles"]

    try:
        doc = await collection.find_one({"order_id": order_id})

        if not doc:
            return OrderLookupResponse(status="not_found", result=None)

        logger.info("🔍  Order lookup order_id=%s → found", order_id)

        return OrderLookupResponse(
            status="success",
            result=_doc_to_response(doc),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("❌  Failed to look up order details")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred. Please try again later.",
        ) from exc


# ── PUT: Update Order ────────────────────────────────────────────


@router.put(
    "/update-order",
    response_model=UpdateProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing order/profile",
    description=(
        "Updates one or more fields on an existing child profile. "
        "The order_id (OUM format) is required; all other fields are optional."
    ),
)
async def update_order(
    body: UpdateProfileRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> UpdateProfileResponse:
    """Partially update a child profile by order_id."""

    _validate_order_id(body.order_id)
    collection = db["profiles"]

    # Build the $set document from only the provided (non-None) fields
    update_fields: dict = {}
    updatable = ["name", "age", "gender", "order_type", "interests"]
    for field in updatable:
        value = getattr(body, field)
        if value is not None:
            update_fields[field] = value

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update. Provide at least one of: name, age, gender, order_type, interests.",
        )

    # Add an updated_at timestamp
    update_fields["updated_at"] = datetime.now(timezone.utc)

    try:
        result = await collection.update_one(
            {"order_id": body.order_id},
            {"$set": update_fields},
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No order found with id '{body.order_id}'.",
            )

        changed = [f for f in update_fields if f != "updated_at"]
        logger.info("✏️  Updated order %s — fields: %s", body.order_id, changed)

        return UpdateProfileResponse(
            status="success",
            message=f"Order {body.order_id} updated successfully.",
            updated_fields=changed,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("❌  Failed to update order %s", body.order_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred. Please try again later.",
        ) from exc


# ── DELETE: Cancel Order ─────────────────────────────────────────


@router.delete(
    "/cancel-order",
    response_model=CancelOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel (delete) an order",
    description=(
        "Permanently deletes a child profile from the database. "
        "Requires the order_id (OUM format)."
    ),
)
async def cancel_order(
    order_id: str = Query(
        ..., description="Custom order ID (e.g. OUM12345678) of the order to cancel"
    ),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> CancelOrderResponse:
    """Delete a child profile by order_id."""

    _validate_order_id(order_id)
    collection = db["profiles"]

    try:
        result = await collection.delete_one({"order_id": order_id})

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No order found with id '{order_id}'.",
            )

        logger.info("🗑️  Cancelled order %s", order_id)

        return CancelOrderResponse(
            status="success",
            message=f"Order {order_id} has been cancelled and removed.",
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("❌  Failed to cancel order %s", order_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred. Please try again later.",
        ) from exc

"""
Review management router.
"""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from typing import List
from app.database import get_db
from app.schemas import ReviewCreate, ReviewUpdate, ReviewResponse
from app.services.auth import get_current_user
from app.kafka_client import get_kafka_client
from app.schemas.kafka_events import ReviewCreatedEvent, ReviewUpdatedEvent, ReviewDeletedEvent
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/reviews", tags=["Reviews"])

UPLOAD_DIR = "uploads/review_photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def _build_review_response(review: dict, db) -> dict:
    """Build a review dict with user_name and photos."""
    user = await db.users.find_one({"_id": review.get("user_id")})
    user_name = user["name"] if user else "Unknown"
    photos = await db.review_photos.find({"review_id": review["_id"]}).to_list(None)
    review["user_name"] = user_name
    review["review_photos"] = [p["photo_url"] for p in photos]
    return review


@router.get("/restaurants/{restaurant_id}/reviews", response_model=List[ReviewResponse])
async def get_restaurant_reviews(
    restaurant_id: str,
    db=Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Get all reviews for a restaurant."""
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")

    reviews = await db.reviews.find(
        {"restaurant_id": ObjectId(restaurant_id)}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(None)

    results = []
    for review in reviews:
        review_dict = await _build_review_response(review, db)
        results.append(ReviewResponse.model_validate(review_dict))
    return results


@router.post("/restaurants/{restaurant_id}/reviews", status_code=202)
async def create_review(
    restaurant_id: str,
    review_data: ReviewCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    kafka=Depends(get_kafka_client)
):
    """
    Create a new review (async via Kafka).
    Publishes to review.created topic — worker writes to MongoDB.
    Returns 202 Accepted.
    """
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")

    existing = await db.reviews.find_one({
        "restaurant_id": ObjectId(restaurant_id),
        "user_id": current_user["_id"]
    })
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already reviewed this restaurant")

    # Generate review ID upfront so we can return it immediately
    review_id = str(ObjectId())

    event = ReviewCreatedEvent(
        review_id=review_id,
        restaurant_id=restaurant_id,
        user_id=str(current_user["_id"]),
        rating=review_data.rating,
        review_text=review_data.review_text,
        photos=review_data.photos if hasattr(review_data, "photos") and review_data.photos else []
    )

    await kafka.publish_event(
        topic="review.created",
        event=event.model_dump(mode="json"),
        key=review_id
    )

    return {
        "status": "pending",
        "message": "Review is being processed",
        "review_id": review_id,
        "restaurant_id": restaurant_id
    }


@router.put("/{review_id}", status_code=202)
async def update_review(
    review_id: str,
    review_data: ReviewUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    kafka=Depends(get_kafka_client)
):
    """
    Update a review (async via Kafka).
    Publishes to review.updated topic — worker writes to MongoDB.
    Returns 202 Accepted.
    """
    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review["user_id"] != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    event = ReviewUpdatedEvent(
        review_id=review_id,
        restaurant_id=str(review["restaurant_id"]),
        user_id=str(current_user["_id"]),
        rating=review_data.rating if hasattr(review_data, "rating") else None,
        review_text=review_data.review_text if hasattr(review_data, "review_text") else None,
        photos=review_data.photos if hasattr(review_data, "photos") else None
    )

    await kafka.publish_event(
        topic="review.updated",
        event=event.model_dump(mode="json"),
        key=review_id
    )

    return {
        "status": "pending",
        "message": "Review update is being processed",
        "review_id": review_id
    }


@router.delete("/{review_id}", status_code=202)
async def delete_review(
    review_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    kafka=Depends(get_kafka_client)
):
    """
    Delete a review (async via Kafka).
    Publishes to review.deleted topic — worker deletes from MongoDB.
    Returns 202 Accepted.
    """
    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review["user_id"] != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    event = ReviewDeletedEvent(
        review_id=review_id,
        restaurant_id=str(review["restaurant_id"]),
        user_id=str(current_user["_id"])
    )

    await kafka.publish_event(
        topic="review.deleted",
        event=event.model_dump(mode="json"),
        key=review_id
    )

    return {
        "status": "pending",
        "message": "Review deletion is being processed",
        "review_id": review_id
    }


@router.post("/{review_id}/photos")
async def upload_review_photo(
    review_id: str,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Upload a photo for a review (own reviews only)."""
    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review["user_id"] != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only JPEG, PNG, GIF, WEBP allowed")

    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    photo_url = f"/uploads/review_photos/{filename}"
    await db.review_photos.insert_one({
        "review_id": ObjectId(review_id),
        "photo_url": photo_url,
        "created_at": datetime.utcnow()
    })
    return {"photo_url": photo_url}

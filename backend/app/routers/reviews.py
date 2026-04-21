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


@router.post("/restaurants/{restaurant_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    restaurant_id: str,
    review_data: ReviewCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Create a new review."""
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")

    existing = await db.reviews.find_one({
        "restaurant_id": ObjectId(restaurant_id),
        "user_id": current_user["_id"]
    })
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already reviewed this restaurant")

    new_review = {
        "restaurant_id": ObjectId(restaurant_id),
        "user_id": current_user["_id"],
        "rating": review_data.rating,
        "review_text": review_data.review_text,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await db.reviews.insert_one(new_review)
    new_review["_id"] = result.inserted_id
    review_dict = await _build_review_response(new_review, db)
    return ReviewResponse.model_validate(review_dict)


@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: str,
    review_data: ReviewUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Update a review (own reviews only)."""
    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review["user_id"] != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    update_fields = review_data.model_dump(exclude_unset=True)
    update_fields["updated_at"] = datetime.utcnow()
    await db.reviews.update_one({"_id": ObjectId(review_id)}, {"$set": update_fields})

    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    review_dict = await _build_review_response(review, db)
    return ReviewResponse.model_validate(review_dict)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Delete a review (own reviews only)."""
    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review["user_id"] != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    await db.reviews.delete_one({"_id": ObjectId(review_id)})


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
from app.models import to_str_id
from bson import ObjectId
"""
User history router for tracking reviews and restaurant submissions.
"""
from fastapi import APIRouter, Depends
from typing import List
from app.database import get_db
from app.schemas import ReviewResponse, RestaurantResponse
from app.services.auth import get_current_user
from app.routers.restaurants import calculate_restaurant_stats
from bson import ObjectId

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/reviews", response_model=List[ReviewResponse])
async def get_user_review_history(
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Get all reviews written by the current user."""
    reviews = await db.reviews.find(
        {"user_id": ObjectId(current_user["id"])}
    ).sort("created_at", -1).to_list(None)

    results = []
    for review in reviews:
        restaurant = await db.restaurants.find_one({"_id": review.get("restaurant_id")})
        photos = await db.review_photos.find({"review_id": review["_id"]}).to_list(None)
        review["user_name"] = current_user.get("name", "Unknown")
        review["restaurant_name"] = restaurant["name"] if restaurant else "Unknown Restaurant"
        review["review_photos"] = [p["photo_url"] for p in photos]
        results.append(ReviewResponse.model_validate(to_str_id(review)))
    return results


@router.get("/restaurants", response_model=List[RestaurantResponse])
async def get_user_restaurant_history(
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Get all restaurants added by the current user."""
    restaurants = await db.restaurants.find(
        {"owner_id": ObjectId(current_user["id"])}
    ).sort("created_at", -1).to_list(None)

    results = []
    for restaurant in restaurants:
        stats = await calculate_restaurant_stats(restaurant["_id"], db)
        restaurant.update(stats)
        results.append(RestaurantResponse.model_validate(to_str_id(restaurant)))
    return results
from app.models import to_str_id
"""
Owner-specific router for restaurant management and analytics.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.database import get_db
from app.schemas import RestaurantResponse, ReviewResponse, RestaurantClaimCreate, RestaurantClaimResponse
from app.services.auth import get_current_owner, get_current_user
from app.routers.restaurants import calculate_restaurant_stats
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/owner", tags=["Owner"])


def _simple_sentiment(rating: int) -> str:
    if rating >= 4:
        return "positive"
    elif rating == 3:
        return "neutral"
    else:
        return "negative"


@router.get("/restaurants", response_model=List[RestaurantResponse])
async def get_owned_restaurants(
    current_user=Depends(get_current_owner),
    db=Depends(get_db)
):
    """Get all restaurants owned by the current user."""
    restaurants = await db.restaurants.find({"owner_id": ObjectId(current_user["id"])}).to_list(None)
    results = []
    for r in restaurants:
        stats = await calculate_restaurant_stats(r["_id"], db)
        r.update(stats)
        results.append(RestaurantResponse.model_validate(to_str_id(r)))
    return results


@router.get("/dashboard")
async def get_owner_dashboard(
    current_user=Depends(get_current_owner),
    db=Depends(get_db)
):
    """Get aggregated dashboard stats across all owned restaurants."""
    restaurants = await db.restaurants.find({"owner_id": ObjectId(current_user["id"])}).to_list(None)
    restaurant_ids = [r["_id"] for r in restaurants]

    if not restaurant_ids:
        return {
            "total_restaurants": 0, "total_views": 0, "total_reviews": 0,
            "average_rating": None,
            "sentiment": {"positive": 0, "neutral": 0, "negative": 0, "overall": "N/A"},
            "recent_reviews": [],
        }

    total_views = sum(r.get("view_count") or 0 for r in restaurants)
    all_reviews = await db.reviews.find({"restaurant_id": {"$in": restaurant_ids}}).to_list(None)
    total_reviews = len(all_reviews)
    ratings = [r["rating"] for r in all_reviews if "rating" in r]
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None

    sentiment = {"positive": 0, "neutral": 0, "negative": 0}
    for review in all_reviews:
        s = _simple_sentiment(review["rating"])
        sentiment[s] += 1

    if total_reviews > 0:
        if sentiment["positive"] > sentiment["negative"] * 2:
            sentiment["overall"] = "Positive"
        elif sentiment["negative"] > sentiment["positive"]:
            sentiment["overall"] = "Negative"
        else:
            sentiment["overall"] = "Mixed"
    else:
        sentiment["overall"] = "N/A"

    recent_raw = await db.reviews.find(
        {"restaurant_id": {"$in": restaurant_ids}}
    ).sort("created_at", -1).limit(5).to_list(None)

    recent_reviews = []
    for r in recent_raw:
        user = await db.users.find_one({"_id": r.get("user_id")})
        restaurant = await db.restaurants.find_one({"_id": r.get("restaurant_id")})
        recent_reviews.append({
            "id": str(r["_id"]),
            "rating": r.get("rating"),
            "review_text": r.get("review_text"),
            "created_at": r.get("created_at"),
            "user_name": user["name"] if user else "Unknown",
            "restaurant_name": restaurant["name"] if restaurant else "Unknown",
        })

    return {
        "total_restaurants": len(restaurants),
        "total_views": total_views,
        "total_reviews": total_reviews,
        "average_rating": avg_rating,
        "sentiment": sentiment,
        "recent_reviews": recent_reviews,
    }


@router.get("/restaurants/{restaurant_id}/analytics")
async def get_restaurant_analytics(
    restaurant_id: str,
    current_user=Depends(get_current_owner),
    db=Depends(get_db)
):
    """Get analytics for a specific restaurant."""
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    if restaurant.get("owner_id") != ObjectId(current_user["id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    all_reviews = await db.reviews.find({"restaurant_id": ObjectId(restaurant_id)}).to_list(None)
    stats = await calculate_restaurant_stats(ObjectId(restaurant_id), db)

    sentiment = {"positive": 0, "neutral": 0, "negative": 0}
    for r in all_reviews:
        s = _simple_sentiment(r["rating"])
        sentiment[s] += 1

    rating_distribution = {}
    for r in all_reviews:
        key = str(r["rating"])
        rating_distribution[key] = rating_distribution.get(key, 0) + 1

    recent_reviews = await db.reviews.find(
        {"restaurant_id": ObjectId(restaurant_id)}
    ).sort("created_at", -1).limit(5).to_list(None)

    return {
        "restaurant_id": restaurant_id,
        "restaurant_name": restaurant["name"],
        "average_rating": stats["average_rating"],
        "total_reviews": stats["review_count"],
        "view_count": restaurant.get("view_count") or 0,
        "rating_distribution": rating_distribution,
        "sentiment": sentiment,
        "recent_reviews": [
            {"id": str(r["_id"]), "rating": r["rating"], "review_text": r.get("review_text"), "created_at": r.get("created_at")}
            for r in recent_reviews
        ]
    }


@router.get("/restaurants/{restaurant_id}/reviews", response_model=List[ReviewResponse])
async def get_restaurant_reviews_owner(
    restaurant_id: str,
    current_user=Depends(get_current_owner),
    db=Depends(get_db)
):
    """Get all reviews for an owned restaurant (read-only)."""
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    if restaurant.get("owner_id") != ObjectId(current_user["id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    reviews = await db.reviews.find({"restaurant_id": ObjectId(restaurant_id)}).to_list(None)
    results = []
    for review in reviews:
        user = await db.users.find_one({"_id": review.get("user_id")})
        review["user_name"] = user["name"] if user else "Unknown"
        review["review_photos"] = []
        results.append(ReviewResponse.model_validate(to_str_id(review)))
    return results


# ============= Restaurant Claims =============

@router.get("/claim/search")
async def search_restaurants_for_claim(
    q: str = Query(..., min_length=1),
    current_user=Depends(get_current_owner),
    db=Depends(get_db)
):
    """Search unclaimed restaurants for claiming."""
    restaurants = await db.restaurants.find({
        "owner_id": None,
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"zip_code": q}
        ]
    }).limit(10).to_list(None)

    results = []
    for r in restaurants:
        stats = await calculate_restaurant_stats(r["_id"], db)
        results.append({
            "id": str(r["_id"]), "name": r["name"],
            "cuisine_type": r.get("cuisine_type"), "price_range": r.get("price_range"),
            "city": r.get("city"), "state": r.get("state"),
            "average_rating": stats["average_rating"], "review_count": stats["review_count"],
        })
    return results


@router.post("/claims", response_model=RestaurantClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim(
    claim_data: RestaurantClaimCreate,
    current_user=Depends(get_current_owner),
    db=Depends(get_db)
):
    """Submit a claim for an existing restaurant."""
    restaurant = await db.restaurants.find_one({"_id": ObjectId(claim_data.restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    if restaurant.get("owner_id"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Restaurant already claimed")

    existing = await db.restaurant_claims.find_one({
        "restaurant_id": ObjectId(claim_data.restaurant_id),
        "owner_id": ObjectId(current_user["id"]),
        "status": "pending"
    })
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already have a pending claim")

    claim = {
        "restaurant_id": ObjectId(claim_data.restaurant_id),
        "owner_id": ObjectId(current_user["id"]),
        "status": "approved",
        "created_at": datetime.utcnow()
    }
    result = await db.restaurant_claims.insert_one(claim)
    await db.restaurants.update_one(
        {"_id": ObjectId(claim_data.restaurant_id)},
        {"$set": {"owner_id": ObjectId(current_user["id"])}}
    )
    claim["_id"] = result.inserted_id
    return RestaurantClaimResponse.model_validate(to_str_id(claim))


@router.get("/claims", response_model=List[RestaurantClaimResponse])
async def get_my_claims(
    current_user=Depends(get_current_owner),
    db=Depends(get_db)
):
    """Get all claims submitted by the current owner."""
    claims = await db.restaurant_claims.find({"owner_id": ObjectId(current_user["id"])}).to_list(None)
    return [RestaurantClaimResponse.model_validate(to_str_id(c)) for c in claims]
"""
Owner-specific router for restaurant management and analytics.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from app.database import get_db
from app.models import Restaurant, Review, User, RestaurantClaim
from app.schemas import RestaurantResponse, ReviewResponse, RestaurantClaimCreate, RestaurantClaimResponse
from app.services.auth import get_current_owner, get_current_user
from app.routers.restaurants import calculate_restaurant_stats

router = APIRouter(prefix="/owner", tags=["Owner"])


def _simple_sentiment(rating: int) -> str:
    """Classify a review rating into sentiment category."""
    if rating >= 4:
        return "positive"
    elif rating == 3:
        return "neutral"
    else:
        return "negative"


@router.get("/restaurants", response_model=List[RestaurantResponse])
async def get_owned_restaurants(
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Get all restaurants owned by the current user."""
    restaurants = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).all()
    
    results = []
    for restaurant in restaurants:
        stats = calculate_restaurant_stats(restaurant, db)
        restaurant_dict = restaurant.__dict__.copy()
        restaurant_dict.update(stats)
        results.append(RestaurantResponse.model_validate(restaurant_dict))
    
    return results


@router.get("/dashboard")
async def get_owner_dashboard(
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Get aggregated dashboard stats across all owned restaurants."""
    restaurants = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).all()
    restaurant_ids = [r.id for r in restaurants]
    
    if not restaurant_ids:
        return {
            "total_restaurants": 0,
            "total_views": 0,
            "total_reviews": 0,
            "average_rating": None,
            "sentiment": {"positive": 0, "neutral": 0, "negative": 0, "overall": "N/A"},
            "recent_reviews": [],
        }
    
    # Aggregate stats
    total_views = sum(r.view_count or 0 for r in restaurants)
    
    review_stats = db.query(
        func.count(Review.id).label('count'),
        func.avg(Review.rating).label('avg')
    ).filter(Review.restaurant_id.in_(restaurant_ids)).first()
    
    total_reviews = review_stats.count or 0
    avg_rating = float(review_stats.avg) if review_stats.avg else None
    
    # Sentiment analysis from ratings
    all_reviews = db.query(Review).filter(Review.restaurant_id.in_(restaurant_ids)).all()
    sentiment = {"positive": 0, "neutral": 0, "negative": 0}
    for review in all_reviews:
        s = _simple_sentiment(review.rating)
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
    
    # Recent reviews across all restaurants
    recent = db.query(Review).filter(
        Review.restaurant_id.in_(restaurant_ids)
    ).order_by(Review.created_at.desc()).limit(5).all()
    
    recent_reviews = []
    for r in recent:
        user = db.query(User).filter(User.id == r.user_id).first()
        restaurant = db.query(Restaurant).filter(Restaurant.id == r.restaurant_id).first()
        recent_reviews.append({
            "id": r.id,
            "rating": r.rating,
            "review_text": r.review_text,
            "created_at": r.created_at,
            "user_name": user.name if user else "Unknown",
            "restaurant_name": restaurant.name if restaurant else "Unknown",
        })
    
    return {
        "total_restaurants": len(restaurants),
        "total_views": total_views,
        "total_reviews": total_reviews,
        "average_rating": round(avg_rating, 1) if avg_rating else None,
        "sentiment": sentiment,
        "recent_reviews": recent_reviews,
    }


@router.get("/restaurants/{restaurant_id}/analytics")
async def get_restaurant_analytics(
    restaurant_id: int,
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Get analytics for a specific restaurant."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    if restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view analytics for this restaurant")
    
    rating_distribution = db.query(
        Review.rating, func.count(Review.id).label('count')
    ).filter(Review.restaurant_id == restaurant_id).group_by(Review.rating).all()
    
    recent_reviews = db.query(Review).filter(
        Review.restaurant_id == restaurant_id
    ).order_by(Review.created_at.desc()).limit(5).all()
    
    stats = calculate_restaurant_stats(restaurant, db)
    
    # Sentiment for this restaurant
    all_reviews = db.query(Review).filter(Review.restaurant_id == restaurant_id).all()
    sentiment = {"positive": 0, "neutral": 0, "negative": 0}
    for r in all_reviews:
        s = _simple_sentiment(r.rating)
        sentiment[s] += 1
    
    return {
        "restaurant_id": restaurant_id,
        "restaurant_name": restaurant.name,
        "average_rating": stats['average_rating'],
        "total_reviews": stats['review_count'],
        "view_count": restaurant.view_count or 0,
        "rating_distribution": {str(rating): count for rating, count in rating_distribution},
        "sentiment": sentiment,
        "recent_reviews": [
            {"id": r.id, "rating": r.rating, "review_text": r.review_text, "created_at": r.created_at}
            for r in recent_reviews
        ]
    }


@router.get("/restaurants/{restaurant_id}/reviews", response_model=List[ReviewResponse])
async def get_restaurant_reviews_owner(
    restaurant_id: int,
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Get all reviews for an owned restaurant (read-only)."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    if restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view reviews for this restaurant")
    
    reviews = db.query(Review).filter(Review.restaurant_id == restaurant_id).all()
    
    results = []
    for review in reviews:
        user = db.query(User).filter(User.id == review.user_id).first()
        review_dict = review.__dict__.copy()
        review_dict['user_name'] = user.name if user else "Unknown"
        review_dict['review_photos'] = []
        results.append(ReviewResponse.model_validate(review_dict))
    
    return results


# ============= Restaurant Claims =============

@router.get("/claim/search")
async def search_restaurants_for_claim(
    q: str = Query(..., min_length=1, description="Search by restaurant name or zip code"),
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Search unclaimed restaurants for claiming."""
    restaurants = db.query(Restaurant).filter(
        Restaurant.owner_id.is_(None),
        or_(
            Restaurant.name.ilike(f"%{q}%"),
            Restaurant.zip_code == q,
        )
    ).limit(10).all()
    
    results = []
    for r in restaurants:
        stats = calculate_restaurant_stats(r, db)
        results.append({
            "id": r.id,
            "name": r.name,
            "cuisine_type": r.cuisine_type,
            "price_range": r.price_range,
            "city": r.city,
            "state": r.state,
            "average_rating": stats['average_rating'],
            "review_count": stats['review_count'],
        })
    return results


@router.post("/claims", response_model=RestaurantClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim(
    claim_data: RestaurantClaimCreate,
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Submit a claim for an existing restaurant."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == claim_data.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    
    if restaurant.owner_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Restaurant already has an owner")
    
    existing_claim = db.query(RestaurantClaim).filter(
        RestaurantClaim.restaurant_id == claim_data.restaurant_id,
        RestaurantClaim.owner_id == current_user.id,
        RestaurantClaim.status == 'pending'
    ).first()
    if existing_claim:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already have a pending claim for this restaurant")
    
    claim = RestaurantClaim(restaurant_id=claim_data.restaurant_id, owner_id=current_user.id)
    db.add(claim)
    db.commit()
    db.refresh(claim)
    
    # Auto-approve for now
    claim.status = 'approved'
    restaurant.owner_id = current_user.id
    db.commit()
    db.refresh(claim)
    
    return RestaurantClaimResponse.model_validate(claim)


@router.get("/claims", response_model=List[RestaurantClaimResponse])
async def get_my_claims(
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Get all claims submitted by the current owner."""
    claims = db.query(RestaurantClaim).filter(RestaurantClaim.owner_id == current_user.id).all()
    return [RestaurantClaimResponse.model_validate(c) for c in claims]

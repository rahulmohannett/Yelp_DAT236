"""
User history router for tracking reviews and restaurant submissions.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Review, Restaurant, User
from app.schemas import ReviewResponse, RestaurantResponse
from app.services.auth import get_current_user
from app.routers.restaurants import calculate_restaurant_stats
from app.models import Review, Restaurant, User, ReviewPhoto

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/reviews", response_model=List[ReviewResponse])
async def get_user_review_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all reviews written by the current user."""
    reviews = db.query(Review).filter(
        Review.user_id == current_user.id
    ).order_by(Review.created_at.desc()).all()
    
    results = []
    for review in reviews:
        restaurant = db.query(Restaurant).filter(Restaurant.id == review.restaurant_id).first()
        photos = db.query(ReviewPhoto.photo_url).filter(ReviewPhoto.review_id == review.id).all()
        review_dict = review.__dict__.copy()
        review_dict['user_name'] = current_user.name
        review_dict['restaurant_name'] = restaurant.name if restaurant else "Unknown Restaurant"
        review_dict['review_photos'] = [p.photo_url for p in photos]
        results.append(ReviewResponse.model_validate(review_dict))
    
    return results


@router.get("/restaurants", response_model=List[RestaurantResponse])
async def get_user_restaurant_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all restaurants added by the current user."""
    restaurants = db.query(Restaurant).filter(
        Restaurant.owner_id == current_user.id
    ).order_by(Restaurant.created_at.desc()).all()
    
    results = []
    for restaurant in restaurants:
        stats = calculate_restaurant_stats(restaurant, db)
        restaurant_dict = restaurant.__dict__.copy()
        restaurant_dict.update(stats)
        results.append(RestaurantResponse.model_validate(restaurant_dict))
    
    return results

"""
Favorites/bookmarks router.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Favorite, Restaurant, User
from app.schemas import FavoriteCreate, RestaurantResponse
from app.services.auth import get_current_user
from app.routers.restaurants import calculate_restaurant_stats

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("", response_model=List[RestaurantResponse])
async def get_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's favorite restaurants."""
    favorites = db.query(Favorite).filter(Favorite.user_id == current_user.id).all()
    
    results = []
    for favorite in favorites:
        restaurant = db.query(Restaurant).filter(Restaurant.id == favorite.restaurant_id).first()
        if restaurant:
            stats = calculate_restaurant_stats(restaurant, db)
            restaurant_dict = restaurant.__dict__.copy()
            restaurant_dict.update(stats)
            results.append(RestaurantResponse.model_validate(restaurant_dict))
    
    return results


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite_data: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a restaurant to favorites."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == favorite_data.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.restaurant_id == favorite_data.restaurant_id
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Restaurant already in favorites")
    
    db.add(Favorite(user_id=current_user.id, restaurant_id=favorite_data.restaurant_id))
    db.commit()
    return {"message": "Restaurant added to favorites"}


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    restaurant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a restaurant from favorites."""
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.restaurant_id == restaurant_id
    ).first()
    if not favorite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")
    
    db.delete(favorite)
    db.commit()

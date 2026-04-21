"""
Favorites/bookmarks router.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.database import get_db
from app.schemas import FavoriteCreate, RestaurantResponse
from app.services.auth import get_current_user
from app.routers.restaurants import calculate_restaurant_stats
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("", response_model=List[RestaurantResponse])
async def get_favorites(
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Get user's favorite restaurants."""
    favorites = await db.favorites.find({"user_id": current_user["_id"]}).to_list(None)
    results = []
    for favorite in favorites:
        restaurant = await db.restaurants.find_one({"_id": favorite["restaurant_id"]})
        if restaurant:
            stats = await calculate_restaurant_stats(restaurant["_id"], db)
            restaurant.update(stats)
            results.append(RestaurantResponse.model_validate(restaurant))
    return results


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite_data: FavoriteCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Add a restaurant to favorites."""
    restaurant = await db.restaurants.find_one({"_id": ObjectId(favorite_data.restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")

    existing = await db.favorites.find_one({
        "user_id": current_user["_id"],
        "restaurant_id": ObjectId(favorite_data.restaurant_id)
    })
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Restaurant already in favorites")

    await db.favorites.insert_one({
        "user_id": current_user["_id"],
        "restaurant_id": ObjectId(favorite_data.restaurant_id),
        "created_at": datetime.utcnow()
    })
    return {"message": "Restaurant added to favorites"}


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    restaurant_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Remove a restaurant from favorites."""
    favorite = await db.favorites.find_one({
        "user_id": current_user["_id"],
        "restaurant_id": ObjectId(restaurant_id)
    })
    if not favorite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")
    await db.favorites.delete_one({"_id": favorite["_id"]})
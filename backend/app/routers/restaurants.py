"""
Restaurant management router.
"""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from app.database import get_db
from app.models import Restaurant, Review, User, RestaurantPhoto
from app.schemas import RestaurantCreate, RestaurantUpdate, RestaurantResponse
from app.services.auth import get_current_user, get_current_owner

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])

UPLOAD_DIR = "uploads/restaurant_photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def calculate_restaurant_stats(restaurant: Restaurant, db: Session) -> dict:
    """Calculate average rating, review count, and photos for a restaurant."""
    stats = db.query(
        func.avg(Review.rating).label('avg_rating'),
        func.count(Review.id).label('review_count')
    ).filter(Review.restaurant_id == restaurant.id).first()
    
    photos = db.query(RestaurantPhoto.photo_url).filter(
        RestaurantPhoto.restaurant_id == restaurant.id
    ).all()
    
    return {
        'average_rating': float(stats.avg_rating) if stats.avg_rating else None,
        'review_count': stats.review_count or 0,
        'photos': [photo.photo_url for photo in photos]
    }


def _save_photo_urls(restaurant_id: int, photo_urls: List[str], db: Session, replace: bool = False):
    """Save photo URLs to restaurant_photos table. If replace=True, remove existing photos first."""
    if replace:
        db.query(RestaurantPhoto).filter(RestaurantPhoto.restaurant_id == restaurant_id).delete()
    for url in photo_urls:
        if url and url.strip():
            db.add(RestaurantPhoto(restaurant_id=restaurant_id, photo_url=url.strip()))


@router.get("", response_model=List[RestaurantResponse])
async def search_restaurants(
    db: Session = Depends(get_db),
    cuisine: Optional[str] = Query(None),
    price_range: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    keywords: Optional[str] = Query(None, description="Amenities keywords: quiet, family-friendly, wifi, outdoor seating"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Search and browse restaurants with filters."""
    query = db.query(Restaurant)
    
    if cuisine:
        query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))
    if price_range:
        query = query.filter(Restaurant.price_range == price_range)
    if city:
        query = query.filter(Restaurant.city.ilike(f"%{city}%"))
    if zip_code:
        query = query.filter(Restaurant.zip_code == zip_code)
    if search:
        query = query.filter(
            or_(
                Restaurant.name.ilike(f"%{search}%"),
                Restaurant.description.ilike(f"%{search}%")
            )
        )
    if keywords:
        keyword_list = [k.strip().lower() for k in keywords.split(',')]
        for keyword in keyword_list:
            query = query.filter(Restaurant.amenities.contains([keyword]))
    
    restaurants = query.offset(skip).limit(limit).all()
    
    results = []
    for restaurant in restaurants:
        stats = calculate_restaurant_stats(restaurant, db)
        restaurant_dict = restaurant.__dict__.copy()
        restaurant_dict.update(stats)
        results.append(RestaurantResponse.model_validate(restaurant_dict))
    
    return results


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    """Get restaurant details and increment view count."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    
    # Increment view count
    restaurant.view_count = (restaurant.view_count or 0) + 1
    db.commit()
    db.refresh(restaurant)
    
    stats = calculate_restaurant_stats(restaurant, db)
    restaurant_dict = restaurant.__dict__.copy()
    restaurant_dict.update(stats)
    return RestaurantResponse.model_validate(restaurant_dict)


@router.post("", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    restaurant_data: RestaurantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new restaurant (any authenticated user can add listings)."""
    photo_urls = restaurant_data.photo_urls
    restaurant_fields = restaurant_data.model_dump(exclude={'photo_urls'})

    new_restaurant = Restaurant(
        **restaurant_fields,
        owner_id=current_user.id if current_user.role == 'owner' else None
    )
    db.add(new_restaurant)
    db.commit()
    db.refresh(new_restaurant)
    
    if photo_urls:
        _save_photo_urls(new_restaurant.id, photo_urls, db)
        db.commit()
    
    stats = calculate_restaurant_stats(new_restaurant, db)
    restaurant_dict = new_restaurant.__dict__.copy()
    restaurant_dict.update(stats)
    return RestaurantResponse.model_validate(restaurant_dict)


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant(
    restaurant_id: int,
    restaurant_data: RestaurantUpdate,
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Update a restaurant (owner only)."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    if restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this restaurant")
    
    update_fields = restaurant_data.model_dump(exclude_unset=True)
    photo_urls = update_fields.pop('photo_urls', None)

    for key, value in update_fields.items():
        setattr(restaurant, key, value)
    
    if photo_urls is not None:
        _save_photo_urls(restaurant_id, photo_urls, db, replace=True)
    
    db.commit()
    db.refresh(restaurant)
    
    stats = calculate_restaurant_stats(restaurant, db)
    restaurant_dict = restaurant.__dict__.copy()
    restaurant_dict.update(stats)
    return RestaurantResponse.model_validate(restaurant_dict)


@router.post("/{restaurant_id}/photos")
async def upload_restaurant_photo(
    restaurant_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a photo for a restaurant."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only JPEG, PNG, GIF, and WebP images are allowed")
    
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)
    
    photo_url = f"/uploads/restaurant_photos/{filename}"
    photo = RestaurantPhoto(restaurant_id=restaurant_id, photo_url=photo_url)
    db.add(photo)
    db.commit()
    db.refresh(photo)
    
    return {"id": photo.id, "photo_url": photo_url}


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_restaurant(
    restaurant_id: int,
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """Delete a restaurant (owner only)."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    if restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this restaurant")
    
    db.delete(restaurant)
    db.commit()

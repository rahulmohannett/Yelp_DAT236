"""
Restaurant management router.
"""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from typing import List, Optional
from app.database import get_db
from app.schemas import RestaurantCreate, RestaurantUpdate, RestaurantResponse
from app.services.auth import get_current_user, get_current_owner
from app.kafka_client import get_kafka_client
from app.schemas.kafka_events import RestaurantCreatedEvent
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])

UPLOAD_DIR = "uploads/restaurant_photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def calculate_restaurant_stats(restaurant_id, db) -> dict:
    """Calculate average rating, review count, and photos for a restaurant."""
    reviews = await db.reviews.find({"restaurant_id": restaurant_id}).to_list(None)
    ratings = [r["rating"] for r in reviews if "rating" in r]
    avg_rating = sum(ratings) / len(ratings) if ratings else None
    photos = restaurant_id and [r.get("photo_url") for r in await db.restaurant_photos.find({"restaurant_id": restaurant_id}).to_list(None)]
    return {
        "average_rating": avg_rating,
        "review_count": len(ratings),
        "photos": photos or []
    }


@router.get("", response_model=List[RestaurantResponse])
async def search_restaurants(
    db=Depends(get_db),
    cuisine: Optional[str] = Query(None),
    price_range: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    keywords: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Search and browse restaurants with filters."""
    query = {}
    if cuisine:
        query["cuisine_type"] = {"$regex": cuisine, "$options": "i"}
    if price_range:
        query["price_range"] = price_range
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    if zip_code:
        query["zip_code"] = zip_code
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    if keywords:
        keyword_list = [k.strip().lower() for k in keywords.split(",")]
        query["amenities"] = {"$all": keyword_list}

    restaurants = await db.restaurants.find(query).skip(skip).limit(limit).to_list(None)
    results = []
    for r in restaurants:
        stats = await calculate_restaurant_stats(r["_id"], db)
        r.update(stats)
        results.append(RestaurantResponse.model_validate(r))
    return results


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(restaurant_id: str, db=Depends(get_db)):
    """Get restaurant details and increment view count."""
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")

    await db.restaurants.update_one(
        {"_id": ObjectId(restaurant_id)},
        {"$inc": {"view_count": 1}}
    )
    restaurant["view_count"] = (restaurant.get("view_count") or 0) + 1
    stats = await calculate_restaurant_stats(restaurant["_id"], db)
    restaurant.update(stats)
    return RestaurantResponse.model_validate(restaurant)


@router.post("", status_code=202)
async def create_restaurant(
    restaurant_data: RestaurantCreate,
    current_user=Depends(get_current_user),
    kafka=Depends(get_kafka_client)
):
    """
    Create a new restaurant (async via Kafka).
    Publishes to restaurant.created topic — worker writes to MongoDB.
    Returns 202 Accepted.
    """
    restaurant_id = str(ObjectId())

    event = RestaurantCreatedEvent(
        restaurant_id=restaurant_id,
        name=restaurant_data.name,
        cuisine_type=restaurant_data.cuisine_type,
        price_range=restaurant_data.price_range,
        address=restaurant_data.address,
        city=restaurant_data.city,
        state=restaurant_data.state if hasattr(restaurant_data, "state") else None,
        zip_code=restaurant_data.zip_code if hasattr(restaurant_data, "zip_code") else None,
        phone=restaurant_data.phone if hasattr(restaurant_data, "phone") else None,
        website=restaurant_data.website if hasattr(restaurant_data, "website") else None,
        hours=restaurant_data.hours if hasattr(restaurant_data, "hours") else None,
        amenities=restaurant_data.amenities if hasattr(restaurant_data, "amenities") and restaurant_data.amenities else [],
        owner_id=str(current_user["_id"]) if current_user.get("role") == "owner" else None,
        photos=restaurant_data.photo_urls if hasattr(restaurant_data, "photo_urls") and restaurant_data.photo_urls else []
    )

    await kafka.publish_event(
        topic="restaurant.created",
        event=event.model_dump(mode="json"),
        key=restaurant_id
    )

    return {
        "status": "pending",
        "message": "Restaurant is being processed",
        "restaurant_id": restaurant_id
    }


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant(
    restaurant_id: str,
    restaurant_data: RestaurantUpdate,
    current_user=Depends(get_current_owner),
    db=Depends(get_db)
):
    """Update a restaurant (owner only). Direct DB write — no Kafka needed for updates."""
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    if restaurant.get("owner_id") != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    update_fields = restaurant_data.model_dump(exclude_unset=True)
    update_fields["updated_at"] = datetime.utcnow()
    await db.restaurants.update_one({"_id": ObjectId(restaurant_id)}, {"$set": update_fields})

    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    stats = await calculate_restaurant_stats(restaurant["_id"], db)
    restaurant.update(stats)
    return RestaurantResponse.model_validate(restaurant)


@router.post("/{restaurant_id}/photos")
async def upload_restaurant_photo(
    restaurant_id: str,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Upload a photo for a restaurant."""
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")

    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only JPEG, PNG, GIF, WEBP allowed")

    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    photo_url = f"/uploads/restaurant_photos/{filename}"
    await db.restaurant_photos.insert_one({
        "restaurant_id": ObjectId(restaurant_id),
        "photo_url": photo_url,
        "uploaded_at": datetime.utcnow()
    })
    return {"photo_url": photo_url}

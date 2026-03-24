"""
Review management router.
"""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Review, Restaurant, User, ReviewPhoto
from app.schemas import ReviewCreate, ReviewUpdate, ReviewResponse
from app.services.auth import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])

UPLOAD_DIR = "uploads/review_photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _build_review_response(review: Review, db: Session, user_name: str = None) -> dict:
    """Build a review dict with user_name and photos for ReviewResponse."""
    if not user_name:
        user = db.query(User).filter(User.id == review.user_id).first()
        user_name = user.name if user else "Unknown"
    
    photos = db.query(ReviewPhoto.photo_url).filter(
        ReviewPhoto.review_id == review.id
    ).all()
    
    review_dict = review.__dict__.copy()
    review_dict['user_name'] = user_name
    review_dict['review_photos'] = [p.photo_url for p in photos]
    return review_dict


@router.get("/restaurants/{restaurant_id}/reviews", response_model=List[ReviewResponse])
async def get_restaurant_reviews(
    restaurant_id: int,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Get all reviews for a restaurant."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    
    reviews = db.query(Review).filter(
        Review.restaurant_id == restaurant_id
    ).order_by(Review.created_at.desc()).offset(skip).limit(limit).all()
    
    results = []
    for review in reviews:
        review_dict = _build_review_response(review, db)
        results.append(ReviewResponse.model_validate(review_dict))
    
    return results


@router.post("/restaurants/{restaurant_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    restaurant_id: int,
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new review."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    
    existing_review = db.query(Review).filter(
        Review.restaurant_id == restaurant_id,
        Review.user_id == current_user.id
    ).first()
    if existing_review:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already reviewed this restaurant")
    
    new_review = Review(
        restaurant_id=restaurant_id,
        user_id=current_user.id,
        rating=review_data.rating,
        review_text=review_data.review_text
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    
    review_dict = _build_review_response(new_review, db, user_name=current_user.name)
    return ReviewResponse.model_validate(review_dict)


@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: int,
    review_data: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a review (own reviews only)."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this review")
    
    for key, value in review_data.model_dump(exclude_unset=True).items():
        setattr(review, key, value)
    
    db.commit()
    db.refresh(review)
    
    review_dict = _build_review_response(review, db, user_name=current_user.name)
    return ReviewResponse.model_validate(review_dict)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a review (own reviews only)."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this review")
    
    db.delete(review)
    db.commit()


@router.post("/{review_id}/photos")
async def upload_review_photo(
    review_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a photo for a review (own reviews only)."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to add photos to this review")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only JPEG, PNG, GIF, and WebP images are allowed")
    
    # Save file
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)
    
    # Save to DB
    photo_url = f"/uploads/review_photos/{filename}"
    photo = ReviewPhoto(review_id=review_id, photo_url=photo_url)
    db.add(photo)
    db.commit()
    db.refresh(photo)
    
    return {"id": photo.id, "photo_url": photo_url}

"""
Pydantic schemas for Kafka event messages.
Each event type has a defined schema for validation.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================
# REVIEW EVENTS
# ============================================================

class ReviewCreatedEvent(BaseModel):
    """Event published when a review is created."""
    event_type: str = Field(default="review.created", const=True)
    review_id: str = Field(..., description="MongoDB ObjectId as string")
    restaurant_id: str = Field(..., description="MongoDB ObjectId as string")
    user_id: str = Field(..., description="MongoDB ObjectId as string")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5 stars")
    review_text: Optional[str] = None
    photos: List[str] = Field(default_factory=list, description="Photo URLs")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewUpdatedEvent(BaseModel):
    """Event published when a review is updated."""
    event_type: str = Field(default="review.updated", const=True)
    review_id: str = Field(..., description="MongoDB ObjectId as string")
    restaurant_id: str = Field(..., description="MongoDB ObjectId as string")
    user_id: str = Field(..., description="MongoDB ObjectId as string")
    rating: Optional[int] = Field(None, ge=1, le=5)
    review_text: Optional[str] = None
    photos: Optional[List[str]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewDeletedEvent(BaseModel):
    """Event published when a review is deleted."""
    event_type: str = Field(default="review.deleted", const=True)
    review_id: str = Field(..., description="MongoDB ObjectId as string")
    restaurant_id: str = Field(..., description="MongoDB ObjectId as string")
    user_id: str = Field(..., description="MongoDB ObjectId as string")
    deleted_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# RESTAURANT EVENTS
# ============================================================

class RestaurantCreatedEvent(BaseModel):
    """Event published when a restaurant is created."""
    event_type: str = Field(default="restaurant.created", const=True)
    restaurant_id: str = Field(..., description="MongoDB ObjectId as string")
    name: str
    cuisine_type: str
    price_range: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[dict] = None
    amenities: List[str] = Field(default_factory=list)
    owner_id: Optional[str] = None
    photos: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RestaurantUpdatedEvent(BaseModel):
    """Event published when a restaurant is updated."""
    event_type: str = Field(default="restaurant.updated", const=True)
    restaurant_id: str = Field(..., description="MongoDB ObjectId as string")
    name: Optional[str] = None
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[dict] = None
    amenities: Optional[List[str]] = None
    photos: Optional[List[str]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# USER EVENTS (Optional - for future use)
# ============================================================

class UserCreatedEvent(BaseModel):
    """Event published when a user is created."""
    event_type: str = Field(default="user.created", const=True)
    user_id: str = Field(..., description="MongoDB ObjectId as string")
    email: str
    name: str
    role: str  # customer or owner
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserUpdatedEvent(BaseModel):
    """Event published when a user profile is updated."""
    event_type: str = Field(default="user.updated", const=True)
    user_id: str = Field(..., description="MongoDB ObjectId as string")
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# BOOKING STATUS EVENT (for future async feedback)
# ============================================================

class BookingStatusEvent(BaseModel):
    """
    Event published by workers to signal completion.
    Consumers: Frontend services (for async status updates to UI)
    """
    event_type: str = Field(default="booking.status", const=True)
    entity_type: str = Field(..., description="review or restaurant")
    entity_id: str = Field(..., description="MongoDB ObjectId as string")
    status: str = Field(..., description="pending, success, failed")
    message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

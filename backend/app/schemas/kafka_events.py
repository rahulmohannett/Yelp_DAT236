"""
Pydantic schemas for Kafka event messages.
Each event type has a defined schema for validation.
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================
# REVIEW EVENTS
# ============================================================

class ReviewCreatedEvent(BaseModel):
    event_type: Literal["review.created"] = "review.created"
    review_id: str
    restaurant_id: str
    user_id: str
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None
    photos: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewUpdatedEvent(BaseModel):
    event_type: Literal["review.updated"] = "review.updated"
    review_id: str
    restaurant_id: str
    user_id: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    review_text: Optional[str] = None
    photos: Optional[List[str]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewDeletedEvent(BaseModel):
    event_type: Literal["review.deleted"] = "review.deleted"
    review_id: str
    restaurant_id: str
    user_id: str
    deleted_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# RESTAURANT EVENTS
# ============================================================

class RestaurantCreatedEvent(BaseModel):
    event_type: Literal["restaurant.created"] = "restaurant.created"
    restaurant_id: str
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
    event_type: Literal["restaurant.updated"] = "restaurant.updated"
    restaurant_id: str
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
# USER EVENTS
# ============================================================

class UserCreatedEvent(BaseModel):
    event_type: Literal["user.created"] = "user.created"
    user_id: str
    email: str
    name: str
    role: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserUpdatedEvent(BaseModel):
    event_type: Literal["user.updated"] = "user.updated"
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# BOOKING STATUS EVENT
# ============================================================

class BookingStatusEvent(BaseModel):
    event_type: Literal["booking.status"] = "booking.status"
    entity_type: str
    entity_id: str
    status: str
    message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
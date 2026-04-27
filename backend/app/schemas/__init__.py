"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    CUSTOMER = "customer"
    OWNER = "owner"


class ClaimStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ============= User Schemas =============

class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.CUSTOMER
    city: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    about_me: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    languages: Optional[List[str]] = None
    gender: Optional[str] = None
    profile_picture: Optional[str] = None


class UserResponse(UserBase):
    id: str                          # MongoDB ObjectId as string
    role: UserRole
    phone: Optional[str] = None
    about_me: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    languages: Optional[List[str]] = None
    gender: Optional[str] = None
    profile_picture: Optional[str] = None
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============= User Preferences Schemas =============

class UserPreferencesBase(BaseModel):
    cuisine_preferences: Optional[List[str]] = None
    price_range: Optional[str] = None
    dietary_needs: Optional[List[str]] = None
    location: Optional[str] = None
    ambiance_preferences: Optional[List[str]] = None
    sort_preference: Optional[str] = None


class UserPreferencesCreate(UserPreferencesBase):
    pass


class UserPreferencesResponse(UserPreferencesBase):
    user_id: str
    updated_at: datetime


# ============= Restaurant Schemas =============

class RestaurantBase(BaseModel):
    name: str
    description: Optional[str] = None
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[Dict[str, Any]] = None
    amenities: Optional[List[str]] = None


class RestaurantCreate(RestaurantBase):
    photo_urls: Optional[List[str]] = None


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[Dict[str, Any]] = None
    amenities: Optional[List[str]] = None
    photo_urls: Optional[List[str]] = None


class RestaurantResponse(RestaurantBase):
    id: str                          # MongoDB ObjectId as string
    owner_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    average_rating: Optional[float] = None
    review_count: int = 0
    photos: List[str] = []


# ============= Review Schemas =============

class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None


class ReviewCreate(ReviewBase):
    pass                             # restaurant_id comes from URL path param


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    review_text: Optional[str] = None


class ReviewResponse(ReviewBase):
    id: str
    restaurant_id: str
    user_id: str
    user_name: str
    restaurant_name: Optional[str] = None
    review_photos: List[str] = []
    created_at: datetime
    updated_at: datetime


# ============= Favorite Schemas =============

class FavoriteCreate(BaseModel):
    restaurant_id: str               # MongoDB ObjectId as string


class FavoriteResponse(BaseModel):
    user_id: str
    restaurant_id: str
    created_at: datetime
    restaurant: RestaurantResponse


# ============= Restaurant Claim Schemas =============

class RestaurantClaimCreate(BaseModel):
    restaurant_id: str


class RestaurantClaimResponse(BaseModel):
    id: str
    restaurant_id: str
    owner_id: str
    status: ClaimStatus
    created_at: datetime


# ============= AI Assistant Schemas =============

class ChatMessageSchema(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None   # MongoDB ObjectId as string
    conversation_history: List[ChatMessageSchema] = []


class RestaurantRecommendation(BaseModel):
    restaurant: RestaurantResponse
    reason: str


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    recommendations: List[RestaurantRecommendation] = []


# ============= Conversation Schemas =============

class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    recommendations: Optional[List[Any]] = None
    created_at: datetime


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = []


class ConversationListItem(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
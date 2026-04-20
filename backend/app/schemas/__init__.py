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
    id: int
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
    
    model_config = ConfigDict(from_attributes=True)


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
    user_id: int
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


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
    id: int
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    average_rating: Optional[float] = None
    review_count: int = 0
    photos: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)


# ============= Review Schemas =============

class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None


class ReviewCreate(ReviewBase):
    restaurant_id: int


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    review_text: Optional[str] = None


class ReviewResponse(ReviewBase):
    id: int
    restaurant_id: int
    user_id: int
    user_name: str
    restaurant_name: Optional[str] = None
    review_photos: List[str] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============= Favorite Schemas =============

class FavoriteCreate(BaseModel):
    restaurant_id: int


class FavoriteResponse(BaseModel):
    user_id: int
    restaurant_id: int
    created_at: datetime
    restaurant: RestaurantResponse
    
    model_config = ConfigDict(from_attributes=True)


# ============= Restaurant Claim Schemas =============

class RestaurantClaimCreate(BaseModel):
    restaurant_id: int


class RestaurantClaimResponse(BaseModel):
    id: int
    restaurant_id: int
    owner_id: int
    status: ClaimStatus
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============= AI Assistant Schemas =============

class ChatMessageSchema(BaseModel):
    """Used in conversation_history field of ChatRequest."""
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    conversation_history: List[ChatMessageSchema] = []


class RestaurantRecommendation(BaseModel):
    restaurant: RestaurantResponse
    reason: str


class ChatResponse(BaseModel):
    message: str
    conversation_id: int
    recommendations: List[RestaurantRecommendation] = []


# ============= Conversation Schemas =============

class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    recommendations: Optional[List[Any]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class ConversationListItem(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

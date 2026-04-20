"""
SQLAlchemy models for the Yelp Prototype database.
"""
from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, JSON, TIMESTAMP, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(Enum('customer', 'owner', name='userrole'), nullable=False, default='customer', index=True)
    phone = Column(String(20))
    about_me = Column(Text)
    city = Column(String(100))
    country = Column(String(100))
    state = Column(String(50))
    languages = Column(JSON)
    gender = Column(String(50))
    profile_picture = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    owned_restaurants = relationship("Restaurant", back_populates="owner")
    conversations = relationship("ChatConversation", back_populates="user", cascade="all, delete-orphan")


class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    cuisine_preferences = Column(JSON)
    price_range = Column(String(10))
    dietary_needs = Column(JSON)
    location = Column(String(255))
    ambiance_preferences = Column(JSON)
    sort_preference = Column(String(50))
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    user = relationship("User", back_populates="preferences")


class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    cuisine_type = Column(String(100), index=True)
    price_range = Column(String(10), index=True)
    address = Column(String(255))
    city = Column(String(100), index=True)
    state = Column(String(50))
    zip_code = Column(String(20))
    phone = Column(String(20))
    website = Column(String(255))
    hours = Column(JSON)
    amenities = Column(JSON)
    view_count = Column(Integer, nullable=False, server_default="0")
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    owner = relationship("User", back_populates="owned_restaurants")
    photos = relationship("RestaurantPhoto", back_populates="restaurant", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="restaurant", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="restaurant", cascade="all, delete-orphan")
    claims = relationship("RestaurantClaim", back_populates="restaurant", cascade="all, delete-orphan")


class RestaurantPhoto(Base):
    __tablename__ = "restaurant_photos"
    
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    photo_url = Column(String(500), nullable=False)
    uploaded_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    restaurant = relationship("Restaurant", back_populates="photos")


class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer, nullable=False, index=True)
    review_text = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )
    
    restaurant = relationship("Restaurant", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
    photos = relationship("ReviewPhoto", back_populates="review", cascade="all, delete-orphan")


class ReviewPhoto(Base):
    __tablename__ = "review_photos"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    photo_url = Column(String(500), nullable=False)
    uploaded_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    review = relationship("Review", back_populates="photos")


class Favorite(Base):
    __tablename__ = "favorites"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    user = relationship("User", back_populates="favorites")
    restaurant = relationship("Restaurant", back_populates="favorites")


class RestaurantClaim(Base):
    __tablename__ = "restaurant_claims"
    
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum('pending', 'approved', 'rejected', name='claimstatus'), nullable=False, default='pending', index=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    restaurant = relationship("Restaurant", back_populates="claims")


# ============= Chat Models =============

class ChatConversation(Base):
    __tablename__ = "chat_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False, default="New conversation")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    user = relationship("User", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum('user', 'assistant', name='messagerole'), nullable=False)
    content = Column(Text, nullable=False)
    recommendations = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    conversation = relationship("ChatConversation", back_populates="messages")

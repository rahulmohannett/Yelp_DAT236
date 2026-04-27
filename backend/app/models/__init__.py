"""
MongoDB document helpers for the Yelp Prototype.
No ORM - just constants and helper functions for working with MongoDB collections.
"""
from datetime import datetime
from bson import ObjectId


# Collection names
USERS = "users"
RESTAURANTS = "restaurants"
REVIEWS = "reviews"
FAVORITES = "favorites"
USER_PREFERENCES = "user_preferences"
RESTAURANT_PHOTOS = "restaurant_photos"
REVIEW_PHOTOS = "review_photos"
RESTAURANT_CLAIMS = "restaurant_claims"
CHAT_CONVERSATIONS = "chat_conversations"
CHAT_MESSAGES = "chat_messages"
SESSIONS = "sessions"


def to_str_id(doc: dict) -> dict:
    """Convert MongoDB _id ObjectId to string 'id' field for API responses."""
    if doc is None:
        return None
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    # Convert any nested ObjectId references
    for key in ["user_id", "restaurant_id", "owner_id", "conversation_id", "review_id"]:
        if key in doc and isinstance(doc[key], ObjectId):
            doc[key] = str(doc[key])
    return doc


def to_object_id(id_str: str) -> ObjectId:
    """Convert string ID to ObjectId, raise ValueError if invalid."""
    try:
        return ObjectId(id_str)
    except Exception:
        raise ValueError(f"Invalid ID format: {id_str}")


def now() -> datetime:
    """Return current UTC datetime."""
    return datetime.utcnow()
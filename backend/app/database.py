"""
Database connection and session management.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from datetime import datetime

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client.yelp_db

async def get_db():
    """Return MongoDB database instance."""
    return db

async def init_db():
    """Create indexes when app starts."""
    # Sessions: auto-delete when expires_at passes
    await db.sessions.create_index("expires_at", expireAfterSeconds=0)
    # Users: email must be unique
    await db.users.create_index("email", unique=True)
    # Search indexes
    await db.restaurants.create_index("city")
    await db.restaurants.create_index("cuisine_type")
    await db.reviews.create_index("restaurant_id")
    await db.favorites.create_index([("user_id", 1), ("restaurant_id", 1)])
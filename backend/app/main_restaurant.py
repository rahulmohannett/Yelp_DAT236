"""
Restaurant Service - Port 8003
Handles: restaurant CRUD, search, filtering, photos, view count tracking
Routers: restaurants
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import get_settings
from app.database import Base, engine
from app.routers import restaurants

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

settings = get_settings()

app = FastAPI(
    title="Yelp Prototype - Restaurant Service",
    description="Restaurant discovery, search, filtering, and management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(os.path.join(uploads_dir, "profile_pictures"), exist_ok=True)
    os.makedirs(os.path.join(uploads_dir, "restaurant_photos"), exist_ok=True)
    os.makedirs(os.path.join(uploads_dir, "review_photos"), exist_ok=True)

app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Include routers
app.include_router(restaurants.router, tags=["restaurants"])

@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint for load balancers and orchestrators."""
    return {"status": "healthy", "service": "restaurant-service"}
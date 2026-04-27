"""
User Service - Port 8001
Handles: authentication, user profiles, favorites, review history, AI assistant
Routers: auth, users, favorites, history, ai_assistant
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.database import init_db
from app.routers import auth, users, favorites, history, ai_assistant

app = FastAPI(
    title="Yelp Prototype - User Service",
    description="User authentication, profile management, favorites, history, and AI assistant",
    version="1.0.0"
)

@app.on_event("startup")
async def startup():
    await init_db()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
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
app.include_router(auth.router, tags=["auth"])
app.include_router(users.router, tags=["users"])
app.include_router(favorites.router, tags=["favorites"])
app.include_router(history.router, tags=["history"])
app.include_router(ai_assistant.router, tags=["ai_assistant"])

@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint for load balancers and orchestrators."""
    return {"status": "healthy", "service": "user-service"}
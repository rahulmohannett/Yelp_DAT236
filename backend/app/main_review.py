"""
Review Service - Port 8004
Handles: review CRUD, rating management, review photos
Routers: reviews
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.database import init_db
from app.kafka_client import init_kafka_client, kafka_client
from app.routers import reviews


app = FastAPI(
    title="Yelp Prototype - Review Service",
    description="Restaurant review management, ratings, and review photos",
    version="1.0.0"
)

@app.on_event("startup")
async def startup():
    await init_db()
    # Initialize Kafka producer for publishing review events
    client = init_kafka_client(settings.KAFKA_BOOTSTRAP_SERVERS)
    await client.start_producer()

@app.on_event("shutdown")
async def shutdown():
    # Gracefully stop Kafka producer
    if kafka_client:
        await kafka_client.stop_producer()

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
app.include_router(reviews.router, tags=["reviews"])

@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint for load balancers and orchestrators."""
    return {"status": "healthy", "service": "review-service"}

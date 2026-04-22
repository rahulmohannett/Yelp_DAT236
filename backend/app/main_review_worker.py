"""
Review Worker Service
Consumes review events from Kafka and persists them to MongoDB.
"""

import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from bson import ObjectId
from datetime import datetime

from app.config import get_settings
from app.database import get_db
from app.kafka_client import init_kafka_client, kafka_client
from app.schemas.kafka_events import ReviewCreatedEvent, ReviewUpdatedEvent, ReviewDeletedEvent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Topics this worker subscribes to
REVIEW_TOPICS = [
    "review.created",
    "review.updated",
    "review.deleted"
]


async def handle_review_event(topic: str, event: dict) -> bool:
    """
    Process review events from Kafka.
    
    Returns:
        True if processing succeeded, False otherwise
    """
    try:
        db = await get_db()
        
        if topic == "review.created":
            # Validate event schema
            event_obj = ReviewCreatedEvent(**event)
            
            # Insert into MongoDB
            review_doc = {
                "_id": ObjectId(event_obj.review_id),
                "restaurant_id": ObjectId(event_obj.restaurant_id),
                "user_id": ObjectId(event_obj.user_id),
                "rating": event_obj.rating,
                "review_text": event_obj.review_text,
                "photos": event_obj.photos,
                "created_at": event_obj.created_at,
                "updated_at": event_obj.created_at
            }
            
            result = await db.reviews.insert_one(review_doc)
            logger.info(f"✅ Review created in DB: {result.inserted_id}")
            
            # Update restaurant's review count and average rating
            await update_restaurant_stats(db, event_obj.restaurant_id)
            
            return True
        
        elif topic == "review.updated":
            # Validate event schema
            event_obj = ReviewUpdatedEvent(**event)
            
            # Build update document
            update_doc = {"updated_at": event_obj.updated_at}
            if event_obj.rating is not None:
                update_doc["rating"] = event_obj.rating
            if event_obj.review_text is not None:
                update_doc["review_text"] = event_obj.review_text
            if event_obj.photos is not None:
                update_doc["photos"] = event_obj.photos
            
            # Update in MongoDB
            result = await db.reviews.update_one(
                {"_id": ObjectId(event_obj.review_id)},
                {"$set": update_doc}
            )
            
            logger.info(f"✅ Review updated in DB: {event_obj.review_id}, matched={result.matched_count}")
            
            # Update restaurant stats if rating changed
            if event_obj.rating is not None:
                await update_restaurant_stats(db, event_obj.restaurant_id)
            
            return True
        
        elif topic == "review.deleted":
            # Validate event schema
            event_obj = ReviewDeletedEvent(**event)
            
            # Delete from MongoDB
            result = await db.reviews.delete_one(
                {"_id": ObjectId(event_obj.review_id)}
            )
            
            logger.info(f"✅ Review deleted from DB: {event_obj.review_id}, deleted={result.deleted_count}")
            
            # Update restaurant stats
            await update_restaurant_stats(db, event_obj.restaurant_id)
            
            return True
        
        else:
            logger.warning(f"Unknown topic: {topic}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error processing review event from {topic}: {e}", exc_info=True)
        return False


async def update_restaurant_stats(db, restaurant_id: str):
    """
    Recalculate and update restaurant's average rating and review count.
    """
    try:
        # Aggregate reviews for this restaurant
        pipeline = [
            {"$match": {"restaurant_id": ObjectId(restaurant_id)}},
            {"$group": {
                "_id": None,
                "avg_rating": {"$avg": "$rating"},
                "review_count": {"$sum": 1}
            }}
        ]
        
        result = await db.reviews.aggregate(pipeline).to_list(length=1)
        
        if result:
            avg_rating = round(result[0]["avg_rating"], 1)
            review_count = result[0]["review_count"]
        else:
            avg_rating = 0.0
            review_count = 0
        
        # Update restaurant document
        await db.restaurants.update_one(
            {"_id": ObjectId(restaurant_id)},
            {"$set": {
                "average_rating": avg_rating,
                "review_count": review_count,
                "updated_at": datetime.utcnow()
            }}
        )
        
        logger.info(f"📊 Updated restaurant stats: {restaurant_id}, avg={avg_rating}, count={review_count}")
    
    except Exception as e:
        logger.error(f"Error updating restaurant stats: {e}", exc_info=True)


# Background task to consume Kafka events
async def consume_kafka_events():
    """Background task that consumes events from Kafka."""
    try:
        # Start consumer
        await kafka_client.start_consumer(
            topics=REVIEW_TOPICS,
            group_id="review-worker-group"
        )
        
        # Consume events indefinitely
        await kafka_client.consume_events(handler=handle_review_event)
    
    except Exception as e:
        logger.error(f"Kafka consumer error: {e}", exc_info=True)
    finally:
        await kafka_client.stop_consumer()


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Review Worker starting up...")
    
    # Initialize Kafka client
    init_kafka_client(settings.KAFKA_BOOTSTRAP_SERVERS)
    
    # Start Kafka consumer in background
    consumer_task = asyncio.create_task(consume_kafka_events())
    
    yield
    
    # Shutdown
    logger.info("⏹️  Review Worker shutting down...")
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass


# FastAPI app
app = FastAPI(
    title="Yelp Prototype - Review Worker",
    description="Consumes review events from Kafka and writes to MongoDB",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "review-worker"}


@app.get("/", tags=["root"])
def root():
    """Root endpoint."""
    return {
        "service": "review-worker",
        "topics": REVIEW_TOPICS,
        "status": "running"
    }

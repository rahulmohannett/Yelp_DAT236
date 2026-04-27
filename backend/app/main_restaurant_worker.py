"""
Restaurant Worker Service
Consumes restaurant events from Kafka and persists them to MongoDB.
"""

import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from bson import ObjectId
from datetime import datetime

from app.config import settings
from app.database import get_db
from app.kafka_client import init_kafka_client, kafka_client
from app.schemas.kafka_events import RestaurantCreatedEvent, RestaurantUpdatedEvent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Topics this worker subscribes to
RESTAURANT_TOPICS = [
    "restaurant.created",
    "restaurant.updated"
]


async def handle_restaurant_event(topic: str, event: dict) -> bool:
    """
    Process restaurant events from Kafka.
    
    Returns:
        True if processing succeeded, False otherwise
    """
    try:
        db = await get_db()
        
        if topic == "restaurant.created":
            # Validate event schema
            event_obj = RestaurantCreatedEvent(**event)
            
            # Insert into MongoDB
            restaurant_doc = {
                "_id": ObjectId(event_obj.restaurant_id),
                "name": event_obj.name,
                "cuisine_type": event_obj.cuisine_type,
                "price_range": event_obj.price_range,
                "address": event_obj.address,
                "city": event_obj.city,
                "state": event_obj.state,
                "zip_code": event_obj.zip_code,
                "phone": event_obj.phone,
                "website": event_obj.website,
                "hours": event_obj.hours or {},
                "amenities": event_obj.amenities,
                "owner_id": ObjectId(event_obj.owner_id) if event_obj.owner_id else None,
                "photos": event_obj.photos,
                "view_count": 0,
                "average_rating": 0.0,
                "review_count": 0,
                "created_at": event_obj.created_at,
                "updated_at": event_obj.created_at
            }
            
            result = await db.restaurants.insert_one(restaurant_doc)
            logger.info(f"✅ Restaurant created in DB: {result.inserted_id}")
            
            return True
        
        elif topic == "restaurant.updated":
            # Validate event schema
            event_obj = RestaurantUpdatedEvent(**event)
            
            # Build update document (only include fields that were provided)
            update_doc = {"updated_at": event_obj.updated_at}
            
            if event_obj.name is not None:
                update_doc["name"] = event_obj.name
            if event_obj.cuisine_type is not None:
                update_doc["cuisine_type"] = event_obj.cuisine_type
            if event_obj.price_range is not None:
                update_doc["price_range"] = event_obj.price_range
            if event_obj.address is not None:
                update_doc["address"] = event_obj.address
            if event_obj.city is not None:
                update_doc["city"] = event_obj.city
            if event_obj.state is not None:
                update_doc["state"] = event_obj.state
            if event_obj.zip_code is not None:
                update_doc["zip_code"] = event_obj.zip_code
            if event_obj.phone is not None:
                update_doc["phone"] = event_obj.phone
            if event_obj.website is not None:
                update_doc["website"] = event_obj.website
            if event_obj.hours is not None:
                update_doc["hours"] = event_obj.hours
            if event_obj.amenities is not None:
                update_doc["amenities"] = event_obj.amenities
            if event_obj.photos is not None:
                update_doc["photos"] = event_obj.photos
            
            # Update in MongoDB
            result = await db.restaurants.update_one(
                {"_id": ObjectId(event_obj.restaurant_id)},
                {"$set": update_doc}
            )
            
            logger.info(f"✅ Restaurant updated in DB: {event_obj.restaurant_id}, matched={result.matched_count}")
            
            return True
        
        else:
            logger.warning(f"Unknown topic: {topic}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error processing restaurant event from {topic}: {e}", exc_info=True)
        return False


# Background task to consume Kafka events
async def consume_kafka_events(client):
    """Background task that consumes events from Kafka."""
    try:
        await client.start_consumer(
            topics=RESTAURANT_TOPICS,
            group_id="restaurant-worker-group"
        )
        await client.consume_events(handler=handle_restaurant_event)
    except Exception as e:
        logger.error(f"Kafka consumer error: {e}", exc_info=True)
    finally:
        await client.stop_consumer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Restaurant Worker starting up...")
    
    # Initialize and store client locally
    client = init_kafka_client(settings.KAFKA_BOOTSTRAP_SERVERS)
    
    # Pass client explicitly to avoid module-level None race
    consumer_task = asyncio.create_task(consume_kafka_events(client))
    
    yield
    
    logger.info("⏹️  Restaurant Worker shutting down...")
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass


# FastAPI app
app = FastAPI(
    title="Yelp Prototype - Restaurant Worker",
    description="Consumes restaurant events from Kafka and writes to MongoDB",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "restaurant-worker"}


@app.get("/", tags=["root"])
def root():
    """Root endpoint."""
    return {
        "service": "restaurant-worker",
        "topics": RESTAURANT_TOPICS,
        "status": "running"
    }

"""
Test Kafka producer/consumer flow end-to-end.

Run this after deploying Kafka and worker services:
python backend/tests/test_kafka.py
"""

import asyncio
import json
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from bson import ObjectId
from datetime import datetime

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

async def test_producer():
    """Test publishing a review.created event."""
    print("🚀 Starting producer test...")
    
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    await producer.start()
    
    try:
        # Build test event
        event = {
            "event_type": "review.created",
            "review_id": str(ObjectId()),
            "restaurant_id": str(ObjectId()),
            "user_id": str(ObjectId()),
            "rating": 5,
            "review_text": "Test review from Kafka producer",
            "photos": [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Send to Kafka
        metadata = await producer.send_and_wait("review.created", value=event)
        
        print(f"✅ Event published successfully!")
        print(f"   Topic: review.created")
        print(f"   Partition: {metadata.partition}")
        print(f"   Offset: {metadata.offset}")
        print(f"   Event: {json.dumps(event, indent=2)}")
        
    finally:
        await producer.stop()


async def test_consumer():
    """Test consuming from review.created topic."""
    print("\n🔍 Starting consumer test (will consume for 10 seconds)...")
    
    consumer = AIOKafkaConsumer(
        "review.created",
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id="test-consumer-group",
        auto_offset_reset='earliest'
    )
    
    await consumer.start()
    
    try:
        # Consume for 10 seconds
        async def consume_with_timeout():
            count = 0
            async for msg in consumer:
                count += 1
                print(f"\n📨 Message {count} received:")
                print(f"   Topic: {msg.topic}")
                print(f"   Partition: {msg.partition}")
                print(f"   Offset: {msg.offset}")
                print(f"   Event: {json.dumps(msg.value, indent=2)}")
                
                # Stop after 5 messages or 10 seconds
                if count >= 5:
                    break
        
        await asyncio.wait_for(consume_with_timeout(), timeout=10.0)
        print("\n✅ Consumer test complete!")
        
    except asyncio.TimeoutError:
        print("\n⏱️  No more messages in 10 seconds - test complete!")
    
    finally:
        await consumer.stop()


async def test_end_to_end():
    """Test full producer → consumer flow."""
    print("=" * 60)
    print("KAFKA END-TO-END TEST")
    print("=" * 60)
    
    # Step 1: Produce an event
    await test_producer()
    
    # Step 2: Wait a moment for Kafka to process
    await asyncio.sleep(2)
    
    # Step 3: Consume the event
    await test_consumer()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_end_to_end())

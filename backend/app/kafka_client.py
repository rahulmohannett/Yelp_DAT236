"""
Kafka client utility for async event publishing and consumption.
Uses aiokafka for async-compatible producer/consumer.
"""

import json
import logging
from typing import Any, Dict, Callable
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError

logger = logging.getLogger(__name__)

# Kafka configuration - loaded from environment
KAFKA_BOOTSTRAP_SERVERS = None  # Set via config at runtime


class KafkaClient:
    """Async Kafka client for producing and consuming events."""
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.consumer = None
    
    async def start_producer(self):
        """Initialize and start Kafka producer."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                compression_type='gzip',
                acks='all',  # Wait for all replicas
                retries=3
            )
            await self.producer.start()
            logger.info(f"Kafka producer started: {self.bootstrap_servers}")
        except KafkaError as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise
    
    async def stop_producer(self):
        """Stop Kafka producer."""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")
    
    async def publish_event(self, topic: str, event: Dict[str, Any], key: str = None):
        """
        Publish an event to a Kafka topic.
        
        Args:
            topic: Kafka topic name
            event: Event payload (will be JSON serialized)
            key: Optional partition key (uses event ID if available)
        
        Returns:
            RecordMetadata if successful
        
        Raises:
            KafkaError if publish fails
        """
        if not self.producer:
            raise RuntimeError("Producer not started. Call start_producer() first.")
        
        try:
            # Use event ID as key for ordering guarantee (same ID = same partition)
            partition_key = key or str(event.get('id', ''))
            key_bytes = partition_key.encode('utf-8') if partition_key else None
            
            # Send to Kafka
            metadata = await self.producer.send_and_wait(
                topic,
                value=event,
                key=key_bytes
            )
            
            logger.info(f"Published event to {topic}: partition={metadata.partition}, offset={metadata.offset}")
            return metadata
            
        except KafkaError as e:
            logger.error(f"Failed to publish event to {topic}: {e}")
            raise
    
    async def start_consumer(self, topics: list, group_id: str):
        """
        Initialize and start Kafka consumer.
        
        Args:
            topics: List of topics to subscribe to
            group_id: Consumer group ID
        """
        try:
            self.consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',  # Start from beginning if no offset
                enable_auto_commit=False  # Manual commit for reliability
            )
            await self.consumer.start()
            logger.info(f"Kafka consumer started: topics={topics}, group={group_id}")
        except KafkaError as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            raise
    
    async def stop_consumer(self):
        """Stop Kafka consumer."""
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")
    
    async def consume_events(self, handler: Callable):
        """
        Consume events from subscribed topics and process with handler.
        
        Args:
            handler: Async function that processes each event
                     Signature: async def handler(topic: str, event: dict) -> bool
                     Returns True if processing succeeded, False otherwise
        
        Runs indefinitely until stopped.
        """
        if not self.consumer:
            raise RuntimeError("Consumer not started. Call start_consumer() first.")
        
        logger.info("Starting event consumption loop...")
        
        try:
            async for msg in self.consumer:
                topic = msg.topic
                event = msg.value
                
                logger.info(f"Received event from {topic}: partition={msg.partition}, offset={msg.offset}")
                
                try:
                    # Process event with handler
                    success = await handler(topic, event)
                    
                    if success:
                        # Commit offset only if processing succeeded
                        await self.consumer.commit()
                        logger.info(f"Successfully processed and committed: {topic} offset={msg.offset}")
                    else:
                        logger.warning(f"Handler returned False for {topic} offset={msg.offset} - not committing")
                
                except Exception as e:
                    logger.error(f"Error processing event from {topic}: {e}", exc_info=True)
                    # Do not commit - message will be reprocessed
        
        except Exception as e:
            logger.error(f"Consumer loop error: {e}", exc_info=True)
            raise


# Global Kafka client instance (initialized by services)
kafka_client: KafkaClient = None


async def get_kafka_client() -> KafkaClient:
    """Dependency to get Kafka client instance."""
    if not kafka_client:
        raise RuntimeError("Kafka client not initialized")
    return kafka_client


def init_kafka_client(bootstrap_servers: str) -> KafkaClient:
    """Initialize global Kafka client instance."""
    global kafka_client
    kafka_client = KafkaClient(bootstrap_servers)
    return kafka_client

from typing import Dict, Any
import json
import logging
import asyncio
from nats.aio.client import Client as NATS
from datetime import datetime
import os
import dotenv
from src.services.promotion_service import PromotionService

# Load environment variables
dotenv.load_dotenv()

logger = logging.getLogger(__name__)

class PromotionSyncHandler:
    def __init__(self):
        self.promotion_service = PromotionService()
        self.nats = NATS()
        
    async def initialize(self):
        """Initialize NATS connection and subscriptions."""
        try:
            await self.nats.connect(
                servers=[os.getenv("NATS_SERVER_URL", "nats://localhost:4222")],
                user=os.getenv("NATS_USER"),
                password=os.getenv("NATS_PASSWORD"),
                max_reconnect_attempts=5,
                reconnect_time_wait=1
            )
            
            # Subscribe to different promotion sync channels
            await self.nats.subscribe(
                "promotion.created",
                cb=self.handle_promotion_created
            )
            await self.nats.subscribe(
                "promotion.updated",
                cb=self.handle_promotion_updated
            )
            await self.nats.subscribe(
                "promotion.deleted",
                cb=self.handle_promotion_deleted
            )
            
            logger.info("Promotion sync handler initialized with all channels")
            
        except Exception as e:
            logger.error(f"Error initializing variant sync handler: {e}")
            raise
            
    async def handle_promotion_created(self, msg):
        """Handle promotion creation messages."""
        try:
            data = json.loads(msg.data.decode())
            logger.info(f"Received promotion creation message: {data}")
            
            await self.promotion_service.create_promotion(data)
            
            # Acknowledge successful processing
            await self.nats.publish(
                "promotion.created.ack",
                json.dumps({
                    "success": True,
                    "promotion_id": data.get('id'),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )
                
        except Exception as e:
            logger.error(f"Error handling promotion creation: {e}")
            await self.nats.publish(
                "promotion.created.ack",
                json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )

    async def handle_promotion_updated(self, msg):
        """Handle promotion update messages."""
        try:
            data = json.loads(msg.data.decode())

            await self.promotion_service.update_promotion(id=data.get('id'), promotion_data=data)

            # Acknowledge successful processing
            await self.nats.publish(
                "promotion.updated.ack",
                json.dumps({
                    "success": True,
                    "promotion_id": data.get('id'),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )
                
        except Exception as e:
            logger.error(f"Error handling promotion update: {e}")
            await self.nats.publish(
                "promotion.updated.ack",
                json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )

    async def handle_promotion_deleted(self, msg):
        """Handle promotion deletion messages."""
        try:
            data = json.loads(msg.data.decode())

            await self.promotion_service.delete_promotion(id=data.get('id'))

            # Acknowledge successful processing
            await self.nats.publish(
                "promotion.deleted.ack",
                json.dumps({
                    "success": True,
                    "promotion_id": data.get('id'),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )
                
        except Exception as e:
            logger.error(f"Error handling promotion deletion: {e}")
            await self.nats.publish(
                "promotion.deleted.ack",
                json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )

promotion_sync_handler = PromotionSyncHandler()
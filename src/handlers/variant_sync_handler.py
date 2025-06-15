from typing import Dict, Any
import json
import logging
import asyncio
from nats.aio.client import Client as NATS
from datetime import datetime
import os
import dotenv
from src.services.variant_service import VariantService

# Load environment variables
dotenv.load_dotenv()

logger = logging.getLogger(__name__)

class VariantSyncHandler:
    def __init__(self):
        self.variant_service = VariantService()
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
            
            # Subscribe to different variant sync channels
            await self.nats.subscribe(
                "variant.created",
                cb=self.handle_variant_created
            )
            await self.nats.subscribe(
                "variant.updated",
                cb=self.handle_variant_updated
            )
            await self.nats.subscribe(
                "variant.deleted",
                cb=self.handle_variant_deleted
            )
            
            logger.info("Variant sync handler initialized with all channels")
            
        except Exception as e:
            logger.error(f"Error initializing variant sync handler: {e}")
            raise
            
    async def handle_variant_created(self, msg):
        """Handle variant creation messages."""
        try:
            data = json.loads(msg.data.decode())
            logger.info(f"Received variant creation message: {data}")

            if not data.get('id'):
                logger.error("No variant ID in creation message")
                return
                
            await self.variant_service.create_variant(variant_data=data)

            # Acknowledge successful processing
            await self.nats.publish(
                "variant.created.ack",
                json.dumps({
                    "success": True,
                    "variant_id": data.get('id'),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )
                
        except Exception as e:
            logger.error(f"Error handling variant creation: {e}")
            await self.nats.publish(
                "variant.created.ack",
                json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )

    async def handle_variant_updated(self, msg):
        """Handle variant update messages."""
        try:
            data = json.loads(msg.data.decode())
            logger.info(f"Received variant update message: {data}")

            if not data.get('id'):
                logger.error("No variant ID in update message")
                return

            await self.variant_service.update_variant(id=data.get('id'), variant_data=data)

            # Acknowledge successful processing
            await self.nats.publish(
                "variant.updated.ack",
                json.dumps({
                    "success": True,
                    "variant_id": data.get('id'),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )
                
        except Exception as e:
            logger.error(f"Error handling variant update: {e}")
            await self.nats.publish(
                "variant.updated.ack",
                json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )

    async def handle_variant_deleted(self, msg):
        """Handle variant deletion messages."""
        try:
            data = json.loads(msg.data.decode())
            id = data.get('id')
            logger.info(f"Received variant deletion message: {data}")

            if not id:
                logger.error("No variant ID in deletion message")
                return

            await self.variant_service.delete_variant(id=id)

            # Acknowledge successful processing
            await self.nats.publish(
                "variant.deleted.ack",
                json.dumps({
                    "success": True,
                    "variant_id": id,
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )
                
        except Exception as e:
            logger.error(f"Error handling variant deletion: {e}")
            await self.nats.publish(
                "variant.deleted.ack",
                json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )

variant_sync_handler = VariantSyncHandler()
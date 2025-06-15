from typing import Dict, Any
import json
import logging
import asyncio
from nats.aio.client import Client as NATS
from datetime import datetime
import os
import dotenv
from src.services.order_service import OrderService

# Load environment variables
dotenv.load_dotenv()

logger = logging.getLogger(__name__)

class OrderSyncHandler:
    def __init__(self):
        self.order_service = OrderService()
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
            
            # Subscribe to different order sync channels
            await self.nats.subscribe(
                "order.created",
                cb=self.handle_order_created
            )
            await self.nats.subscribe(
                "order.updated",
                cb=self.handle_order_updated
            )
            await self.nats.subscribe(
                "order.deleted",
                cb=self.handle_order_deleted
            )
            await self.nats.subscribe(
                "order.status_changed",
                cb=self.handle_order_status_changed
            )
            
            logger.info("Order sync handler initialized with all channels")
            
        except Exception as e:
            logger.error(f"Error initializing order sync handler: {e}")
            raise
            
    async def handle_order_created(self, msg):
        """Handle order creation messages."""
        try:
            data = json.loads(msg.data.decode()).get('result', {})
            logger.info(f"Received order creation message: {data}")
            
            await self.order_service.create_order(data)
            
            # Acknowledge successful processing
            await self.nats.publish(
                "order.created.ack",
                json.dumps({
                    "success": True,
                    "order_id": data.get('id'),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )
                
        except Exception as e:
            logger.error(f"Error handling order creation: {e}")
            await self.nats.publish(
                "order.created.ack",
                json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )

    async def handle_order_updated(self, msg):
        """Handle order update messages."""
        try:
            data = json.loads(msg.data.decode())
            logger.info(f"Received order update message: {data}")

            await self.order_service.update_order(id=data.get('id'), order_data=data)

            # Acknowledge successful processing
            await self.nats.publish(
                "order.updated.ack",
                json.dumps({
                    "success": True,
                    "order_id": data.get('id'),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )
                
        except Exception as e:
            logger.error(f"Error handling order update: {e}")
            await self.nats.publish(
                "order.updated.ack",
                json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )

    async def handle_order_deleted(self, msg):
        """Handle order deletion messages."""
        try:
            data = json.loads(msg.data.decode())
            logger.info(f"Received order deletion message: {data}")

            await self.order_service.delete_order(id=data.get('id'))

            # Acknowledge successful processing
            await self.nats.publish(
                "order.deleted.ack",
                json.dumps({
                    "success": True,
                    "order_id": data.get('id'),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )
                
        except Exception as e:
            logger.error(f"Error handling order deletion: {e}")
            await self.nats.publish(
                "order.deleted.ack",
                json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )
            
    async def handle_order_status_changed(self, msg):
        """Handle order status change messages."""
        try:
            data = json.loads(msg.data.decode())
            logger.info(f"Received order status change message: {data}")

            await self.order_service.update_order_status(
                id=data.get('id'),
                status=data.get('status'),
                status_data=data.get('status_data', {})
            )

            # Acknowledge successful processing
            await self.nats.publish(
                "order.status_changed.ack",
                json.dumps({
                    "success": True,
                    "order_id": data.get('id'),
                    "status": data.get('status'),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )
                
        except Exception as e:
            logger.error(f"Error handling order status change: {e}")
            await self.nats.publish(
                "order.status_changed.ack",
                json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )

order_sync_handler = OrderSyncHandler()
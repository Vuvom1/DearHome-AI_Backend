from typing import Dict, Any
import json
import logging
from src.services.chroma_service import ChromaService
import asyncio
from nats.aio.client import Client as NATS
from datetime import datetime
import os
import dotenv

# Load environment variables
dotenv.load_dotenv()

logger = logging.getLogger(__name__)

class ProductSyncHandler:
    def __init__(self):
        self.chroma_service = ChromaService()
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
            
            # Subscribe to product sync messages
            await self.nats.subscribe(
                "product.sync",
                cb=self.handle_product_sync
            )
            
            logger.info("Product sync handler initialized")
            
        except Exception as e:
            logger.error(f"Error initializing product sync handler: {e}")
            raise
            
    async def handle_product_sync(self, msg):
        """Handle product sync messages from ASP.NET server."""
        try:
            data = json.loads(msg.data.decode())
            operation = data.get('operation')
            product = data.get('product')
            logger.info(f"Received product sync message: {data}")
            
            if not product:
                logger.error("No product data in sync message")
                return
                
            if operation == "create":
                await self.chroma_service.add_documents(product)
            elif operation == "update":
                await self.chroma_service.update_document(id=product.get('id'), data=product)
            elif operation == "delete":
                await self.chroma_service.delete_documents([product.get('id')])

            # Acknowledge successful processing
            await self.nats.publish(
                "product.sync.ack",
                json.dumps({
                    "success": True,
                    "product_id": product.get('id'),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )
                
        except Exception as e:
            logger.error(f"Error handling product sync: {e}")
            # Send error acknowledgment
            await self.nats.publish(
                "product.sync.ack",
                json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }).encode()
            )

product_sync_handler = ProductSyncHandler()
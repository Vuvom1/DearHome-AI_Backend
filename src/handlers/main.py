from fastapi import WebSocket, WebSocketDisconnect
from logging import getLogger
import traceback
import time
import asyncio

from datetime import datetime

logger = getLogger(__name__)

WEBSOCKET_PING_INTERVAL = 30  # seconds

async def web_socket_ping_handler(websocket: WebSocket, client_id: str):
    """Send periodic pings to keep the WebSocket connection alive"""
    try:
        ping_count = 0
        while True:
            # Wait for ping interval
            await asyncio.sleep(WEBSOCKET_PING_INTERVAL)
            
            # Send ping message
            ping_id = f"ping-{int(time.time())}"
            ping_message = {
                "type": "ping",
                "id": ping_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            try:
                ping_count += 1
                logger.debug(f"Sending ping #{ping_count} to client {client_id} [id={ping_id}]")
                await websocket.send_json(ping_message)
                
                # Azure monitoring best practice: Log periodic health metrics
                if ping_count % 10 == 0:
                    logger.info(f"WebSocket connection health: client={client_id}, pings_sent={ping_count}")
                
            except Exception as e:
                logger.warning(f"Failed to send ping to client {client_id}: {str(e)}")
                # If ping fails, the connection is likely broken
                break
                
    except asyncio.CancelledError:
        # Task was cancelled - normal during WebSocket disconnect
        logger.debug(f"Ping handler for client {client_id} stopped")
    except Exception as e:
        logger.error(f"Error in WebSocket ping handler for client {client_id}: {str(e)}")

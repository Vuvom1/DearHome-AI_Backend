from fastapi import APIRouter, WebSocket, Depends, Request, Response, WebSocket, WebSocketDisconnect
import asyncio
from datetime import datetime
import uuid
import logging
from src.websockets.manager import ConnectionManager
from src.handlers.main import web_socket_ping_handler
import traceback
from src.authentication.auth_depends import get_current_user_ws
from src.managers.chatbot_manager import chatbot_manager


router = APIRouter()

logger = logging.getLogger(__name__)

websocket_manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, current_user_id: str = Depends(get_current_user_ws)):
# async def websocket_endpoint(websocket: WebSocket):

    client_id = str(uuid.uuid4())
    request_id = getattr(websocket, "request_id", str(uuid.uuid4()))

    await websocket.accept()
    ping_task = asyncio.create_task(web_socket_ping_handler(websocket, client_id))

    try:
       await websocket.send_json({
           "type": "connection",
           "status": "connected",
           "client_id": client_id,
           "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
        })
       
       await websocket_manager.connect(websocket)

       while True:
            data = await websocket.receive_text()
            logger.info(f"Received message from client {client_id}: {data}")
            
            # Process the incoming message
            # response = generate_response(data, current_user)
            response = await chatbot_manager.process_query(data, user_id=current_user_id)

            # Send the response back to the client
            message = {
                "type": "message",
                "client_id": client_id,
                "response": response,
                "timestamp": datetime.now().isoformat(),
            }

            await websocket_manager.send_personal_message(message, websocket)
       
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()
        logger.debug(traceback.format_exc())
    
"""
WebSocket endpoints for real-time processing updates
"""

import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import logging
from ..websockets import websocket_manager
# from ..auth import get_current_user_websocket  # Will implement authentication later

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, 
    token: Optional[str] = Query(None),
    connection_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time updates
    
    Query parameters:
    - token: JWT authentication token
    - connection_id: Optional client-provided connection ID
    """
    
    # Generate connection ID if not provided
    if not connection_id:
        connection_id = str(uuid.uuid4())
    
    try:
        # Authenticate user (optional for now, can be enforced later)
        user = None
        if token:
            try:
                # Note: We'll implement get_current_user_websocket later
                # user = await get_current_user_websocket(token)
                pass
            except Exception as e:
                logger.warning(f"WebSocket authentication failed: {e}")
        
        # Connect to WebSocket manager
        await websocket_manager.connect(websocket, connection_id)
        
        try:
            while True:
                # Receive messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                message_type = message.get("type")
                
                if message_type == "subscribe_script":
                    script_id = message.get("script_id")
                    if script_id:
                        await websocket_manager.subscribe_to_script(connection_id, script_id)
                
                elif message_type == "subscribe_session":
                    session_id = message.get("session_id")
                    if session_id:
                        await websocket_manager.subscribe_to_session(connection_id, session_id)
                
                elif message_type == "ping":
                    await websocket_manager.send_personal_message(connection_id, {
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    })
                
                elif message_type == "get_stats":
                    stats = await websocket_manager.get_connection_stats()
                    await websocket_manager.send_personal_message(connection_id, {
                        "type": "stats",
                        "data": stats
                    })
                
                else:
                    await websocket_manager.send_personal_message(connection_id, {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
                
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"WebSocket error for {connection_id}: {e}")
        
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close()
        except:
            pass
    
    finally:
        # Clean up connection
        websocket_manager.disconnect(connection_id)

@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return await websocket_manager.get_connection_stats()
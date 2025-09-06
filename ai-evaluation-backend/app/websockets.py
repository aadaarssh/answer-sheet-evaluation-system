"""
WebSocket manager for real-time processing updates
Handles WebSocket connections and broadcasts processing status
"""

import json
import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Store active connections
        self.active_connections: Dict[str, WebSocket] = {}
        # Track which users are subscribed to which script updates
        self.script_subscriptions: Dict[str, Set[str]] = {}  # script_id -> set of connection_ids
        # Track which users are subscribed to session updates
        self.session_subscriptions: Dict[str, Set[str]] = {}  # session_id -> set of connection_ids
        
    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connected: {connection_id}")
        
        # Send welcome message with connection ID
        await self.send_personal_message(connection_id, {
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    def disconnect(self, connection_id: str):
        """Remove connection and clean up subscriptions"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from all subscriptions
        for script_id in list(self.script_subscriptions.keys()):
            if connection_id in self.script_subscriptions[script_id]:
                self.script_subscriptions[script_id].discard(connection_id)
                if not self.script_subscriptions[script_id]:
                    del self.script_subscriptions[script_id]
                    
        for session_id in list(self.session_subscriptions.keys()):
            if connection_id in self.session_subscriptions[session_id]:
                self.session_subscriptions[session_id].discard(connection_id)
                if not self.session_subscriptions[session_id]:
                    del self.session_subscriptions[session_id]
                    
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, connection_id: str, message: dict):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def subscribe_to_script(self, connection_id: str, script_id: str):
        """Subscribe connection to script processing updates"""
        if script_id not in self.script_subscriptions:
            self.script_subscriptions[script_id] = set()
        self.script_subscriptions[script_id].add(connection_id)
        
        await self.send_personal_message(connection_id, {
            "type": "subscribed",
            "resource": "script",
            "resource_id": script_id
        })
        logger.info(f"Connection {connection_id} subscribed to script {script_id}")
    
    async def subscribe_to_session(self, connection_id: str, session_id: str):
        """Subscribe connection to session processing updates"""
        if session_id not in self.session_subscriptions:
            self.session_subscriptions[session_id] = set()
        self.session_subscriptions[session_id].add(connection_id)
        
        await self.send_personal_message(connection_id, {
            "type": "subscribed",
            "resource": "session",
            "resource_id": session_id
        })
        logger.info(f"Connection {connection_id} subscribed to session {session_id}")
    
    async def broadcast_script_update(self, script_id: str, update_data: dict):
        """Broadcast update to all connections subscribed to a script"""
        script_id_str = str(script_id) if isinstance(script_id, ObjectId) else script_id
        
        if script_id_str in self.script_subscriptions:
            message = {
                "type": "script_update",
                "script_id": script_id_str,
                "timestamp": asyncio.get_event_loop().time(),
                **update_data
            }
            
            # Send to all subscribers
            connections_to_remove = []
            for connection_id in self.script_subscriptions[script_id_str]:
                if connection_id in self.active_connections:
                    try:
                        await self.active_connections[connection_id].send_text(json.dumps(message))
                    except Exception as e:
                        logger.error(f"Error broadcasting to {connection_id}: {e}")
                        connections_to_remove.append(connection_id)
                else:
                    connections_to_remove.append(connection_id)
            
            # Clean up dead connections
            for connection_id in connections_to_remove:
                self.script_subscriptions[script_id_str].discard(connection_id)
            
            if not self.script_subscriptions[script_id_str]:
                del self.script_subscriptions[script_id_str]
                
            logger.info(f"Broadcasted script update for {script_id_str} to {len(self.script_subscriptions.get(script_id_str, []))} connections")
    
    async def broadcast_session_update(self, session_id: str, update_data: dict):
        """Broadcast update to all connections subscribed to a session"""
        session_id_str = str(session_id) if isinstance(session_id, ObjectId) else session_id
        
        if session_id_str in self.session_subscriptions:
            message = {
                "type": "session_update",
                "session_id": session_id_str,
                "timestamp": asyncio.get_event_loop().time(),
                **update_data
            }
            
            # Send to all subscribers
            connections_to_remove = []
            for connection_id in self.session_subscriptions[session_id_str]:
                if connection_id in self.active_connections:
                    try:
                        await self.active_connections[connection_id].send_text(json.dumps(message))
                    except Exception as e:
                        logger.error(f"Error broadcasting to {connection_id}: {e}")
                        connections_to_remove.append(connection_id)
                else:
                    connections_to_remove.append(connection_id)
            
            # Clean up dead connections
            for connection_id in connections_to_remove:
                self.session_subscriptions[session_id_str].discard(connection_id)
            
            if not self.session_subscriptions[session_id_str]:
                del self.session_subscriptions[session_id_str]
                
            logger.info(f"Broadcasted session update for {session_id_str} to {len(self.session_subscriptions.get(session_id_str, []))} connections")
    
    async def broadcast_processing_stage(self, script_id: str, stage: str, progress: int, 
                                       estimated_time: float = None, details: dict = None):
        """Broadcast processing stage update with time estimates"""
        stage_estimates = {
            "database_connected": {"time": 2, "description": "Connecting to database and validating script"},
            "image_validated": {"time": 3, "description": "Validating image file and format"},
            "ocr_processing": {"time": 20, "description": "Extracting text using OpenAI Vision API"},
            "ocr_completed": {"time": 25, "description": "OCR processing completed successfully"},
            "evaluation": {"time": 30, "description": "Evaluating answers with AI semantic analysis"},
            "evaluation_completed": {"time": 50, "description": "AI evaluation completed"},
            "verification": {"time": 15, "description": "Verifying results with Gemini AI"},
            "verification_completed": {"time": 65, "description": "Gemini verification completed"},
            "review_check": {"time": 5, "description": "Checking if manual review is required"},
            "review_check_completed": {"time": 70, "description": "Manual review check completed"},
            "completed": {"time": 0, "description": "All processing completed successfully"}
        }
        
        stage_info = stage_estimates.get(stage, {"time": 0, "description": f"Processing stage: {stage}"})
        
        update_data = {
            "status": "processing",
            "stage": stage,
            "progress": progress,
            "stage_description": stage_info["description"],
            "estimated_remaining_time": estimated_time or stage_info["time"],
            "details": details or {}
        }
        
        await self.broadcast_script_update(script_id, update_data)
    
    async def broadcast_processing_complete(self, script_id: str, result: dict):
        """Broadcast processing completion with final results"""
        update_data = {
            "status": "completed",
            "stage": "completed",
            "progress": 100,
            "stage_description": "Processing completed successfully",
            "estimated_remaining_time": 0,
            "result": result
        }
        
        await self.broadcast_script_update(script_id, update_data)
    
    async def broadcast_processing_error(self, script_id: str, error: str, stage: str = None):
        """Broadcast processing error"""
        update_data = {
            "status": "failed",
            "stage": stage or "error",
            "progress": 0,
            "stage_description": f"Processing failed: {error}",
            "estimated_remaining_time": 0,
            "error": error
        }
        
        await self.broadcast_script_update(script_id, update_data)
    
    async def get_connection_stats(self) -> dict:
        """Get statistics about active connections"""
        return {
            "total_connections": len(self.active_connections),
            "script_subscriptions": len(self.script_subscriptions),
            "session_subscriptions": len(self.session_subscriptions),
            "active_connections": list(self.active_connections.keys())
        }

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
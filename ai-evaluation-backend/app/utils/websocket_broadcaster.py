"""
WebSocket broadcasting utilities for worker tasks
Handles sending WebSocket updates from Celery workers
"""

import asyncio
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

async def broadcast_processing_update(script_id: str, stage: str, progress: int, 
                                    estimated_time: float = None, details: Dict[str, Any] = None):
    """
    Broadcast processing update via WebSocket
    
    Args:
        script_id: ID of the script being processed
        stage: Current processing stage
        progress: Progress percentage (0-100)
        estimated_time: Estimated remaining time in seconds
        details: Additional details about the processing
    """
    try:
        # Import websocket_manager here to avoid circular imports
        from ..websockets import websocket_manager
        
        await websocket_manager.broadcast_processing_stage(
            script_id=script_id,
            stage=stage,
            progress=progress,
            estimated_time=estimated_time,
            details=details or {}
        )
        
        logger.debug(f"Broadcasted WebSocket update for script {script_id}: {stage} ({progress}%)")
        
    except Exception as e:
        # Don't let WebSocket errors crash the worker
        logger.warning(f"Failed to broadcast WebSocket update for script {script_id}: {e}")

async def broadcast_processing_complete(script_id: str, result: Dict[str, Any]):
    """
    Broadcast processing completion via WebSocket
    
    Args:
        script_id: ID of the script that was processed
        result: Final processing result
    """
    try:
        from ..websockets import websocket_manager
        
        await websocket_manager.broadcast_processing_complete(script_id, result)
        
        logger.info(f"Broadcasted completion for script {script_id}")
        
    except Exception as e:
        logger.warning(f"Failed to broadcast completion for script {script_id}: {e}")

async def broadcast_processing_error(script_id: str, error: str, stage: str = None):
    """
    Broadcast processing error via WebSocket
    
    Args:
        script_id: ID of the script that failed
        error: Error message
        stage: Stage where the error occurred
    """
    try:
        from ..websockets import websocket_manager
        
        await websocket_manager.broadcast_processing_error(script_id, error, stage)
        
        logger.info(f"Broadcasted error for script {script_id}: {error}")
        
    except Exception as e:
        logger.warning(f"Failed to broadcast error for script {script_id}: {e}")

def run_in_background(coro):
    """
    Helper to run async coroutine in background from sync context
    Creates new event loop if needed
    """
    try:
        # Try to get existing loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, schedule the task
            asyncio.create_task(coro)
        else:
            # If loop exists but not running, run the coroutine
            loop.run_until_complete(coro)
    except RuntimeError:
        # No loop exists, create new one
        asyncio.run(coro)

# Convenience functions for sync context (Celery workers)
def sync_broadcast_update(script_id: str, stage: str, progress: int, 
                         estimated_time: float = None, details: Dict[str, Any] = None):
    """Synchronous wrapper for broadcast_processing_update"""
    coro = broadcast_processing_update(script_id, stage, progress, estimated_time, details)
    run_in_background(coro)

def sync_broadcast_complete(script_id: str, result: Dict[str, Any]):
    """Synchronous wrapper for broadcast_processing_complete"""
    coro = broadcast_processing_complete(script_id, result)
    run_in_background(coro)

def sync_broadcast_error(script_id: str, error: str, stage: str = None):
    """Synchronous wrapper for broadcast_processing_error"""
    coro = broadcast_processing_error(script_id, error, stage)
    run_in_background(coro)
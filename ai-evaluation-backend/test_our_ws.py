"""
Test our specific WebSocket handler implementation
"""
from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
import uuid
import json
import logging

# Import our WebSocket manager
from app.websockets import websocket_manager

app = FastAPI()

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, 
    token: Optional[str] = Query(None),
    connection_id: Optional[str] = Query(None)
):
    """
    Copy of our WebSocket endpoint for testing
    """
    print(f"WebSocket connection attempt - token: {token}, connection_id: {connection_id}")
    
    # Generate connection ID if not provided
    if not connection_id:
        connection_id = str(uuid.uuid4())
    
    try:
        print(f"Attempting to connect with connection_id: {connection_id}")
        
        # Connect to WebSocket manager
        await websocket_manager.connect(websocket, connection_id)
        
        print(f"WebSocket connected successfully: {connection_id}")
        
        try:
            while True:
                # Receive messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                print(f"Received message: {message}")
                
                # Handle different message types
                message_type = message.get("type")
                
                if message_type == "ping":
                    await websocket_manager.send_personal_message(connection_id, {
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    })
                else:
                    await websocket_manager.send_personal_message(connection_id, {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
                
        except Exception as e:
            print(f"WebSocket inner loop error for {connection_id}: {e}")
        
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.close()
        except:
            pass
    
    finally:
        # Clean up connection
        print(f"Cleaning up connection: {connection_id}")
        websocket_manager.disconnect(connection_id)

@app.get("/")
async def root():
    return {"message": "Testing our WebSocket implementation"}

if __name__ == "__main__":
    print("Starting WebSocket test server with our implementation...")
    print("WebSocket endpoint: ws://localhost:8002/ws")
    uvicorn.run(app, host="localhost", port=8002)
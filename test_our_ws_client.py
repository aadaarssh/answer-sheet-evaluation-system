#!/usr/bin/env python3
"""
Test our WebSocket implementation
"""

import asyncio
import websockets
import json

async def test_our_websocket():
    url = "ws://localhost:8002/ws"
    
    try:
        print(f"Connecting to {url}...")
        
        async with websockets.connect(url) as websocket:
            print("[OK] WebSocket connection successful!")
            
            # Send a ping message
            message = {
                "type": "ping",
                "timestamp": 1234567890
            }
            
            await websocket.send(json.dumps(message))
            print(f"Sent: {message}")
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Received: {response_data}")
            
            return True
            
    except Exception as e:
        print(f"[ERROR] WebSocket connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_our_websocket())
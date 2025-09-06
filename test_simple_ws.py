#!/usr/bin/env python3
"""
Simple WebSocket connection test using Python websockets library
"""

import asyncio
import websockets
import json
import sys

async def test_websocket():
    uri = "ws://localhost:8000/api/ws"
    
    try:
        print(f"Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection successful!")
            
            # Send a ping message
            message = {
                "type": "ping",
                "timestamp": 1234567890
            }
            
            await websocket.send(json.dumps(message))
            print(f"📤 Sent: {message}")
            
            # Wait for response
            response = await websocket.recv()
            print(f"📥 Received: {response}")
            
            print("✅ WebSocket test completed successfully!")
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket connection closed: {e}")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Invalid status code: {e}")
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")

if __name__ == "__main__":
    print("Testing WebSocket connection to FastAPI server...")
    asyncio.run(test_websocket())
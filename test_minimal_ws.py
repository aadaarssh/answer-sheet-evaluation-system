#!/usr/bin/env python3
"""
Test WebSocket connection to minimal server
"""

import asyncio
import websockets
import json

async def test_websocket(url):
    try:
        print(f"Connecting to {url}...")
        
        async with websockets.connect(url) as websocket:
            print("[OK] WebSocket connection successful!")
            
            # Send a test message
            await websocket.send("Hello from test client!")
            
            # Wait for response
            response = await websocket.recv()
            print(f"Received: {response}")
            
            return True
            
    except Exception as e:
        print(f"[ERROR] WebSocket connection failed: {e}")
        return False

async def main():
    print("Testing minimal WebSocket server...")
    
    # Test both endpoints
    urls = [
        "ws://localhost:8001/ws",
        "ws://localhost:8001/api/ws"
    ]
    
    for url in urls:
        success = await test_websocket(url)
        if success:
            print(f"[OK] {url} works!")
        else:
            print(f"[ERROR] {url} failed!")
        print()

if __name__ == "__main__":
    asyncio.run(main())
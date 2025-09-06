"""
Minimal FastAPI WebSocket test to debug the routing issue
"""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        

@app.websocket("/api/ws")
async def websocket_api_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"API Message text was: {data}")
    except Exception as e:
        print(f"WebSocket API error: {e}")

@app.get("/")
async def root():
    return {"message": "Minimal WebSocket test server"}

if __name__ == "__main__":
    print("Starting minimal WebSocket test server...")
    print("WebSocket endpoints:")
    print("  - ws://localhost:8001/ws")
    print("  - ws://localhost:8001/api/ws")
    uvicorn.run(app, host="localhost", port=8001)
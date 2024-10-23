import asyncio
import websockets
import json
from datetime import datetime
from services.sync_service import sync_service

async def websocket_handler(websocket, path):
    """Handle WebSocket connections"""
    try:
        await sync_service.register(websocket)
        await websocket.send(json.dumps({
            "type": "connection",
            "message": "Connected to sync service",
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        while True:
            try:
                message = await websocket.recv()
                # Keep connection alive
                await asyncio.sleep(0.1)
            except websockets.ConnectionClosed:
                break
            
    finally:
        await sync_service.unregister(websocket)

async def start_websocket_server():
    """Start the WebSocket server"""
    return await websockets.serve(websocket_handler, "0.0.0.0", 8765)

import asyncio
import websockets
import json
from datetime import datetime
from services.sync_service import sync_service

async def websocket_handler(websocket, path):
    """Handle WebSocket connections with improved error handling"""
    try:
        await sync_service.register(websocket)
        
        while True:
            try:
                # Keep the connection alive with periodic health checks
                await websocket.ping()
                message = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                
                # Process any incoming messages (for future extensibility)
                if message:
                    try:
                        data = json.loads(message)
                        if data.get('type') == 'ping':
                            await websocket.send(json.dumps({
                                "type": "pong",
                                "timestamp": datetime.utcnow().isoformat()
                            }))
                    except json.JSONDecodeError:
                        pass
                
                await asyncio.sleep(0.1)
                
            except asyncio.TimeoutError:
                try:
                    await websocket.ping()
                except:
                    break
            except websockets.ConnectionClosed:
                break
            except Exception as e:
                await sync_service.broadcast({
                    "type": "error",
                    "message": f"WebSocket error: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                })
                break
    
    finally:
        await sync_service.unregister(websocket)

async def start_websocket_server():
    """Start the WebSocket server"""
    return await websockets.serve(websocket_handler, "0.0.0.0", 8765)

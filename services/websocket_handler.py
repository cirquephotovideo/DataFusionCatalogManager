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
    """Start the WebSocket server with port fallback"""
    ports = [8766, 8767, 8768, 8769, 8770]  # List of ports to try
    
    for port in ports:
        try:
            server = await websockets.serve(websocket_handler, "localhost", port)
            print(f"WebSocket server started on port {port}")
            return server
        except OSError:
            print(f"Port {port} is in use, trying next port...")
            if port == ports[-1]:  # If this was the last port to try
                print(f"Warning: Could not bind WebSocket server to any port. Sync features may be unavailable.")
                return None
            continue  # Try next port
    
    return None  # Fallback return if no ports work

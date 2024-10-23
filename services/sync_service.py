from datetime import datetime
from typing import Dict, List, Tuple
import asyncio
import websockets
import json
from sqlalchemy import text
from models.database import SessionLocal, Catalog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

class SyncService:
    def __init__(self):
        self.connected_clients = set()
        self.scheduler = AsyncIOScheduler()
        self.last_sync = datetime.utcnow()
        
    async def register(self, websocket):
        """Register a new WebSocket client"""
        self.connected_clients.add(websocket)
        
    async def unregister(self, websocket):
        """Unregister a WebSocket client"""
        self.connected_clients.remove(websocket)
        
    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients"""
        if self.connected_clients:
            websockets_copy = self.connected_clients.copy()
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in websockets_copy]
            )
    
    async def check_for_updates(self):
        """Check for catalog updates"""
        db = SessionLocal()
        try:
            # Use scalar() to get the actual integer value
            update_count = db.execute(text(
                """
                SELECT COUNT(*) as count 
                FROM catalogs 
                WHERE updated_at > :last_sync
                """
            ), {"last_sync": self.last_sync}).scalar()
            
            if update_count and update_count > 0:
                await self.broadcast({
                    "type": "update",
                    "message": f"Found {update_count} new updates",
                    "timestamp": datetime.utcnow().isoformat()
                })
                self.last_sync = datetime.utcnow()
                
        except Exception as e:
            await self.broadcast({
                "type": "error",
                "message": f"Error checking updates: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
        finally:
            db.close()
    
    def start_scheduler(self):
        """Start the background scheduler"""
        if not self.scheduler.running:
            self.scheduler.add_job(
                self.check_for_updates,
                trigger=IntervalTrigger(seconds=30),
                id='sync_check',
                replace_existing=True
            )
            self.scheduler.start()
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()

sync_service = SyncService()

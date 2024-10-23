from datetime import datetime
from typing import Dict, List, Tuple
import asyncio
import websockets
import json
from sqlalchemy import text
from models.database import SessionLocal, Catalog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from tenacity import retry, stop_after_attempt, wait_exponential

class SyncService:
    def __init__(self):
        self.connected_clients = set()
        self.scheduler = AsyncIOScheduler()
        self.last_sync = datetime.utcnow()
        self.retry_count = 0
        self.max_retries = 3
        
    async def register(self, websocket):
        """Register a new WebSocket client"""
        self.connected_clients.add(websocket)
        await self.broadcast({
            "type": "connection",
            "message": "Connected to sync service",
            "timestamp": datetime.utcnow().isoformat(),
            "client_count": len(self.connected_clients)
        })
        
    async def unregister(self, websocket):
        """Unregister a WebSocket client"""
        self.connected_clients.remove(websocket)
        await self.broadcast({
            "type": "connection",
            "message": "Client disconnected",
            "timestamp": datetime.utcnow().isoformat(),
            "client_count": len(self.connected_clients)
        })
        
    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients with error handling"""
        if self.connected_clients:
            websockets_copy = self.connected_clients.copy()
            failed_clients = set()
            
            for client in websockets_copy:
                try:
                    await client.send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    failed_clients.add(client)
                except Exception as e:
                    print(f"Error broadcasting to client: {str(e)}")
                    failed_clients.add(client)
            
            # Remove failed clients
            for failed_client in failed_clients:
                await self.unregister(failed_client)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def check_for_updates(self):
        """Check for catalog updates with retry mechanism"""
        db = SessionLocal()
        try:
            # Get update statistics
            update_count = db.execute(text(
                """
                SELECT COUNT(*) as count 
                FROM catalogs 
                WHERE updated_at > :last_sync
                """
            ), {"last_sync": self.last_sync}).scalar()
            
            total_records = db.query(Catalog).count()
            
            if update_count and update_count > 0:
                await self.broadcast({
                    "type": "update",
                    "message": f"Found {update_count} new updates",
                    "timestamp": datetime.utcnow().isoformat(),
                    "stats": {
                        "total_records": total_records,
                        "recent_updates": update_count
                    }
                })
                self.last_sync = datetime.utcnow()
                self.retry_count = 0  # Reset retry count on successful sync
                
            # Periodic status update even without changes
            elif self.connected_clients:
                await self.broadcast({
                    "type": "status",
                    "message": "Sync service running",
                    "timestamp": datetime.utcnow().isoformat(),
                    "stats": {
                        "total_records": total_records,
                        "recent_updates": 0
                    }
                })
                
        except Exception as e:
            self.retry_count += 1
            error_msg = f"Error checking updates (attempt {self.retry_count}/{self.max_retries}): {str(e)}"
            await self.broadcast({
                "type": "error",
                "message": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            })
            if self.retry_count >= self.max_retries:
                await self.broadcast({
                    "type": "error",
                    "message": "Max retry attempts reached. Sync service will restart.",
                    "timestamp": datetime.utcnow().isoformat()
                })
                self.restart_scheduler()
            raise  # Re-raise for retry mechanism
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
    
    def restart_scheduler(self):
        """Restart the scheduler after errors"""
        self.stop_scheduler()
        self.retry_count = 0
        self.last_sync = datetime.utcnow()
        self.start_scheduler()

# Global instance
sync_service = SyncService()

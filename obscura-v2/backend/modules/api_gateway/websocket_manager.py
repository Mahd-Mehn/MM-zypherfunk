"""
WebSocket Manager

Handles real-time updates to the frontend via WebSockets.
Bridges Redis Pub/Sub channels to WebSocket clients.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any
from fastapi import WebSocket, WebSocketDisconnect

from shared.services import redis_service

logger = logging.getLogger("obscura.websocket")

class ConnectionManager:
    def __init__(self):
        # Map: user_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.pubsub_task = None

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected: {user_id}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected: {user_id}")

    async def send_personal_message(self, message: Any, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending WS message to {user_id}: {e}")

    async def broadcast(self, message: Any):
        """Broadcast to ALL connected users (e.g. global ticker updates)"""
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting: {e}")

    async def start_redis_listener(self):
        """
        Listens to Redis channels and forwards messages to appropriate WebSockets.
        """
        if self.pubsub_task:
            return

        logger.info("Starting WebSocket Redis Listener...")
        pubsub = redis_service.redis.pubsub()
        
        # Subscribe to relevant channels
        # 1. Global Copy Trades (for visualization/ticker)
        # 2. User specific notifications (we might need a specific channel pattern for this)
        await pubsub.subscribe("queue:copy_trade", "queue:proof_generation")

        async def reader():
            try:
                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        await self._handle_redis_message(message)
            except Exception as e:
                logger.error(f"Redis Listener Error: {e}")

        self.pubsub_task = asyncio.create_task(reader())

    async def _handle_redis_message(self, message):
        channel = message['channel'].decode('utf-8')
        data = json.loads(message['data'])
        
        # Forward to frontend
        # For now, we broadcast everything to everyone for the demo
        # In production, we'd filter by user_id if the message is private
        
        msg_type = "trade_update" if "copy_trade" in channel else "proof_update"
        
        payload = {
            "type": msg_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self.broadcast(payload)

manager = ConnectionManager()

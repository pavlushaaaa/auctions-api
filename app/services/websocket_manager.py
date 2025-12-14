from typing import Dict, List
from fastapi import WebSocket
import json
import asyncio


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.user_connections: Dict[int, Dict[int, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, auction_id: int, user_id: int = None):
        await websocket.accept()

        if auction_id not in self.active_connections:
            self.active_connections[auction_id] = []
        self.active_connections[auction_id].append(websocket)

        if user_id:
            if auction_id not in self.user_connections:
                self.user_connections[auction_id] = {}
            self.user_connections[auction_id][user_id] = websocket

        await self.broadcast_online_count(auction_id)

    def disconnect(self, websocket: WebSocket, auction_id: int, user_id: int = None):
        if auction_id in self.active_connections:
            if websocket in self.active_connections[auction_id]:
                self.active_connections[auction_id].remove(websocket)

            if not self.active_connections[auction_id]:
                del self.active_connections[auction_id]

        if user_id and auction_id in self.user_connections:
            if user_id in self.user_connections[auction_id]:
                del self.user_connections[auction_id][user_id]

            if not self.user_connections[auction_id]:
                del self.user_connections[auction_id]

    async def broadcast(self, auction_id: int, message: dict):
        if auction_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[auction_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)

            for conn in disconnected:
                self.disconnect(conn, auction_id)

    async def broadcast_online_count(self, auction_id: int):
        count = len(self.active_connections.get(auction_id, []))
        await self.broadcast(auction_id, {
            "type": "online_count",
            "count": count
        })

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception:
            pass

    def get_online_users(self, auction_id: int) -> int:
        return len(self.active_connections.get(auction_id, []))


manager = ConnectionManager()

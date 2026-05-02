import asyncio
import uuid
from typing import Dict, List, Set, Optional
from fastapi import WebSocket
from datetime import datetime

class GameSession:
    def __init__(self, start_page: str, target_page: str):
        self.id = str(uuid.uuid4())
        self.start_page = start_page
        self.target_page = target_page
        self.human_current_page = start_page
        self.bot_current_path = [start_page]
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.winner: Optional[str] = None # "human" or "bot"
        self.status = "waiting" # "waiting", "playing", "finished"
        self.bot_delay = 5.0
        self.connections: List[WebSocket] = []
        self.bot_task: Optional[asyncio.Task] = None

    async def broadcast(self, message: dict):
        for connection in self.connections:
            await connection.send_json(message)

class GameManager:
    def __init__(self):
        self.sessions: Dict[str, GameSession] = {}

    def create_session(self, start_page: str, target_page: str) -> GameSession:
        session = GameSession(start_page, target_page)
        self.sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> Optional[GameSession]:
        return self.sessions.get(session_id)

    async def connect(self, session_id: str, websocket: WebSocket):
        session = self.get_session(session_id)
        if session:
            await websocket.accept()
            session.connections.append(websocket)
            return session
        return None

    def disconnect(self, session_id: str, websocket: WebSocket):
        session = self.get_session(session_id)
        if session:
            session.connections.remove(websocket)

game_manager = GameManager()

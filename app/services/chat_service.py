import uuid
from datetime import datetime
from collections import deque
from fastapi import WebSocket

MAX_HISTORY = 50
ALLOWED_ROOMS = ['general', 'support', 'products-discussion', 'random']


class ChatService:
    def __init__(self):
        # Состояние приложения (State)
        self.active_connections: dict[str, WebSocket] = {}
        self.users_data: dict[str, dict] = {}
        self.rooms: dict[str, set[str]] = {room: set() for room in ALLOWED_ROOMS}
        self.history: dict[str, deque] = {room: deque(maxlen=MAX_HISTORY) for room in ALLOWED_ROOMS}

    async def connect(self, websocket: WebSocket, token: str, client_ip: str) -> str:
        """Регистрация нового подключения"""
        await websocket.accept()
        socket_id = str(uuid.uuid4())
        self.active_connections[socket_id] = websocket

        # Логика определения пользователя
        user_name = "Авторизованный" if token else f"Гость {socket_id[:4]}"
        user_id = f"user_{socket_id[:6]}" if token else f"guest_{socket_id[:6]}"

        self.users_data[socket_id] = {
            "user_id": user_id, "name": user_name, "is_guest": not bool(token),
            "current_room": None, "avatar": None
        }
        return socket_id

    async def disconnect(self, socket_id: str):
        """Очистка данных при отключении"""
        user = self.users_data.get(socket_id)
        if user and user["current_room"]:
            room = user["current_room"]
            self.rooms[room].discard(socket_id)
            await self.broadcast(room, "user_left", {"name": user["name"]})

        self.active_connections.pop(socket_id, None)
        self.users_data.pop(socket_id, None)

    # --- Бизнес-методы (Use Cases) ---

    async def join_room(self, socket_id: str, room: str):
        if room not in ALLOWED_ROOMS:
            await self.send_personal(socket_id, "error", {"message": "Комната не найдена"})
            return

        user = self.users_data[socket_id]
        old_room = user["current_room"]

        # Покидаем старую комнату
        if old_room:
            self.rooms[old_room].discard(socket_id)
            await self.broadcast(old_room, "user_left", {"name": user["name"]})

        # Входим в новую
        user["current_room"] = room
        self.rooms[room].add(socket_id)

        # Отправляем историю и уведомляем остальных
        await self.send_personal(socket_id, "room_history", {"room": room, "messages": list(self.history[room])})
        await self.broadcast(room, "user_joined", {"name": user["name"]}, exclude_socket=socket_id)

    async def handle_message(self, socket_id: str, room: str, text: str):
        if room not in ALLOWED_ROOMS: return
        user = self.users_data[socket_id]

        msg_obj = {
            "id": str(uuid.uuid4())[:8], "text": text, "authorName": user["name"],
            "timestamp": datetime.now().isoformat()
        }
        self.history[room].append(msg_obj)
        await self.broadcast(room, "message", msg_obj)

    async def handle_typing(self, socket_id: str, room: str, is_typing: bool):
        if room not in ALLOWED_ROOMS: return
        user = self.users_data[socket_id]
        await self.broadcast(room, "typing_status", {"name": user["name"], "isTyping": is_typing},
                             exclude_socket=socket_id)

    async def get_online_users(self, socket_id: str, room: str):
        if room not in ALLOWED_ROOMS: return
        users_in_room = [self.users_data[sid] for sid in self.rooms[room]]
        await self.send_personal(socket_id, "online_users", {"room": room, "users": users_in_room})

    async def send_personal(self, socket_id: str, event: str, data: dict):
        if ws := self.active_connections.get(socket_id):
            await ws.send_json({"event": event, "data": data})

    async def broadcast(self, room: str, event: str, data: dict, exclude_socket: str = None):
        if room not in self.rooms: return
        for sid in self.rooms[room]:
            if sid == exclude_socket: continue
            if ws := self.active_connections.get(sid):
                await ws.send_json({"event": event, "data": data})

chat_service = ChatService()
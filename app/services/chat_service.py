import uuid
from datetime import datetime
from collections import deque
from typing import Optional
from fastapi import WebSocket

from app.schemas.chat import ALLOWED_ROOMS, OutgoingMessage

MAX_HISTORY = 50


class ChatService:
    """
    Сервисный слой (Use Cases).
    Содержит всю бизнес-логику чата.
    Не зависит от FastAPI роутеров и HTTP протокола.
    """

    def __init__(self):
        # Активные WebSocket соединения: socket_id -> WebSocket
        self.active_connections: dict[str, WebSocket] = {}

        # Данные пользователей: socket_id -> dict
        self.users_data: dict[str, dict] = {}

        # Комнаты: room_name -> set of socket_ids
        self.rooms: dict[str, set[str]] = {
            room: set() for room in ALLOWED_ROOMS
        }

        # История сообщений: room_name -> deque (авто-обрезка при MAX_HISTORY)
        self.history: dict[str, deque] = {
            room: deque(maxlen=MAX_HISTORY) for room in ALLOWED_ROOMS
        }

    # ------------------------------------------------------------------
    # Управление подключениями
    # ------------------------------------------------------------------

    async def connect(
        self,
        websocket: WebSocket,
        token: Optional[str],
        client_ip: str
    ) -> str:
        """
        Принимает новое WebSocket-соединение.
        Возвращает уникальный socket_id.
        """
        await websocket.accept()
        socket_id = str(uuid.uuid4())
        self.active_connections[socket_id] = websocket

        # Определяем пользователя по токену (заглушка — в реальном проекте JWT-проверка)
        if token:
            user_id = f"user_{socket_id[:6]}"
            user_name = "Пользователь"
            is_guest = False
            avatar = None
        else:
            user_id = f"guest_{socket_id[:6]}"
            user_name = f"Гость {socket_id[:4].upper()}"
            is_guest = True
            avatar = None

        self.users_data[socket_id] = {
            "user_id": user_id,
            "name": user_name,
            "is_guest": is_guest,
            "current_room": None,
            "avatar": avatar,
        }

        connect_time = datetime.now().strftime("%H:%M:%S")
        print(
            f"[{connect_time}] CONNECT | socket_id={socket_id} "
            f"| ip={client_ip} | user={user_name}"
        )
        return socket_id

    async def disconnect(self, socket_id: str) -> None:
        """
        Корректно отключает пользователя:
        - Удаляет из текущей комнаты
        - Уведомляет других участников
        - Очищает данные
        """
        user = self.users_data.get(socket_id)

        if user and user["current_room"]:
            room = user["current_room"]
            self.rooms[room].discard(socket_id)
            await self._broadcast_to_room(
                room=room,
                event="user_left",
                data={"userId": user["user_id"], "name": user["name"], "room": room},
            )
            # Обновляем список участников для оставшихся
            await self._send_online_users_to_room(room)

        self.active_connections.pop(socket_id, None)
        self.users_data.pop(socket_id, None)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] DISCONNECT | socket_id={socket_id}")

    # ------------------------------------------------------------------
    # Use Cases (Бизнес-логика)
    # ------------------------------------------------------------------

    async def join_room(self, socket_id: str, room: str) -> None:
        """
        Переводит пользователя в новую комнату:
        1. Покидает старую комнату
        2. Входит в новую
        3. Отправляет историю
        4. Уведомляет участников
        """
        if room not in ALLOWED_ROOMS:
            await self._send_error(socket_id, "Комната не существует")
            return

        user = self.users_data[socket_id]
        old_room = user["current_room"]

        # Покидаем старую комнату
        if old_room and old_room != room:
            self.rooms[old_room].discard(socket_id)
            await self._broadcast_to_room(
                room=old_room,
                event="user_left",
                data={"userId": user["user_id"], "name": user["name"], "room": old_room},
            )
            await self._send_online_users_to_room(old_room)

        # Входим в новую
        user["current_room"] = room
        self.rooms[room].add(socket_id)

        # Отправляем историю только что вошедшему
        await self._send_personal(
            socket_id=socket_id,
            event="room_history",
            data={
                "room": room,
                "messages": list(self.history[room]),
            },
        )

        # Уведомляем остальных участников комнаты
        await self._broadcast_to_room(
            room=room,
            event="user_joined",
            data={"userId": user["user_id"], "name": user["name"], "room": room},
            exclude_socket=socket_id,
        )

        # Обновляем список участников для всех в комнате
        await self._send_online_users_to_room(room)

    async def leave_room(self, socket_id: str, room: str) -> None:
        """Явный выход пользователя из комнаты"""
        user = self.users_data.get(socket_id)
        if not user or socket_id not in self.rooms.get(room, set()):
            return

        self.rooms[room].discard(socket_id)
        user["current_room"] = None

        await self._broadcast_to_room(
            room=room,
            event="user_left",
            data={"userId": user["user_id"], "name": user["name"], "room": room},
        )
        await self._send_online_users_to_room(room)

    async def send_message(self, socket_id: str, room: str, text: str) -> None:
        """
        Обрабатывает отправку сообщения:
        1. Создает объект сообщения
        2. Сохраняет в историю
        3. Рассылает всем в комнате
        """
        if room not in ALLOWED_ROOMS:
            await self._send_error(socket_id, "Нельзя отправить сообщение в эту комнату")
            return

        user = self.users_data[socket_id]

        msg = OutgoingMessage(
            id=str(uuid.uuid4())[:8],
            text=text,
            authorId=user["user_id"],
            authorName=user["name"],
            authorAvatar=user.get("avatar"),
            timestamp=datetime.now().isoformat(),
        )

        # Сохраняем в историю (deque сам обрежет при превышении MAX_HISTORY)
        self.history[room].append(msg.model_dump())

        # Рассылаем ВСЕМ в комнате (включая отправителя)
        await self._broadcast_to_room(room=room, event="message", data=msg.model_dump())

    async def handle_typing(self, socket_id: str, room: str, is_typing: bool) -> None:
        """Рассылает статус набора текста всем, кроме самого печатающего"""
        if room not in ALLOWED_ROOMS:
            return

        user = self.users_data[socket_id]
        await self._broadcast_to_room(
            room=room,
            event="typing_status",
            data={
                "userId": user["user_id"],
                "name": user["name"],
                "isTyping": is_typing,
            },
            exclude_socket=socket_id,
        )

    async def get_online_users(self, socket_id: str, room: str) -> None:
        """Отправляет список онлайн-пользователей в комнате конкретному клиенту"""
        if room not in ALLOWED_ROOMS:
            return

        users_in_room = [
            self.users_data[sid]
            for sid in self.rooms[room]
            if sid in self.users_data
        ]
        await self._send_personal(
            socket_id=socket_id,
            event="online_users",
            data={"room": room, "users": users_in_room},
        )

    # ------------------------------------------------------------------
    # Вспомогательные приватные методы
    # ------------------------------------------------------------------

    async def _send_personal(self, socket_id: str, event: str, data: dict) -> None:
        """Отправка события конкретному клиенту"""
        ws = self.active_connections.get(socket_id)
        if ws:
            try:
                await ws.send_json({"event": event, "data": data})
            except Exception as e:
                print(f"[ERROR] _send_personal: {e}")

    async def _broadcast_to_room(
        self,
        room: str,
        event: str,
        data: dict,
        exclude_socket: Optional[str] = None,
    ) -> None:
        """Рассылка события всем клиентам в комнате"""
        if room not in self.rooms:
            return

        message = {"event": event, "data": data}
        disconnected = []

        for sid in list(self.rooms[room]):
            if sid == exclude_socket:
                continue
            ws = self.active_connections.get(sid)
            if ws:
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(sid)

        # Чистим отвалившихся
        for sid in disconnected:
            self.rooms[room].discard(sid)
            self.active_connections.pop(sid, None)
            self.users_data.pop(sid, None)

    async def _send_online_users_to_room(self, room: str) -> None:
        """Рассылает обновленный список участников всем в комнате"""
        users_in_room = [
            self.users_data[sid]
            for sid in self.rooms[room]
            if sid in self.users_data
        ]
        await self._broadcast_to_room(
            room=room,
            event="online_users",
            data={"room": room, "users": users_in_room},
        )

    async def _send_error(self, socket_id: str, message: str) -> None:
        """Отправка ошибки конкретному клиенту"""
        await self._send_personal(
            socket_id=socket_id,
            event="error",
            data={"message": message},
        )

chat_service = ChatService()
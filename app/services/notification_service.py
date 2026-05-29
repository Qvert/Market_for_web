import uuid
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional
from fastapi import WebSocket

from app.schemas.notification_schemas import NotificationPayload, NotificationType


class NotificationService:
    def __init__(self):
        self.subscribers: dict[str, dict] = {}
        self.ntfy_url = "https://ntfy.sh"

    async def subscribe(self, websocket: WebSocket, user_id: Optional[str] = None) -> str:
        await websocket.accept()
        socket_id = str(uuid.uuid4())
        self.subscribers[socket_id] = {
            "ws": websocket,
            "user_id": user_id or f"guest_{socket_id[:6]}",
            "joined": datetime.now().isoformat(),
        }
        return socket_id

    def unsubscribe(self, socket_id: str) -> None:
        if socket_id in self.subscribers:
            del self.subscribers[socket_id]

    # --- Отправка через встроенный urllib (Заменяет requests) ---

    def _send_external_push(self, topic: str, title: str, body: str, click_url: str = ""):
        """Вспомогательный метод для отправки через urllib"""
        url = f"{self.ntfy_url}/{topic}"

        # Кодируем заголовки (ntfy любит UTF-8 в заголовках через плейн-текст)
        headers = {
            "Title": title.encode('utf-8'),
            "Priority": "high",
            "Tags": "bell"
        }
        if click_url:
            headers["Click"] = click_url

        try:
            # Создаем запрос
            req = urllib.request.Request(
                url,
                data=body.encode('utf-8'),
                headers=headers,
                method='POST'
            )
            # Отправляем
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception as e:
            print(f"[ntfy] Ошибка отправки: {e}")
            return False

    async def broadcast(self, notification: NotificationPayload) -> int:
        delivered = 0
        # 1. WebSocket
        for socket_id in list(self.subscribers.keys()):
            if await self._send_to_socket(socket_id, notification):
                delivered += 1

        # 2. ntfy (Общий канал)
        self._send_external_push("app_broadcast_topic", notification.title, notification.body, notification.url)
        return delivered

    async def send_to_user(self, user_id: str, notification: NotificationPayload) -> bool:
        # 1. WebSocket
        ws_success = False
        for socket_id, data in list(self.subscribers.items()):
            if data["user_id"] == user_id:
                if await self._send_to_socket(socket_id, notification):
                    ws_success = True

        # 2. ntfy (Персональный канал по email/id)
        topic = f"ntfy_user_{user_id}"
        self._send_external_push(topic, notification.title, notification.body, notification.url)

        return ws_success

    async def _send_to_socket(self, socket_id: str, notification: NotificationPayload) -> bool:
        subscriber = self.subscribers.get(socket_id)
        if not subscriber: return False
        try:
            await subscriber["ws"].send_json({
                "event": "push_notification",
                "data": {
                    "id": str(uuid.uuid4())[:8],
                    "title": notification.title,
                    "body": notification.body,
                    "type": notification.type,
                    "icon": notification.icon,
                    "url": notification.url,
                    "ts": datetime.now().isoformat(),
                }
            })
            return True
        except:
            return False

    def get_stats(self) -> dict:
        return {"total_subscribers": len(self.subscribers)}


notification_service = NotificationService()
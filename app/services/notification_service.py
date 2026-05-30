import re
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
        ws_delivered = False
        for socket_id, data in list(self.subscribers.items()):
            if data["user_id"] == user_id:
                # Метод _send_to_socket отправит JSON, который JS превратит в Toast
                success = await self._send_to_socket(socket_id, notification)
                if success:
                    ws_delivered = True

        # --- КАНАЛ 2: Внешний Push (ntfy.sh) ---
        # Очищаем email для топика: glscharow@yandex.ru -> glscharow_yandex_ru
        clean_id = re.sub(r'[^a-zA-Z0-9]', '_', user_id)
        topic = f"ntfy_user_{clean_id}"

        self._send_external_push(
            topic=topic,
            title=notification.title,
            body=notification.body,
            click_url=notification.url
        )

        return ws_delivered

    async def _send_to_socket(self, socket_id: str, notification: NotificationPayload) -> bool:
        subscriber = self.subscribers.get(socket_id)
        if not subscriber:
            return False
        try:
            await subscriber["ws"].send_json({
                "event": "push_notification",
                "data": {
                    "id": str(uuid.uuid4())[:8],
                    "title": notification.title,
                    "body": notification.body,
                    "type": notification.type,
                    "ts": datetime.now().isoformat(),
                    "url": notification.url
                }
            })
            return True
        except Exception as e:
            print(f"[WS] Ошибка отправки: {e}")
            return False

    def get_stats(self) -> dict:
        return {"total_subscribers": len(self.subscribers)}


notification_service = NotificationService()
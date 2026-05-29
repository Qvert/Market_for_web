import uuid
from datetime import datetime
from typing import Optional
from fastapi import WebSocket

from app.schemas.notification_schemas import NotificationPayload, NotificationType


class NotificationService:
    """
    Сервис Push-уведомлений.

    Хранит список подписанных WebSocket-клиентов
    и умеет делать рассылку по всем или конкретному пользователю.
    """

    def __init__(self):
        # Подписанные клиенты: socket_id -> {"ws": WebSocket, "user_id": str}
        self.subscribers: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Управление подписками
    # ------------------------------------------------------------------

    async def subscribe(
            self,
            websocket: WebSocket,
            user_id: Optional[str] = None
    ) -> str:
        """
        Регистрирует клиента как подписчика на уведомления.
        Возвращает socket_id для последующего управления.
        """
        await websocket.accept()
        socket_id = str(uuid.uuid4())

        self.subscribers[socket_id] = {
            "ws": websocket,
            "user_id": user_id or f"guest_{socket_id[:6]}",
            "joined": datetime.now().isoformat(),
        }

        print(
            f"[Notifications] Подписка: socket_id={socket_id}, "
            f"user_id={self.subscribers[socket_id]['user_id']}"
        )

        # Сразу отправляем приветственное уведомление
        await self._send_to_socket(socket_id, NotificationPayload(
            title="Уведомления подключены",
            body="Вы будете получать уведомления о заказах, акциях и сообщениях.",
            type=NotificationType.SUCCESS,
            url="/"
        ))

        return socket_id

    def unsubscribe(self, socket_id: str) -> None:
        """Удаляет клиента из списка подписчиков"""
        if socket_id in self.subscribers:
            user_id = self.subscribers[socket_id]["user_id"]
            del self.subscribers[socket_id]
            print(f"[Notifications] Отписка: socket_id={socket_id}, user_id={user_id}")

    # ------------------------------------------------------------------
    # Отправка уведомлений (Use Cases)
    # ------------------------------------------------------------------

    async def broadcast(self, notification: NotificationPayload) -> int:
        """
        Рассылка уведомления ВСЕМ подписанным клиентам.
        Возвращает количество успешно доставленных уведомлений.
        """
        delivered = 0
        failed = []

        for socket_id in list(self.subscribers.keys()):
            success = await self._send_to_socket(socket_id, notification)
            if success:
                delivered += 1
            else:
                failed.append(socket_id)

        # Чистим отвалившихся
        for sid in failed:
            self.unsubscribe(sid)

        print(f"[Notifications] Broadcast: доставлено {delivered}/{len(self.subscribers) + len(failed)}")
        return delivered

    async def send_to_user(self, user_id: str, notification: NotificationPayload) -> bool:
        """
        Отправка уведомления конкретному пользователю.
        Ищет все сокеты с нужным user_id (пользователь может быть в нескольких вкладках).
        """
        delivered = False

        for socket_id, data in list(self.subscribers.items()):
            if data["user_id"] == user_id:
                success = await self._send_to_socket(socket_id, notification)
                if success:
                    delivered = True

        return delivered

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------

    async def _send_to_socket(self, socket_id: str, notification: NotificationPayload) -> bool:
        """Отправляет одно уведомление по socket_id. Возвращает True при успехе."""
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
                    "icon": notification.icon,
                    "url": notification.url,
                    "room": notification.room,
                    "ts": datetime.now().isoformat(),
                }
            })
            return True
        except Exception as e:
            print(f"[Notifications] Ошибка отправки {socket_id}: {e}")
            return False

    def get_stats(self) -> dict:
        """Возвращает статистику подписчиков (для отладки/дашборда)"""
        return {
            "total_subscribers": len(self.subscribers),
            "subscribers": [
                {"socket_id": sid, "user_id": d["user_id"], "joined": d["joined"]}
                for sid, d in self.subscribers.items()
            ]
        }


notification_service = NotificationService()
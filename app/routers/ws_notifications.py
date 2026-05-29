from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.services.notification_service import notification_service
from app.schemas.notification_schemas import (
    NotificationPayload,
    BroadcastRequest,
    NotificationType,
)

router = APIRouter(prefix="/api/notify", tags=["Notifications"])


@router.websocket("/subscribe")
async def notifications_ws(
        websocket: WebSocket,
        token: str = Query(None),
):
    """
    Клиент подключается сюда, чтобы подписаться на Push-уведомления.
    Параметр token здесь используется как user_id для ntfy и сокетов.
    """
    # Определяем пользователя по токену
    user_id = token if token else None

    # Регистрация в нашем сервисе (сохраняем сокет)
    socket_id = await notification_service.subscribe(websocket, user_id)

    try:
        while True:
            # Ожидаем данные от клиента (например, ping)
            raw = await websocket.receive_json()
            event = raw.get("event")

            if event == "unsubscribe":
                await websocket.send_json({
                    "event": "unsubscribed",
                    "data": {"message": "Вы отписались от уведомлений"}
                })
                break

            elif event == "ping":
                await websocket.send_json({
                    "event": "pong",
                    "data": {"status": "subscribed", "socket_id": socket_id}
                })

    except WebSocketDisconnect:
        # Соединение закрыто (вкладка закрыта)
        pass
    finally:
        # Удаляем только из списка активных сокетов.
        # Внешний Push через ntfy всё равно будет работать!
        notification_service.unsubscribe(socket_id)


@router.post("/broadcast")
async def broadcast_notification(payload: BroadcastRequest):
    """
    HTTP эндпоинт для рассылки — это и есть ТРИГГЕР на стороне сервера.
    Он отправляет данные в сокеты И на сторонний сервер ntfy.
    """
    notification = NotificationPayload(
        title=payload.title,
        body=payload.body,
        type=payload.type,
        icon=payload.icon,
        url=payload.url,
    )

    if payload.target == "all":
        # Уйдет всем в сокеты и в общий канал ntfy
        delivered = await notification_service.broadcast(notification)
        return {"status": "ok", "delivered": delivered, "external_service": "sent to ntfy"}
    else:
        # Уйдет конкретному юзеру в сокет и в его персональный канал ntfy
        success = await notification_service.send_to_user(payload.target, notification)
        return {
            "status": "ok",
            "delivered": 1 if success else 0,
            "external_push": "triggered"
        }


@router.post("/send-test")
async def send_test_notification():
    """Тестовая рассылка для проверки системы (Сокеты + ntfy)"""
    delivered = await notification_service.broadcast(NotificationPayload(
        title="🎉 Тестовое уведомление",
        body="Система Push-уведомлений (WS + ntfy) работает корректно!",
        type=NotificationType.SUCCESS,
        url="/"
    ))
    return {"status": "ok", "delivered": delivered}


@router.get("/stats")
async def get_stats():
    """Статистика активных WebSocket-подключений"""
    return notification_service.get_stats()
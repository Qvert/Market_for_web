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
    Этот сокет живёт всё время, пока открыта вкладка.
    """
    # Определяем пользователя по токену (в реальности — JWT проверка)
    user_id = token if token else None
    socket_id = await notification_service.subscribe(websocket, user_id)

    try:
        # Держим соединение живым, обрабатываем входящие команды
        while True:
            raw = await websocket.receive_json()
            event = raw.get("event")

            # Клиент может явно отписаться
            if event == "unsubscribe":
                await websocket.send_json({
                    "event": "unsubscribed",
                    "data":  {"message": "Вы отписались от уведомлений"}
                })
                break

            # Клиент запрашивает статус подписки
            elif event == "ping":
                await websocket.send_json({
                    "event": "pong",
                    "data":  {"status": "subscribed", "socket_id": socket_id}
                })

    except WebSocketDisconnect:
        pass
    finally:
        notification_service.unsubscribe(socket_id)


@router.post("/broadcast")
async def broadcast_notification(payload: BroadcastRequest):
    """
    HTTP эндпоинт для рассылки уведомлений.
    Можно вызвать из других частей приложения (например, при оформлении заказа).
    """
    notification = NotificationPayload(
        title=payload.title,
        body=payload.body,
        type=payload.type,
        icon=payload.icon,
        url=payload.url,
    )

    if payload.target == "all":
        delivered = await notification_service.broadcast(notification)
        return {"status": "ok", "delivered": delivered}
    else:
        success = await notification_service.send_to_user(payload.target, notification)
        return {"status": "ok", "delivered": 1 if success else 0}


@router.post("/send-test")
async def send_test_notification():
    """Тестовая рассылка для проверки работы системы"""
    delivered = await notification_service.broadcast(NotificationPayload(
        title="🎉 Тестовое уведомление",
        body="Система Push-уведомлений работает корректно!",
        type=NotificationType.SUCCESS,
        url="/"
    ))
    return {"status": "ok", "delivered": delivered}


@router.get("/stats")
async def get_stats():
    """Статистика подписчиков (для отладки)"""
    return notification_service.get_stats()
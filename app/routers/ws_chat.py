from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.config import templates
from app.services.chat_service import chat_service
from app.schemas.chat import (
    WSIncomingMessage,
    JoinRoomPayload,
    LeaveRoomPayload,
    SendMessagePayload,
    TypingPayload,
    GetOnlineUsersPayload,
)

router = APIRouter(tags=["WebSockets"])


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None),
):
    """
    Транспортный слой WebSocket.
    Задача: принять JSON, провалидировать через Pydantic, передать в сервис.
    Никакой бизнес-логики здесь нет.
    """
    client_ip = websocket.client.host
    socket_id = await chat_service.connect(websocket, token, client_ip)

    try:
        while True:
            try:
                raw = await websocket.receive_json()
            except Exception:
                break

            # Валидация базовой структуры {"event": "...", "data": {...}}
            try:
                msg = WSIncomingMessage(**raw)
            except ValidationError:
                await chat_service._send_error(
                    socket_id, "Неверный формат: ожидается {event, data}"
                )
                continue

            event = msg.event
            data = msg.data

            # Роутинг событий -> сервис
            try:
                if event == "join_room":
                    payload = JoinRoomPayload(**data)
                    await chat_service.join_room(socket_id, payload.room)

                elif event == "leave_room":
                    payload = LeaveRoomPayload(**data)
                    await chat_service.leave_room(socket_id, payload.room)

                elif event == "send_message":
                    payload = SendMessagePayload(**data)
                    await chat_service.send_message(socket_id, payload.room, payload.text)

                elif event == "typing":
                    payload = TypingPayload(**data)
                    await chat_service.handle_typing(socket_id, payload.room, payload.isTyping)

                elif event == "get_online_users":
                    payload = GetOnlineUsersPayload(**data)
                    await chat_service.get_online_users(socket_id, payload.room)

                else:
                    await chat_service._send_error(socket_id, f"Неизвестное событие: {event}")

            except ValidationError as e:
                await chat_service._send_error(socket_id, f"Ошибка данных: {e.errors()[0]['msg']}")

    except WebSocketDisconnect:
        pass
    finally:
        await chat_service.disconnect(socket_id)
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from pydantic import ValidationError

from app.services.chat_service import chat_service
from app.schemas.chat import WSMessage

router = APIRouter()


@router.websocket("/ws")
async def websocket_chat_endpoint(websocket: WebSocket, token: str = Query(None)):
    client_ip = websocket.client.host
    socket_id = await chat_service.connect(websocket, token, client_ip)

    try:
        while True:
            raw_data = await websocket.receive_json()

            try:
                # Валидация входящего JSON через Pydantic схему
                msg = WSMessage(**raw_data)
            except ValidationError:
                await chat_service.send_personal(socket_id, "error", {"message": "Неверный формат данных"})
                continue

            # Роутинг событий в Service-слой
            if msg.event == "join_room":
                await chat_service.join_room(socket_id, msg.data.get("room"))

            elif msg.event == "send_message":
                await chat_service.handle_message(socket_id, msg.data.get("room"), msg.data.get("text"))

            elif msg.event == "typing":
                await chat_service.handle_typing(socket_id, msg.data.get("room"), msg.data.get("isTyping"))

            elif msg.event == "get_online_users":
                await chat_service.get_online_users(socket_id, msg.data.get("room"))

    except WebSocketDisconnect:
        await chat_service.disconnect(socket_id)
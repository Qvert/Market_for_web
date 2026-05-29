from pydantic import BaseModel, field_validator
from typing import Any, Dict, Optional

ALLOWED_ROOMS = ['general', 'support', 'products-discussion', 'random']

class WSIncomingMessage(BaseModel):
    """Базовая схема входящего WebSocket сообщения"""
    event: str
    data: Dict[str, Any] = {}

class JoinRoomPayload(BaseModel):
    room: str

    @field_validator('room')
    @classmethod
    def room_must_be_valid(cls, v):
        if v not in ALLOWED_ROOMS:
            raise ValueError(f"Комната '{v}' не существует")
        return v

class LeaveRoomPayload(BaseModel):
    room: str

class SendMessagePayload(BaseModel):
    room: str
    text: str

    @field_validator('text')
    @classmethod
    def text_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Сообщение не может быть пустым")
        return v.strip()

class TypingPayload(BaseModel):
    room: str
    isTyping: bool

class GetOnlineUsersPayload(BaseModel):
    room: str

class OutgoingMessage(BaseModel):
    """Схема исходящего сообщения"""
    id: str
    text: str
    authorId: str
    authorName: str
    authorAvatar: Optional[str] = None
    timestamp: str

class UserInfo(BaseModel):
    user_id: str
    name: str
    is_guest: bool
    current_room: Optional[str] = None
    avatar: Optional[str] = None
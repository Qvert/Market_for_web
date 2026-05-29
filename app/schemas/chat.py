from pydantic import BaseModel
from typing import Any, Dict, Optional

class WSMessage(BaseModel):
    event: str
    data: Dict[str, Any] = {}

class JoinRoomData(BaseModel):
    room: str

class SendMessageData(BaseModel):
    room: str
    text: str

class TypingData(BaseModel):
    room: str
    isTyping: bool
from pydantic import BaseModel
from typing import Optional
from enum import Enum


class NotificationType(str, Enum):
    """Типы уведомлений"""
    INFO    = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR   = "error"
    ORDER   = "order"      # Новый заказ
    PROMO   = "promo"      # Акция/скидка
    CHAT    = "chat"       # Новое сообщение в чате


class SubscribePayload(BaseModel):
    """Клиент подписывается на уведомления"""
    event: str  # Должен быть "subscribe"
    data: dict  = {}


class NotificationPayload(BaseModel):
    """Схема уведомления для отправки клиенту"""
    title:   str
    body:    str
    type:    NotificationType = NotificationType.INFO
    icon:    Optional[str]    = "/static/img/logo.png"
    url:     Optional[str]    = "/"   # Куда вести при клике
    room:    Optional[str]    = None  # Если уведомление о сообщении в комнате


class BroadcastRequest(BaseModel):
    """
    Схема для HTTP-запроса рассылки уведомлений.
    Используется в REST эндпоинте /api/notify/broadcast
    """
    title:      str
    body:       str
    type:       NotificationType = NotificationType.INFO
    icon:       Optional[str]    = None
    url:        Optional[str]    = "/"
    target:     str              = "all"  # "all" или конкретный user_id
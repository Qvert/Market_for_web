# app/schemas/fcm_schemas.py
from pydantic import BaseModel
from typing import Optional
from enum import Enum


class TriggerType(str, Enum):
    """
    Типы триггеров, которые вызывают рассылку уведомлений.
    Пункт задания: "триггер произошедший на стороне сервера"
    """
    NEW_MESSAGE   = "new_message"    # Новое сообщение в чате
    NEW_ORDER     = "new_order"      # Оформлен заказ
    ORDER_STATUS  = "order_status"   # Изменился статус заказа
    PRICE_DROP    = "price_drop"     # Снижение цены на товар
    NEW_PRODUCT   = "new_product"    # Новый товар в каталоге
    PROMO         = "promo"          # Акция/промокод
    CUSTOM        = "custom"         # Произвольное уведомление


class SaveTokenRequest(BaseModel):
    """Клиент отправляет свой FCM токен на сервер"""
    token:      str
    user_agent: Optional[str] = None


class FCMNotification(BaseModel):
    """Структура уведомления для отправки через FCM"""
    title:      str
    body:       str
    icon:       Optional[str] = "/static/img/logo.png"
    url:        Optional[str] = "/"
    image:      Optional[str] = None


class TriggerRequest(BaseModel):
    """
    HTTP запрос для ручного запуска триггера.
    В реальном проекте триггеры вызываются автоматически из кода.
    """
    trigger:      TriggerType
    user_id:      Optional[str] = None   # None = рассылка всем
    extra_data:   Optional[dict] = {}    # Дополнительные данные


class BroadcastRequest(BaseModel):
    """Произвольная рассылка всем подписчикам"""
    title:    str
    body:     str
    url:      Optional[str] = "/"
    image:    Optional[str] = None
    user_id:  Optional[str] = None       # None = всем
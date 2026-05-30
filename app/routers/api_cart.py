from fastapi import APIRouter, Request, Depends, status, HTTPException

from app.data import PRODUCTS
from app.schemas.cart import CartItemAdd, CartItemUpdate
from app.security import get_current_user
from app.services.notification_service import notification_service
from app.schemas.notification_schemas import NotificationPayload, NotificationType

router = APIRouter(prefix="/api/cart", tags=["Cart"])

@router.get("")
async def get_cart(request: Request, current_user: dict = Depends(get_current_user)):
    return request.session.get("cart", {})


@router.post("/items")
async def add_to_cart(request: Request, payload: dict):
    product_id = payload.get("product_id")
    quantity = payload.get("quantity", 1)

    # 1. Логика корзины (обычно через сессии)
    cart = request.session.get("cart", {})
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)

    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    # Сохраняем в сессию
    cart[str(product_id)] = {"name": product["name"], "price": product["price"], "quantity": quantity}
    request.session["cart"] = cart

    # 2. ТРИГГЕР: Отправляем Push-уведомление конкретному пользователю
    user_email = request.session.get("user")  # Твой glscharow@yandex.ru

    if user_email:
        await notification_service.send_to_user(user_email, NotificationPayload(
            title="Корзина обновлена",
            body=f"Товар '{product['name']}' добавлен в корзину!",
            type=NotificationType.SUCCESS,
            url="/cart"
        ))

    return {"status": "success", "cart_count": len(cart)}

@router.put("/items/{product_id}")
async def update_cart(product_id: int, item: CartItemUpdate, request: Request, current_user: dict = Depends(get_current_user)):
    if item.quantity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Кол-во < 0")
    cart = request.session.get("cart", {})
    i_id_str = str(product_id)

    if i_id_str not in cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не в корзине")

    cart[i_id_str]["quantity"] = item.quantity
    request.session["cart"] = cart
    return cart[i_id_str]

@router.delete("/items/{product_id}")
async def delete_from_cart(product_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    cart = request.session.get("cart", {})
    i_id_str = str(product_id)

    if i_id_str in cart:
        del cart[i_id_str]
        request.session["cart"] = cart

    return {"message": "Товар удалён"}

@router.get("/count")
async def get_cart_count(request: Request):
    cart = request.session.get("cart", [])
    return {"count": len(cart)}

@router.delete("/clear")
async def clear_cart(request: Request, current_user: dict = Depends(get_current_user)):
    request.session["cart"] = {}
    return {"message": "Корзина очищена"}


@router.post("/checkout")
async def checkout(request: Request):
    """Эндпоинт 'Оформить заказ'"""
    user_email = request.session.get("user")
    cart = request.session.get("cart", {})

    if not cart:
        raise HTTPException(status_code=400, detail="Корзина пуста")

    request.session["cart"] = {}

    if user_email:
        await notification_service.send_to_user(user_email, NotificationPayload(
            title="📦 Заказ оформлен!",
            body=f"Ваш заказ на сумму {sum(item['price'] for item in cart.values())} руб. принят в обработку.",
            type=NotificationType.ORDER,
            url="/"
        ))

    return {"status": "ok", "message": "Заказ создан"}
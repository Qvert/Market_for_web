from fastapi import APIRouter, Request, Depends, status, HTTPException
from app.modules.catalog.service import catalog_service
from app.security import get_current_user
from app.services.notification_service import notification_service
from app.schemas.notification_schemas import NotificationPayload, NotificationType

router = APIRouter(prefix="/api/cart", tags=["Cart"])

class CartService:
    def get_cart(self, request: Request):
        return request.session.get("cart", {})

    async def add_item(self, request: Request, product_id: int, quantity: int):
        cart = self.get_cart(request)
        product = catalog_service.get_product(product_id)

        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")

        cart[str(product_id)] = {
            "name": product.name,
            "price": product.price,
            "quantity": quantity
        }
        request.session["cart"] = cart
        
        user_email = request.session.get("user")
        if user_email:
            await notification_service.send_to_user(user_email, NotificationPayload(
                title="Корзина обновлена",
                body=f"Товар '{product.name}' добавлен в корзину!",
                type=NotificationType.SUCCESS,
                url="/cart"
            ))
        return len(cart)

    def update_item(self, request: Request, product_id: int, quantity: int):
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="Кол-во < 0")
        cart = self.get_cart(request)
        pid_str = str(product_id)
        if pid_str not in cart:
            raise HTTPException(status_code=404, detail="Товар не в корзине")
        cart[pid_str]["quantity"] = quantity
        request.session["cart"] = cart
        return cart[pid_str]

    def remove_item(self, request: Request, product_id: int):
        cart = self.get_cart(request)
        pid_str = str(product_id)
        if pid_str in cart:
            del cart[pid_str]
            request.session["cart"] = cart

    def clear(self, request: Request):
        request.session["cart"] = {}

cart_logic_service = CartService()

@router.get("")
async def get_cart(request: Request, current_user=Depends(get_current_user)):
    return cart_logic_service.get_cart(request)

@router.post("/items")
async def add_to_cart(request: Request, payload: dict):
    count = await cart_logic_service.add_item(
        request, 
        payload.get("product_id"), 
        payload.get("quantity", 1)
    )
    return {"status": "success", "cart_count": count}

@router.put("/items/{product_id}")
async def update_cart(product_id: int, payload: dict, request: Request, current_user=Depends(get_current_user)):
    return cart_logic_service.update_item(request, product_id, payload.get("quantity"))

@router.delete("/items/{product_id}")
async def delete_from_cart(product_id: int, request: Request, current_user=Depends(get_current_user)):
    cart_logic_service.remove_item(request, product_id)
    return {"message": "Товар удалён"}

@router.get("/count")
async def get_cart_count(request: Request):
    return {"count": len(cart_logic_service.get_cart(request))}

@router.delete("/clear")
async def clear_cart(request: Request, current_user=Depends(get_current_user)):
    cart_logic_service.clear(request)
    return {"message": "Корзина очищена"}

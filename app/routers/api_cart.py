from fastapi import APIRouter, Request, Depends, status, HTTPException
from pydantic import BaseModel

from app.data import PRODUCTS
from app.security import get_current_user

router = APIRouter(prefix="/api/cart", tags=["Cart"])

class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemUpdate(BaseModel):
    quantity: int

@router.get("")
async def get_cart(request: Request, current_user: dict = Depends(get_current_user)):
    return request.session.get("cart", {})


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def add_to_cart(item: CartItemAdd, request: Request, current_user: dict = Depends(get_current_user)):
    product = next((i for i in PRODUCTS if i["id"] == item.product_id), None)
    if not product:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")

    cart = request.session.get("cart", {})
    i_id_str = str(item.product_id)

    if i_id_str in cart:
        cart[i_id_str]["quantity"] += item.quantity
    else:
        cart[i_id_str] = {
            "productId": item.product_id,
            "name": product["name"],
            "price": product["price"],
            "quantity": item.quantity
        }
    request.session["cart"] = cart
    return cart[i_id_str]

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
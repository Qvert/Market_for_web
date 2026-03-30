from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.config import templates
from app.data import fake_products

router = APIRouter(prefix="/cart", tags=["Cart"])

def get_base_context(request: Request, **kwargs):
    cart = request.session.get("cart", {})
    # Считаем общее количество товаров в корзине
    cart_count = sum(item["quantity"] for item in cart.values())

    context = {"request": request, "cart_count": cart_count}
    context.update(kwargs)
    return context

@router.post("/add/{product_id}")
async def add_to_cart(request: Request, product_id: int):
    product = fake_products[product_id - 1]
    if not product:
        return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)
    cart = request.session.get("cart", {})

    p_id_str = str(product_id)
    if p_id_str in cart:
        cart[p_id_str]["quantity"] += 1
    else:
        cart[p_id_str] = {
            "name": product["name"],
            "price": product["price"],
            "quantity": 1
        }

    request.session["cart"] = cart
    return RedirectResponse(url="/products", status_code=HTTP_303_SEE_OTHER)

@router.get("/", response_class=HTMLResponse)
async def view_cart(request: Request):
    cart = request.session.get("cart", {})

    total_sum = sum(item["price"] * item["quantity"] for item in cart.values())
    is_empty = len(cart) == 0

    return templates.TemplateResponse(
        "cart.html",
        get_base_context(
            request, cart_items=cart, total_sum=total_sum, is_empty=is_empty
        )
    )

@router.post("/remove/{product_id}")
async def remove_from_cart(request: Request, product_id: int):
    cart = request.session.get("cart", {})
    p_id_str = str(product_id)

    if p_id_str in cart:
        del cart[p_id_str]
        request.session["cart"] = cart
    return RedirectResponse(url="/cart", status_code=HTTP_303_SEE_OTHER)

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.config import templates
from app.modules.catalog.service import catalog_service

router = APIRouter(tags=["Views"])

@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Главная"})

@router.get("/products")
async def catalog(request: Request):
    products = catalog_service.get_products()
    return templates.TemplateResponse("products.html", {
        "request": request,
        "title": "Каталог",
        "products": products
    })


@router.get("/product/{product_id}")
async def get_product_detail_page(request: Request, product_id: int):
    product = catalog_service.get_product(product_id)
    if not product:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    return templates.TemplateResponse("product_detail.html", {
        "request": request,
        "product": product,
        "title": product.name
    })

@router.get("/cart")
async def cart_page(request: Request):
    cart = request.session.get("cart", {})
    total_sum = sum(item["price"] * item["quantity"] for item in cart.values())
    is_empty = len(cart) == 0

    return templates.TemplateResponse("cart.html", {
        "request": request,
        "cart_items": cart,
        "total_sum": total_sum,
        "is_empty": is_empty,
        "title": "Корзина"
    })

@router.get("/auth/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "title": "Вход"})

@router.get("/auth/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "title": "Регистрация"})

@router.get("/auth/logout")
async def logout_view(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
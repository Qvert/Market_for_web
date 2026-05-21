from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.config import templates
from app.data import PRODUCTS

router = APIRouter(tags=["Views"])

@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Главная"})

@router.get("/products")
async def catalog(request: Request):
    products = PRODUCTS
    return templates.TemplateResponse("products.html", {"request": request, "title": "Каталог", "product": products})

@router.get("/cart")
async def cart_page(request: Request):
    return templates.TemplateResponse("cart.html", {"request": request, "title": "Корзина"})

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
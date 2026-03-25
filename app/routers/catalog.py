from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from app.data import fake_products, categories
from app.config import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Главная страница"""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Главная страница"}
    )

@router.get("/products", response_class=HTMLResponse)
async def read_products(request: Request):
    """Страница каталога товаров"""
    return templates.TemplateResponse(
        request=request,
        name="products.html",
        context={
            "title": "Каталог товаров",
            "products": fake_products
        }
    )

@router.get("/product/{product_id}", response_class=HTMLResponse)
async def read_product(request: Request, product_id: int):
    product = next((p for p in fake_products if p["id"] == product_id), None)
    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    return templates.TemplateResponse(
        request=request,
        name="product_detail.html",
        context={"product": product}
    )

@router.get("/category/{category_id}", response_class=HTMLResponse)
async def read_category(request: Request, category_id: int):
    if category_id not in categories:
        return HTTPException(status_code=404, detail="Категория не найдена")
    category_products = [p for p in fake_products if p.get("category_id") == category_id]
    return templates.TemplateResponse(
        request=request,
        name="products.html",
        context={
            "title": categories[category_id],
            "products": category_products,
        }
    )



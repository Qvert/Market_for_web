from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from data import fake_products

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Главная страница"""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Главная страница"}
    )

@app.get("/products", response_class=HTMLResponse)
async def read_products(request: Request):
    """Страница каталога товаров"""
    return templates.TemplateResponse(
        request=request,
        name="products.html",
        context={
            "title": "Каталог товаров",
            "products": fake_products  # Передаем список товаров в шаблон
        }
    )

@app.get("/product/{product_id}", responses=HTMLResponse)
async def read_product(request: Request, product_id: int):
    product = next((p for p in fake_products if p["id"] == product_id), None)

    # Если товар не найден — выбрасываем 404 ошибку
    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    return templates.TemplateResponse(
        request=request,
        name="product_detail.html",
        context={"product": product}
    )
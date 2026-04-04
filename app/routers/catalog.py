from fastapi import APIRouter, Request, HTTPException, status

from app.data import PRODUCTS, CATEGORIES

router = APIRouter(prefix="/api", tags=["Catalog"])

@router.get("/products")
async def get_products():
    return PRODUCTS

@router.get("/product/{id}")
async def get_product(id: int):
    product = next((i for i in PRODUCTS if i["id"] == id), None)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    return product

@router.get("/categories")
async def get_categories():
    return CATEGORIES

@router.get("/categories/{id}/products")
async def get_products_by_category(id: int):
    category = next((c for c in CATEGORIES if c["id"] == id), None)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена")

    return [p for p in PRODUCTS if p["categoryId"] == id]



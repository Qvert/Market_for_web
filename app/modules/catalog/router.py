from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Query
from .service import catalog_service
from .models import Product, Category

router = APIRouter(prefix="/api/catalog", tags=["Catalog"])

@router.get("/products", response_model=List[Product])
async def get_products(category_id: Optional[int] = Query(None)):
    return catalog_service.get_products(category_id)

@router.get("/product/{id}", response_model=Product)
async def get_product(id: int):
    product = catalog_service.get_product(id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )
    return product

@router.get("/categories", response_model=List[Category])
async def get_categories():
    return catalog_service.get_categories()

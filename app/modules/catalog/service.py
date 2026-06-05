from typing import List, Optional
from .repository import catalog_repository
from .models import Product, Category

class CatalogService:
    def get_products(self, category_id: Optional[int] = None) -> List[Product]:
        if category_id:
            return catalog_repository.get_products_by_category(category_id)
        return catalog_repository.get_all_products()

    def get_product(self, product_id: int) -> Optional[Product]:
        return catalog_repository.get_product_by_id(product_id)

    def get_categories(self) -> List[Category]:
        return catalog_repository.get_all_categories()

catalog_service = CatalogService()

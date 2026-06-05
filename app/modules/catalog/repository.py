from typing import List, Optional
from .models import Product, Category

class CatalogRepository:
    def __init__(self):
        self._categories = [
            Category(id=1, name="Ноутбуки"),
            Category(id=2, name="Периферия")
        ]
        self._products = [
            Product(id=1, categoryId=1, name="Ноутбук ASUS", price=75000, description="..."),
            Product(id=2, categoryId=2, name="Беспроводная мышь", price=1500, description="..."),
            Product(id=3, categoryId=2, name="Клавиатура", price=3000, description="...")
        ]

    def get_all_products(self) -> List[Product]:
        return self._products

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        return next((p for p in self._products if p.id == product_id), None)

    def get_all_categories(self) -> List[Category]:
        return self._categories

    def get_products_by_category(self, category_id: int) -> List[Product]:
        return [p for p in self._products if p.categoryId == category_id]

catalog_repository = CatalogRepository()

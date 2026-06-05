from pydantic import BaseModel
from typing import List

class Category(BaseModel):
    id: int
    name: str

class Product(BaseModel):
    id: int
    categoryId: int
    name: str
    price: int
    description: str

from pydantic import BaseModel
from typing import List, Optional


class CategoryRead(BaseModel):
    id: int
    name: str
    slug: str
    parent_id: int | None
    children: List["CategoryRead"] | None = None

    class Config:
        from_attributes = True


class ProductRead(BaseModel):
    id: int
    name: str
    slug: str
    sku: str
    description: Optional[str] = None
    is_active: bool
    category_id: Optional[int] = None

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str
    slug: str
    sku: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    is_active: bool = True


class ProductPriceRead(BaseModel):
    tier: str
    currency: str
    amount: float
    minimum_qty: Optional[int] = None

    class Config:
        from_attributes = True


class ProductDetailRead(ProductRead):
    prices: List[ProductPriceRead] = []
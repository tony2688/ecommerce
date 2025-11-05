from pydantic import BaseModel
from typing import List, Optional


class CheckoutOrderItemRead(BaseModel):
    product_id: int
    name: str
    sku: str
    tier: str
    currency: str
    qty: int
    unit_price: str
    subtotal: str


class CheckoutOrderRead(BaseModel):
    order_id: int
    order_number: str
    cart_id: int
    status: str
    currency: str
    subtotal: str
    shipping_cost: str
    discount_total: str
    grand_total: str


class CheckoutStartResponse(BaseModel):
    ok: bool
    order: CheckoutOrderRead
    items: List[CheckoutOrderItemRead]
    error: Optional[str] = None
    status_code: Optional[int] = None
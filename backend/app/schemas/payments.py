from pydantic import BaseModel
from typing import Optional


class PaymentIntentRead(BaseModel):
    id: int
    status: str
    amount: str
    currency: str
    preference_id: Optional[str] = None
    preference_url: Optional[str] = None


class PaymentsMPCreateResponse(BaseModel):
    ok: bool
    intent: PaymentIntentRead
    error: Optional[str] = None
    status_code: Optional[int] = None


class PaymentsMPWebhookResponse(BaseModel):
    ok: bool
    order_status: str
    order_payment_status: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
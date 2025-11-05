from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, ForeignKey, DateTime, func, Numeric, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from .order import Order


class PaymentIntent(Base):
    __tablename__ = "payment_intents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(16), default="mp", index=True)
    status: Mapped[str] = mapped_column(
        SQLEnum("created", "approved", "rejected", "cancelled", "expired", name="payment_intent_status_enum"),
        default="created",
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    mp_preference_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mp_preference_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mp_payment_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    mp_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mp_external_reference: Mapped[str | None] = mapped_column(String(32), nullable=True)
    raw_request_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_response_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    order: Mapped["Order"] = relationship(back_populates="payments")
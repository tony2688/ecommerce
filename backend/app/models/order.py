from __future__ import annotations
from typing import TYPE_CHECKING, List
from sqlalchemy import Integer, String, ForeignKey, DateTime, func, Numeric, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from .order_item import OrderItem
    from .payment_intent import PaymentIntent
    from .shipment import Shipment


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    cart_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(
        SQLEnum("pending", "addresses_selected", "paid", "cancelled", "expired", name="order_status_enum"),
        default="pending",
        index=True,
    )
    # Estado de pago a nivel de orden (refleja estado de MP)
    payment_status: Mapped[str] = mapped_column(
        SQLEnum("pending", "approved", "rejected", "cancelled", "expired", "in_process", name="order_payment_status_enum"),
        default="pending",
        index=True,
    )
    currency: Mapped[str] = mapped_column(String(3))
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2))
    shipping_cost: Mapped[float] = mapped_column(Numeric(12, 2))
    discount_total: Mapped[float] = mapped_column(Numeric(12, 2))
    grand_total: Mapped[float] = mapped_column(Numeric(12, 2))
    pricing_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tax_profile: Mapped[str | None] = mapped_column(String(40), nullable=True)
    shipping_address_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    billing_address_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Selected address foreign keys (nullable until selected)
    shipping_address_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("addresses.id", ondelete="SET NULL"), index=True, nullable=True)
    billing_address_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("addresses.id", ondelete="SET NULL"), index=True, nullable=True)

    # Snapshots captured at address confirmation stage
    shipping_address_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    billing_address_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    payments: Mapped[List["PaymentIntent"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    shipments: Mapped[List["Shipment"]] = relationship(back_populates="order", cascade="all, delete-orphan")
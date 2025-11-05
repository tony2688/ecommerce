from __future__ import annotations
from typing import TYPE_CHECKING, List
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base

if TYPE_CHECKING:
    from .user import User
    from .cart_item import CartItem

class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="ARS")
    status: Mapped[str] = mapped_column(
        SQLEnum("draft", "locked", name="cart_status_enum"),
        default="draft",
        index=True,
    )
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="carts")
    items: Mapped[List["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan")
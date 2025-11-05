from __future__ import annotations
from sqlalchemy import Integer, String, ForeignKey, Boolean, DateTime, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(SQLEnum("shipping", "billing", name="address_kind_enum"), default="shipping")
    name: Mapped[str] = mapped_column(String(120))
    street: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(120))
    province: Mapped[str] = mapped_column(String(120))
    zip_code: Mapped[str] = mapped_column(String(16))
    country: Mapped[str] = mapped_column(String(2), default="AR")
    phone: Mapped[str | None] = mapped_column(String(24), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")
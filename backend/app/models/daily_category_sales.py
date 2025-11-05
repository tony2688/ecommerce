from __future__ import annotations
from sqlalchemy import Integer, Date, String, Numeric, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class DailyCategorySales(Base):
    __tablename__ = "daily_category_sales"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, nullable=True)
    category_name: Mapped[str] = mapped_column(String(160), nullable=False)
    revenue_paid: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("date", "category_id", name="uq_daily_category_sales_date_cat"),
    )
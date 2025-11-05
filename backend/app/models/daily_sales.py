from __future__ import annotations
from sqlalchemy import Integer, Date, Numeric, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class DailySales(Base):
    __tablename__ = "daily_sales"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    orders_paid: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    orders_cancelled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_paid: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    avg_order_value: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("date", name="uq_daily_sales_date"),
    )
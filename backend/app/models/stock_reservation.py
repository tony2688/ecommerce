from sqlalchemy import Integer, ForeignKey, DateTime, func, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class StockReservation(Base):
    __tablename__ = "stock_reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cart_id: Mapped[int] = mapped_column(Integer, ForeignKey("carts.id"), index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), index=True)
    location_id: Mapped[int] = mapped_column(Integer, ForeignKey("inventory_locations.id"), index=True)
    qty: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(SQLEnum("active", "released", "consumed", name="reservation_status_enum"), index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
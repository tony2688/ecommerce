from sqlalchemy import ForeignKey, String, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ProductPrice(Base):
    __tablename__ = "product_prices"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    tier: Mapped[str] = mapped_column(String(32), nullable=False)  # retail/wholesale
    currency: Mapped[str] = mapped_column(String(3), default="ARS", nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    minimum_qty: Mapped[int | None]
    product = relationship("Product", backref="prices")
    __table_args__ = (UniqueConstraint("product_id", "tier", name="uq_product_tier"),)

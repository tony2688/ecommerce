from sqlalchemy import Date
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class OrderSeq(Base):
    __tablename__ = "order_seq"

    seq_date: Mapped[Date] = mapped_column(Date, primary_key=True)
    last_seq: Mapped[int] = mapped_column(default=0)
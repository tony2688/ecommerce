from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.order_seq import OrderSeq


def next_order_number(db: Session) -> str:
    today = date.today()
    row = db.execute(select(OrderSeq).where(OrderSeq.seq_date == today).with_for_update()).scalar_one_or_none()
    if not row:
        row = OrderSeq(seq_date=today, last_seq=0)
        db.add(row)
        db.flush()
    row.last_seq = int(row.last_seq) + 1
    seq_str = str(row.last_seq).zfill(6)
    return f"{today.strftime('%Y%m%d')}-{seq_str}"
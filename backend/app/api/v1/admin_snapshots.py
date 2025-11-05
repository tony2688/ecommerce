import csv
import io
import logging
from datetime import date, datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin-snapshots"])


def _ensure_admin(user: Dict[str, Any] | Any) -> None:
    if not user or getattr(user, "role", "user") != "admin":
        raise HTTPException(status_code=403, detail="admin_only")


@router.get("/snapshots/daily")
def get_daily_snapshots(
    from_: str = Query(alias="from"),
    to_: str = Query(alias="to"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> Dict[str, Any]:
    _ensure_admin(user)
    start = datetime.strptime(from_, "%Y-%m-%d").date()
    end = datetime.strptime(to_, "%Y-%m-%d").date()
    sql = text(
        """
        SELECT date, orders_paid, orders_cancelled, revenue_paid, avg_order_value
        FROM daily_sales
        WHERE date BETWEEN :from_date AND :to_date
        ORDER BY date
        """
    )
    rows = db.execute(sql, {"from_date": str(start), "to_date": str(end)}).all()
    orders_paid = [{"date": str(r[0]), "count": int(r[1])} for r in rows]
    orders_cancelled = [{"date": str(r[0]), "count": int(r[2])} for r in rows]
    revenue_paid = [{"date": str(r[0]), "amount": float(r[3] or 0.0)} for r in rows]
    avg_order_value = [{"date": str(r[0]), "amount": float(r[4] or 0.0)} for r in rows]
    logger.info("admin_snapshots_daily", extra={"from": str(start), "to": str(end), "rows": len(rows)})
    return {
        "orders_paid": orders_paid,
        "orders_cancelled": orders_cancelled,
        "revenue_paid": revenue_paid,
        "avg_order_value": avg_order_value,
    }


@router.get("/snapshots/categories")
def get_category_snapshots(
    from_: str = Query(alias="from"),
    to_: str = Query(alias="to"),
    limit: int = 10,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> List[Dict[str, Any]]:
    _ensure_admin(user)
    start = datetime.strptime(from_, "%Y-%m-%d").date()
    end = datetime.strptime(to_, "%Y-%m-%d").date()
    sql = text(
        """
        SELECT category_name, SUM(revenue_paid) AS rev, SUM(orders_count) AS cnt
        FROM daily_category_sales
        WHERE date BETWEEN :from_date AND :to_date
        GROUP BY category_name
        ORDER BY rev DESC
        """
    )
    rows = db.execute(sql, {"from_date": str(start), "to_date": str(end)}).all()
    data = [{"category": str(r[0]), "amount": float(r[1] or 0.0), "orders": int(r[2] or 0)} for r in rows]
    data = data[: max(1, int(limit))]
    logger.info("admin_snapshots_categories", extra={"from": str(start), "to": str(end), "rows": len(rows), "limit": limit})
    return data


@router.get("/exports/daily.csv")
def export_daily_csv(
    from_: str = Query(alias="from"),
    to_: str = Query(alias="to"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _ensure_admin(user)
    start = datetime.strptime(from_, "%Y-%m-%d").date()
    end = datetime.strptime(to_, "%Y-%m-%d").date()
    sql = text(
        """
        SELECT date, orders_paid, orders_cancelled, revenue_paid, avg_order_value
        FROM daily_sales
        WHERE date BETWEEN :from_date AND :to_date
        ORDER BY date
        """
    )
    rows = db.execute(sql, {"from_date": str(start), "to_date": str(end)}).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "orders_paid", "orders_cancelled", "revenue_paid", "avg_order_value"])
    for r in rows:
        w.writerow([str(r[0]), int(r[1]), int(r[2]), float(r[3] or 0.0), float(r[4] or 0.0)])
    content = buf.getvalue()
    headers = {"Content-Disposition": f"attachment; filename=daily_{from_}_{to_}.csv"}
    return StreamingResponse(iter([content]), media_type="text/csv; charset=utf-8", headers=headers)


@router.get("/exports/categories.csv")
def export_categories_csv(
    from_: str = Query(alias="from"),
    to_: str = Query(alias="to"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _ensure_admin(user)
    start = datetime.strptime(from_, "%Y-%m-%d").date()
    end = datetime.strptime(to_, "%Y-%m-%d").date()
    sql = text(
        """
        SELECT date, category_name, revenue_paid, orders_count
        FROM daily_category_sales
        WHERE date BETWEEN :from_date AND :to_date
        ORDER BY date, category_name
        """
    )
    rows = db.execute(sql, {"from_date": str(start), "to_date": str(end)}).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "category_name", "revenue_paid", "orders_count"])
    for r in rows:
        w.writerow([str(r[0]), str(r[1]), float(r[2] or 0.0), int(r[3] or 0)])
    content = buf.getvalue()
    headers = {"Content-Disposition": f"attachment; filename=categories_{from_}_{to_}.csv"}
    return StreamingResponse(iter([content]), media_type="text/csv; charset=utf-8", headers=headers)
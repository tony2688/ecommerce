import logging
from datetime import datetime
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.deps import get_db, get_current_user
from app.observability.counters import inc_counter

logger = logging.getLogger(__name__)

TZ = "America/Argentina/Buenos_Aires"
PAID_STATUS = "approved"  # en modelo, el pago aprobado se refleja como 'approved'

router = APIRouter(prefix="/admin/metrics", tags=["admin-metrics"])


def _ensure_admin(user) -> None:
    if getattr(user, "role", "user") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/daily")
def metrics_daily(
    from_: str = Query(alias="from"),
    to_: str = Query(alias="to"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> Dict[str, Any]:
    _ensure_admin(user)
    start = datetime.strptime(from_, "%Y-%m-%d").date()
    end = datetime.strptime(to_, "%Y-%m-%d").date()
    t0 = datetime.utcnow()

    # Agregados por día en TZ local (Buenos Aires)
    sql_total = text(
        """
        SELECT DATE(CONVERT_TZ(o.created_at, 'UTC', :tz)) AS d, COUNT(*) AS cnt
        FROM orders o
        WHERE DATE(CONVERT_TZ(o.created_at, 'UTC', :tz)) BETWEEN :from_date AND :to_date
        GROUP BY d
        ORDER BY d
        """
    )
    rows_total = db.execute(sql_total, {"tz": TZ, "from_date": str(start), "to_date": str(end)}).all()

    sql_paid = text(
        """
        SELECT DATE(CONVERT_TZ(o.created_at, 'UTC', :tz)) AS d, COUNT(*) AS cnt
        FROM orders o
        WHERE o.payment_status = :paid AND DATE(CONVERT_TZ(o.created_at, 'UTC', :tz)) BETWEEN :from_date AND :to_date
        GROUP BY d
        ORDER BY d
        """
    )
    rows_paid = db.execute(sql_paid, {"tz": TZ, "from_date": str(start), "to_date": str(end), "paid": PAID_STATUS}).all()

    sql_cancelled = text(
        """
        SELECT DATE(CONVERT_TZ(o.created_at, 'UTC', :tz)) AS d, COUNT(*) AS cnt
        FROM orders o
        WHERE o.payment_status = 'cancelled' AND DATE(CONVERT_TZ(o.created_at, 'UTC', :tz)) BETWEEN :from_date AND :to_date
        GROUP BY d
        ORDER BY d
        """
    )
    rows_cancelled = db.execute(sql_cancelled, {"tz": TZ, "from_date": str(start), "to_date": str(end)}).all()

    sql_revenue = text(
        """
        SELECT DATE(CONVERT_TZ(o.created_at, 'UTC', :tz)) AS d, SUM(oi.qty * oi.unit_price) AS amt
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.payment_status = :paid AND DATE(CONVERT_TZ(o.created_at, 'UTC', :tz)) BETWEEN :from_date AND :to_date
        GROUP BY d
        ORDER BY d
        """
    )
    rows_revenue = db.execute(sql_revenue, {"tz": TZ, "from_date": str(start), "to_date": str(end), "paid": PAID_STATUS}).all()

    # Mapear por día para calcular AOV
    paid_by_day = {str(r[0]): int(r[1]) for r in rows_paid}
    revenue_by_day = {str(r[0]): float(r[1] or 0.0) for r in rows_revenue}

    def _series(rows: List[tuple], key_name: str) -> List[Dict[str, Any]]:
        out = []
        for r in rows:
            out.append({"date": str(r[0]), key_name: (float(r[1]) if key_name != "count" else int(r[1]))})
        return out

    orders_total = [{"date": str(r[0]), "count": int(r[1])} for r in rows_total]
    orders_paid = [{"date": str(r[0]), "count": int(r[1])} for r in rows_paid]
    orders_cancelled = [{"date": str(r[0]), "count": int(r[1])} for r in rows_cancelled]
    revenue_paid = [{"date": str(r[0]), "amount": float(r[1] or 0.0)} for r in rows_revenue]

    avg_order_value: List[Dict[str, Any]] = []
    # Usar union de días vistos en revenue y paid
    for d in sorted(set(list(revenue_by_day.keys()) + list(paid_by_day.keys()))):
        rev = revenue_by_day.get(d, 0.0)
        cnt = paid_by_day.get(d, 0)
        aov = rev / cnt if cnt > 0 else 0.0
        avg_order_value.append({"date": d, "amount": float(aov)})

    # Observabilidad
    inc_counter("admin.metrics.daily.requests")
    elapsed_ms = int((datetime.utcnow() - t0).total_seconds() * 1000)
    logger.info(
        "admin_metrics_daily",
        extra={"from": str(start), "to": str(end), "elapsed_ms": elapsed_ms},
    )
    return {
        "orders_total": orders_total,
        "orders_paid": orders_paid,
        "orders_cancelled": orders_cancelled,
        "revenue_paid": revenue_paid,
        "avg_order_value": avg_order_value,
    }


@router.get("/categories")
def metrics_categories(
    limit: int = 5,
    from_: str = Query(alias="from"),
    to_: str = Query(alias="to"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> List[Dict[str, Any]]:
    _ensure_admin(user)
    start = datetime.strptime(from_, "%Y-%m-%d").date()
    end = datetime.strptime(to_, "%Y-%m-%d").date()
    t0 = datetime.utcnow()

    sql = text(
        """
        SELECT COALESCE(c.name, 'Sin categoría') AS category, SUM(oi.qty * oi.unit_price) AS amt
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        LEFT JOIN products p ON oi.product_id = p.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE o.payment_status = :paid AND DATE(CONVERT_TZ(o.created_at, 'UTC', :tz)) BETWEEN :from_date AND :to_date
        GROUP BY category
        ORDER BY amt DESC
        """
    )
    rows = db.execute(sql, {"tz": TZ, "from_date": str(start), "to_date": str(end), "paid": PAID_STATUS}).all()
    data = [{"category": str(r[0]), "amount": float(r[1] or 0.0)} for r in rows]
    data = data[: max(1, int(limit))]

    inc_counter("admin.metrics.categories.requests")
    elapsed_ms = int((datetime.utcnow() - t0).total_seconds() * 1000)
    logger.info(
        "admin_metrics_categories",
        extra={"from": str(start), "to": str(end), "elapsed_ms": elapsed_ms, "limit": limit},
    )
    return data


LOW_STOCK_THRESHOLD_DEFAULT = 5


@router.get("/stock")
def metrics_stock(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> Dict[str, Any]:
    _ensure_admin(user)
    t0 = datetime.utcnow()

    # Reservas activas
    sql_res = text("SELECT COUNT(*) FROM stock_reservations WHERE status = 'active'")
    res_count = db.execute(sql_res).scalar() or 0

    # Items con stock bajo (available <= threshold)
    sql_low = text(
        """
        SELECT p.sku, p.name, (si.on_hand - si.committed) AS available
        FROM stock_items si
        JOIN products p ON p.id = si.product_id
        WHERE (si.on_hand - si.committed) <= :threshold
        ORDER BY available ASC
        """
    )
    low_rows = db.execute(sql_low, {"threshold": LOW_STOCK_THRESHOLD_DEFAULT}).all()
    low_items = [
        {
            "sku": str(r[0]),
            "name": str(r[1]),
            "available": int(r[2] or 0),
            "threshold": LOW_STOCK_THRESHOLD_DEFAULT,
        }
        for r in low_rows
    ]

    inc_counter("admin.metrics.stock.requests")
    elapsed_ms = int((datetime.utcnow() - t0).total_seconds() * 1000)
    logger.info("admin_metrics_stock", extra={"elapsed_ms": elapsed_ms, "low_items": len(low_items)})
    return {
        "reservations_active": int(res_count),
        "stock_low_items": low_items,
    }
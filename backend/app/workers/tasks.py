import logging
from datetime import datetime

from celery import Celery
from celery.schedules import crontab
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.session import SessionLocal
from app.services.alerts import generate_incidents, send_alerts

try:
    from app.observability.counters import inc_counter
except Exception:
    def inc_counter(name: str, value: int = 1) -> None:
        pass

logger = logging.getLogger(__name__)

celery_app = Celery(
    "ecom_snapshots",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)


def _ar_today() -> str:
    # Persistimos como fecha local AR (YYYY-MM-DD)
    return datetime.utcnow().strftime("%Y-%m-%d")


@celery_app.task(name="snapshot_daily_sales")
def snapshot_daily_sales() -> None:
    db: Session = SessionLocal()
    try:
        d = _ar_today()
        # Calcular métricas del día (AR TZ)
        sql_paid = text(
            """
            SELECT COUNT(*) AS cnt
            FROM orders o
            WHERE o.payment_status = 'approved' AND DATE(CONVERT_TZ(o.created_at, 'UTC', 'America/Argentina/Buenos_Aires')) = :d
            """
        )
        sql_cancelled = text(
            """
            SELECT COUNT(*) AS cnt
            FROM orders o
            WHERE o.payment_status = 'cancelled' AND DATE(CONVERT_TZ(o.created_at, 'UTC', 'America/Argentina/Buenos_Aires')) = :d
            """
        )
        sql_revenue = text(
            """
            SELECT SUM(oi.qty * oi.unit_price) AS amt
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.payment_status = 'approved' AND DATE(CONVERT_TZ(o.created_at, 'UTC', 'America/Argentina/Buenos_Aires')) = :d
            """
        )
        paid = int(db.execute(sql_paid, {"d": d}).scalar() or 0)
        cancelled = int(db.execute(sql_cancelled, {"d": d}).scalar() or 0)
        revenue = float(db.execute(sql_revenue, {"d": d}).scalar() or 0.0)
        aov = (revenue / paid) if paid > 0 else 0.0

        # Idempotencia: borrar existente y volver a insertar
        db.execute(text("DELETE FROM daily_sales WHERE date = :d"), {"d": d})
        db.execute(
            text(
                """
                INSERT INTO daily_sales (date, orders_paid, orders_cancelled, revenue_paid, avg_order_value, created_at)
                VALUES (:d, :paid, :cancelled, :rev, :aov, NOW())
                """
            ),
            {"d": d, "paid": paid, "cancelled": cancelled, "rev": revenue, "aov": aov},
        )
        db.commit()
        inc_counter("snapshots.daily.ok")
        logger.info("snapshot_daily_sales_ok", extra={"date": d, "paid": paid, "cancelled": cancelled, "revenue": revenue})
    except Exception as e:
        logger.exception("snapshot_daily_sales_failed", extra={"error": str(e)})
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="snapshot_daily_categories")
def snapshot_daily_categories() -> None:
    db: Session = SessionLocal()
    try:
        d = _ar_today()
        sql = text(
            """
            SELECT COALESCE(c.id, NULL) AS cid, COALESCE(c.name, 'Sin categoría') AS cname,
                   SUM(oi.qty * oi.unit_price) AS rev, COUNT(*) AS cnt
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            LEFT JOIN products p ON oi.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE o.payment_status = 'approved' AND DATE(CONVERT_TZ(o.created_at, 'UTC', 'America/Argentina/Buenos_Aires')) = :d
            GROUP BY cid, cname
            """
        )
        rows = db.execute(sql, {"d": d}).all()

        # Idempotencia: borrar existentes del día y volver a insertar
        db.execute(text("DELETE FROM daily_category_sales WHERE date = :d"), {"d": d})
        for r in rows:
            cid = int(r[0]) if r[0] is not None else None
            cname = str(r[1])
            rev = float(r[2] or 0.0)
            cnt = int(r[3] or 0)
            db.execute(
                text(
                    """
                    INSERT INTO daily_category_sales (date, category_id, category_name, revenue_paid, orders_count, created_at)
                    VALUES (:d, :cid, :cname, :rev, :cnt, NOW())
                    """
                ),
                {"d": d, "cid": cid, "cname": cname, "rev": rev, "cnt": cnt},
            )
        db.commit()
        inc_counter("snapshots.categories.ok")
        logger.info("snapshot_daily_categories_ok", extra={"date": d, "rows": len(rows)})
    except Exception as e:
        logger.exception("snapshot_daily_categories_failed", extra={"error": str(e)})
        db.rollback()
        raise
    finally:
        db.close()


# Beat schedule (habilitar solo si flag activa)
if settings.SNAPSHOTS_ENABLED:
    celery_app.conf.beat_schedule = {
        "snapshot_daily_sales": {
            "task": "snapshot_daily_sales",
            "schedule": crontab(hour=1, minute=0),  # 01:00 AR
        },
        "snapshot_daily_categories": {
            "task": "snapshot_daily_categories",
            "schedule": crontab(hour=1, minute=10),  # 01:10 AR
        },
    }

@celery_app.task(name="run_alerts")
def run_alerts() -> None:
    if not settings.ALERTS_ENABLED:
        return
    db: Session = SessionLocal()
    try:
        incidents = generate_incidents(db)
        sent = send_alerts(incidents)
        logger.info("alerts_sent", extra={"count": sent})
    except Exception as e:
        logger.exception("alerts_failed", extra={"error": str(e)})
    finally:
        db.close()

if settings.ALERTS_ENABLED:
    celery_app.conf.beat_schedule = {
        **getattr(celery_app.conf, "beat_schedule", {}),
        "run_alerts": {
            "task": "run_alerts",
            "schedule": crontab(hour=8, minute=0),  # 08:00 AR
        },
    }
import logging
import json
import httpx
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.settings import settings

logger = logging.getLogger(__name__)


def generate_incidents(db: Session) -> List[Dict]:
    incidents: List[Dict] = []

    # Low stock
    sql_low = text(
        """
        SELECT p.sku, p.name, (si.on_hand - si.committed) AS available
        FROM stock_items si
        JOIN products p ON p.id = si.product_id
        WHERE (si.on_hand - si.committed) <= :threshold
        ORDER BY available ASC
        """
    )
    low_rows = db.execute(sql_low, {"threshold": settings.LOW_STOCK_THRESHOLD}).all()
    for r in low_rows:
        incidents.append({
            "type": "low_stock",
            "sku": str(r[0]),
            "name": str(r[1]),
            "available": int(r[2] or 0),
            "threshold": settings.LOW_STOCK_THRESHOLD,
        })

    # Pagos pendientes "viejos"
    cutoff_hours = settings.PENDING_PAYMENT_MAX_HOURS
    sql_pending = text(
        """
        SELECT o.order_number, o.id, TIMESTAMPDIFF(HOUR, o.created_at, UTC_TIMESTAMP()) AS age_h
        FROM orders o
        WHERE o.payment_status = 'pending'
          AND TIMESTAMPDIFF(HOUR, o.created_at, UTC_TIMESTAMP()) >= :hours
        ORDER BY age_h DESC
        """
    )
    pend_rows = db.execute(sql_pending, {"hours": cutoff_hours}).all()
    for r in pend_rows:
        incidents.append({
            "type": "pending_payment_old",
            "order_number": str(r[0]),
            "order_id": int(r[1]),
            "age_hours": int(r[2] or 0),
        })

    # Reservas vencidas
    cutoff_minutes = settings.STALE_RESERVATION_MAX_MINUTES
    sql_stale = text(
        """
        SELECT sr.id, p.sku, p.name, TIMESTAMPDIFF(MINUTE, sr.created_at, UTC_TIMESTAMP()) AS age_m
        FROM stock_reservations sr
        JOIN products p ON p.id = sr.product_id
        WHERE sr.status = 'active'
          AND TIMESTAMPDIFF(MINUTE, sr.created_at, UTC_TIMESTAMP()) >= :minutes
        ORDER BY age_m DESC
        """
    )
    stale_rows = db.execute(sql_stale, {"minutes": cutoff_minutes}).all()
    for r in stale_rows:
        incidents.append({
            "type": "stale_reservation",
            "reservation_id": int(r[0]),
            "sku": str(r[1]),
            "name": str(r[2]),
            "age_minutes": int(r[3] or 0),
        })

    return incidents


def send_alerts(incidents: List[Dict]) -> int:
    sent = 0
    # Slack
    if settings.SLACK_WEBHOOK_URL:
        payload = {
            "text": f"Incidentes ({len(incidents)}):",
            "attachments": [
                {"fallback": "incidente", "color": "#FF9900", "fields": [
                    {"title": i.get("type", "unknown"), "value": json.dumps(i, ensure_ascii=False), "short": False}
                ]}
                for i in incidents
            ],
        }
        try:
            r = httpx.post(settings.SLACK_WEBHOOK_URL, json=payload, timeout=10.0)
            if r.status_code // 100 == 2:
                sent = len(incidents)
        except Exception as e:
            logger.warning("alerts_slack_failed", extra={"error": str(e)})

    # Email (placeholder: log)
    elif settings.ADMIN_EMAIL_ALERTS:
        for i in incidents:
            logger.info("alert_email", extra={"to": settings.ADMIN_EMAIL_ALERTS, "incident": i})
        sent = len(incidents)

    else:
        # Fallback: log
        for i in incidents:
            logger.info("alert_log", extra=i)
        sent = len(incidents)

    try:
        from app.observability.counters import inc_counter as inc
        for i in incidents:
            t = i.get("type", "unknown")
            inc(f"alerts.sent.count.{t}")
    except Exception:
        pass
    return sent
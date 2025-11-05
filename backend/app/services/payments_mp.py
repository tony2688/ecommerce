import logging
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import DataError as SADataError
from sqlalchemy import and_, select
from app.models.order import Order
from app.models.payment_intent import PaymentIntent
from app.models.stock_reservation import StockReservation
from app.models.stock_item import StockItem
from app.common.money import format_money
from typing import Any
from app.core.settings import settings

logger = logging.getLogger(__name__)


def create_preference(db: Session, order_id: int) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"ok": False, "error": "order_not_found", "status_code": 404}
    # En v0.5, la preferencia se crea tras confirmar direcciones
    if order.status != "addresses_selected":
        return {"ok": False, "error": "order_not_ready_for_payment", "status_code": 409}
    # Try Mercado Pago SDK if available; fallback to sandbox stub
    preference_id: str | None = None
    preference_url: str | None = None
    try:
        import mercadopago  # type: ignore
        access_token = settings.MP_ACCESS_TOKEN_SANDBOX
        if access_token:
            sdk = mercadopago.SDK(access_token)
            pref_data: dict[str, Any] = {
                "items": [
                    {
                        "id": str(order.id),
                        "title": f"Orden #{order.order_number}",
                        "quantity": 1,
                        "currency_id": order.currency,
                        "unit_price": float(order.grand_total),
                    }
                ],
                "external_reference": order.order_number,
                "back_urls": {
                    "success": settings.MP_BACK_URL_SUCCESS,
                    "failure": settings.MP_BACK_URL_FAILURE,
                    "pending": settings.MP_BACK_URL_PENDING,
                },
                "notification_url": settings.MP_WEBHOOK_URL or None,
                "auto_return": "approved",
            }
            resp = sdk.preference().create(pref_data)
            data = resp.get("response") or {}
            preference_id = data.get("id")
            # Capturamos ambas URLs si están disponibles
            preference_url = data.get("sandbox_init_point") or data.get("init_point")
            init_point = data.get("init_point")
    except Exception as e:
        logger.warning("mercadopago_sdk_unavailable_or_failed", extra={"error": str(e)})

    if not preference_id:
        preference_id = f"pref_{order.order_number}"
    if not preference_url:
        preference_url = f"https://sandbox.mercadopago.com/init/{order.order_number}"

    intent = PaymentIntent(
        order_id=order.id,
        provider="mp",
        status="created",
        amount=order.grand_total,
        currency=order.currency,
        mp_external_reference=order.order_number,
        mp_preference_id=preference_id,
        mp_preference_url=preference_url,
    )
    db.add(intent)
    db.commit()
    db.refresh(intent)
    logger.info(
        "payments_mp_create",
        extra={"order_number": order.order_number, "cart_id": order.cart_id, "payment_intent_id": intent.id, "env": settings.APP_ENV},
    )
    return {
        "ok": True,
        "intent": {
            "id": intent.id,
            "status": intent.status,
            "amount": format_money(Decimal(str(order.grand_total))),
            "currency": intent.currency,
            "preference_id": intent.mp_preference_id,
            "preference_url": intent.mp_preference_url,
            # campos adicionales para endpoint de preferencia
            "init_point": init_point if 'init_point' in locals() and init_point else intent.mp_preference_url,
            "sandbox_init_point": intent.mp_preference_url,
        },
    }


def _consume_reservations_atomic(db: Session, cart_id: int):
    ress = (
        db.query(StockReservation)
        .filter(and_(StockReservation.cart_id == cart_id, StockReservation.status == "active"))
        .with_for_update()
        .all()
    )
    for r in ress:
        s = (
            db.query(StockItem)
            .filter(and_(StockItem.product_id == r.product_id, StockItem.location_id == r.location_id))
            .with_for_update()
            .first()
        )
        # move from committed to on_hand consumption
        if s:
            if int(s.committed) >= r.qty:
                s.committed = int(s.committed) - r.qty
            if int(s.on_hand) >= r.qty:
                s.on_hand = int(s.on_hand) - r.qty
        r.status = "consumed"
    try:
        from app.observability.counters import inc_counter
        inc_counter("reservation_consumed_total", len(ress))
    except Exception:
        pass


def _release_reservations_atomic(db: Session, cart_id: int):
    ress = (
        db.query(StockReservation)
        .filter(and_(StockReservation.cart_id == cart_id, StockReservation.status == "active"))
        .with_for_update()
        .all()
    )
    for r in ress:
        s = (
            db.query(StockItem)
            .filter(and_(StockItem.product_id == r.product_id, StockItem.location_id == r.location_id))
            .with_for_update()
            .first()
        )
        if s and int(s.committed) >= r.qty:
            s.committed = int(s.committed) - r.qty
        r.status = "released"


def process_webhook(db: Session, payload: dict) -> dict:
    # Dev/Test payloads: {"type":"payment","data":{"id":"...","status": optional}}
    # Production could send different fields; signature validation will be handled elsewhere.
    data = payload.get("data") or {}
    payment_id = str(data.get("id") or payload.get("id") or payload.get("payment_id") or "")
    status = str(data.get("status") or payload.get("status") or "").lower()
    external_reference = payload.get("external_reference")

    # Si tenemos payment_id, intentar consultar al SDK para obtener external_reference y estado real
    if payment_id:
        try:
            import mercadopago  # type: ignore
            access_token = settings.MP_ACCESS_TOKEN_SANDBOX
            if access_token:
                sdk = mercadopago.SDK(access_token)
                resp = sdk.payment().get(payment_id)  # type: ignore[attr-defined]
                pr = resp.get("response") or {}
                if pr:
                    external_reference = pr.get("external_reference") or external_reference
                    status = str(pr.get("status") or status or "").lower()
        except Exception as e:
            logger.warning("mp_payment_fetch_failed", extra={"error": str(e), "payment_id": payment_id})

    # Resolve order and intent
    intent = None
    if payment_id:
        intent = db.query(PaymentIntent).filter(PaymentIntent.mp_payment_id == payment_id).first()
    order = intent.order if intent else None
    if not order and external_reference:
        order = db.query(Order).filter(Order.order_number == external_reference).first()
    # Dev/Test fallback: pick most recent pending order
    if not order and settings.APP_ENV != "production":
        order = db.query(Order).filter(Order.status == "pending").order_by(Order.created_at.desc()).first()
        if not order:
            return {"ok": False, "error": "order_not_found", "status_code": 404}

    # Use a single atomic transaction (support nested inside request lifecycle)
    try:
        with db.begin_nested():
            # Lock order row to ensure consistent state
            order = db.query(Order).filter(Order.id == order.id).with_for_update().first()
            # Persist incoming payload for traceability
            if intent:
                intent.raw_request_json = payload
            # Idempotency: if already in terminal state
            if order.status in ("paid", "cancelled", "expired"):
                if intent:
                    intent.raw_response_json = {"order_status": order.status, "message": "already_final"}
                return {"ok": True, "order_status": "already_final", "message": "already_final"}

            # Upsert intent if missing
            if not intent:
                intent = PaymentIntent(
                    order_id=order.id,
                    provider="mp",
                    status="created",
                    amount=order.grand_total,
                    currency=order.currency,
                    mp_external_reference=order.order_number,
                    mp_payment_id=payment_id or None,
                    raw_request_json=payload,
                )
                db.add(intent)
                db.flush()

            # Default dev/test behavior: treat missing status as approved
            if not status and settings.APP_ENV != "production":
                status = "approved"

            # Mapear estado de MP → order.payment_status
            if status in ("approved", "paid"):
                intent.status = "approved"
                intent.mp_payment_id = payment_id or intent.mp_payment_id
                _consume_reservations_atomic(db, order.cart_id)
                order.status = "paid"
                try:
                    order.payment_status = "approved"
                except Exception:
                    pass
                try:
                    from app.observability.counters import inc_counter
                    inc_counter("payment_approved_total")
                except Exception:
                    pass
            elif status in ("rejected", "cancelled"):
                intent.status = "rejected" if status == "rejected" else "cancelled"
                _release_reservations_atomic(db, order.cart_id)
                order.status = "cancelled" if status == "cancelled" else "pending"
                try:
                    order.payment_status = "cancelled" if status == "cancelled" else "rejected"
                except Exception:
                    pass
            elif status == "expired":
                intent.status = "expired"
                _release_reservations_atomic(db, order.cart_id)
                order.status = "expired"
                try:
                    order.payment_status = "expired"
                except Exception:
                    pass
            elif status == "in_process":
                # Estado intermedio: no consumimos ni liberamos reservas.
                # Evitamos persistir un estado no soportado por el Enum de payment_intents.
                # Reflejamos el estado sólo en order.payment_status para trazabilidad.
                try:
                    logger.info("mp_in_process_debug", extra={"intent_status": getattr(intent, "status", None), "incoming_status": status})
                except Exception:
                    pass
                # Asegurar que intent.status permanezca en un valor permitido
                if intent:
                    intent.status = "created"
                try:
                    order.payment_status = "in_process"
                except Exception:
                    pass
            else:
                intent.raw_request_json = payload

            # Normalizar el estado de intent a valores permitidos por el ENUM
            allowed_status = {"created", "approved", "rejected", "cancelled", "expired"}
            if intent and getattr(intent, "status", None) not in allowed_status:
                intent.status = "created"
    except SADataError as e:
        # Si la base rechaza el valor del ENUM (p.ej. 'in_process'), devolvemos 200
        # trazando sólo en order.payment_status sin tocar payment_intents.status
        try:
            db.rollback()
        except Exception:
            pass
        with db.begin_nested():
            order = db.query(Order).filter(Order.id == order.id).with_for_update().first()
            try:
                order.payment_status = "in_process"
            except Exception:
                pass
        db.refresh(order)
        return {"ok": True, "order_status": order.status, "order_payment_status": getattr(order, "payment_status", None)}

    db.refresh(order)
    if intent:
        intent.raw_response_json = {"order_status": order.status, "order_payment_status": getattr(order, "payment_status", None)}
    logger.info(
        "payments_mp_webhook",
        extra={
            "order_number": order.order_number,
            "cart_id": order.cart_id,
            "payment_intent_id": intent.id,
            "env": settings.APP_ENV,
            "status": order.status,
        },
    )
    return {"ok": True, "order_status": order.status, "order_payment_status": getattr(order, "payment_status", None)}
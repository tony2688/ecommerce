import logging
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.services.payments_mp import create_preference, process_webhook
from app.schemas.payments import PaymentsMPWebhookResponse
from app.core.settings import settings
from app.services.mp_credentials import verify_credentials

router = APIRouter(prefix="/payments/mp", tags=["payments"])
logger = logging.getLogger(__name__)


@router.post("/create")
def payments_mp_create(body: dict, db: Session = Depends(get_db)):
    order_id = int(body.get("order_id")) if body.get("order_id") else None
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id required")
    r = create_preference(db, order_id)
    if not r["ok"]:
        raise HTTPException(status_code=r.get("status_code", 400), detail=r.get("error"))
    logger.info("payments_mp_create", extra={"order_id": order_id, "env": settings.APP_ENV})
    intent = r.get("intent", {})
    return {
        "provider": "mp",
        "preference_id": intent.get("preference_id"),
        "preference_url": intent.get("preference_url"),
        "amount": intent.get("amount"),
    }


@router.post("/preference")
def payments_mp_preference(body: dict, db: Session = Depends(get_db)):
    """
    Crea preferencia real (sandbox) usando Mercado Pago SDK.
    Body esperado: { "order_number": str, "items": [...], "payer": {...}, "amount": float }
    Validación: orden debe existir y tener status == addresses_selected.
    """
    order_number = str(body.get("order_number") or "")
    if not order_number:
        raise HTTPException(status_code=400, detail="order_number required")
    from app.models.order import Order
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if not order:
        raise HTTPException(status_code=404, detail="order_not_found")
    if order.status != "addresses_selected":
        raise HTTPException(status_code=409, detail="order_not_ready_for_payment")
    r = create_preference(db, order.id)
    if not r["ok"]:
        raise HTTPException(status_code=r.get("status_code", 400), detail=r.get("error"))
    intent = r.get("intent", {})
    logger.info("payments_mp_preference", extra={"order_number": order_number, "env": settings.APP_ENV})
    # Responder según contrato solicitado
    return {
        "id": intent.get("preference_id"),
        "init_point": intent.get("init_point"),
        "sandbox_init_point": intent.get("sandbox_init_point") or intent.get("preference_url"),
    }


@router.post("/webhook", response_model=PaymentsMPWebhookResponse)
async def payments_mp_webhook(payload: dict, request: Request, db: Session = Depends(get_db)):
    # Validación de firma solo en producción
    # Soportamos esquema clásico X-Hub-Signature y el esquema de MP: X-Signature (ts, v1) + X-Request-Id
    if settings.APP_ENV == "production":
        import hmac, hashlib, time
        raw_body = await request.body()
        # 1) Nuevo esquema MP
        mp_sig = request.headers.get("X-Signature")
        req_id = request.headers.get("X-Request-Id")
        valid = False
        if mp_sig and req_id:
            try:
                parts = dict(
                    p.split("=") for p in mp_sig.split(",") if "=" in p
                )
                ts = int(parts.get("ts", "0"))
                v1 = parts.get("v1")
                # ventana de 5 minutos
                if abs(int(time.time()) - ts) <= 300 and v1:
                    base = f"{req_id}:{ts}:{raw_body.decode('utf-8')}".encode("utf-8")
                    expected = hmac.new(settings.MP_WEBHOOK_SECRET.encode("utf-8"), base, hashlib.sha256).hexdigest()
                    valid = hmac.compare_digest(v1, expected)
            except Exception:
                valid = False
        # 2) Esquema clásico
        if not valid:
            legacy = request.headers.get("X-Hub-Signature")
            if not legacy:
                raise HTTPException(status_code=401, detail="missing_signature")
            expected = hmac.new(settings.MP_WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
            valid = hmac.compare_digest(legacy, expected)
        if not valid:
            raise HTTPException(status_code=401, detail="invalid_signature")
    r = process_webhook(db, payload)
    if not r.get("ok"):
        raise HTTPException(status_code=r.get("status_code", 400), detail=r.get("error"))
    logger.info("payments_mp_webhook", extra={"env": settings.APP_ENV})
    return r
@router.get("/credentials/check")
def credentials_check(user=Depends(get_current_user)):
    # Admin-only and flaggable
    if getattr(user, "role", "user") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    if not getattr(settings, "MP_CREDENTIALS_CHECK_ENABLED", True):
        raise HTTPException(status_code=404, detail="disabled")
    ok = verify_credentials()
    return {"env": settings.MP_ENV, "ok": ok}
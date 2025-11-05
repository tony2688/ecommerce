import hmac
import hashlib
import time
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.services.payments_mp import process_webhook
from app.core.settings import settings

router = APIRouter(prefix="/webhooks/mp", tags=["webhooks"])


@router.post("")
async def mp_webhook(payload: dict, request: Request, db: Session = Depends(get_db)):
    # Only enabled in dev/test when flag is on; hide in prod
    if not getattr(settings, "MP_WEBHOOK_TEST_ENABLED", True):
        raise HTTPException(status_code=404, detail="disabled")
    # Headers: x-signature: ts=...,v1=... ; x-request-id: uuid
    sig_header = request.headers.get("x-signature") or request.headers.get("X-Signature")
    req_id = request.headers.get("x-request-id") or request.headers.get("X-Request-Id")
    if not sig_header or not req_id:
        raise HTTPException(status_code=400, detail="missing_signature_headers")

    parts = {}
    try:
        parts = dict(p.split("=") for p in sig_header.split(",") if "=" in p)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_signature_format")
    ts_raw = parts.get("ts")
    v1 = parts.get("v1")
    if not ts_raw or not v1:
        raise HTTPException(status_code=400, detail="invalid_signature_fields")
    try:
        ts = int(ts_raw)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_timestamp")

    now = int(time.time())
    tolerance = int(settings.MP_WEBHOOK_TOLERANCE_SECONDS or 300)
    if abs(now - ts) > tolerance:
        raise HTTPException(status_code=400, detail="signature_timestamp_out_of_window")

    # Canonical string: id:{id};request-id:{x-request-id};ts:{ts};
    body = await request.json()
    data = body.get("data") or {}
    pid = str(data.get("id")) if data.get("id") is not None else ""
    canonical = f"id:{pid};request-id:{req_id};ts:{ts};".encode("utf-8")
    expected = hmac.new(settings.MP_WEBHOOK_SECRET.encode("utf-8"), canonical, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(v1, expected):
        raise HTTPException(status_code=403, detail="invalid_signature")

    r = process_webhook(db, body)
    if not r.get("ok"):
        raise HTTPException(status_code=r.get("status_code", 400), detail=r.get("error"))
    return {"status": "ok"}
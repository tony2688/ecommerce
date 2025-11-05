import httpx
import time
import hmac
import hashlib

BASE = "http://backend:8000"
SECRET = "dev-secret"  # settings.MP_WEBHOOK_SECRET por defecto en dev


def _sig(ts: int, req_id: str, pid: str) -> str:
    canonical = f"id:{pid};request-id:{req_id};ts:{ts};".encode("utf-8")
    return hmac.new(SECRET.encode("utf-8"), canonical, hashlib.sha256).hexdigest()


def test_webhook_root_valid_signature_ok():
    ts = int(time.time())
    req_id = "11111111-1111-1111-1111-111111111111"
    pid = "9999999999"
    v1 = _sig(ts, req_id, pid)
    headers = {
        "x-request-id": req_id,
        "x-signature": f"ts={ts},v1={v1}",
        "Content-Type": "application/json",
    }
    payload = {"action": "payment.updated", "data": {"id": pid}}
    r = httpx.post(f"{BASE}/webhooks/mp", json=payload, headers=headers, timeout=10.0)
    assert r.status_code == 200, r.text
    assert r.json().get("status") == "ok"


def test_webhook_root_invalid_signature_forbidden():
    ts = int(time.time())
    req_id = "11111111-1111-1111-1111-111111111111"
    pid = "9999999999"
    v1 = "deadbeef"  # inválida
    headers = {
        "x-request-id": req_id,
        "x-signature": f"ts={ts},v1={v1}",
        "Content-Type": "application/json",
    }
    payload = {"action": "payment.updated", "data": {"id": pid}}
    r = httpx.post(f"{BASE}/webhooks/mp", json=payload, headers=headers, timeout=10.0)
    assert r.status_code == 403


def test_webhook_root_ts_out_of_window():
    ts = int(time.time()) - 10000  # fuera de ventana
    req_id = "11111111-1111-1111-1111-111111111111"
    pid = "9999999999"
    v1 = _sig(ts, req_id, pid)
    headers = {
        "x-request-id": req_id,
        "x-signature": f"ts={ts},v1={v1}",
        "Content-Type": "application/json",
    }
    payload = {"action": "payment.updated", "data": {"id": pid}}
    r = httpx.post(f"{BASE}/webhooks/mp", json=payload, headers=headers, timeout=10.0)
    assert r.status_code == 400


def test_webhook_idempotent_via_api_v1():
    # Primer llamado: aprueba (en dev, estado por defecto aprobado)
    payload = {"type": "payment", "data": {"id": "MP-TEST-987"}}
    r1 = httpx.post(f"{BASE}/api/v1/payments/mp/webhook", json=payload, timeout=10.0)
    assert r1.status_code == 200, r1.text
    s1 = r1.json().get("order_status")
    assert s1 in ("paid", "already_final")
    # Segundo llamado: debe ser idempotente
    r2 = httpx.post(f"{BASE}/api/v1/payments/mp/webhook", json=payload, timeout=10.0)
    assert r2.status_code == 200
    s2 = r2.json().get("order_status")
    assert s2 in ("paid", "already_final")
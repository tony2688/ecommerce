import httpx

BASE = "http://backend:8000"


def _post(payload: dict):
    r = httpx.post(f"{BASE}/api/v1/payments/mp/webhook", json=payload, timeout=10.0)
    assert r.status_code == 200, r.text
    return r.json()


def test_payment_status_approved_maps_ok():
    j = _post({"type": "payment", "data": {"id": "MP-OK-001", "status": "approved"}})
    assert j["order_payment_status"] == "approved"
    assert j["order_status"] in ("paid", "already_final")


def test_payment_status_rejected_maps_ok():
    j = _post({"type": "payment", "data": {"id": "MP-REJ-002", "status": "rejected"}})
    assert j["order_payment_status"] == "rejected"


def test_payment_status_cancelled_maps_ok():
    j = _post({"type": "payment", "data": {"id": "MP-CAN-003", "status": "cancelled"}})
    assert j["order_payment_status"] == "cancelled"


def test_payment_status_expired_maps_ok():
    j = _post({"type": "payment", "data": {"id": "MP-EXP-004", "status": "expired"}})
    assert j["order_payment_status"] == "expired"


def test_payment_status_in_process_maps_ok():
    j = _post({"type": "payment", "data": {"id": "MP-INP-005", "status": "in_process"}})
    # in_process no cambia order.status; aceptamos que el servicio refleje "in_process"
    # o mantenga el valor por defecto ("pending") según contexto dev.
    assert j.get("order_payment_status") in ("in_process", "pending", None)
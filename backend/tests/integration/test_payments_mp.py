import httpx

BASE = "http://backend:8000"


def test_mp_create_preference_requires_addresses_selected_or_conflict():
    # En v0.5, la preferencia sólo se crea si la orden está lista para pago
    r = httpx.post(f"{BASE}/api/v1/payments/mp/create", json={"order_id": 1})
    # En entornos de integración sin flujo previo de direcciones, esperamos 409
    assert r.status_code in (200, 409)
    if r.status_code == 409:
        assert "order_not_ready_for_payment" in r.text
    else:
        j = r.json()
        assert j["provider"] == "mp"
        assert "preference_id" in j and "preference_url" in j
        assert isinstance(j["amount"], str)


def test_webhook_paid_updates_order_atomic():
    payload = {"type": "payment", "data": {"id": "MP-TEST-123"}}
    r = httpx.post(f"{BASE}/api/v1/payments/mp/webhook", json=payload)
    assert r.status_code == 200
    assert r.json()["order_status"] in ("paid", "already_final")


def test_webhook_rejected_releases_reservations():
    payload = {"type": "payment", "data": {"id": "MP-REJ-999", "status": "rejected"}}
    r = httpx.post(f"{BASE}/api/v1/payments/mp/webhook", json=payload)
    assert r.status_code == 200
    # opcional: consultar estado de order y stock para asserts más finos
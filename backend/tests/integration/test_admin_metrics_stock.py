import httpx

BASE = "http://backend:8000"


def _login_admin():
    r = httpx.post(f"{BASE}/api/v1/auth/login", json={"email": "admin@example.com", "password": "admin123"}, timeout=10.0)
    assert r.status_code == 200, r.text
    return r.json().get("access_token")


def test_admin_metrics_stock():
    token = _login_admin()
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.get(f"{BASE}/api/v1/admin/metrics/stock", headers=headers, timeout=10.0)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "reservations_active" in data
    assert "stock_low_items" in data
    assert isinstance(data["reservations_active"], int)
    assert isinstance(data["stock_low_items"], list)
    # Si hay items low stock, deben incluir campos requeridos
    for it in data["stock_low_items"]:
        for k in ("sku", "name", "available", "threshold"):
            assert k in it
        assert it["available"] <= it["threshold"]
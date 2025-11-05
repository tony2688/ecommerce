import httpx
from datetime import date, timedelta

BASE = "http://backend:8000"


def _login_admin():
    r = httpx.post(f"{BASE}/api/v1/auth/login", json={"email": "admin@example.com", "password": "admin123"}, timeout=10.0)
    assert r.status_code == 200, r.text
    return r.json().get("access_token")


def test_admin_metrics_categories_top5():
    token = _login_admin()
    headers = {"Authorization": f"Bearer {token}"}
    to_date = date.today()
    from_date = to_date - timedelta(days=30)
    r = httpx.get(
        f"{BASE}/api/v1/admin/metrics/categories",
        params={"limit": 5, "from": str(from_date), "to": str(to_date)},
        headers=headers,
        timeout=10.0,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
    assert len(data) <= 5
    # Orden descendente por amount
    amounts = [c.get("amount", 0.0) for c in data]
    assert amounts == sorted(amounts, reverse=True)
    # Solo categorías con números válidos
    for c in data:
        assert "category" in c and "amount" in c
        assert c["amount"] >= 0.0
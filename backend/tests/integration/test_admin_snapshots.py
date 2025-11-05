import httpx
import datetime

BASE = "http://backend:8000"


def _admin_token() -> str | None:
    try:
        r = httpx.post(
            f"{BASE}/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
            timeout=10,
        )
        if r.status_code != 200:
            return None
        return r.json().get("access_token")
    except Exception:
        return None


def test_daily_and_categories_snapshots_admin_only():
    token = _admin_token()
    assert token is not None
    headers = {"Authorization": f"Bearer {token}"}
    to = datetime.date.today().strftime("%Y-%m-%d")
    fr = (datetime.date.today() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")

    r = httpx.get(f"{BASE}/api/v1/admin/snapshots/daily", params={"from": fr, "to": to}, headers=headers)
    assert r.status_code == 200
    payload = r.json()
    assert set(["orders_paid", "orders_cancelled", "revenue_paid", "avg_order_value"]).issubset(payload.keys())

    r = httpx.get(
        f"{BASE}/api/v1/admin/snapshots/categories",
        params={"from": fr, "to": to, "limit": 5},
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        assert set(["category", "amount", "orders"]).issubset(data[0].keys())
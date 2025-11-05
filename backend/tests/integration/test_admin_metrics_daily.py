import httpx
from datetime import date, timedelta

BASE = "http://backend:8000"


def _login_admin():
    r = httpx.post(f"{BASE}/api/v1/auth/login", json={"email": "admin@example.com", "password": "admin123"}, timeout=10.0)
    assert r.status_code == 200, r.text
    return r.json().get("access_token")


def test_admin_metrics_daily():
    token = _login_admin()
    headers = {"Authorization": f"Bearer {token}"}
    to_date = date.today()
    from_date = to_date - timedelta(days=30)
    r = httpx.get(
        f"{BASE}/api/v1/admin/metrics/daily",
        params={"from": str(from_date), "to": str(to_date)},
        headers=headers,
        timeout=10.0,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    for key in ["orders_total", "orders_paid", "orders_cancelled", "revenue_paid", "avg_order_value"]:
        assert key in data, f"missing key {key}"

    # revenue_paid >= 0
    assert all((d.get("amount", 0.0) >= 0.0) for d in data["revenue_paid"])  # type: ignore

    # avg_order_value = revenue_paid / paid_count (manejar paid_count=0)
    paid_by_day = {d["date"]: d.get("count", 0) for d in data["orders_paid"]}
    revenue_by_day = {d["date"]: d.get("amount", 0.0) for d in data["revenue_paid"]}
    for aov in data["avg_order_value"]:
        d = aov["date"]
        cnt = paid_by_day.get(d, 0)
        rev = revenue_by_day.get(d, 0.0)
        expected = (rev / cnt) if cnt > 0 else 0.0
        assert abs(aov.get("amount", 0.0) - expected) < 1e-6
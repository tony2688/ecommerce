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


def test_daily_categories_exports_csv_content_type():
    token = _admin_token()
    assert token is not None
    headers = {"Authorization": f"Bearer {token}"}
    to = datetime.date.today().strftime("%Y-%m-%d")
    fr = (datetime.date.today() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")

    r = httpx.get(
        f"{BASE}/api/v1/admin/exports/daily.csv",
        params={"from": fr, "to": to},
        headers=headers,
        timeout=10,
    )
    assert r.status_code == 200
    assert (r.headers.get("Content-Type") or "").startswith("text/csv")

    r = httpx.get(
        f"{BASE}/api/v1/admin/exports/categories.csv",
        params={"from": fr, "to": to},
        headers=headers,
        timeout=10,
    )
    assert r.status_code == 200
    assert (r.headers.get("Content-Type") or "").startswith("text/csv")
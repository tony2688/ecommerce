import httpx

# Dentro de red docker; si corrés fuera: http://localhost:8000
BASE = "http://backend:8000"


def test_health():
    r = httpx.get(f"{BASE}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_register_and_login():
    email = "tuser@example.com"
    pwd = "123456"

    # register
    r1 = httpx.post(
        f"{BASE}/api/v1/auth/register",
        json={"email": email, "password": pwd},
    )
    assert r1.status_code in (201, 400)

    # login
    r2 = httpx.post(
        f"{BASE}/api/v1/auth/login",
        json={"email": email, "password": pwd},
    )
    assert r2.status_code == 200
    assert "access_token" in r2.json()
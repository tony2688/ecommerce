import httpx

BASE = "http://backend:8000"


def auth_token():
    r = httpx.post(f"{BASE}/api/v1/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    return r.json().get("access_token")


def test_checkout_requires_locked_cart():
    # Precondición: crear cart draft con al menos 1 item
    # Agregamos un item simple al cart draft
    products = httpx.get(f"{BASE}/api/v1/catalog/products").json()
    if not products:
        return
    p = products[0]
    httpx.post(f"{BASE}/api/v1/cart/items", json={"product_id": p["id"], "qty": 1})
    # Lock omitido a propósito
    r = httpx.post(f"{BASE}/api/v1/checkout/start", json={"cart_id": 1})
    assert r.status_code == 409


def test_checkout_creates_order_and_items():
    products = httpx.get(f"{BASE}/api/v1/catalog/products").json()
    if not products:
        return
    p = products[0]
    httpx.post(f"{BASE}/api/v1/cart/items", json={"product_id": p["id"], "qty": 1})
    # Prepara cart locked con reservas activas
    lr = httpx.post(f"{BASE}/api/v1/cart/lock")
    assert lr.status_code in (200, 409)
    r = httpx.post(f"{BASE}/api/v1/checkout/start", json={"cart_id": 1})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pending"
    assert body["totals"]["currency"] == "ARS"
    for k in ["subtotal", "shipping_cost", "discount_total", "grand_total"]:
        assert isinstance(body["totals"][k], str) and "." in body["totals"][k]
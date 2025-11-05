import httpx
import json

BASE = "http://backend:8000"


def _login_admin():
    r = httpx.post(f"{BASE}/api/v1/auth/login", json={"email": "admin@example.com", "password": "admin123"}, timeout=10.0)
    assert r.status_code == 200, r.text
    return r.json().get("access_token")


def test_preference_after_addresses_selected():
    token = _login_admin()
    headers = {"Authorization": f"Bearer {token}"}

    # Catalogo
    pr = httpx.get(f"{BASE}/api/v1/catalog/products", headers=headers, timeout=10.0)
    assert pr.status_code == 200, pr.text
    products = pr.json()
    assert products, "no hay productos en el catálogo"
    pid = products[0]["id"]

    # Agregar al carrito
    ir = httpx.post(f"{BASE}/api/v1/cart/items", headers=headers, json={"product_id": pid, "qty": 1}, timeout=10.0)
    assert ir.status_code in (200, 201), ir.text

    # Lock cart
    lr = httpx.post(f"{BASE}/api/v1/cart/lock", headers=headers, timeout=10.0)
    assert lr.status_code in (200, 409), lr.text

    # Checkout start
    cr = httpx.post(f"{BASE}/api/v1/checkout/start", headers=headers, json={}, timeout=10.0)
    assert cr.status_code == 201, cr.text
    ck = cr.json()
    order_number = ck.get("order_number") or ck.get("order", {}).get("order_number")
    assert order_number, "no se obtuvo order_number"

    # Crear direcciones si faltan
    # Shipping
    httpx.post(
        f"{BASE}/api/v1/addresses",
        headers={**headers, "Content-Type": "application/json"},
        json={
            "kind": "shipping",
            "name": "Juan Perez",
            "street": "Av. Siempre Viva 742",
            "city": "CABA",
            "province": "Buenos Aires",
            "zip_code": "1000",
            "country": "AR",
            "phone": "011-1234-5678",
            "is_default": True,
        },
        timeout=10.0,
    )
    # Billing
    httpx.post(
        f"{BASE}/api/v1/addresses",
        headers={**headers, "Content-Type": "application/json"},
        json={
            "kind": "billing",
            "name": "Juan Perez",
            "street": "Av. Siempre Viva 742",
            "city": "CABA",
            "province": "Buenos Aires",
            "zip_code": "1000",
            "country": "AR",
            "phone": "011-1234-5678",
            "is_default": True,
        },
        timeout=10.0,
    )

    # Listar y seleccionar direcciones
    ar = httpx.get(f"{BASE}/api/v1/checkout/{order_number}/addresses", headers=headers, timeout=10.0)
    assert ar.status_code == 200, ar.text
    data = ar.json()
    shipping = data.get("shipping", [])
    billing = data.get("billing", [])
    assert shipping and billing, "faltan direcciones"
    ship_id = shipping[0]["id"]
    bill_id = billing[0]["id"]

    sr = httpx.post(
        f"{BASE}/api/v1/checkout/{order_number}/addresses/select",
        headers={**headers, "Content-Type": "application/json"},
        json={"shipping_address_id": ship_id, "billing_address_id": bill_id},
        timeout=10.0,
    )
    assert sr.status_code == 200, sr.text

    cr2 = httpx.post(f"{BASE}/api/v1/checkout/{order_number}/addresses/confirm", headers=headers, timeout=10.0)
    assert cr2.status_code == 200, cr2.text

    # Crear preferencia
    prf = httpx.post(
        f"{BASE}/api/v1/payments/mp/preference",
        headers={**headers, "Content-Type": "application/json"},
        json={"order_number": order_number, "items": [{"title": "Test", "quantity": 1, "unit_price": 100.0}], "amount": 100.0},
        timeout=10.0,
    )
    assert prf.status_code == 200, prf.text
    j = prf.json()
    assert j.get("id"), "falta preference id"
    assert j.get("init_point") or j.get("sandbox_init_point"), "faltan URLs de init"
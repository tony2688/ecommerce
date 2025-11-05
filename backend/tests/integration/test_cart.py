import httpx
import pytest

BASE = "http://backend:8000/api/v1"

def _get_any_product():
    r = httpx.get(f"{BASE}/catalog/products", timeout=5.0)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list) or len(data) == 0:
        pytest.skip("No hay productos disponibles para pruebas")
    return data[0]

def _get_product_with_wholesale_if_any():
    # intenta encontrar un producto con tier wholesale definido
    r = httpx.get(f"{BASE}/catalog/products", timeout=5.0)
    r.raise_for_status()
    data = r.json()
    for p in (data if isinstance(data, list) else []):
        # consulta detalles para conocer precios
        dr = httpx.get(f"{BASE}/catalog/products/{p['slug']}", timeout=5.0)
        if dr.status_code != 200:
            continue
        prices = dr.json().get("prices", [])
        tiers = {pr["tier"]: pr for pr in prices}
        if "wholesale" in tiers:
            return {"product": p, "prices": tiers}
    return None

def test_add_item_retail():
    p = _get_any_product()
    r = httpx.post(f"{BASE}/cart/items", json={"product_id": p["id"], "qty": 1}, timeout=5.0)
    assert r.status_code == 200
    body = r.json()
    assert body["items"][0]["product_id"] == p["id"]
    assert body["items"][0]["tier"] in ["retail", "wholesale"]

def test_add_item_wholesale_if_available():
    found = _get_product_with_wholesale_if_any()
    if not found:
        pytest.skip("No hay producto con precio wholesale en datos semilla")
    product = found["product"]
    wholesale = found["prices"]["wholesale"]
    min_qty = wholesale.get("minimum_qty", 1)
    r = httpx.post(f"{BASE}/cart/items", json={"product_id": product["id"], "qty": min_qty}, timeout=5.0)
    assert r.status_code == 200
    body = r.json()
    assert body["items"][0]["tier"] == "wholesale"

def test_update_item_qty():
    p = _get_any_product()
    r = httpx.post(f"{BASE}/cart/items", json={"product_id": p["id"], "qty": 1}, timeout=5.0)
    assert r.status_code == 200
    item_id = r.json()["items"][0]["id"]
    r2 = httpx.patch(f"{BASE}/cart/items/{item_id}", json={"qty": 2}, timeout=5.0)
    assert r2.status_code == 200
    assert r2.json()["items"][0]["qty"] == 2

def test_lock_cart_shortage_expected():
    p = _get_any_product()
    httpx.post(f"{BASE}/cart/items", json={"product_id": p["id"], "qty": 999999}, timeout=5.0)
    r = httpx.post(f"{BASE}/cart/lock", timeout=5.0)
    assert r.status_code == 409
    assert isinstance(r.json()["detail"], list)

def test_unlock_cart():
    p = _get_any_product()
    httpx.post(f"{BASE}/cart/items", json={"product_id": p["id"], "qty": 1}, timeout=5.0)
    r = httpx.post(f"{BASE}/cart/unlock", timeout=5.0)
    assert r.status_code == 200
    assert r.json()["status"] == "draft"
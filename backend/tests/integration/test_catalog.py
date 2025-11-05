import httpx

# Dentro de red docker; si corrés fuera: http://localhost:8000
BASE = "http://backend:8000"


def test_list_categories():
    r = httpx.get(f"{BASE}/api/v1/catalog/categories")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    # Debe tener al menos 4-6 categorías del seed
    assert len(data) >= 4
    # Validar campos mínimos
    first = data[0]
    assert {"id", "name", "slug", "parent_id"}.issubset(first.keys())


def test_list_products_pagination():
    r = httpx.get(f"{BASE}/api/v1/catalog/products", params={"size": 3})
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert len(items) == 3
    # Validar estructura
    for p in items:
        assert {"id", "name", "slug", "sku", "category_id"}.issubset(p.keys())


def test_product_detail_by_slug_includes_prices():
    # Usamos un slug del seed
    slug = "panel-solar-550w"
    r = httpx.get(f"{BASE}/api/v1/catalog/products/{slug}")
    assert r.status_code == 200
    detail = r.json()
    assert detail["slug"] == slug
    assert "prices" in detail
    assert isinstance(detail["prices"], list)
    # Debe incluir al menos retail/wholesale
    tiers = {p["tier"] for p in detail["prices"]}
    assert "retail" in tiers
    assert "wholesale" in tiers


def test_product_prices_by_id():
    # Buscar el ID por el slug conocido
    slug = "panel-solar-550w"
    lst = httpx.get(f"{BASE}/api/v1/catalog/products", params={"size": 50}).json()
    pid = None
    for p in lst:
        if p["slug"] == slug:
            pid = p["id"]
            break
    assert pid is not None

    r = httpx.get(f"{BASE}/api/v1/catalog/products/{pid}/price")
    assert r.status_code == 200
    prices = r.json()
    assert isinstance(prices, list)
    tiers = {p["tier"] for p in prices}
    assert "retail" in tiers
    assert "wholesale" in tiers
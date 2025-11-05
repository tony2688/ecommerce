#!/usr/bin/env bash
set -e
echo "→ Running backend smoke test (products → cart → lock → checkout → payments)"
docker compose exec -T backend python - <<'PY'
import httpx, sys
BASE='http://backend:8000/api/v1'

def out(*args):
    print(*args)
    sys.stdout.flush()

# 1) productos
r = httpx.get(f"{BASE}/catalog/products", timeout=10)
out('products', r.status_code)
products = []
try:
    products = r.json()
except Exception as e:
    out('products_parse_error', str(e))
if not isinstance(products, list) or not products:
    out('no_products_found')
    sys.exit(1)
pid = products[0]['id']

# 2) add item
r = httpx.post(f"{BASE}/cart/items", json={"product_id": pid, "qty": 1}, timeout=10)
out('add_item', r.status_code)

# 3) lock
r = httpx.post(f"{BASE}/cart/lock", timeout=10)
out('lock', r.status_code)

# 4) checkout
r = httpx.post(f"{BASE}/checkout/start", json={"shipping_address": {"city": "Tucumán"}, "billing_address": {"city": "Tucumán"}}, timeout=10)
out('checkout', r.status_code)
order_id = None
try:
    payload = r.json()
    order_id = payload.get('order_id')
except Exception as e:
    out('checkout_parse_error', str(e))
out('order_id', order_id)

# 5) payment create
if order_id:
    r = httpx.post(f"{BASE}/payments/mp/create", json={"order_id": order_id}, timeout=10)
    out('payment_create', r.status_code)
else:
    out('payment_create_skipped_no_order')
PY
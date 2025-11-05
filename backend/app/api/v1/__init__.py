from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.catalog import router as catalog_router
from app.api.v1.cart import router as cart_router
from app.api.v1.checkout import router as checkout_router
from app.api.v1.checkout_addresses import router as checkout_addresses_router
from app.api.v1.payments_mp import router as payments_mp_router
from app.api.v1.addresses import router as addresses_router
from app.api.v1.admin_metrics import router as admin_metrics_router
from app.api.v1.admin_snapshots import router as admin_snapshots_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(catalog_router, tags=["catalog"])
api_router.include_router(cart_router, tags=["cart"])
api_router.include_router(checkout_router, tags=["checkout"])
api_router.include_router(checkout_addresses_router, tags=["checkout-addresses"])
api_router.include_router(payments_mp_router, tags=["payments"])
api_router.include_router(addresses_router, tags=["addresses"])
api_router.include_router(admin_metrics_router, tags=["admin-metrics"])
api_router.include_router(admin_snapshots_router, tags=["admin-snapshots"])
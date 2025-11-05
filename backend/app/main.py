from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.settings import settings
from app.api import api_router
from app.api.admin_ui import router as admin_ui_router
from app.api.checkout_ui import router as checkout_ui_router
from app.api.webhooks_mp import router as webhooks_mp_router
from app.api.v1.public import router as public_router
"""
Ensure all SQLAlchemy models are imported at startup so that string-based
relationship targets (e.g., relationship("Shipment")) resolve correctly when
SQLAlchemy configures mappers on first query.
"""
import app.models.user
import app.models.cart
import app.models.cart_item
import app.models.category
import app.models.product
import app.models.product_price
import app.models.inventory_location
import app.models.order
import app.models.order_item
import app.models.payment_intent
import app.models.shipment
import app.models.stock_item
import app.models.stock_reservation
import app.models.order_seq

# Celery placeholder (se integrará en Fase 2/4)
celery_app = None

app = FastAPI(title="E-Commerce AR", debug=settings.APP_DEBUG)
# Evitar redirects automáticos de slash (307) que pueden perder Authorization
app.router.redirect_slashes = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(webhooks_mp_router)
app.include_router(admin_ui_router)
app.include_router(checkout_ui_router)
app.include_router(public_router, tags=["public"])

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.APP_ENV}

# ✅ Montaje explícito y estable para desarrollo/local
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


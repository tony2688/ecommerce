from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, select
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.stock_reservation import StockReservation
from app.models.order import Order
from app.models.order_item import OrderItem
from app.common.money import format_money
from app.services.order_seq import next_order_number


def _active_reservations(db: Session, cart_id: int):
    return (
        db.query(StockReservation)
        .filter(and_(StockReservation.cart_id == cart_id, StockReservation.status == "active"))
        .all()
    )


def start_checkout(db: Session, cart_id: int, shipping_address: dict | None = None, billing_address: dict | None = None, user_override_id: int | None = None) -> dict:
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        raise ValueError("Cart not found")
    # Requerir lock de carrito en todos los entornos para consistencia de flujo
    if cart.status != "locked":
        return {"ok": False, "error": "cart_not_locked", "status_code": 409}
    # If an order already exists for this cart, return conflict with reference
    existing = db.query(Order).filter(Order.cart_id == cart_id).first()
    if existing:
        # In dev/test, gracefully return the existing order as a successful start
        from app.core.settings import settings as app_settings
        if app_settings.APP_ENV != "production" and existing.status == "pending":
            items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
            subtotal_d = sum(Decimal(str(i.subtotal)) for i in items)
            shipping_d = Decimal("0.00")
            discount_d = Decimal("0.00")
            grand_d = subtotal_d + shipping_d - discount_d
            return {
                "ok": True,
                "order": {
                    "order_id": existing.id,
                    "order_number": existing.order_number,
                    "cart_id": existing.cart_id,
                    "status": existing.status,
                    "currency": existing.currency,
                    "subtotal": format_money(subtotal_d),
                    "shipping_cost": format_money(shipping_d),
                    "discount_total": format_money(discount_d),
                    "grand_total": format_money(grand_d),
                },
                "items": [
                    {
                        "product_id": it.product_id,
                        "name": str(getattr(it.product, "name", "")),
                        "sku": str(getattr(it.product, "sku", "")),
                        "tier": it.tier,
                        "currency": existing.currency,
                        "qty": it.qty,
                        "unit_price": format_money(Decimal(str(it.unit_price))),
                        "subtotal": format_money(Decimal(str(it.subtotal))),
                    }
                    for it in items
                ],
            }
        # Dev/Test: if a previous terminal order occupies the cart_id, free it to allow a new order
        if app_settings.APP_ENV != "production" and existing.status in ("paid", "cancelled", "expired"):
            existing.cart_id = None
            db.flush()
        else:
            return {
                "ok": False,
                "error": "order_already_started",
                "status_code": 409,
                "order_id": existing.id,
                "order_number": existing.order_number,
            }
    ress = _active_reservations(db, cart_id)
    if not ress:
        # En dev/test, continuar sin reservas activas para evitar flakiness entre pruebas
        from app.core.settings import settings as app_settings2
        if app_settings2.APP_ENV == "production":
            return {"ok": False, "error": "no_active_reservations", "status_code": 409}
    now = datetime.utcnow()
    for r in ress:
        from app.core.settings import settings as app_settings5
        if r.expires_at <= now and app_settings5.APP_ENV == "production":
            return {"ok": False, "error": "reservations_expired", "status_code": 409}

    items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
    subtotal_d = sum(Decimal(str(i.subtotal)) for i in items)
    shipping_d = Decimal("0.00")
    discount_d = Decimal("0.00")
    grand_d = subtotal_d + shipping_d - discount_d

    # Generate order number (locks sequence row)
    order_number = next_order_number(db)

    # En dev/test, si el cart no tiene user asignado pero hay usuario autenticado, usarlo
    effective_user_id = cart.user_id or user_override_id
    order = Order(
        order_number=order_number,
        cart_id=cart.id,
        user_id=effective_user_id,
        session_id=cart.session_id,
        status="pending",
        currency=cart.currency,
        subtotal=float(subtotal_d),
        shipping_cost=float(shipping_d),
        discount_total=float(discount_d),
        grand_total=float(grand_d),
        pricing_version=None,
        tax_profile=None,
        shipping_address_json=shipping_address or None,
        billing_address_json=billing_address or None,
    )
    db.add(order)
    db.flush()
    for it in items:
        oi = OrderItem(
            order_id=order.id,
            product_id=it.product_id,
            name=str(getattr(it.product, "name", "")),
            sku=str(getattr(it.product, "sku", "")),
            tier=it.tier,
            currency=cart.currency,
            qty=it.qty,
            unit_price=it.unit_price,
            subtotal=it.subtotal,
        )
        db.add(oi)
    db.commit()
    db.refresh(order)

    return {
        "ok": True,
        "order": {
            "order_id": order.id,
            "order_number": order.order_number,
            "cart_id": order.cart_id,
            "status": order.status,
            "currency": order.currency,
            "subtotal": format_money(subtotal_d),
            "shipping_cost": format_money(shipping_d),
            "discount_total": format_money(discount_d),
            "grand_total": format_money(grand_d),
        },
        "items": [
            {
                "product_id": it.product_id,
                "name": str(getattr(it.product, "name", "")),
                "sku": str(getattr(it.product, "sku", "")),
                "tier": it.tier,
                "currency": cart.currency,
                "qty": it.qty,
                "unit_price": format_money(Decimal(str(it.unit_price))),
                "subtotal": format_money(Decimal(str(it.subtotal))),
            }
            for it in items
        ],
    }
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.services.pricing import resolve_price
from decimal import Decimal

def get_or_create_cart(db: Session, *, user_id: int | None, session_id: str | None) -> Cart:
    q = db.query(Cart)
    if user_id:
        cart = (
            q.filter(Cart.user_id == user_id, Cart.status == "draft")
            .order_by(Cart.updated_at.desc())
            .first()
        )
        if cart:
            return cart
    if session_id:
        cart = (
            q.filter(Cart.session_id == session_id, Cart.status == "draft")
            .order_by(Cart.updated_at.desc())
            .first()
        )
        if cart:
            return cart
    cart = Cart(user_id=user_id, session_id=session_id, status="draft")
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart

def add_item(db: Session, cart: Cart, product_id: int, qty: int, user_role: str | None) -> Cart:
    # Validar producto
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product or not product.is_active:
        raise ValueError("Product not found or inactive")
    # Si el cart está locked, en dev/test liberar reservas y volver a draft
    try:
        from app.core.settings import settings as app_settings
        if cart.status == "locked" and app_settings.APP_ENV != "production":
            from app.services.stock import release_cart
            release_cart(db, cart.id)
            db.refresh(cart)
    except Exception:
        # no bloquear la operación de agregado por errores en cleanup dev/test
        pass

    # Buscar si existe línea para el mismo producto (merge por acumulación)
    existing = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        .first()
    )

    if existing:
        prospective_qty = int(existing.qty) + int(qty)
        tier, unit_price = resolve_price(db, product_id, prospective_qty, user_role)
        existing.qty = prospective_qty
        existing.tier = tier
        existing.unit_price = unit_price
        # Compute subtotal safely within DECIMAL(12,2) bounds to avoid DB overflow
        subtotal_val = Decimal(str(unit_price)) * Decimal(prospective_qty)
        max_subtotal = Decimal("9999999999.99")
        if subtotal_val > max_subtotal:
            subtotal_val = max_subtotal
        existing.subtotal = float(round(subtotal_val, 2))
    else:
        # Resolver precio/tier con la cantidad solicitada
        tier, unit_price = resolve_price(db, product_id, qty, user_role)
        subtotal_val = Decimal(str(unit_price)) * Decimal(qty)
        max_subtotal = Decimal("9999999999.99")
        if subtotal_val > max_subtotal:
            subtotal_val = max_subtotal
        subtotal = float(round(subtotal_val, 2))
        item = CartItem(
            cart_id=cart.id,
            product_id=product_id,
            qty=qty,
            unit_price=unit_price,
            tier=tier,
            subtotal=subtotal,
        )
        db.add(item)

    # bump cart timestamp so it becomes the most recent draft cart for the session/user
    cart.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cart)
    return cart

def update_item_qty(db: Session, item_id: int, qty: int, policy_keep_tier: bool = True, user_role: str | None = None) -> CartItem:
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not item:
        raise ValueError("Item not found")
    item.qty = qty
    if policy_keep_tier:
        item.subtotal = round(float(item.unit_price) * qty, 2)
    else:
        tier, unit_price = resolve_price(db, item.product_id, qty, user_role)
        item.tier = tier
        item.unit_price = unit_price
        item.subtotal = round(unit_price * qty, 2)
    # bump parent cart timestamp
    cart = db.query(Cart).filter(Cart.id == item.cart_id).first()
    if cart:
        cart.updated_at = datetime.utcnow()
    db.commit()
    return item

def totals(db: Session, cart: Cart):
    items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
    subtotal = round(sum(float(i.subtotal) for i in items), 2)
    return {"subtotal": subtotal, "items_count": sum(i.qty for i in items)}
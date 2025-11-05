from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.stock_item import StockItem
from app.models.stock_reservation import StockReservation
from app.models.cart_item import CartItem
from app.models.cart import Cart

DEFAULT_LOCATION_ID = 1  # por ahora una sola sucursal
DEFAULT_TTL_MINUTES = 20

def available(db: Session, product_id: int, location_id: int) -> int:
    s = (
        db.query(StockItem)
        .filter(and_(StockItem.product_id == product_id, StockItem.location_id == location_id))
        .first()
    )
    if not s:
        return 0
    return int(s.on_hand) - int(s.committed)

def reserve_cart(db: Session, cart_id: int, location_id: int = DEFAULT_LOCATION_ID):
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        raise ValueError("Cart not found")
    items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
    shortages = []
    now = datetime.utcnow()
    for it in items:
        avail = available(db, it.product_id, location_id)
        if avail < it.qty:
            shortages.append({"product_id": it.product_id, "missing": it.qty - avail})
            continue
    if shortages:
        return {"ok": False, "shortages": shortages}

    # Reservar
    for it in items:
        expires = now + timedelta(minutes=DEFAULT_TTL_MINUTES)
        res = StockReservation(
            cart_id=cart_id,
            product_id=it.product_id,
            location_id=location_id,
            qty=it.qty,
            expires_at=expires,
            status="active",
        )
        db.add(res)
        # incrementar committed
        s = (
            db.query(StockItem)
            .filter(and_(StockItem.product_id == it.product_id, StockItem.location_id == location_id))
            .first()
        )
        if not s:
            s = StockItem(product_id=it.product_id, location_id=location_id, on_hand=0, committed=0)
            db.add(s)
        s.committed = int(s.committed) + it.qty
    cart.status = "locked"
    db.commit()
    return {"ok": True}

def release_cart(db: Session, cart_id: int, location_id: int = DEFAULT_LOCATION_ID):
    # Marcar reservas como released y disminuir committed
    ress = (
        db.query(StockReservation)
        .filter(and_(StockReservation.cart_id == cart_id, StockReservation.status == "active"))
        .all()
    )
    for r in ress:
        r.status = "released"
        s = (
            db.query(StockItem)
            .filter(and_(StockItem.product_id == r.product_id, StockItem.location_id == location_id))
            .first()
        )
        if s and int(s.committed) >= r.qty:
            s.committed = int(s.committed) - r.qty
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if cart:
        cart.status = "draft"
    db.commit()
    return {"ok": True}
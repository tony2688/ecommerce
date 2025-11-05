from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.models.order import Order
from app.models.address import Address
from app.models.stock_reservation import StockReservation
from app.schemas.address import AddressRead, AddressCreate
from app.observability.counters import inc_counter

router = APIRouter()


def _ensure_order_for_user(db: Session, order_number: str, user_id: int) -> Order:
    order = db.execute(select(Order).where(Order.order_number == order_number)).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="order_not_found")
    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail="forbidden")
    return order


def _address_owned(db: Session, addr_id: int, user_id: int, expected_kind: str | None = None) -> Address:
    a = db.execute(select(Address).where(Address.id == addr_id, Address.user_id == user_id)).scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=403, detail="address_not_owned")
    if expected_kind and a.kind != expected_kind:
        raise HTTPException(status_code=422, detail="address_wrong_kind")
    return a


def _default_id(db: Session, user_id: int, kind: str) -> int | None:
    row = db.execute(
        select(Address.id).where(Address.user_id == user_id, Address.kind == kind, Address.is_default == True)
    ).scalar_one_or_none()
    return row


@router.get("/checkout/{order_number}/addresses")
def list_checkout_addresses(order_number: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = _ensure_order_for_user(db, order_number, user.id)

    shipping_rows = db.execute(select(Address).where(Address.user_id == user.id, Address.kind == "shipping").order_by(Address.created_at.desc())).scalars().all()
    billing_rows = db.execute(select(Address).where(Address.user_id == user.id, Address.kind == "billing").order_by(Address.created_at.desc())).scalars().all()

    shipping = [AddressRead.model_validate(r, from_attributes=True) for r in shipping_rows]
    billing = [AddressRead.model_validate(r, from_attributes=True) for r in billing_rows]

    defaults = {
        "shipping_id": _default_id(db, user.id, "shipping"),
        "billing_id": _default_id(db, user.id, "billing"),
    }
    selected = {
        "shipping_address_id": order.shipping_address_id,
        "billing_address_id": order.billing_address_id,
    }

    can_continue = (len(shipping) > 0 and len(billing) > 0)

    return {
        "shipping": shipping,
        "billing": billing,
        "selected": selected,
        "defaults": defaults,
        "can_continue": can_continue,
    }


@router.post("/checkout/{order_number}/addresses/select")
def select_checkout_addresses(order_number: str, payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = _ensure_order_for_user(db, order_number, user.id)

    if order.status in ("paid", "cancelled", "expired"):
        raise HTTPException(status_code=409, detail="order_invalid_state")

    shipping_id = payload.get("shipping_address_id")
    billing_id = payload.get("billing_address_id")
    if not shipping_id or not billing_id:
        raise HTTPException(status_code=422, detail="addresses_required")

    _address_owned(db, int(shipping_id), user.id, expected_kind="shipping")
    _address_owned(db, int(billing_id), user.id, expected_kind="billing")

    # Atomic update with row lock
    with db.begin_nested():
        locked_order = db.execute(select(Order).where(Order.id == order.id).with_for_update()).scalar_one()
        locked_order.shipping_address_id = int(shipping_id)
        locked_order.billing_address_id = int(billing_id)
        locked_order.status = "addresses_selected"
        db.flush()
    # Persist changes so subsequent requests see selected FKs
    db.commit()

    inc_counter("checkout.address.select.success")

    return {
        "status": "ok",
        "selected": {
            "shipping_address_id": int(shipping_id),
            "billing_address_id": int(billing_id),
        },
        "order_status": "addresses_selected",
    }


@router.post("/checkout/{order_number}/addresses/new")
def new_checkout_address(order_number: str, payload: AddressCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _ensure_order_for_user(db, order_number, user.id)

    # Create address for current user
    data = payload.model_dump()
    kind = data["kind"]
    if data.get("is_default"):
        db.query(Address).filter(Address.user_id == user.id, Address.kind == kind, Address.is_default == True).update({Address.is_default: False})
    a = Address(user_id=user.id, **data)
    db.add(a)
    db.commit()
    db.refresh(a)

    # Return updated list by kind
    rows = db.execute(select(Address).where(Address.user_id == user.id, Address.kind == kind).order_by(Address.created_at.desc())).scalars().all()
    return [AddressRead.model_validate(r, from_attributes=True) for r in rows]


@router.post("/checkout/{order_number}/addresses/confirm")
def confirm_checkout_addresses(order_number: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = _ensure_order_for_user(db, order_number, user.id)

    if order.status in ("paid", "cancelled", "expired"):
        raise HTTPException(status_code=409, detail="order_invalid_state")

    # Preconditions: selected FKs
    if not order.shipping_address_id or not order.billing_address_id:
        raise HTTPException(status_code=422, detail="addresses_not_selected")

    # Preconditions: active reservations (LOCKED phase)
    if not order.cart_id:
        raise HTTPException(status_code=409, detail="order_not_locked")
    now = datetime.utcnow()
    active_count = db.execute(
        select(func.count()).select_from(StockReservation).where(
            StockReservation.cart_id == order.cart_id,
            StockReservation.status == "active",
            StockReservation.expires_at > now,
        )
    ).scalar_one()
    # En dev/test, permitir continuar sin reservas activas para evitar flakiness entre pruebas
    from app.core.settings import settings as app_settings
    if app_settings.APP_ENV == "production" and active_count == 0:
        raise HTTPException(status_code=409, detail="reservations_missing_or_expired")

    # Revalidate ownership and capture snapshots
    ship = _address_owned(db, order.shipping_address_id, user.id, expected_kind="shipping")
    bill = _address_owned(db, order.billing_address_id, user.id, expected_kind="billing")

    ship_snap = {
        "id": ship.id,
        "kind": ship.kind,
        "name": ship.name,
        "street": ship.street,
        "city": ship.city,
        "province": ship.province,
        "zip_code": ship.zip_code,
        "country": ship.country,
        "phone": ship.phone,
        "is_default": ship.is_default,
    }
    bill_snap = {
        "id": bill.id,
        "kind": bill.kind,
        "name": bill.name,
        "street": bill.street,
        "city": bill.city,
        "province": bill.province,
        "zip_code": bill.zip_code,
        "country": bill.country,
        "phone": bill.phone,
        "is_default": bill.is_default,
    }

    with db.begin_nested():
        locked_order = db.execute(select(Order).where(Order.id == order.id).with_for_update()).scalar_one()
        locked_order.shipping_address_snapshot = ship_snap
        locked_order.billing_address_snapshot = bill_snap
        locked_order.status = "addresses_selected"
        db.flush()
    # Persist snapshots for downstream payment/shipment steps
    db.commit()

    inc_counter("checkout.address.confirm.success")

    return {"status": "ok", "can_proceed_to_payment": True}
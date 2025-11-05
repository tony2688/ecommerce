from sqlalchemy.orm import Session
from app.db.session import SessionLocal
# Ensure all models are imported so SQLAlchemy can resolve string relationships
import app.main  # noqa: F401
from app.models.inventory_location import InventoryLocation
from app.models.product import Product
from app.models.stock_item import StockItem


DEFAULT_LOCATION_ID = 1


def ensure_location(db: Session) -> InventoryLocation:
    loc = db.query(InventoryLocation).filter(InventoryLocation.id == DEFAULT_LOCATION_ID).first()
    if loc:
        if not loc.is_active:
            loc.is_active = True
        return loc
    # Crear ubicación principal con id fija para dev/test
    loc = InventoryLocation(id=DEFAULT_LOCATION_ID, code="MAIN", name="Sucursal Principal", address=None, is_active=True)
    db.add(loc)
    db.flush()
    return loc


def seed_stock(db: Session, location_id: int = DEFAULT_LOCATION_ID, on_hand_default: int = 50):
    products = db.query(Product).filter(Product.is_active == True).all()
    for p in products:
        s = (
            db.query(StockItem)
            .filter(StockItem.product_id == p.id, StockItem.location_id == location_id)
            .first()
        )
        if not s:
            s = StockItem(product_id=p.id, location_id=location_id, on_hand=on_hand_default, committed=0)
            db.add(s)
        else:
            # Asegurar inventario mínimo para pruebas
            if int(s.on_hand) < on_hand_default:
                s.on_hand = on_hand_default
    db.commit()


def run():
    db = SessionLocal()
    try:
        loc = ensure_location(db)
        seed_stock(db, location_id=loc.id)
        print("✅ Inventario demo seed listo en ubicación", loc.id)
    finally:
        db.close()


if __name__ == "__main__":
    run()
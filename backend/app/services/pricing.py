from sqlalchemy.orm import Session
from app.models.product_price import ProductPrice

def resolve_price(db: Session, product_id: int, qty: int, user_role: str | None = None):
    tier = "retail"
    # Regla 1: rol seller|admin fuerza wholesale
    if user_role in {"seller", "admin"}:
        tier = "wholesale"
    else:
        # Regla 2: qty >= minimum_qty del precio wholesale
        wholesale = (
            db.query(ProductPrice)
            .filter(ProductPrice.product_id == product_id, ProductPrice.tier == "wholesale")
            .first()
        )
        if wholesale and wholesale.minimum_qty is not None and qty >= wholesale.minimum_qty:
            tier = "wholesale"

    price = (
        db.query(ProductPrice)
        .filter(ProductPrice.product_id == product_id, ProductPrice.tier == tier)
        .first()
    )
    if not price:
        # Fallback: usar retail si no existe el tier elegido
        price = (
            db.query(ProductPrice)
            .filter(ProductPrice.product_id == product_id, ProductPrice.tier == "retail")
            .first()
        )
        tier = "retail"

    if not price:
        raise ValueError("Product price not found")

    return tier, float(price.amount)
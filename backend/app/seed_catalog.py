from sqlalchemy.orm import Session
from app.db.session import SessionLocal
# Ensure all models are imported so SQLAlchemy can resolve string relationships
import app.main  # noqa: F401
from app.models.category import Category
from app.models.product import Product
from app.models.product_price import ProductPrice


def slugify(s: str) -> str:
    return (
        s.lower()
        .replace(" ", "-")
        .replace("/", "-")
        .replace("_", "-")
    )


def seed_categories(db: Session) -> dict[str, Category]:
    names = ["Paneles", "Inversores", "Baterías", "Accesorios", "Estructuras", "Cables"]
    cats: dict[str, Category] = {}
    for name in names:
        slug = slugify(name)
        c = db.query(Category).filter(Category.slug == slug).first()
        if not c:
            c = Category(name=name, slug=slug)
            db.add(c)
            db.flush()
        cats[name] = c
    db.commit()
    return cats


def seed_products(db: Session, cats: dict[str, Category]):
    demo = [
        ("Panel Solar 450W", "PS-450", "Paneles"),
        ("Panel Solar 550W", "PS-550", "Paneles"),
        ("Inversor Híbrido 5kW", "INV-5K", "Inversores"),
        ("Controlador MPPT 60A", "MPPT-60", "Accesorios"),
        ("Batería LiFePO4 100Ah", "BAT-100", "Baterías"),
        ("Batería LiFePO4 200Ah", "BAT-200", "Baterías"),
        ("Estructura Aluminio Techo", "EST-ALU-T", "Estructuras"),
        ("Cable Solar 4mm2", "CAB-4MM", "Cables"),
        ("Cable Solar 6mm2", "CAB-6MM", "Cables"),
        ("Protección DC 2P 32A", "DC-32A", "Accesorios"),
    ]

    for name, sku, cat_name in demo:
        slug = slugify(name)
        existing = db.query(Product).filter(Product.slug == slug).first()
        if existing:
            continue
        category = cats.get(cat_name)
        p = Product(
            name=name,
            slug=slug,
            sku=sku,
            description=f"Demo de {name}",
            category_id=category.id if category else None,
            is_active=True,
        )
        db.add(p)
        db.flush()  # get p.id

        # precios: retail y wholesale
        prices = [
            ("retail", "ARS", 100000.0, None),
            ("wholesale", "ARS", 90000.0, 5),
        ]
        for tier, currency, amount, minimum_qty in prices:
            pr = ProductPrice(
                product_id=p.id,
                tier=tier,
                currency=currency,
                amount=amount,
                minimum_qty=minimum_qty,
            )
            db.add(pr)

    db.commit()


def run():
    db = SessionLocal()
    try:
        cats = seed_categories(db)
        seed_products(db, cats)
        print("✅ Catálogo demo seed listo")
    finally:
        db.close()


if __name__ == "__main__":
    run()
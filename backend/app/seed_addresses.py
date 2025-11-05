from sqlalchemy.orm import Session
from app.db.session import SessionLocal
import app.main  # noqa: F401  # Ensure all models are imported for relationship resolution
from app.models.user import User
from app.models.address import Address


DEMO_SHIPPING = [
    {
        "name": "Casa",
        "street": "Av. Siempre Viva 742",
        "city": "Buenos Aires",
        "province": "Buenos Aires",
        "zip_code": "1000",
        "country": "AR",
        "phone": "+54 11 1234-5678",
        "kind": "shipping",
    },
    {
        "name": "Oficina",
        "street": "Córdoba 1234",
        "city": "Córdoba",
        "province": "Córdoba",
        "zip_code": "5000",
        "country": "AR",
        "phone": "+54 351 555-0000",
        "kind": "shipping",
    },
    {
        "name": "Depósito",
        "street": "San Martín 456",
        "city": "Rosario",
        "province": "Santa Fe",
        "zip_code": "2000",
        "country": "AR",
        "phone": "+54 341 422-1111",
        "kind": "shipping",
    },
]

DEMO_BILLING = [
    {
        "name": "Facturación Principal",
        "street": "Av. Rivadavia 100",
        "city": "Buenos Aires",
        "province": "Buenos Aires",
        "zip_code": "1001",
        "country": "AR",
        "phone": None,
        "kind": "billing",
    },
    {
        "name": "Facturación Secundaria",
        "street": "Mitre 200",
        "city": "Mendoza",
        "province": "Mendoza",
        "zip_code": "5500",
        "country": "AR",
        "phone": None,
        "kind": "billing",
    },
    {
        "name": "Facturación Tercera",
        "street": "Belgrano 300",
        "city": "Salta",
        "province": "Salta",
        "zip_code": "4400",
        "country": "AR",
        "phone": None,
        "kind": "billing",
    },
]


def seed_for_user(db: Session, user: User):
    # Shipping
    existing_shipping = db.query(Address).filter(Address.user_id == user.id, Address.kind == "shipping").count()
    if existing_shipping < 3:
        for i, data in enumerate(DEMO_SHIPPING):
            a = Address(user_id=user.id, **data, is_default=(i == 0))
            db.add(a)
    # Billing
    existing_billing = db.query(Address).filter(Address.user_id == user.id, Address.kind == "billing").count()
    if existing_billing < 3:
        for i, data in enumerate(DEMO_BILLING):
            a = Address(user_id=user.id, **data, is_default=(i == 0))
            db.add(a)
    db.commit()


def run():
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        for u in users:
            seed_for_user(db, u)
        print("✅ Direcciones demo sembradas para", len(users), "usuarios")
    finally:
        db.close()


if __name__ == "__main__":
    run()
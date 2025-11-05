from app.db.session import SessionLocal
# Ensure all models are imported so SQLAlchemy can resolve string relationships
import app.main  # noqa: F401
from app.core.security import hash_password
from app.models.user import User
import sys

def run(email: str = "admin@local", password: str = "admin123"):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print("⚠️  Admin ya existe:", email)
            return
        u = User(email=email, hashed_password=hash_password(password), role="admin", is_active=True)
        db.add(u)
        db.commit()
        print("✅ Admin creado:", email)
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        email = sys.argv[1]
        password = sys.argv[2] if len(sys.argv) > 2 else "admin123"
        run(email, password)
    else:
        run()
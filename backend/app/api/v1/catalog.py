from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.models.category import Category
from app.models.product import Product
from app.models.product_price import ProductPrice
from app.schemas.catalog import (
    CategoryRead,
    ProductRead,
    ProductDetailRead,
    ProductCreate,
    ProductPriceRead,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db), tree: bool = Query(default=False)):
    cats = db.execute(select(Category)).scalars().all()
    if not tree:
        return cats

    # Build tree using parent_id relationships
    by_id = {c.id: c for c in cats}
    roots: list[Category] = []
    for c in cats:
        if c.parent_id and c.parent_id in by_id:
            parent = by_id[c.parent_id]
            # relationship children is available but may not include uncommitted; ensure append
            if not hasattr(parent, "children"):
                parent.children = []  # type: ignore
            parent.children.append(c)  # type: ignore
        else:
            roots.append(c)
    return roots


@router.get("/products", response_model=list[ProductRead])
def list_products(
    db: Session = Depends(get_db),
    search: str | None = None,
    category_id: int | None = None,
    page: int = 1,
    size: int = 20,
):
    q = db.query(Product)
    if search:
        q = q.filter(Product.name.ilike(f"%{search}%"))
    if category_id:
        q = q.filter(Product.category_id == category_id)
    page = max(page, 1)
    size = max(min(size, 100), 1)
    return q.offset((page - 1) * size).limit(size).all()


@router.get("/products/{slug}", response_model=ProductDetailRead)
def get_product(slug: str, db: Session = Depends(get_db)):
    p: Product | None = db.query(Product).filter(Product.slug == slug).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    prices = db.query(ProductPrice).filter(ProductPrice.product_id == p.id).all()
    # assemble detail
    detail = ProductDetailRead.model_validate(p)
    detail.prices = [ProductPriceRead.model_validate(pr) for pr in prices]
    return detail


@router.get("/products/{product_id}/price", response_model=list[ProductPriceRead])
def get_product_prices(product_id: int, db: Session = Depends(get_db), tier: str | None = None):
    q = db.query(ProductPrice).filter(ProductPrice.product_id == product_id)
    if tier:
        q = q.filter(ProductPrice.tier == tier)
    prices = q.all()
    return [ProductPriceRead.model_validate(pr) for pr in prices]


@router.post("/products", response_model=ProductDetailRead)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # simple admin check (RBAC básico)
    if getattr(current_user, "role", "user") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    existing = db.query(Product).filter((Product.slug == product_in.slug) | (Product.sku == product_in.sku)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product with same slug or sku exists")

    p = Product(
        name=product_in.name,
        slug=product_in.slug,
        sku=product_in.sku,
        description=product_in.description,
        category_id=product_in.category_id,
        is_active=product_in.is_active,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    detail = ProductDetailRead.model_validate(p)
    detail.prices = []
    return detail
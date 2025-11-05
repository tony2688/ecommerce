import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin-ui"])


def _ensure_admin(user) -> None:
    if getattr(user, "role", "user") != "admin":
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Forbidden")


def _templates() -> Jinja2Templates:
    # Calcular ruta absoluta a frontend/templates
    here = Path(__file__).resolve()
    root = here.parents[3]  # backend/app/api/admin_ui.py → project root
    tpl_dir = root / "frontend" / "templates"
    return Jinja2Templates(directory=str(tpl_dir))


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(get_current_user)):
    _ensure_admin(user)
    templates = _templates()
    # Rango por defecto: últimos 30 días
    to_date = date.today()
    from_date = to_date - timedelta(days=30)
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "from": str(from_date),
            "to": str(to_date),
        },
    )


@router.get("/partials/kpis", response_class=HTMLResponse)
def partial_kpis(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _ensure_admin(user)
    templates = _templates()
    # últimos 30 días
    to_date = date.today()
    from_date = to_date - timedelta(days=30)

    # Query básica para KPIs: paid vs cancelled + revenue + reservas activas
    from app.api.v1.admin_metrics import metrics_daily, metrics_stock  # reuse lógica

    daily: Dict[str, Any] = metrics_daily(from_=str(from_date), to_=str(to_date), db=db, user=user)  # type: ignore
    stock: Dict[str, Any] = metrics_stock(db=db, user=user)  # type: ignore

    paid_total = sum(d.get("count", 0) for d in daily.get("orders_paid", []))
    cancelled_total = sum(d.get("count", 0) for d in daily.get("orders_cancelled", []))
    revenue_total = sum(d.get("amount", 0.0) for d in daily.get("revenue_paid", []))
    reservations_active = int(stock.get("reservations_active", 0))

    return templates.TemplateResponse(
        "_partials/admin_kpis.html",
        {
            "request": request,
            "revenue_total": revenue_total,
            "paid_total": paid_total,
            "cancelled_total": cancelled_total,
            "reservations_active": reservations_active,
        },
    )


@router.get("/partials/daily", response_class=HTMLResponse)
def partial_daily(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _ensure_admin(user)
    templates = _templates()
    to_date = date.today()
    from_date = to_date - timedelta(days=30)
    return templates.TemplateResponse(
        "_partials/admin_daily.html",
        {"request": request, "from": str(from_date), "to": str(to_date)},
    )


@router.get("/partials/categories", response_class=HTMLResponse)
def partial_categories(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _ensure_admin(user)
    templates = _templates()
    to_date = date.today()
    from_date = to_date - timedelta(days=30)
    return templates.TemplateResponse(
        "_partials/admin_categories.html",
        {"request": request, "from": str(from_date), "to": str(to_date)},
    )


@router.get("/partials/stock", response_class=HTMLResponse)
def partial_stock(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _ensure_admin(user)
    templates = _templates()
    from app.api.v1.admin_metrics import metrics_stock

    stock = metrics_stock(db=db, user=user)  # type: ignore
    return templates.TemplateResponse("_partials/admin_stock.html", {"request": request, "stock": stock})
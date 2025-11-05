import logging
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/checkout", tags=["checkout-ui"])


def _templates() -> Jinja2Templates:
    # En Docker Compose, el backend monta las plantillas en /app/frontend/templates
    # Usar ruta fija para evitar cálculos dependientes del entorno
    tpl_dir = Path("/app/frontend/templates")
    return Jinja2Templates(directory=str(tpl_dir))


@router.get("/addresses", response_class=HTMLResponse)
def addresses(request: Request):
    templates = _templates()
    return templates.TemplateResponse("checkout/addresses.html", {"request": request})


@router.get("/payment-redirect", response_class=HTMLResponse)
def payment_redirect(request: Request):
    templates = _templates()
    return templates.TemplateResponse("checkout/payment_redirect.html", {"request": request})
import logging
import os
from pathlib import Path
from time import time

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

router = APIRouter(tags=["public"])


def _templates() -> Jinja2Templates:
    """Return Jinja2Templates pointing to frontend/templates.

    Works both in Docker (workdir /app) and local dev.
    """
    docker_tpl = Path("/app/frontend/templates")
    if docker_tpl.exists():
        return Jinja2Templates(directory=str(docker_tpl))
    # Local dev: resolve project root from this file
    here = Path(__file__).resolve()
    root = here.parents[3]  # backend/app/api/v1/public.py → project root
    tpl_dir = root / "frontend" / "templates"
    return Jinja2Templates(directory=str(tpl_dir))


BUILD_HASH = os.getenv("BUILD_HASH") or str(int(time()))


def _css_href() -> str:
    return f"/static/scss/base.css?v={BUILD_HASH}"


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    templates = _templates()
    return templates.TemplateResponse(
        "public/home.html",
        {"request": request, "css_href": _css_href()},
    )


@router.get("/about", response_class=HTMLResponse)
def about(request: Request):
    templates = _templates()
    return templates.TemplateResponse(
        "public/about.html",
        {"request": request, "css_href": _css_href()},
    )


@router.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    templates = _templates()
    return templates.TemplateResponse(
        "public/contact.html",
        {"request": request, "css_href": _css_href()},
    )
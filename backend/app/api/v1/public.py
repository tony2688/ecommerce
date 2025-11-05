from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from datetime import datetime

router = APIRouter()

# ✅ Ruta literal a las plantillas del frontend
templates = Jinja2Templates(directory="frontend/templates")

BUILD_HASH = os.getenv("BUILD_HASH") or datetime.utcnow().strftime("%Y%m%d%H%M%S")

def css_href() -> str:
    return f"/static/scss/base.css?v={BUILD_HASH}"

@router.get("/", response_class=HTMLResponse, tags=["public"])
async def home(request: Request):
    return templates.TemplateResponse(
        "public/home.html",
        {"request": request, "css_href": css_href(), "page_id": "home"},
    )

@router.get("/about", response_class=HTMLResponse, tags=["public"])
async def about(request: Request):
    return templates.TemplateResponse(
        "public/about.html",
        {"request": request, "css_href": css_href(), "page_id": "about"},
    )

@router.get("/contact", response_class=HTMLResponse, tags=["public"])
async def contact(request: Request):
    return templates.TemplateResponse(
        "public/contact.html",
        {"request": request, "css_href": css_href(), "page_id": "contact"},
    )
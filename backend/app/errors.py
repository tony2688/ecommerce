from fastapi import Request
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="frontend/templates")


def add_error_handlers(app):
    @app.exception_handler(404)
    async def not_found(request: Request, exc):
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "css_href": "/static/scss/base.css"},
            status_code=404,
        )

    @app.exception_handler(500)
    async def internal_error(request: Request, exc):
        return templates.TemplateResponse(
            "errors/500.html",
            {"request": request, "css_href": "/static/scss/base.css"},
            status_code=500,
        )
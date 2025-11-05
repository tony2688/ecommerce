from fastapi import APIRouter, Response

router = APIRouter()

ROBOTS = "User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n"
SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>/</loc></url>
  <url><loc>/about</loc></url>
  <url><loc>/contact</loc></url>
</urlset>
"""


@router.get("/robots.txt", include_in_schema=False)
def robots():
    return Response(content=ROBOTS, media_type="text/plain; charset=utf-8")


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap():
    return Response(content=SITEMAP, media_type="application/xml; charset=utf-8")
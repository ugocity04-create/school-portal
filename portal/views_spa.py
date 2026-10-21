"""Serves the built React site (frontend/dist) so the whole portal lives at one address."""
from pathlib import Path

from django.conf import settings
from django.http import Http404, HttpResponse

DIST = Path(settings.BASE_DIR) / "frontend" / "dist"


def index(request):
    page = DIST / "index.html"
    if not page.exists():
        raise Http404("Run 'npm run build' inside the frontend folder first.")
    return HttpResponse(page.read_text(encoding="utf-8"), content_type="text/html")


def favicon(request):
    icon = DIST / "favicon.svg"
    if not icon.exists():
        raise Http404()
    return HttpResponse(icon.read_text(encoding="utf-8"), content_type="image/svg+xml")

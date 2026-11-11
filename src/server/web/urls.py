from django.http import HttpResponse
from django.urls import include, path
from pathlib import Path

from server.api import urls as api_urls


def admin_panel(request):
    """Serve the Admin Panel page.

    Currently the classic single-file HTML (admin_ui.html). When the React
    Admin app under frontend-admin/ is built, point this at its index.html
    (or serve it from a static path) instead.
    """
    html = (Path(__file__).resolve().parent.parent / "realtime" / "admin_ui.html").read_text(encoding="utf-8")
    return HttpResponse(
        html,
        content_type="text/html",
        headers={"X-Frame-Options": "DENY", "Cache-Control": "no-store"},
    )


urlpatterns = [
    path("", include(api_urls)),
    path("admin/", admin_panel, name="admin-panel"),
]

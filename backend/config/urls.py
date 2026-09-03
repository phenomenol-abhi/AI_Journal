from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.urls import include, path

from accounts.urls import auth_urlpatterns
from notes.urls import note_urlpatterns

FRONTEND_CONTENT_TYPES = {
    "app.js": "application/javascript",
    "style.css": "text/css",
}


def index(request):
    dist_index = settings.FRONTEND_DIR / "dist" / "index.html"
    if dist_index.exists():
        return FileResponse(dist_index.open("rb"), content_type="text/html")
    return JsonResponse(
        {"detail": "Frontend not built. Run 'npm install && npm run build' in frontend/."},
        status=404,
    )


def asset(request, name):
    target = settings.FRONTEND_DIR / "dist" / name
    if not target.exists():
        return JsonResponse({"detail": "Not found"}, status=404)
    content_type = "text/javascript" if name.endswith(".js") else (
        "text/css" if name.endswith(".css") else "application/octet-stream"
    )
    return FileResponse(target.open("rb"), content_type=content_type)


api_urlpatterns = auth_urlpatterns + note_urlpatterns

urlpatterns = [
    path("api/", include(api_urlpatterns)),
    path("assets/<str:name>", asset),
    path("", index),
]

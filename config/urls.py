from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("", include("core.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("data/", include("datahub.urls")),
]

# The admin panels need a writable database, so they only run locally.
if not settings.IS_LIVE:
    urlpatterns += [
        path("panel/", include("adminpanel.urls")),
        path("django-admin/", admin.site.urls),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif settings.IS_RENDER:
    # Render has no separate file server, so Django serves the uploaded files
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]

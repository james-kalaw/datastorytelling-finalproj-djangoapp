from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("core.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("data/", include("datahub.urls")),
]

# The admin panels need a writable database, so they only run locally.
if not settings.IS_VERCEL:
    urlpatterns += [
        path("panel/", include("adminpanel.urls")),
        path("django-admin/", admin.site.urls),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

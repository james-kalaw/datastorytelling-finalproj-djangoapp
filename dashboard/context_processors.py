from django.conf import settings

from .models import PowerBIPage


def dashboard_nav(request):
    """Makes the dashboard pages available to the navigation dropdown on every page."""
    return {"nav_pages": PowerBIPage.objects.all(), "is_live": settings.IS_LIVE}

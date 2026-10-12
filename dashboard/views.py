from django.conf import settings
from django.shortcuts import get_object_or_404, render

from .models import PowerBIPage, Recommendation

# Python visuals that Django draws (see: python manage.py build_charts)
PYTHON_CHARTS = {
    "impact": {
        "file": "charts/provinces_map.png",
        "title": "Opportunities Across the Philippines",
        "subtitle": "Average Underemployment Rate by Province, 2023–2025 (Darker = Higher)",
        "tag": "PYTHON · GEOPANDAS · DRAWN BY DJANGO",
        "note": "Metro Manila is shown as its 4 districts (average of their cities). Highly urbanized "
        "cities outside NCR have no separate shape; their values appear in the bar charts. "
        "Source: PSA Provincial Labor Market Statistics, 2023–2025 (2025 preliminary).",
    },
    "reality": {
        "file": "charts/education_bubble.png",
        "title": "The Outlier Illusion",
        "subtitle": "Sample Size vs. Rate Volatility, by Education Tier",
        "tag": "PYTHON · MATPLOTLIB · DRAWN BY DJANGO",
        "note": "Senior high's line jumps more because its group is small, not because its "
        "situation is worse. Source: PSA employed and underemployed by highest grade completed, "
        "January 2023–June 2026.",
    },
}


def chart_for(slug):
    """Returns the Python chart for a page, only if build_charts has created the image."""
    chart = PYTHON_CHARTS.get(slug)
    if chart and (settings.BASE_DIR / "static" / chart["file"]).exists():
        return chart
    return None


def with_charts(insights):
    """Gives each insight a `chart` path only if its generated chart file exists."""
    insights = list(insights)
    for insight in insights:
        chart_file = insight.chart_file.strip()
        exists = chart_file and (settings.BASE_DIR / "static" / chart_file).is_file()
        insight.chart = chart_file if exists else ""
    return insights


def overview(request):
    pages = PowerBIPage.objects.all()
    return render(
        request,
        "dashboard/overview.html",
        {"pages": pages, "current": "all", "report_url": settings.POWERBI_REPORT_URL},
    )


def page_detail(request, slug):
    page = get_object_or_404(PowerBIPage, slug=slug)
    insights = with_charts(page.insights.filter(is_published=True))
    pages = list(PowerBIPage.objects.all())
    index = pages.index(page)
    previous_page = pages[index - 1] if index > 0 else None
    next_page = pages[index + 1] if index + 1 < len(pages) else None
    return render(
        request,
        "dashboard/page.html",
        {
            "page": page,
            "insights": insights,
            "chart": chart_for(slug),
            "current": slug,
            "previous_page": previous_page,
            "next_page": next_page,
        },
    )


def recommendations(request):
    items = Recommendation.objects.filter(is_published=True).select_related("related_page")
    return render(
        request,
        "dashboard/recommendations.html",
        {"items": items, "current": "recommendations"},
    )

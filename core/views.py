from django.shortcuts import render

from dashboard.models import PowerBIPage


def home(request):
    acts = PowerBIPage.objects.exclude(slug="synthesis").order_by("order")
    return render(request, "core/home.html", {"acts": acts})


def about(request):
    team = [
        {"name": "Kalaw, James Andre L.", "role": "Data analysis, Power BI and the website"},
    ]
    return render(request, "core/about.html", {"team": team})

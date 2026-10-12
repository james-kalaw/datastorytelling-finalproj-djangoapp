from django.shortcuts import render

from dashboard.models import PowerBIPage


def home(request):
    acts = PowerBIPage.objects.exclude(slug="synthesis").order_by("order")
    return render(request, "core/home.html", {"acts": acts})


def about(request):
    team = [
        {"name": "Detera, Juliana Ysabel D.C.", "role": "Business Intelligence Developer"},
        {"name": "Ituralde, Josh Andrei A.", "role": "Data Acquisition Specialist"},
        {"name": "Kalaw, James Andre L.", "role": "Project Lead and Full-Stack Developer"},
        {"name": "Valdestamon, Ramon Antonio Simon", "role": "Business Intelligence Developer"},
    ]
    return render(request, "core/about.html", {"team": team})

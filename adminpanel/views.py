from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import LoginView
from django.forms import modelform_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .sections import SECTIONS


class PanelLoginView(LoginView):
    template_name = "adminpanel/login.html"
    redirect_authenticated_user = True


def staff_required(view):
    return staff_member_required(view, login_url="adminpanel:login")


def get_section(key):
    section = SECTIONS.get(key)
    if section is None:
        raise Http404("Unknown section")
    return section


def nav_items(active=None):
    return [
        {"key": key, "title": s["title"], "count": s["model"].objects.count(), "on": key == active}
        for key, s in SECTIONS.items()
    ]


def display(value):
    if hasattr(value, "strftime"):
        return timezone.localtime(value).strftime("%Y-%m-%d %H:%M")
    return "" if value is None else str(value)


@staff_required
def home(request):
    return render(request, "adminpanel/home.html", {"nav": nav_items()})


@staff_required
def section_view(request, key):
    section = get_section(key)
    model = section["model"]
    form_class = modelform_factory(model, fields=section["fields"])

    if request.method == "POST":
        # Saving: an existing item (pk sent by the form) or a new one
        pk = request.POST.get("pk")
        instance = get_object_or_404(model, pk=pk) if pk else None
        form = form_class(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f"Saved: {obj}")
            return redirect(f"{request.path}?edit={obj.pk}")
        messages.error(request, "Please fix the highlighted fields.")
    elif request.GET.get("new") == "1":
        instance = None
        form = form_class()
    else:
        edit_id = request.GET.get("edit")
        instance = get_object_or_404(model, pk=edit_id) if edit_id else model.objects.first()
        form = form_class(instance=instance)
    creating = instance is None

    rows = []
    for obj in model.objects.all():
        rows.append({
            "pk": obj.pk,
            "cells": [display(getattr(obj, field)) for field, _ in section["columns"]],
            "on": instance is not None and obj.pk == instance.pk,
        })

    return render(request, "adminpanel/section.html", {
        "nav": nav_items(key),
        "key": key,
        "section": section,
        "headers": [label for _, label in section["columns"]],
        "rows": rows,
        "form": form,
        "instance": instance,
        "creating": creating,
    })


@staff_required
def delete_view(request, key, pk):
    section = get_section(key)
    obj = get_object_or_404(section["model"], pk=pk)
    if request.method == "POST":
        name = str(obj)
        obj.delete()
        messages.success(request, f"Deleted: {name}")
    return redirect("adminpanel:section", key=key)

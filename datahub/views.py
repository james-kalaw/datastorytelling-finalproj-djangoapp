from urllib.parse import urlencode

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render

from .models import Dataset, ExploreItem
from .search import EXAMPLES, run_search

MAX_RESULTS = 25


def data_page(request):
    tab = request.GET.get("tab", "explore")
    context = {"tab": tab}

    if tab == "download":
        datasets = list(Dataset.objects.filter(is_published=True))
        chosen = request.GET.get("ds")
        current = next((d for d in datasets if d.slug == chosen), datasets[0] if datasets else None)
        columns, rows = current.preview() if current else ([], [])
        context.update(
            {"datasets": datasets, "current": current, "columns": columns, "rows": rows}
        )
        return render(request, "datahub/data.html", context)

    # Explore tab
    query = request.GET.get("q", "").strip()
    category = request.GET.get("cat", "All")
    items = list(ExploreItem.objects.all())
    hits, read_as = run_search(items, query, category)

    counts = {}
    for item in items:
        counts[item.category] = counts.get(item.category, 0) + 1
    chips = [{"label": "All", "count": len(items), "on": category == "All",
              "url": "?" + urlencode({"q": query, "cat": "All"})}]
    for value, label in ExploreItem.CATEGORIES:
        chips.append({"label": label, "count": counts.get(value, 0), "on": category == value,
                      "url": "?" + urlencode({"q": query, "cat": value})})

    # Bar widths: each value compared with the largest value in its category
    largest = {}
    for item in items:
        largest[item.category] = max(largest.get(item.category, 0), item.value, item.average)

    shown = hits[:MAX_RESULTS]
    selected_id = request.GET.get("sel")
    selected = next((h for h in hits if str(h.id) == selected_id), hits[0] if hits else None)

    results = []
    for item in shown:
        results.append({
            "item": item,
            "bar": max(2, round(item.value / largest[item.category] * 100)),
            "url": "?" + urlencode({"q": query, "cat": category, "sel": item.id}),
            "on": selected is not None and item.id == selected.id,
        })

    if hits:
        count_text = f"Showing {len(shown)} of {len(hits)} results"
        if len(hits) > MAX_RESULTS:
            count_text += " · type to narrow down"
    else:
        count_text = "0 results"

    context.update({
        "query": query,
        "category": category,
        "chips": chips,
        "examples": [{"text": e, "url": "?" + urlencode({"q": e})} for e in EXAMPLES],
        "results": results,
        "count_text": count_text,
        "read_as": read_as,
        "selected": selected,
        "selected_bar": max(2, round(selected.value / largest[selected.category] * 100)) if selected else 0,
        "average_bar": max(2, round(selected.average / largest[selected.category] * 100)) if selected else 0,
        "total_items": len(items),
    })
    return render(request, "datahub/data.html", context)


def download(request, slug):
    dataset = get_object_or_404(Dataset, slug=slug, is_published=True)
    if not dataset.csv_file:
        raise Http404("This dataset has no file yet.")
    return FileResponse(
        dataset.csv_file.open("rb"), as_attachment=True, filename=f"{dataset.slug}.csv"
    )

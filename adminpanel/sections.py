"""
The content the admin panel can manage. Each section = one model, the fields the
edit form shows, and the columns of the list table.
"""

from dashboard.models import Insight, PowerBIPage, Recommendation
from datahub.models import Dataset

SECTIONS = {
    "insights": {
        "model": Insight,
        "title": "Page insights",
        "description": "The Question / Results / Conclusion cards under each dashboard page. "
        "Upload a Results image to replace the generated chart.",
        "add_label": "New insight",
        "fields": ["page", "label", "question", "summary", "chart_file", "result_image",
                   "image_alt", "caption", "answer", "full_text", "order", "is_published"],
        "columns": [("page", "Page"), ("label", "Label"), ("caption", "Conclusion"),
                    ("updated_at", "Updated")],
    },
    "embeds": {
        "model": PowerBIPage,
        "title": "Power BI pages",
        "description": "Each website dashboard page and the Power BI page ID it opens.",
        "add_label": "New page",
        "fields": ["title", "slug", "page_id", "act_label", "question", "intro", "order"],
        "columns": [("title", "Website page"), ("page_id", "Power BI page ID"),
                    ("slug", "Web address"), ("order", "Order")],
    },
    "recommendations": {
        "model": Recommendation,
        "title": "Recommendations",
        "description": "The actions on the Recommendations page, with their evidence and images.",
        "add_label": "New recommendation",
        "fields": ["number", "title", "evidence", "action", "who", "focus", "related_page",
                   "image", "image_alt", "is_published"],
        "columns": [("number", "#"), ("title", "Title"), ("who", "Who could act"),
                    ("updated_at", "Updated")],
    },
    "datasets": {
        "model": Dataset,
        "title": "Datasets",
        "description": "The cleaned CSVs offered on the Data page. Upload a new file to replace one.",
        "add_label": "New dataset",
        "fields": ["name", "slug", "tag", "description", "coverage", "source", "dictionary",
                   "csv_file", "order", "is_published"],
        "columns": [("name", "Dataset"), ("tag", "Tag"), ("row_count", "Rows"),
                    ("updated_at", "Updated")],
    },
}

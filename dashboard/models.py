from urllib.parse import quote

from django.conf import settings
from django.db import models


class PowerBIPage(models.Model):
    """One page of the published Power BI report (Trends, Impact, Reality, Synthesis)."""

    slug = models.SlugField(unique=True, help_text="Used in the web address, e.g. trends")
    title = models.CharField(max_length=60)
    act_label = models.CharField(max_length=80, help_text="e.g. Act I · Trends · 2005–2026")
    question = models.CharField(max_length=200)
    intro = models.TextField(
        help_text="The proposal's answer to the main research question, shown beside it"
    )
    page_id = models.CharField(
        max_length=40, help_text="Power BI page ID, e.g. 29c29917e904611d106b"
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "Power BI page"

    def __str__(self):
        return self.title

    @property
    def embed_url(self):
        return f"{settings.POWERBI_REPORT_URL}&pageName={quote(self.page_id)}"


class Insight(models.Model):
    """One sub-question card: Question, Results (chart + key numbers) and Conclusion."""

    page = models.ForeignKey(PowerBIPage, on_delete=models.CASCADE, related_name="insights")
    label = models.CharField(max_length=80, help_text="e.g. Sub-Question 1 · The Headline Gap")
    question = models.CharField(max_length=220, blank=True, help_text="The sub-question")
    summary = models.TextField(
        "Results text", help_text="The key numbers, shown under the Results chart"
    )
    result_image = models.ImageField(
        upload_to="insights/", blank=True,
        help_text="Optional. Replaces the generated chart in the Results box",
    )
    image_alt = models.CharField("Image description", max_length=200, blank=True)
    chart_file = models.CharField(
        max_length=120, blank=True,
        help_text="Generated chart under static/, e.g. charts/insights/sq1.png",
    )
    caption = models.CharField("Conclusion", max_length=160, help_text="The one-line answer")
    answer = models.TextField(
        "Proposal answer", blank=True, help_text="The proposal's answer, under the conclusion"
    )
    full_text = models.TextField(blank=True, help_text="Shown under 'Read the full insight'")
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["page__order", "order"]

    def __str__(self):
        return f"{self.page.title}: {self.caption}"


class Recommendation(models.Model):
    """An action on the Recommendations page, tied to the evidence behind it."""

    number = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=160)
    evidence = models.TextField()
    action = models.TextField()
    who = models.CharField("Who could act", max_length=200)
    focus = models.CharField(max_length=120)
    related_page = models.ForeignKey(
        PowerBIPage, on_delete=models.SET_NULL, null=True, blank=True
    )
    image = models.ImageField(upload_to="recommendations/", blank=True)
    image_alt = models.CharField("Image description", max_length=160, blank=True)
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number:02d} · {self.title}"

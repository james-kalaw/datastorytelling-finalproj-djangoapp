import csv

from django.db import models


class Dataset(models.Model):
    """A cleaned CSV offered on the Data page (one per research question)."""

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=80)
    tag = models.CharField(max_length=40, help_text="e.g. SQ 1–2 · TRENDS")
    description = models.TextField()
    coverage = models.CharField(max_length=60, help_text="e.g. 2005–2026")
    source = models.CharField(max_length=200)
    dictionary = models.TextField(
        blank=True, help_text="One line per column: Column name | meaning and unit"
    )
    csv_file = models.FileField(upload_to="datasets/")
    row_count = models.PositiveIntegerField(default=0, editable=False)
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Count the data rows every time the file is saved or replaced.
        super().save(*args, **kwargs)
        if self.csv_file:
            with self.csv_file.open("rb") as f:
                text = f.read()
            if isinstance(text, bytes):
                text = text.decode("utf-8-sig")
            rows = max(len(text.strip().splitlines()) - 1, 0)
            if rows != self.row_count:
                Dataset.objects.filter(pk=self.pk).update(row_count=rows)
                self.row_count = rows

    def dictionary_rows(self):
        rows = []
        for line in self.dictionary.splitlines():
            if "|" in line:
                column, meaning = line.split("|", 1)
                rows.append((column.strip(), meaning.strip()))
        return rows

    def preview(self, limit=8):
        """Returns (columns, first rows) for the preview table."""
        if not self.csv_file:
            return [], []
        with self.csv_file.open("rb") as f:
            text = f.read().decode("utf-8-sig")
        reader = csv.reader(text.splitlines())
        columns = next(reader, [])
        rows = [row for _, row in zip(range(limit), reader)]
        return columns, rows


class ExploreItem(models.Model):
    """One searchable value on the Explore tab (a province, sector, industry, ...)."""

    CATEGORIES = [
        ("Province", "Province"),
        ("Sector", "Sector"),
        ("Industry pay", "Industry pay"),
        ("Education", "Education"),
        ("Age and sex", "Age and sex"),
        ("Reason", "Reason"),
    ]

    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    value = models.FloatField()
    unit = models.CharField(max_length=30)
    context = models.CharField(max_length=160)
    average = models.FloatField()
    average_label = models.CharField(max_length=60)
    page_slug = models.CharField(max_length=30)
    source = models.CharField(max_length=160)
    keywords = models.TextField(blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.category}: {self.name}"

    def formatted(self, number=None):
        number = self.value if number is None else number
        if self.unit == "PHP per day":
            return f"₱{number:,.2f}"
        if self.unit == "% of answers":
            return f"{number:.2f}%"
        return f"{number:.1f}%"

    def formatted_average(self):
        return self.formatted(self.average)

    def comparison(self):
        """Plain-language comparison with the category average."""
        ratio = self.value / self.average if self.average else 1
        diff = self.value - self.average
        if self.unit == "PHP per day":
            if ratio >= 1:
                return f"{ratio:.1f}× the {self.average_label}"
            return f"{round((1 - ratio) * 100)}% below the {self.average_label}"
        if abs(diff) < 0.05:
            return f"About equal to the {self.average_label}"
        if ratio >= 1.5:
            return f"{ratio:.1f}× the {self.average_label}"
        direction = "above" if diff > 0 else "below"
        return f"{abs(diff):.1f} points {direction} the {self.average_label}"

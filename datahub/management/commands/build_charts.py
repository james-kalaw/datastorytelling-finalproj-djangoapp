"""
Draws the Python visuals that cannot run inside a Power BI web embed:
  static/charts/provinces_map.png    (GeoPandas choropleth, Impact page)
  static/charts/education_bubble.png (matplotlib bubble chart, Reality page)
  static/charts/insights/sq1.png ... sq8.png
                                     (one Results chart per sub-question card)

Run after prepare_data:
    python manage.py build_charts
"""

import re
import textwrap

import matplotlib

matplotlib.use("Agg")  # draw to files, no window

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import MaxNLocator  # noqa: E402
import pandas as pd  # noqa: E402
from django.conf import settings  # noqa: E402
from django.core.management.base import BaseCommand, CommandError  # noqa: E402

CLEAN = settings.DATA_DIR / "clean"
GEOJSON = settings.DATA_DIR / "geo" / "geoBoundaries-PHL-ADM2_simplified.geojson"
OUT = settings.BASE_DIR / "static" / "charts"

NAVY = "#0B2545"
GREY = "#5B6B7D"
BLUE = "#2E5C8A"
SOFT = "#7FA7D1"
LIGHT = "#A9B7C6"
SECTOR_COLORS = {"Agriculture": NAVY, "Industry": BLUE, "Services": SOFT}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
SMALL_WORDS = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to", "vs"}

# PSA area names -> map shape names (NCR cities go into their district;
# new or split provinces use the map file's older names)
RENAME = {
    "City of Manila": "NCR, City of Manila, First District",
    "City of Mandaluyong": "NCR, Second District",
    "City of Marikina": "NCR, Second District",
    "City of Pasig": "NCR, Second District",
    "Quezon City": "NCR, Second District",
    "City of San Juan": "NCR, Second District",
    "City of Caloocan": "NCR, Third District",
    "City of Malabon": "NCR, Third District",
    "City of Navotas": "NCR, Third District",
    "City of Valenzuela": "NCR, Third District",
    "City of Las Piñas": "NCR, Fourth District",
    "City of Makati": "NCR, Fourth District",
    "City of Muntinlupa": "NCR, Fourth District",
    "City of Parañaque": "NCR, Fourth District",
    "Pasay City": "NCR, Fourth District",
    "Pateros": "NCR, Fourth District",
    "City of Taguig": "NCR, Fourth District",
    "Davao de Oro": "Compostela Valley",
    "Maguindanao del Norte": "Maguindanao",
    "Maguindanao del Sur": "Maguindanao",
    "City of Cotabato": "Cotabato City",
}


class Command(BaseCommand):
    help = "Draws the province map and the education bubble chart as PNG files."

    def handle(self, *args, **options):
        OUT.mkdir(parents=True, exist_ok=True)
        self.draw_map()
        self.draw_bubble()
        self.draw_insight_charts()
        self.stdout.write(self.style.SUCCESS("Charts are ready in static/charts/."))

    def draw_map(self):
        try:
            import geopandas as gpd
        except ImportError as exc:
            # Skip the map (keeping the last one drawn) so the other charts still get built
            self.stderr.write(self.style.WARNING(
                f"  provinces_map.png skipped: GeoPandas could not load ({exc}). "
                "Run: pip install geopandas"))
            return
        if not GEOJSON.exists():
            raise CommandError(f"Missing map file: {GEOJSON}")

        prov = pd.read_csv(CLEAN / "provincial.csv")
        prov = prov[prov["Year"].isin([2023, 2024, 2025])]
        rates = prov.groupby("Province / City", as_index=False)["Underemployment Rate (%)"].mean()
        rates["MapName"] = rates["Province / City"].replace(RENAME)
        rates = rates.groupby("MapName", as_index=False)["Underemployment Rate (%)"].mean()

        gdf = gpd.read_file(GEOJSON)
        merged = gdf.merge(rates, left_on="shapeName", right_on="MapName", how="left")
        missing = merged["Underemployment Rate (%)"].isna().sum()

        minx, miny, maxx, maxy = merged.total_bounds
        width = 6
        fig, ax = plt.subplots(figsize=(width, width * (maxy - miny) / (maxx - minx)))
        merged.plot(
            column="Underemployment Rate (%)",
            cmap="Blues",
            linewidth=0.4,
            edgecolor="0.6",
            ax=ax,
            legend=True,
            legend_kwds={"shrink": 0.55, "pad": 0.02, "label": "Underemployment Rate (%)"},
            missing_kwds={"color": "lightgrey", "label": "No Data"},
        )
        ax.set_axis_off()
        ax.margins(0)
        fig.tight_layout(pad=0.3)
        fig.savefig(OUT / "provinces_map.png", dpi=170, facecolor="white")
        plt.close(fig)
        self.stdout.write(f"  provinces_map.png  ({missing} map shapes without data)")

    def draw_bubble(self):
        edu = pd.read_csv(CLEAN / "education.csv")
        edu = edu[edu["Tier"] != "No grade"]
        monthly = edu.groupby(["Tier", "Date"])[
            ["Underemployed (thousands)", "Employed (thousands)"]].sum()
        monthly["rate"] = monthly["Underemployed (thousands)"] / monthly["Employed (thousands)"] * 100
        summary = pd.DataFrame({
            "size": edu.groupby("Tier")["Employed (thousands)"].mean(),
            "volatility": monthly.groupby("Tier")["rate"].std(),
            "rate": monthly.groupby("Tier")["rate"].mean(),
        }).dropna()

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(summary["size"], summary["volatility"], s=summary["rate"] * 60,
                   color="#2E5C8A", alpha=0.75, edgecolor=NAVY)
        for tier, row in summary.iterrows():
            ax.annotate(f"{tier}\n{row['rate']:.1f}% Avg", (row["size"], row["volatility"]),
                        xytext=(12, 6), textcoords="offset points", fontsize=10, color=NAVY)
        ax.set_xscale("log")
        ax.set_xlabel("Average Employed per Education Level (Thousands, Log Scale)", color=GREY)
        ax.set_ylabel("Month-to-Month Swing in Rate (Std. Dev., Points)", color=GREY)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=0.25)
        ax.margins(x=0.25, y=0.2)
        fig.tight_layout()
        fig.savefig(OUT / "education_bubble.png", dpi=170, facecolor="white")
        plt.close(fig)
        self.stdout.write("  education_bubble.png")

    # ------------------------------------------------ Results charts (one per sub-question)

    def draw_insight_charts(self):
        """Draws sq1.png ... sq8.png and checks the key numbers against the proposal text."""
        out = OUT / "insights"
        out.mkdir(parents=True, exist_ok=True)
        self.mismatches = []
        for number, draw in enumerate([self.sq1, self.sq2, self.sq3, self.sq4,
                                       self.sq5, self.sq6, self.sq7, self.sq8], start=1):
            self.stdout.write(f"  insights/sq{number}.png")
            fig = draw()
            fig.savefig(out / f"sq{number}.png", dpi=170, facecolor="white")
            plt.close(fig)
        if self.mismatches:
            self.stderr.write(self.style.WARNING(
                "These numbers no longer match the proposal text in seed_content: "
                + ", ".join(self.mismatches)))

    def report(self, label, value, expected=None):
        """Prints a key number; flags it when it is more than 0.2 off the proposal's number
        (or, for a whole number like 61%, when it does not round to it)."""
        line = f"      {label}: {value:.2f}"
        if expected is not None:
            ok = abs(value - expected) <= (0.2 if expected % 1 else 0.5)
            line += f"  (expected {expected}) {'OK' if ok else 'MISMATCH'}"
            if not ok:
                self.mismatches.append(label)
        self.stdout.write(line)

    def sq1(self):
        df = pd.read_csv(CLEAN / "national_rates.csv", parse_dates=["Date"])
        df = df[(df["Sex"] == "Both Sexes") & (df["Survey Round"] == "Quarterly month")]
        df = df.sort_values("Date")
        under, unemp = df["Underemployment Rate (%)"], df["Unemployment Rate (%)"]
        self.report("Average underemployment, 2005–2026", under.mean(), 17.56)
        self.report("Average unemployment, 2005–2026", unemp.mean(), 6.55)

        fig, ax = new_figure("Underemployment vs Unemployment, 2005–2026")
        ax.fill_between(df["Date"], unemp, under, color=SOFT, alpha=0.18, linewidth=0)
        ax.plot(df["Date"], under, color=NAVY, linewidth=2, label="Underemployment Rate")
        ax.plot(df["Date"], unemp, color=SOFT, linewidth=2, label="Unemployment Rate")
        covid = df[df["Date"] == "2020-04-01"]
        if not covid.empty:
            row = covid.iloc[0]
            ax.scatter([row["Date"]] * 2, [row["Underemployment Rate (%)"], row["Unemployment Rate (%)"]],
                       s=36, color=NAVY, zorder=3)
            ax.annotate(f"April 2020 (COVID-19): {row['Underemployment Rate (%)']:.1f}% vs "
                        f"{row['Unemployment Rate (%)']:.1f}%",
                        (row["Date"], row["Underemployment Rate (%)"]),
                        xytext=(pd.Timestamp("2019-01-01"), 11), textcoords="data", ha="right",
                        va="center", fontsize=10, color=NAVY,
                        arrowprops={"arrowstyle": "-", "color": GREY, "linewidth": 1,
                                    "relpos": (1, 0.5)})
        ax.set_ylim(0, max(under.max(), unemp.max()) * 1.12)
        ax.set_xlabel("Survey Date")
        ax.set_ylabel("Rate (%)")
        ax.legend(frameon=False, loc="upper right", fontsize=10)
        return finish(fig, "Source: PSA Labor Force Survey, quarterly months (Jan, Apr, Jul, Oct), "
                           "both sexes.")

    def sq2(self):
        df = pd.read_csv(CLEAN / "national_rates.csv")
        df = df[(df["Sex"] == "Both Sexes") & (df["Year"] >= 2021)]
        by_month = df.groupby("Month")["Underemployment Rate (%)"].mean().reindex(MONTHS).dropna()
        self.report("July average since 2021", by_month["July"], 15.5)
        self.report("April average since 2021", by_month["April"], 14.7)

        fig, ax = new_figure("Underemployment by Survey Month, 2021–2026")
        colors = [NAVY if m in ("July", "April") else SOFT for m in by_month.index]
        bars = ax.bar([m[:3] for m in by_month.index], by_month.values, color=colors, width=0.7)
        ax.bar_label(bars, fmt="%.1f", padding=2, fontsize=9, color=NAVY)
        ax.set_ylim(0, by_month.max() * 1.15)
        ax.grid(axis="x", visible=False)
        ax.set_xlabel("Survey Month")
        ax.set_ylabel("Average Underemployment Rate (%)")
        return finish(fig, "Source: PSA Labor Force Survey, monthly rounds 2021–2026, both sexes.")

    def sq3(self):
        df = pd.read_csv(CLEAN / "provincial.csv")
        df = df[df["Year"].isin([2023, 2024, 2025])]
        rates = df.groupby("Province / City")["Underemployment Rate (%)"].mean().sort_values()
        average = rates.mean()
        self.report(f"Highest ({rates.index[-1]})", rates.iloc[-1], 49.3)
        self.report(f"Lowest ({rates.index[0]})", rates.iloc[0], 2.0)
        self.report(f"Average of {len(rates)} areas", average, 12.3)
        self.report("Highest / lowest ratio", rates.iloc[-1] / rates.iloc[0], 24.8)

        ranked = rates.iloc[::-1]
        top, bottom = ranked.head(5), ranked.tail(5)
        # Highest five at the top, a small gap, then the lowest five
        y_top = [11 - i for i in range(5)]
        y_bottom = [4.5 - i for i in range(5)]

        fig, ax = new_figure("Highest and Lowest Areas, 2023–2025")
        for y, values, color, label in [(y_top, top, NAVY, "Highest 5"),
                                        (y_bottom, bottom, SOFT, "Lowest 5")]:
            bars = ax.barh(y, values.values, color=color, height=0.75, label=label)
            ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9.5, color=NAVY)
        ax.axvline(average, color=GREY, linestyle="--", linewidth=1.2,
                   label=f"Average of {len(rates)} Areas ({average:.1f}%)")
        ax.set_yticks(y_top + y_bottom, [city_name(n) for n in list(top.index) + list(bottom.index)])
        ax.set_xlim(0, rates.max() * 1.15)
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("Average Underemployment Rate (%)")
        ax.legend(frameon=False, loc="lower right", fontsize=9.5)
        return finish(fig, "Source: PSA Provincial Labor Market Statistics, 2023–2025 "
                           "(2025 preliminary).")

    def sq4(self):
        df = pd.read_csv(CLEAN / "age_sex.csv", parse_dates=["Date"])
        df = df[(df["Date"].dt.year >= 2021) & df["Sex"].isin(["Male", "Female"])
                & (df["Age Group"] != "Total")]
        cols = ["Underemployed (thousands)", "Employed (thousands)"]
        groups = df.groupby(["Age Group", "Sex"])[cols].sum()
        rates = (groups[cols[0]] / groups[cols[1]] * 100).unstack("Sex")
        overall = df.groupby("Sex")[cols].sum()
        overall = overall[cols[0]] / overall[cols[1]] * 100
        gap = rates["Male"] - rates["Female"]
        self.report("Men overall since 2021", overall["Male"], 14.7)
        self.report("Women overall since 2021", overall["Female"], 11.0)
        self.report(f"Widest gap ({gap.idxmax()}), points", gap.max())

        fig, ax = new_figure("Underemployment by Sex and Age, 2021–2026")
        x = range(len(rates))
        for offset, sex, color in [(-0.2, "Male", NAVY), (0.2, "Female", SOFT)]:
            bars = ax.bar([i + offset for i in x], rates[sex], width=0.38, color=color,
                          label=f"{sex} ({overall[sex]:.1f}% Overall)")
            ax.bar_label(bars, fmt="%.1f", padding=2, fontsize=8.5, color=NAVY)
        ax.set_xticks(list(x), [a.replace(" - ", "–") for a in rates.index])
        ax.set_ylim(0, rates.values.max() * 1.3)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.grid(axis="x", visible=False)
        ax.set_xlabel("Age Group")
        ax.set_ylabel("Underemployment Rate (%)")
        ax.legend(frameon=False, loc="upper left", ncol=2, fontsize=10)
        return finish(fig, "Source: PSA Labor Force Survey by sex and age group, 2021–2026 "
                           "(underemployed ÷ employed).")

    def sq5(self):
        df = pd.read_csv(CLEAN / "sector.csv")
        means = df.groupby("Sector")[["Underemployment Rate (%)", "Share of Underemployed (%)"]].mean()
        means = means.reindex(list(SECTOR_COLORS))
        for sector, expected in [("Agriculture", 18.9), ("Industry", 12.7), ("Services", 10.6)]:
            self.report(f"{sector} rate", means.loc[sector, "Underemployment Rate (%)"], expected)
        self.report("Services share of underemployed",
                   means.loc["Services", "Share of Underemployed (%)"], 52.9)

        fig, axes = new_figure("Highest Rate vs Most Underemployed Workers", ncols=2)
        sector_bars(axes[0], means["Underemployment Rate (%)"], "%.1f%%", "Underemployment Rate (%)")
        sector_bars(axes[1], means["Share of Underemployed (%)"], "%.1f%%",
                    "Share of All Underemployed (%)")
        return finish(fig, "Source: PSA LFS Table 3 and employed persons by industry, "
                           "Jun 2025–Jun 2026 (mean of monthly values).")

    def sq6(self):
        vis = pd.read_csv(CLEAN / "visible.csv")
        vis = vis[(vis["Sex"] == "Both Sexes") & (vis["Age Group"] == "Total")]
        totals = vis[["Visibly Underemployed (thousands)", "Invisibly Underemployed (thousands)"]].sum()
        shares = pd.Series(totals.values / totals.sum() * 100, index=["Visible", "Invisible"])
        self.report("Visible share", shares["Visible"], 61)

        reasons = pd.read_csv(CLEAN / "reasons.csv", parse_dates=["Date"])
        latest = reasons[reasons["Date"] == reasons["Date"].max()]
        top = latest.nlargest(5, "Share of Answers (%)").iloc[::-1]
        month = latest["Month"].iloc[0]
        self.report(f"Top reason in {month} ({top['Reason'].iloc[-1]})",
                   top["Share of Answers (%)"].iloc[-1], 68.8)

        fig, (left, right) = new_figure("Visible Share and Reasons for Short Hours", ncols=2,
                                        width_ratios=[1, 1.9])
        bars = left.bar(shares.index, shares.values, color=[NAVY, LIGHT], width=0.65)
        left.bar_label(bars, fmt="%.0f%%", padding=2, fontsize=10, color=NAVY)
        left.set_ylim(0, 100)
        left.grid(axis="x", visible=False)
        left.set_title("Share of Underemployed (%)", fontsize=10, color=GREY, loc="left")

        labels = [textwrap.fill(title_case(r), 20) for r in top["Reason"]]
        colors = [SOFT] * (len(top) - 1) + [NAVY]
        bars = right.barh(labels, top["Share of Answers (%)"], color=colors, height=0.7)
        right.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9.5, color=NAVY)
        right.set_xlim(0, top["Share of Answers (%)"].max() * 1.25)
        right.tick_params(axis="y", labelsize=8.5)
        right.grid(axis="y", visible=False)
        right.set_title(f"Top 5 Reasons, {month} (%)", fontsize=10, color=GREY, loc="left")
        return finish(fig, "Source: PSA Labor Force Survey (visible: under 40 hours, all rounds); "
                           "PSA LFS Table C (reasons).")

    def sq7(self):
        df = pd.read_csv(CLEAN / "education.csv")
        cols = ["Underemployed (thousands)", "Employed (thousands)"]
        sums = df.groupby("Education Level")[cols].sum()
        rates = (sums[cols[0]] / sums[cols[1]] * 100).sort_values()
        for level, expected in [("No grade completed", 16.7), ("College Graduate", 7.2),
                                ("Senior High Graduate", 11.7), ("Senior High Undergraduate", 11.8)]:
            self.report(level, rates[level], expected)

        fig, ax = new_figure("Underemployment by Highest Grade Completed")
        highlight = {"Senior High Graduate", "Senior High Undergraduate"}
        colors = [NAVY if level in highlight else SOFT for level in rates.index]
        bars = ax.barh([title_case(level) for level in rates.index], rates.values, color=colors,
                       height=0.72)
        ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9, color=NAVY)
        ax.set_xlim(0, rates.max() * 1.15)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.tick_params(axis="y", labelsize=9.5)
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("Underemployment Rate (%)")
        return finish(fig, "Source: PSA employed and underemployed by highest grade completed, "
                           "Jan 2023–Jun 2026.")

    def sq8(self):
        pay = pd.read_csv(CLEAN / "pay.csv", parse_dates=["Date"])
        avg_pay = pay.groupby("Sector")["Average Daily Basic Pay (PHP)"].mean()
        avg_pay = avg_pay.reindex(list(SECTOR_COLORS))
        rates = pd.read_csv(CLEAN / "sector.csv").groupby("Sector")["Underemployment Rate (%)"].mean()
        rates = rates.reindex(list(SECTOR_COLORS))
        start, end = pay["Date"].min(), pay["Date"].max()
        for sector, expected in [("Agriculture", 299), ("Industry", 542), ("Services", 695)]:
            self.report(f"{sector} pay ({start:%b %Y}–{end:%b %Y})", avg_pay[sector], expected)

        fig, axes = new_figure("Lowest Pay, Highest Underemployment", ncols=2)
        sector_bars(axes[0], avg_pay, "₱%.0f", "Average Daily Basic Pay (₱)")
        sector_bars(axes[1], rates, "%.1f%%", "Underemployment Rate (%)")
        return finish(fig, f"Source: PSA average daily basic pay, {start:%b %Y}–{end:%b %Y} "
                           "(mean across industries);\nPSA LFS Table 3, Jun 2025–Jun 2026.")


# ------------------------------------------------ chart helpers

def new_figure(title, ncols=1, width_ratios=None):
    """A 6.4 x 4.0 in figure in the site style, with its title inside the top-left corner."""
    fig, axes = plt.subplots(1, ncols, figsize=(6.4, 4.0),
                             gridspec_kw={"width_ratios": width_ratios} if width_ratios else None)
    fig.text(0.02, 0.97, title, ha="left", va="top", fontsize=13, fontweight="bold", color=NAVY)
    for ax in (axes if ncols > 1 else [axes]):
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(LIGHT)
        ax.grid(alpha=0.25)
        ax.set_axisbelow(True)
        ax.tick_params(colors=GREY, labelsize=10)
        ax.xaxis.label.set(color=GREY, fontsize=10.5)
        ax.yaxis.label.set(color=GREY, fontsize=10.5)
    return fig, axes


def finish(fig, source):
    """Adds the source note at the bottom-left and fits everything inside the figure."""
    lines = source.count("\n") + 1
    fig.text(0.02, 0.02, source, ha="left", va="bottom", fontsize=7.5, color=GREY, linespacing=1.4)
    fig.tight_layout(rect=(0, 0.02 + 0.035 * lines, 1, 0.91))
    return fig


def sector_bars(ax, values, fmt, title):
    """One bar per sector; each sector keeps the same color on every chart."""
    bars = ax.bar(values.index, values.values, width=0.65,
                  color=[SECTOR_COLORS[s] for s in values.index])
    ax.bar_label(bars, fmt=fmt, padding=2, fontsize=10, color=NAVY)
    ax.set_ylim(0, values.max() * 1.18)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="x", labelsize=9.5)
    ax.set_title(title, fontsize=10, color=GREY, loc="left")


def city_name(name):
    """PSA's "City of Zamboanga" reads better as "Zamboanga City"."""
    return re.sub(r"^City of (.+)$", r"\1 City", name)


def title_case(text):
    words = text.split()
    return " ".join(w if (i and w.lower() in SMALL_WORDS) else w[:1].upper() + w[1:]
                    for i, w in enumerate(words))

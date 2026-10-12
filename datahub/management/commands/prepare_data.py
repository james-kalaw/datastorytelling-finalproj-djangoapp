"""
Cleans the tables exported from Power BI with DAX Studio and loads them into the website.

Input : data/raw/<TableName>.csv   (DAX Studio > Advanced > Export Data > CSV)
Output: data/clean/*.csv           (8 tidy datasets, one per research question)
        Dataset and ExploreItem rows in the database (Data page)

    python manage.py prepare_data
"""

import re

import pandas as pd
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from datahub.models import Dataset, ExploreItem

RAW = settings.DATA_DIR / "raw"
CLEAN = settings.DATA_DIR / "clean"

NEEDED_TABLES = [
    "Fact_Rates", "Fact_Levels", "Fact_AgeGroup", "Fact_Provincial",
    "Fact_SectorUnderemployment", "Fact_Industry_Current", "Fact_Pay",
    "Fact_Education", "Fact_Underemployment_Reasons",
]
AGGREGATE_LEVELS = ["Elementary", "Junior High School", "Senior High School", "Post Secondary", "College"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]


# ---------------------------------------------------------------- helpers

def read_table(name):
    """Reads one DAX Studio CSV and tidies its column names and dates."""
    path = RAW / f"{name}.csv"
    if not path.exists():
        raise CommandError(f"Missing file: {path}. Export it from DAX Studio first.")
    try:
        df = pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False, na_values=[""])
    except UnicodeDecodeError:
        # DAX Studio's "Unicode" option writes UTF-16 files
        df = pd.read_csv(path, encoding="utf-16", keep_default_na=False, na_values=[""])
    # DAX Studio can write headers as Table[Column]; keep only the column name.
    df.columns = [re.sub(r"^.*\[(.+)\]$", r"\1", str(c)).strip() for c in df.columns]
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip().replace({"nan": None})
    return df


def nice_region(region):
    region = str(region)
    if region.startswith("NATIONAL CAPITAL"):
        return "NCR"
    match = re.match(r"REGION ([IVXA-]+) \(", region)
    if match:
        return "Region " + match.group(1).replace("IVA", "IV-A")
    match = re.match(r".*\((.*)\)", region)
    name = match.group(1) if match else region.title()
    return "MIMAROPA" if name.lower().startswith("mimaropa") else name


ISLAND_GROUP = {
    "NCR": "Luzon", "CAR": "Luzon", "Region I": "Luzon", "Region II": "Luzon",
    "Region III": "Luzon", "Region IV-A": "Luzon", "MIMAROPA": "Luzon", "Region V": "Luzon",
    "Region VI": "Visayas", "Region VII": "Visayas", "Region VIII": "Visayas", "NIR": "Visayas",
    "Region IX": "Mindanao", "Region X": "Mindanao", "Region XI": "Mindanao",
    "Region XII": "Mindanao", "Region XIII": "Mindanao", "BARMM": "Mindanao",
}


def month_label(date):
    return f"{MONTHS[date.month - 1]} {date.year}"


# ---------------------------------------------------------------- datasets

def build_national_rates(rates):
    df = rates[rates["Indicator"].isin(["Unemployment Rate", "Underemployment Rate"])]
    wide = df.pivot_table(index=["Date", "Sex"], columns="Indicator", values="Rate").reset_index()
    wide["Ratio"] = wide["Underemployment Rate"] / wide["Unemployment Rate"]
    out = pd.DataFrame({
        "Date": wide["Date"].dt.strftime("%Y-%m-%d"),
        "Year": wide["Date"].dt.year,
        "Month": wide["Date"].dt.month.map(lambda m: MONTHS[m - 1]),
        "Sex": wide["Sex"],
        "Unemployment Rate (%)": wide["Unemployment Rate"].round(2),
        "Underemployment Rate (%)": wide["Underemployment Rate"].round(2),
        "Underemployment-to-Unemployment Ratio": wide["Ratio"].round(2),
        "Survey Round": wide["Date"].dt.month.map(
            lambda m: "Quarterly month" if m in (1, 4, 7, 10) else "Monthly round"),
    })
    return out.sort_values(["Date", "Sex"])


def build_provincial(prov):
    prov = prov[prov["Year"].notna()].copy()
    prov["Year"] = pd.to_numeric(prov["Year"], errors="coerce").astype("Int64")
    est = prov[prov["SubMetric"] == "Estimate"]
    rate = est[est["Metric"] == "UnderemploymentRate"][["Region", "Area", "Year", "Status", "Value"]]
    count = est[est["Metric"] == "TotalUnderemployed"][["Area", "Year", "Value"]]
    merged = rate.merge(count, on=["Area", "Year"], how="left", suffixes=("_rate", "_count"))
    out = pd.DataFrame({
        "Region": merged["Region"].map(nice_region),
        "Province / City": merged["Area"],
        "Year": merged["Year"],
        "Status": merged["Status"].map({"F": "Final", "P": "Preliminary"}),
        "Underemployment Rate (%)": merged["Value_rate"].round(2),
        "Underemployed Persons (thousands)": merged["Value_count"].round(1),
    })
    return out.sort_values(["Region", "Province / City", "Year"])


def build_age_sex(age):
    wide = age.pivot_table(index=["Date", "Sex", "Age Group"], columns="Indicator",
                           values="Value", aggfunc="sum").reset_index()
    out = pd.DataFrame({
        "Date": wide["Date"].dt.strftime("%Y-%m-%d"),
        "Sex": wide["Sex"],
        "Age Group": wide["Age Group"].str.replace(" Years Old", "").str.replace(" and Over", "+"),
        "Labor Force (thousands)": wide["Labor Force"].round(1),
        "Employed (thousands)": wide["Employed"].round(1),
        "Unemployed (thousands)": wide["Unemployed"].round(1),
        "Underemployed (thousands)": wide["Underemployed"].round(1),
        "Unemployment Rate (%)": (wide["Unemployed"] / wide["Labor Force"] * 100).round(2),
        "Underemployment Rate (%)": (wide["Underemployed"] / wide["Employed"] * 100).round(2),
    })
    return out.sort_values(["Date", "Sex", "Age Group"])


def build_sector(sector, levels, industry):
    sector = sector.copy()
    sector["Sector Name"] = sector["Sector Name"].str.strip()
    under = levels[(levels["Indicator"] == "Underemployed Persons") & (levels["Sex"] == "Both Sexes")]
    under = under.set_index("Date")["Level (in thousands)"]
    employed = industry.groupby(["Date", "Macro Sector"])["Employed Count"].sum()
    rows = []
    for _, r in sector.iterrows():
        total = under.get(r["Date"])
        emp = employed.get((r["Date"], r["Sector Name"]))
        share = r["Underemployed Percentage"]
        under_sector = total * share / 100 if total is not None else None
        rows.append({
            "Month": month_label(r["Date"]),
            "Date": r["Date"].strftime("%Y-%m-%d"),
            "Sector": r["Sector Name"],
            "Share of Underemployed (%)": round(share, 1),
            "Underemployed (thousands)": round(under_sector, 1) if under_sector else None,
            "Employed (thousands)": round(emp, 1) if emp else None,
            "Underemployment Rate (%)": round(under_sector / emp * 100, 2) if emp and under_sector else None,
        })
    return pd.DataFrame(rows).sort_values(["Date", "Sector"])


def build_visible(age):
    wide = age[age["Indicator"].isin(["Visibly Underemployed", "Invisibly Underemployed"])]
    wide = wide.pivot_table(index=["Date", "Sex", "Age Group"], columns="Indicator",
                            values="Value", aggfunc="sum").reset_index()
    vis, inv = wide["Visibly Underemployed"], wide["Invisibly Underemployed"]
    out = pd.DataFrame({
        "Date": wide["Date"].dt.strftime("%Y-%m-%d"),
        "Sex": wide["Sex"],
        "Age Group": wide["Age Group"].str.replace(" Years Old", "").str.replace(" and Over", "+"),
        "Visibly Underemployed (thousands)": vis.round(1),
        "Invisibly Underemployed (thousands)": inv.round(1),
        "Visible Share (%)": (vis / (vis + inv) * 100).round(1),
    })
    return out.sort_values(["Date", "Sex", "Age Group"])


def build_reasons(reasons):
    reasons = reasons.copy()
    reasons["Reason"] = reasons["Reason"].str.replace("pat time", "part-time")
    reasons["Rank"] = reasons.groupby("Date")["Percent"].rank(ascending=False, method="first").astype(int)
    out = pd.DataFrame({
        "Month": reasons["Date"].map(month_label),
        "Date": reasons["Date"].dt.strftime("%Y-%m-%d"),
        "Reason": reasons["Reason"],
        "Share of Answers (%)": reasons["Percent"].round(2),
        "Rank": reasons["Rank"],
    })
    return out.sort_values(["Date", "Rank"])


def build_education(edu):
    df = edu[~edu["Education Level"].isin(AGGREGATE_LEVELS)].copy()
    out = pd.DataFrame({
        "Date": df["Date"].dt.strftime("%Y-%m-%d"),
        "Education Level": df["Education Level"],
        "Tier": df["Education Tier"].replace({"Other": "No grade"}),
        "Status": df["Education Status"].replace({"N/A": "None"}),
        "Employed (thousands)": df["Employed Count"],
        "Underemployed (thousands)": df["Underemployed Count"],
        "Underemployment Rate (%)": (df["Underemployed Count"] / df["Employed Count"] * 100).round(2),
    })
    return out.sort_values(["Date", "Education Level"])


def build_pay(pay):
    out = pd.DataFrame({
        "Date": pay["Date"].dt.strftime("%Y-%m-%d"),
        "Industry": pay["Industry"].str.replace("Whosale", "Wholesale"),
        "Sector": pay["Macro Sector"],
        "Average Daily Basic Pay (PHP)": pay["Average Pay"].round(2),
    })
    return out.dropna(subset=["Average Daily Basic Pay (PHP)"]).sort_values(["Date", "Industry"])


# ---------------------------------------------------------------- search index

def build_explore(clean, edu_raw):
    items = []

    prov = clean["provincial"]
    prov = prov[prov["Year"].isin([2023, 2024, 2025])]
    by_area = prov.groupby("Province / City")["Underemployment Rate (%)"].mean()
    by_area = by_area.sort_values(ascending=False)
    # Some areas changed region between releases; use the most recent region name.
    latest_region = prov.sort_values("Year").groupby("Province / City")["Region"].last()
    prov_avg = by_area.mean()
    for rank, (area, value) in enumerate(by_area.items(), start=1):
        region = latest_region[area]
        island = ISLAND_GROUP.get(region, "")
        items.append(dict(
            name=area, category="Province", value=round(value, 1), unit="% underemployed",
            context=f"Rank {rank} of {len(by_area)} · {region}", average=round(prov_avg, 1),
            average_label="provincial average", page_slug="impact",
            source="PSA Provincial LFS, 2023–2025 avg (2025 preliminary)",
            keywords=f"{island} province provincial city area place location".lower()))

    nat = clean["national_rates"]
    recent = nat[(nat["Year"] >= 2021) & (nat["Sex"] == "Both Sexes")]
    national_avg = round(recent["Underemployment Rate (%)"].mean(), 1)

    sec = clean["sector"]
    share = sec.groupby("Sector")["Share of Underemployed (%)"].mean()
    rate = sec.groupby("Sector")["Underemployment Rate (%)"].mean()
    sector_words = {
        "Agriculture": "farm farming farmers fishing fisheries agri agricultural",
        "Industry": "factory factories manufacturing construction mining",
        "Services": "service retail bpo call center",
    }
    highest, lowest = rate.idxmax(), rate.idxmin()
    for name in rate.index:
        note = f"{share[name]:.1f}% of all underemployed"
        if name == highest:
            note = "Highest rate; " + note
        elif name == lowest:
            note = "Lowest rate; " + note
        items.append(dict(
            name=name, category="Sector", value=round(rate[name], 1), unit="% underemployed",
            context=note, average=national_avg, average_label="national average since 2021",
            page_slug="impact", source="PSA Table 3 + industry employment, Jun 2025–Jun 2026",
            keywords=sector_words.get(name, "") + " sector"))

    pay = clean["pay"]
    by_industry = pay.groupby(["Industry", "Sector"])["Average Daily Basic Pay (PHP)"].mean()
    by_industry = by_industry.sort_values(ascending=False)
    pay_avg = pay["Average Daily Basic Pay (PHP)"].mean()
    for rank, ((industry, sector_name), value) in enumerate(by_industry.items(), start=1):
        items.append(dict(
            name=industry, category="Industry pay", value=round(value, 2), unit="PHP per day",
            context=f"{sector_name} sector · rank {rank} of {len(by_industry)}",
            average=round(pay_avg, 2), average_label="all-industry average", page_slug="reality",
            source="PSA average daily basic pay, 2016–2026",
            keywords="pay salary salaries wage wages income earnings paid industry job"))

    agg = edu_raw[edu_raw["Education Level"].isin(AGGREGATE_LEVELS + ["No grade completed"])]
    edu_avg = agg["Underemployed Count"].sum() / agg["Employed Count"].sum() * 100
    edu = clean["education"]
    sums = edu.groupby("Education Level")[["Underemployed (thousands)", "Employed (thousands)"]].sum()
    sums["rate"] = sums["Underemployed (thousands)"] / sums["Employed (thousands)"] * 100
    for level, row in sums.sort_values("rate").iterrows():
        small = level in ("Post Secondary Undergraduate", "No grade completed")
        items.append(dict(
            name=level, category="Education", value=round(row["rate"], 1), unit="% underemployed",
            context="Small group, read with care" if small else "Jan 2023–Jun 2026 average",
            average=round(edu_avg, 1), average_label="all education levels", page_slug="reality",
            source="PSA employed and underemployed by highest grade, 2023–2026",
            keywords="education school schooling diploma degree studies"))

    age = clean["age_sex"]
    age = age[(pd.to_datetime(age["Date"]).dt.year >= 2021) & (age["Sex"] != "Both Sexes")
              & (age["Age Group"] != "Total")]
    grouped = age.groupby(["Sex", "Age Group"])[
        ["Underemployed (thousands)", "Employed (thousands)", "Unemployed (thousands)",
         "Labor Force (thousands)"]].sum()
    for (sex, group), row in grouped.iterrows():
        words = "age sex gender " + ("female women woman" if sex == "Female" else "male men man")
        if group.startswith("15"):
            words += " youth young teen teens"
        if group.startswith("65"):
            words += " elderly older senior seniors"
        unemp = row["Unemployed (thousands)"] / row["Labor Force (thousands)"] * 100
        items.append(dict(
            name=f"{sex}, {group.replace(' - ', '–')}", category="Age and sex",
            value=round(row["Underemployed (thousands)"] / row["Employed (thousands)"] * 100, 1),
            unit="% underemployed", context=f"Unemployment {unemp:.1f}%",
            average=national_avg, average_label="all ages since 2021", page_slug="impact",
            source="PSA LFS by sex and age, 2021–2026", keywords=words))

    reasons = clean["reasons"]
    latest = reasons["Date"].max()
    latest_rows = reasons[reasons["Date"] == latest].sort_values("Rank")
    label = latest_rows["Month"].iloc[0]
    for _, r in latest_rows.iterrows():
        items.append(dict(
            name=r["Reason"], category="Reason", value=round(r["Share of Answers (%)"], 2),
            unit="% of answers", context=f"Rank {r['Rank']} of {len(latest_rows)} reasons, {label}",
            average=round(100 / len(latest_rows), 1), average_label="average reason share",
            page_slug="reality", source=f"PSA Table C, {label}",
            keywords="reason reasons why cause causes hours short"))
    return items


# ---------------------------------------------------------------- catalogue

DATASETS = [
    ("national-rates", "national_rates", "National rates", "SQ 1–2 · TRENDS",
     "Unemployment and underemployment rates by sex, quarterly until 2020 and monthly from 2021.",
     "2005–2026", "PSA OpenSTAT, Rates of Key Employment Indicators",
     "Date | First day of the survey month\nSex | Both Sexes, Male or Female\n"
     "Unemployment Rate (%) | Unemployed as a share of the labor force\n"
     "Underemployment Rate (%) | Underemployed as a share of the employed\n"
     "Underemployment-to-Unemployment Ratio | How many times larger underemployment is\n"
     "Survey Round | Quarterly month (Jan, Apr, Jul, Oct) or monthly round"),
    ("provincial-underemployment", "provincial", "Provincial underemployment", "SQ 3 · GEOGRAPHY",
     "Underemployment rate and underemployed persons by province and highly urbanized city.",
     "2023–2025", "PSA Provincial Labor Market Statistics",
     "Region | Administrative region\nProvince / City | Province or highly urbanized city\n"
     "Year | Survey year\nStatus | Final or Preliminary (PSA)\n"
     "Underemployment Rate (%) | Annual estimate\n"
     "Underemployed Persons (thousands) | Annual estimate"),
    ("age-and-sex", "age_sex", "Age and sex", "SQ 4 · AGE AND SEX",
     "Labor force, employed, unemployed and underemployed by age group and sex, with rates.",
     "2005–2026", "PSA OpenSTAT, files 03–08",
     "Date | First day of the survey month\nSex | Both Sexes, Male or Female\n"
     "Age Group | 15–24 up to 65+, or Total\n"
     "Labor Force / Employed / Unemployed / Underemployed (thousands) | Persons, in thousands\n"
     "Unemployment Rate (%) | Unemployed ÷ labor force\n"
     "Underemployment Rate (%) | Underemployed ÷ employed"),
    ("sector-rates", "sector", "Sector rates", "SQ 5 · SECTORS",
     "Each sector's share of the underemployed, its employment, and the derived underemployment rate.",
     "Jun 2025–Jun 2026", "PSA LFS Table 3 and employed persons by industry",
     "Month | Survey month\nSector | Agriculture, Industry or Services\n"
     "Share of Underemployed (%) | Sector's share of all underemployed persons (PSA Table 3)\n"
     "Underemployed (thousands) | Total underemployed × share\n"
     "Employed (thousands) | Employed persons in the sector\n"
     "Underemployment Rate (%) | Underemployed ÷ employed in the sector"),
    ("visible-invisible", "visible", "Visible vs. invisible", "SQ 6 · HOURS",
     "Visibly (under 40 hours) and invisibly (40+ hours) underemployed persons by age and sex.",
     "2005–2026", "PSA OpenSTAT, files 17–18",
     "Date | First day of the survey month\nSex | Both Sexes, Male or Female\n"
     "Age Group | 15–24 up to 65+, or Total\n"
     "Visibly Underemployed (thousands) | Working under 40 hours, want more hours\n"
     "Invisibly Underemployed (thousands) | Working 40+ hours, want more work\n"
     "Visible Share (%) | Visible ÷ (visible + invisible)"),
    ("reasons-short-hours", "reasons", "Reasons for short hours", "SQ 6 · REASONS",
     "Share of answers by reason for working less than 40 hours.",
     "Jun 2025–Jun 2026", "PSA LFS Table C",
     "Month | Survey month\nReason | Reason given for working under 40 hours\n"
     "Share of Answers (%) | Share of all answers that month\nRank | 1 = most common reason"),
    ("education", "education", "Education", "SQ 7 · EDUCATION",
     "Employed and underemployed persons by highest grade completed, with rates.",
     "2023–2026", "PSA OpenSTAT, files 14–15",
     "Date | First day of the survey month\nEducation Level | Highest grade completed\n"
     "Tier | Elementary, Junior High, Senior High, Post-Secondary, College or No grade\n"
     "Status | Graduate, Undergraduate, Completed or None\n"
     "Employed / Underemployed (thousands) | Persons, in thousands\n"
     "Underemployment Rate (%) | Underemployed ÷ employed"),
    ("pay-by-industry", "pay", "Pay by industry", "SQ 8 · PAY",
     "Average daily basic pay of wage and salary workers by industry.",
     "2016–2026", "PSA OpenSTAT, average daily basic pay",
     "Date | First day of the survey month\nIndustry | Major industry group\n"
     "Sector | Agriculture, Industry or Services\n"
     "Average Daily Basic Pay (PHP) | Pesos per day"),
]


class Command(BaseCommand):
    help = "Cleans the DAX Studio export and loads the datasets and search index."

    def handle(self, *args, **options):
        CLEAN.mkdir(parents=True, exist_ok=True)
        self.stdout.write("Reading the DAX Studio export from data/raw ...")
        t = {name: read_table(name) for name in NEEDED_TABLES}

        clean = {
            "national_rates": build_national_rates(t["Fact_Rates"]),
            "provincial": build_provincial(t["Fact_Provincial"]),
            "age_sex": build_age_sex(t["Fact_AgeGroup"]),
            "sector": build_sector(t["Fact_SectorUnderemployment"], t["Fact_Levels"],
                                   t["Fact_Industry_Current"]),
            "visible": build_visible(t["Fact_AgeGroup"]),
            "reasons": build_reasons(t["Fact_Underemployment_Reasons"]),
            "education": build_education(t["Fact_Education"]),
            "pay": build_pay(t["Fact_Pay"]),
        }
        for key, df in clean.items():
            df.to_csv(CLEAN / f"{key}.csv", index=False, encoding="utf-8")
            self.stdout.write(f"  data/clean/{key}.csv  {len(df):,} rows")

        self.check_against_dashboard(clean)

        # Datasets (copy each clean CSV into media/datasets through the Dataset model)
        for order, (slug, key, name, tag, desc, coverage, source, dictionary) in enumerate(DATASETS, 1):
            dataset, _ = Dataset.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "tag": tag, "description": desc, "coverage": coverage,
                          "source": source, "dictionary": dictionary, "order": order},
            )
            if dataset.csv_file:
                dataset.csv_file.delete(save=False)
            storage = dataset.csv_file.storage
            if storage.exists(f"datasets/{slug}.csv"):
                storage.delete(f"datasets/{slug}.csv")
            with open(CLEAN / f"{key}.csv", "rb") as f:
                dataset.csv_file.save(f"{slug}.csv", File(f), save=False)
            dataset.save()
        self.stdout.write(f"Datasets loaded: {len(DATASETS)}")

        # Search index
        items = build_explore(clean, t["Fact_Education"])
        ExploreItem.objects.all().delete()
        ExploreItem.objects.bulk_create([ExploreItem(**item) for item in items])
        self.stdout.write(f"Search index: {len(items)} values")
        self.stdout.write(self.style.SUCCESS("Data is ready."))

    def check_against_dashboard(self, clean):
        """Prints the key numbers so you can compare them with the Power BI cards."""
        nat = clean["national_rates"]
        both = nat[nat["Sex"] == "Both Sexes"]
        quarterly = both[both["Survey Round"] == "Quarterly month"]
        monthly = both[both["Year"] >= 2021]
        sec = clean["sector"].groupby("Sector")["Underemployment Rate (%)"].mean()
        prov = clean["provincial"]
        prov = prov[prov["Year"].isin([2023, 2024, 2025])]
        by_area = prov.groupby("Province / City")["Underemployment Rate (%)"].mean()
        self.stdout.write("Check against the dashboard:")
        self.stdout.write(
            f"  Quarterly 2005–2026: underemployment {quarterly['Underemployment Rate (%)'].mean():.2f}% "
            f"/ unemployment {quarterly['Unemployment Rate (%)'].mean():.2f}%  (expect 17.56 / 6.55)")
        self.stdout.write(
            f"  Monthly 2021–2026:   underemployment {monthly['Underemployment Rate (%)'].mean():.2f}% "
            f"/ unemployment {monthly['Unemployment Rate (%)'].mean():.2f}%  (expect 13.24 / 5.11)")
        self.stdout.write(
            "  Sector rates: " + ", ".join(f"{k} {v:.1f}%" for k, v in sec.items())
            + "  (expect Agriculture 18.9, Industry 12.7, Services 10.6)")
        self.stdout.write(
            f"  Province range: {by_area.max():.1f}% / {by_area.min():.1f}% = "
            f"{by_area.max() / by_area.min():.1f}x  (expect about 24.8x)")

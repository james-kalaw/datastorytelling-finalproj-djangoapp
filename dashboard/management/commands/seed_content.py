"""
Fills the database with the website text: the 4 Power BI pages, their insights,
and the 6 recommendations. Safe to run again: it updates instead of duplicating
(insights are matched by page and order, and keep their full text and uploaded image).

    python manage.py seed_content
"""

from django.core.management.base import BaseCommand

from dashboard.models import Insight, PowerBIPage, Recommendation

PAGES = [
    {
        "slug": "trends",
        "title": "Trends",
        "order": 1,
        "page_id": "29c29917e904611d106b",
        "act_label": "Act I · Trends · 2005–2026",
        "question": "How Has Underemployment Compared With Unemployment in the Philippines From "
        "2005 to 2026?",
        "intro": "Based on the PSA Labor Force Survey, underemployment has stayed far above "
        "unemployment for two decades. It has averaged 2.7 times unemployment since 2005 (17.6% "
        "vs 6.6%) and still runs 2.6 times higher since 2021 (13.2% vs 5.1%). Both rates fell, "
        "but underemployment never came down to unemployment's level: the persistent problem is "
        "not having enough work, not a lack of jobs.",
    },
    {
        "slug": "impact",
        "title": "Impact",
        "order": 2,
        "page_id": "2681df278bfa7be7d474",
        "act_label": "Act II · Impact · provinces, people, sectors",
        "question": "How Does Underemployment Vary Across Provinces, Sex, Age Groups and Sectors?",
        "intro": "According to PSA provincial and national labor statistics, national averages "
        "hide large extremes. Provinces range about 25 times apart, men are more underemployed "
        "than women at every age, and Agriculture's rate (18.9%) is nearly double Services' "
        "(10.6%). The burden is heaviest in farming and fishing areas, the same low-pay, seasonal "
        "work the Reality page examines.",
    },
    {
        "slug": "reality",
        "title": "Reality",
        "order": 3,
        "page_id": "eea96f35e38c3176fdde",
        "act_label": "Act III · Reality · hours, reasons, school, pay",
        "question": "How Are Working Hours, Education and Pay Related to Underemployment?",
        "intro": "Based on PSA data on working hours, reasons for short hours, education and pay, "
        "studying more mostly helps, but the work itself is the bigger problem. Most "
        "underemployed people want more hours, and the main reason they work short weeks is "
        "variable working time set by the job. Completing college, junior high or elementary "
        "lowers the rate, but even college graduates sit at 7.2%, and the lowest-paid sector has "
        "the highest underemployment rate.",
    },
    {
        "slug": "synthesis",
        "title": "Synthesis",
        "order": 4,
        "page_id": "2955c3076f0dc384c008",
        "act_label": "Synthesis · What the data asks of us",
        "question": "Underemployment hits hardest where pay is lowest and work is seasonal.",
        "intro": "Across all the PSA tables we analyzed, the same pattern holds: lowest pay, most "
        "seasonal work, highest risk. Finishing school helps, but it doesn't close the gap.",
    },
]

# One card per sub-question: Question / Results (chart + text) / Conclusion.
# Questions, conclusions and answers use the wording of the project proposal.
# full_text is only written when the card has none, so edits made in the admin panel stay.
INSIGHTS = {
    "trends": [
        {
            "label": "Sub-Question 1 · The Headline Gap",
            "question": "How Has the Gap Between Underemployment and Unemployment Changed From "
            "2005 to 2026?",
            "summary": "According to the PSA Labor Force Survey, underemployment averaged 17.6% vs "
            "6.6% for unemployment from 2005 to 2026 (quarterly months), and 13.2% vs 5.1% from "
            "2021 (monthly rounds).",
            "chart_file": "charts/insights/sq1.png",
            "image_alt": "Line chart of the underemployment and unemployment rates, 2005 to 2026. "
            "Underemployment stays above unemployment throughout; they come closest in April "
            "2020 (18.9% vs 17.6%).",
            "caption": "Both Rates Fell, but the Gap Never Closed",
            "answer": "Co-movement with a persistent, narrowing gap. The two rates rise and fall "
            "together, but the gap never closed. The closest they came was April 2020, when COVID "
            "pushed unemployment to 17.6%, almost level with underemployment at 18.9%. Since 2021 "
            "the ratio has never fallen below 1.6.",
            "full_text": "The two rates rise and fall together. The closest they came was April "
            "2020, when COVID pushed unemployment to 17.6%, almost level with underemployment at "
            "18.9%. Since 2021 the ratio has never dropped below 1.6. Men's underemployment runs "
            "about 3 times their unemployment (14.7% vs 4.9%); women's about 2 times (11.1% vs "
            "5.4%).",
        },
        {
            "label": "Sub-Question 2 · Seasonality",
            "question": "Does Underemployment Follow a Seasonal Pattern Across Survey Months?",
            "summary": "Based on the PSA monthly Labor Force Survey rounds since 2021, July (15.5%) "
            "and April (14.7%) peak, while December, May and June dip.",
            "chart_file": "charts/insights/sq2.png",
            "image_alt": "Bar chart of the average underemployment rate by survey month since "
            "2021. July (15.5%) and April (14.7%) are highest; December (11.6%) is lowest.",
            "caption": "July and April Run Highest in Both Views",
            "answer": "Yes. There is a repeating rhythm, and the overall level has fallen in two "
            "clear steps: April stayed between 17.8% and 26.1% from 2005 to 2016, dropped after "
            "2017, and has stayed between 12.9% and 17.2% since 2021. Part of the monthly pattern "
            "may reflect the survey's larger quarterly rounds.",
            "full_text": "From 2005 to 2016, April stayed between 17.8% and 26.1%. From 2017 it "
            "fell to a lower level, jumped to 18.9% in the 2020 lockdown, and has stayed between "
            "12.9% and 17.2% since 2021. The lowest reading on record is 7.95% in December 2025. "
            "Part of the monthly pattern may reflect the survey's larger quarterly rounds.",
        },
    ],
    "impact": [
        {
            "label": "Sub-Question 3 · Geography",
            "question": "Which Provinces Have the Highest and Lowest Underemployment Rates "
            "(2023–2025)?",
            "summary": "According to the PSA Provincial Labor Market Statistics (2023–2025, with "
            "2025 preliminary), Sarangani has the highest average rate (49.3%) and Zamboanga City "
            "the lowest (2.0%), around a 12.3% provincial average.",
            "chart_file": "charts/insights/sq3.png",
            "image_alt": "Bar chart of the five highest and five lowest areas, 2023 to 2025. "
            "Sarangani is highest at 49.3% and Zamboanga City lowest at 2.0%, around a 12.3% "
            "average.",
            "caption": "A 25× Gap Between Provinces",
            "answer": "Across 118 provinces and highly urbanized cities (2023–2025, 2025 "
            "preliminary), the average rate is 12.3%, but the highest is about 25 times the "
            "lowest: Sarangani (49.3%) vs Zamboanga City (2.0%). The highest rates cluster in "
            "SOCCSKSARGEN and Bicol; most of the lowest are highly urbanized cities.",
            "full_text": "The highest rates cluster in SOCCSKSARGEN and Bicol, with Batangas also "
            "in the top five. Four of the five lowest are highly urbanized cities. Many high-rate "
            "areas depend on farming and fishing, though the provincial tables cannot prove the "
            "cause.",
        },
        {
            "label": "Sub-Question 4 · Age and Sex",
            "question": "How Do Underemployment Rates Differ by Sex and Age Group?",
            "summary": "Based on the PSA Labor Force Survey by sex and age group, men averaged "
            "14.7% underemployment vs 11.0% for women since 2021, with the widest gap at ages "
            "15–24.",
            "chart_file": "charts/insights/sq4.png",
            "image_alt": "Grouped bar chart of underemployment by age group for men and women "
            "since 2021. Men are higher in every age group: 14.7% vs 11.0% overall.",
            "caption": "Men Are Higher at Every Age",
            "answer": "The male–female gap holds in every age group and is widest among the young. "
            "Young workers, however, are not the most underemployed; their main problem is "
            "unemployment (12.3%), more than double any other age group.",
            "full_text": "The most underemployed ages are 35–54 (about 14.3%). Young people face a "
            "different problem: their unemployment rate is 12.3%, more than double any other age "
            "group.",
        },
        {
            "label": "Sub-Question 5 · Sectors",
            "question": "Which Sector Has the Highest Underemployment Rate, and Which Holds the "
            "Most Underemployed Workers?",
            "summary": "Based on PSA LFS Table 3 and employed persons by industry (June 2025–June "
            "2026), Agriculture's underemployment rate is 18.9%, Industry's 12.7% and Services' "
            "10.6%.",
            "chart_file": "charts/insights/sq5.png",
            "image_alt": "Two bar charts by sector. Left: underemployment rate, Agriculture 18.9%, "
            "Industry 12.7%, Services 10.6%. Right: share of all underemployed, Services 52.9%.",
            "caption": "Agriculture Has the Highest Rate; Services, the Most Workers",
            "answer": "Services holds the most underemployed workers (52.9%) only because it "
            "employs 62.7% of all workers, but Agriculture carries the highest risk per worker: "
            "about 1 in 5 farm and fishery workers is underemployed, against about 1 in 10 in "
            "Services.",
            "full_text": "Services holds 52.9% of the underemployed only because it employs 62.7% "
            "of all workers. About 1 in 5 farm and fishery workers is underemployed, against "
            "about 1 in 10 in Services.",
        },
    ],
    "reality": [
        {
            "label": "Sub-Question 6 · Hours and Reasons",
            "question": "What Share of Underemployment Is Visible, and Why Do Workers Have Short "
            "Hours?",
            "summary": "According to the PSA Labor Force Survey, 61% of the underemployed are "
            "visibly underemployed. Based on PSA LFS Table C, variable working time accounts for "
            "about two-thirds of the reasons for short weeks (68.8% of answers in June 2026).",
            "chart_file": "charts/insights/sq6.png",
            "image_alt": "Left: 61% of the underemployed are visible and 39% invisible. Right: "
            "top five reasons for short hours in June 2026, led by variable working time at "
            "68.8%.",
            "caption": "Most Want More Hours, and Jobs Set the Schedule",
            "answer": "About 61% of the underemployed want more hours (visible: working under 40 "
            "hours); 39% already work full hours but want more work (invisible). The visible "
            "share rises with age, from 54% at 25–34 to 78% at 65+, and variable working time is "
            "the top reason for short weeks.",
            "full_text": "The visible share rises with age, from 54% at 25–34 to 78% at 65+, and "
            "is higher for women (64%) than men (59%). The top three reasons rose from 79.15% of "
            "answers in June 2025 to 82.72% in June 2026.",
        },
        {
            "label": "Sub-Question 7 · Education",
            "question": "Does Completing a Higher Education Level Lower the Underemployment Rate "
            "(2023–2026)?",
            "summary": "Based on PSA data on employed and underemployed persons by highest grade "
            "completed (January 2023–June 2026), the rate falls from 16.7% for those with no "
            "grade to 7.2% for college graduates.",
            "chart_file": "charts/insights/sq7.png",
            "image_alt": "Bar chart of underemployment by highest grade completed, 2023 to 2026. "
            "College graduates are lowest at 7.2%; senior high graduates (11.7%) and "
            "undergraduates (11.8%) are almost equal.",
            "caption": "Finishing School Helps, Except Senior High",
            "answer": "Yes, mostly. The rate falls as schooling rises, and completing a level "
            "clearly lowers it for college, junior high and elementary. Senior high is the "
            "exception: graduates and undergraduates are nearly the same (11.7% vs 11.8%), and "
            "their monthly lines cross.",
            "full_text": "Completing college, junior high or elementary lowers the rate in almost "
            "every month. Senior high graduates and undergraduates are nearly the same (11.7% vs "
            "11.8%), and their lines cross.",
        },
        {
            "label": "Sub-Question 8 · Pay",
            "question": "Do Lower-Paying Sectors Have Higher Underemployment Rates?",
            "summary": "According to PSA average daily basic pay data, Agriculture pays the least "
            "(₱299/day) and has the highest underemployment rate (18.9%), while Services pays the "
            "most (₱695/day) and has the lowest (10.6%).",
            "chart_file": "charts/insights/sq8.png",
            "image_alt": "Two bar charts by sector. Average daily pay: Agriculture ₱299, Industry "
            "₱542, Services ₱695. Underemployment rate: Agriculture 18.9%, Industry 12.7%, "
            "Services 10.6%.",
            "caption": "Lowest Pay, Highest Risk",
            "answer": "Yes, at the sector level. Pay and underemployment move in opposite "
            "directions across the three sectors: Agriculture pays the least and has the highest "
            "rate, Services pays the most and has the lowest, and Industry sits in the middle on "
            "both. With only three sector rates, this is a pattern, not proof that low pay causes "
            "underemployment.",
            "full_text": "Industry sits in the middle on both (₱542/day, 12.7%). With only three "
            "sector rates, this is a pattern, not proof that low pay causes underemployment.",
        },
    ],
    "synthesis": [
        {
            "label": "01 · The Pattern",
            "summary": "Based on 21 years of PSA Labor Force Survey data, underemployment has run "
            "2.6–2.7 times above unemployment, narrowing but never closing.",
            "chart_file": "charts/insights/sq1.png",
            "image_alt": "Line chart of the underemployment and unemployment rates, 2005 to 2026. "
            "Underemployment stays above unemployment throughout.",
            "caption": "A Persistent, Uneven Gap",
            "answer": "According to the PSA tables we analyzed, men's underemployment runs about 3 "
            "times their unemployment and women's about 2 times, and provinces range about 25 "
            "times apart, from Sarangani (49.3%) to Zamboanga City (2.0%). The one exception was "
            "April 2020, when COVID pushed unemployment almost level with underemployment.",
            "full_text": "Men's underemployment runs about 3 times their unemployment, women's "
            "about 2 times, and provinces range about 25 times apart, from Sarangani (49.3%) to "
            "Zamboanga City (2.0%). The one exception was April 2020, when COVID pushed "
            "unemployment almost level with underemployment.",
        },
        {
            "label": "02 · The Cause",
            "summary": "According to PSA sector and pay data, Agriculture, the lowest-paid sector "
            "(₱299/day), has the highest rate (18.9%), while Services (₱695/day) has the lowest "
            "(10.6%).",
            "chart_file": "charts/insights/sq8.png",
            "image_alt": "Two bar charts by sector: Agriculture has the lowest average daily pay "
            "(₱299) and the highest underemployment rate (18.9%).",
            "caption": "It Follows the Season and the Paycheck",
            "answer": "Based on PSA LFS Table C, variable working time explains about two-thirds of "
            "short hours. According to PSA education data, schooling mostly helps, from 16.7% "
            "with no grade to 7.2% for college graduates, though finishing senior high barely "
            "changes the rate.",
            "full_text": "Variable working time explains about two-thirds of short hours. "
            "Schooling mostly helps, from 16.7% with no grade to 7.2% for college graduates, "
            "though finishing senior high barely changes the rate.",
        },
        {
            "label": "The Twist",
            "summary": "According to PSA data on employed persons by class of worker, 60.85% of "
            "employed Filipinos earn a wage or salary, yet about 1 in 8 workers still wants more "
            "work.",
            "caption": "60.85% of Employed Filipinos Are Wage-and-Salary Workers",
            "answer": "Based on these PSA figures, a regular job alone doesn't guarantee enough "
            "hours.",
            "full_text": "A job alone doesn't guarantee enough hours.",
        },
    ],
}

RECOMMENDATIONS = [
    (
        1,
        "Support Off-Season Income in Farming and Fishing Provinces",
        "According to the PSA, Agriculture has the highest underemployment rate (18.9%). Based on "
        "PSA provincial statistics, the worst-hit areas, Sarangani (49.3%), General Santos (37.9%) "
        "and Camarines Sur (34.7%), depend on farming and fishing.",
        "Time short-term work programs, such as DOLE's TUPAD emergency employment, to the lean "
        "months between planting and harvest, and pair them with crop and livelihood "
        "diversification.",
        "DOLE, Department of Agriculture, provincial LGUs",
        "SOCCSKSARGEN, Bicol",
        "impact",
    ),
    (
        2,
        "Make Working Hours More Predictable",
        "Based on PSA LFS Table C, variable working time is the top reason for short weeks in "
        "every month we studied: 68.8% of answers in June 2026.",
        "Encourage advance work schedules and minimum-hours arrangements for shift, contract and "
        "project-based work.",
        "DOLE, employers, industry groups",
        "Shift and project-based jobs",
        "reality",
    ),
    (
        3,
        "Help Students Finish College, Junior High and Elementary",
        "According to PSA data by highest grade completed, finishing these levels clearly lowers "
        "the rate: college graduates 7.2% vs undergraduates 10.5%; junior high completers 12.3% "
        "vs 15.2%.",
        "Expand retention support (scholarships, stipends, flexible schedules for working "
        "students) at the levels where finishing makes a measurable difference.",
        "DepEd, CHED, TESDA",
        "Students at risk of dropping out",
        "reality",
    ),
    (
        4,
        "Review How Senior High Prepares Students for Work",
        "Based on the same PSA education data, senior high graduates and undergraduates are "
        "almost equally underemployed (11.7% vs 11.8%), and their monthly lines cross.",
        "Strengthen work immersion and industry links in senior high tracks so the diploma "
        "carries more weight with employers.",
        "DepEd, partner employers",
        "Senior high tracks",
        "reality",
    ),
    (
        5,
        "Focus Youth Programs on Finding a First Job",
        "According to the PSA Labor Force Survey, young people's main problem is unemployment "
        "(12.3%), more than double any other age group, while their underemployment (11.9%) is "
        "below average.",
        "Link schools with Public Employment Service Offices (PESO) for job matching, "
        "internships and first-job placement.",
        "DOLE PESO, schools, LGUs",
        "Ages 15–24",
        "impact",
    ),
    (
        6,
        "Report Underemployment Next to Unemployment",
        "Based on 21 years of PSA Labor Force Survey data, underemployment has run 2.6–2.7 times "
        "higher than unemployment, yet headlines track only the smaller number.",
        "Publish both rates together, and add sector detail to provincial labor tables so local "
        "causes can be tested.",
        "PSA, media, researchers",
        "National and provincial reporting",
        "trends",
    ),
]


class Command(BaseCommand):
    help = "Creates or updates the Power BI pages, insights and recommendations."

    def handle(self, *args, **options):
        pages = {}
        for data in PAGES:
            slug = data["slug"]
            values = {k: v for k, v in data.items() if k != "slug"}
            page, _ = PowerBIPage.objects.update_or_create(slug=slug, defaults=values)
            pages[slug] = page
        self.stdout.write(f"Pages: {len(pages)}")

        count = 0
        for slug, items in INSIGHTS.items():
            for order, item in enumerate(items, start=1):
                # Matched by page and order; an uploaded result_image is never touched
                values = {k: v for k, v in item.items() if k != "full_text"}
                insight, _ = Insight.objects.update_or_create(
                    page=pages[slug], order=order, defaults=values
                )
                if not insight.full_text:
                    insight.full_text = item.get("full_text", "")
                    insight.save(update_fields=["full_text"])
                count += 1
        self.stdout.write(f"Insights: {count}")

        for number, title, evidence, action, who, focus, slug in RECOMMENDATIONS:
            Recommendation.objects.update_or_create(
                number=number,
                defaults={
                    "title": title,
                    "evidence": evidence,
                    "action": action,
                    "who": who,
                    "focus": focus,
                    "related_page": pages[slug],
                },
            )
        self.stdout.write(f"Recommendations: {len(RECOMMENDATIONS)}")
        self.stdout.write(self.style.SUCCESS("Website content is ready."))

"""
The Explore search. It is not an AI: it reads a typed question, drops filler words,
understands a few everyday words, and matches the rest against our data.
"""

import re

STOP_WORDS = {
    "what", "whats", "what's", "is", "are", "was", "the", "a", "an", "of", "in", "on", "for",
    "show", "me", "rate", "rates", "underemployment", "underemployed", "which", "who", "where",
    "how", "much", "many", "do", "does", "did", "and", "with", "by", "to", "list", "all",
    "data", "about", "please", "find", "give", "tell", "philippines", "ph", "percent",
    "number", "has", "have", "see", "compare", "vs", "versus", "between", "i", "want", "know",
    "get", "there", "their", "people", "workers", "worker", "aged", "years", "year", "yrs",
    "yo", "group", "groups", "level", "levels", "old",
}
HIGHEST_WORDS = {"highest", "top", "worst", "most", "biggest", "largest", "high", "higher",
                 "max", "maximum"}
LOWEST_WORDS = {"lowest", "least", "best", "smallest", "low", "lower", "bottom", "min",
                "minimum"}
CATEGORY_WORDS = {
    "Province": {"province", "provinces", "provincial", "city", "cities", "area", "areas",
                 "place", "places", "location", "locations"},
    "Sector": {"sector", "sectors"},
    "Industry pay": {"pay", "salary", "salaries", "wage", "wages", "income", "earnings", "earn",
                     "paid", "industry", "industries"},
    "Education": {"education", "school", "schooling", "diploma", "degree", "educational"},
    "Age and sex": {"age", "ages", "sex", "gender"},
    "Reason": {"reason", "reasons", "why", "cause", "causes"},
}
SYNONYMS = {
    "women": "female", "woman": "female", "girls": "female",
    "men": "male", "man": "male", "boys": "male",
    "youth": "15-24", "young": "15-24", "teens": "15-24", "teen": "15-24",
    "elderly": "65+", "older": "65+", "seniors": "65+",
    "farm": "agri", "farming": "agri", "farmers": "agri", "fishing": "fish",
    "factory": "manufactur", "factories": "manufactur", "metro": "ncr",
}

EXAMPLES = [
    "Which province has the highest rate?",
    "Lowest provinces",
    "Mindanao",
    "Women",
    "Youth",
    "Farm",
    "Highest salary",
    "College",
    "Why short hours",
]


def normalize(text):
    text = (text or "").lower().replace("–", "-").replace("—", "-")
    return re.sub(r"[?!.,]", " ", text)


def run_search(items, query, chosen_category="All"):
    """
    items: list of ExploreItem
    Returns (hits, read_as) where hits is the filtered, sorted list and read_as explains
    how the search was understood.
    """
    words = [w for w in normalize(query).split() if w]
    sort_direction = 0
    implied_category = None
    terms = []

    for word in words:
        if word in HIGHEST_WORDS:
            sort_direction = -1
            continue
        if word in LOWEST_WORDS:
            sort_direction = 1
            continue
        category_hit = next((c for c, ws in CATEGORY_WORDS.items() if word in ws), None)
        if category_hit:
            implied_category = category_hit
            continue
        if word in STOP_WORDS:
            continue
        terms.append(SYNONYMS.get(word, word))

    category = chosen_category if chosen_category != "All" else implied_category

    def matches(item):
        if category and item.category != category:
            return False
        haystack = normalize(f"{item.name} {item.category} {item.context} {item.keywords}")
        haystack_words = re.split(r"[\s,;/()]+", haystack)
        return all(any(w.startswith(t) for w in haystack_words) for t in terms)

    hits = [item for item in items if matches(item)]
    if sort_direction:
        hits.sort(key=lambda item: item.value, reverse=(sort_direction < 0))

    read_as = ""
    if words:
        parts = [f"{category.lower()} data" if category else "all data"]
        if terms:
            parts.append(f"matching “{' '.join(terms)}”")
        if sort_direction:
            parts.append("highest first" if sort_direction < 0 else "lowest first")
        read_as = "Searching " + " · ".join(parts)
    return hits, read_as

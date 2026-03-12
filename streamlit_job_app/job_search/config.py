from __future__ import annotations

from dataclasses import dataclass

DEFAULT_ROLE_QUERIES = [
    "data analyst",
    "junior data analyst",
    "product analyst",
    "junior product analyst",
    "business intelligence analyst",
    "decision scientist",
    "data scientist",
    "junior data scientist",
    "applied data scientist",
    "analytics engineer",
    "junior analytics engineer",
    "machine learning engineer",
    "junior machine learning engineer",
    "ml engineer",
    "junior ml engineer",
    "mlops engineer",
    "ai engineer",
    "junior ai engineer",
    "artificial intelligence engineer",
    "junior artificial intelligence engineer",
    "data science consultant",
    "junior data science consultant",
    "analytics consultant",
    "junior analytics consultant",
    "data and ai consultant",
    "junior data and ai consultant",
    "data science coach",
    "data analytics coach",
    "machine learning coach",
    "ai trainer",
    "technical trainer data",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

DEFAULT_LOCATION = "London Area, United Kingdom"
DEFAULT_GEO_ID = "90009496"
DEFAULT_DISTANCE_MILES = 50

# Keep these lists easy to edit when tuning filtering behavior.
NEGATIVE_VISA_PATTERNS = [
    r"no\s+(visa\s+)?sponsorship",
    r"no\s+need\s+for\s+(visa\s+)?sponsorship",
    r"does\s+not\s+need\s+(visa\s+)?sponsorship",
    r"no\s+need\s+for\s+sponsorship",
    r"no\s+sponsorship",
    r"cannot\s+sponsor",
    r"can\s*not\s+sponsor",
    r"unable\s+to\s+sponsor",
    r"do\s+not\s+sponsor",
    r"without\s+(visa\s+)?sponsorship",
    r"must\s+have\s+(the\s+)?right\s+to\s+work",
    r"must\s+already\s+have\s+(the\s+)?right\s+to\s+work",
    r"require\s+(the\s+)?right\s+to\s+work",
    r"sponsorship\s+is\s+not\s+available",
    r"cannot\s+provide\s+(a\s+)?(cos|certificate\s+of\s+sponsorship)",
    r"authori[sz]ed\s+to\s+work\s+in\s+(the\s+)?(uk|united\s+kingdom)",
    r"must\s+be\s+authori[sz]ed\s+to\s+work\s+in\s+(the\s+)?(uk|united\s+kingdom)",
]

POSITIVE_VISA_PATTERNS = [
    r"visa\s+sponsorship\s+available",
    r"skilled\s+worker\s+visa\s+sponsorship",
    r"can\s+sponsor",
    r"will\s+sponsor",
    r"sponsorship\s+provided",
    r"able\s+to\s+sponsor",
    r"offer\s+visa\s+sponsorship",
    r"eligible\s+for\s+visa\s+sponsorship",
    r"certificate\s+of\s+sponsorship",
    r"\bcos\b",
    r"licensed\s+sponsor",
]

SENIOR_KEYWORDS = [
    "senior ",
    "lead ",
    "principal ",
    "staff ",
    "head of",
    "director",
    "manager",
    "architect",
]

IRRELEVANT_TITLE_KEYWORDS = [
    "sales",
    "marketing",
    "recruiter",
    "project manager",
    "qa engineer",
]


@dataclass(slots=True)
class SearchOptions:
    keywords: str
    location: str = DEFAULT_LOCATION
    geo_id: str = DEFAULT_GEO_ID
    distance_miles: int = DEFAULT_DISTANCE_MILES
    exclude_explicit_no_visa: bool = True
    request_delay_seconds: float = 1.0
    max_retries_429: int = 2
    max_pages: int = 4

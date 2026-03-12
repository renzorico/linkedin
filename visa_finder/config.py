from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SearchConfig:
    job_titles: list[str] = field(
        default_factory=lambda: [
            # Core analytics/data roles
            "data analyst",
            "junior data analyst",
            "product analyst",
            "business intelligence analyst",
            "decision scientist",
            "data scientist",
            "junior data scientist",
            "applied data scientist",
            "analytics engineer",
            "junior analytics engineer",
            "junior product analyst",
            # ML/AI roles
            "machine learning engineer",
            "junior machine learning engineer",
            "ml engineer",
            "junior ml engineer",
            "mlops engineer",
            "ai engineer",
            "junior ai engineer",
            "artificial intelligence engineer",
            "junior artificial intelligence engineer",
            # Consulting / client-facing roles
            "data science consultant",
            "junior data science consultant",
            "analytics consultant",
            "junior analytics consultant",
            "data and ai consultant",
            "junior data and ai consultant",
            # Education / enablement roles
            "data science coach",
            "data analytics coach",
            "machine learning coach",
            "ai trainer",
            "technical trainer data",
        ]
    )
    london_geo_id: str = "90009496"
    work_types: str = "1,2,3"
    time_filter: str = "r2592000"
    distance: int = 50
    max_pages: int = 4
    output_csv: str = "visa_jobs_results.csv"
    output_html: str = "visa_jobs_results.html"
    output_json: str = "visa_jobs_results.json"
    output_web_json: str = "web/public/data/jobs.json"
    sponsorship_only: bool = False
    fetch_descriptions: bool = True
    request_delay_seconds: float = 1.2
    max_retries_429: int = 2


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

NEGATIVE_SPONSORSHIP_PATTERNS = [
    r"no\s+(visa\s+)?sponsorship",
    r"no\s+need\s+for\s+(visa\s+)?sponsorship",
    r"does\s+not\s+need\s+(visa\s+)?sponsorship",
    r"cannot\s+sponsor",
    r"can\s*not\s+sponsor",
    r"unable\s+to\s+sponsor",
    r"do\s+not\s+sponsor",
    r"without\s+(visa\s+)?sponsorship",
    r"must\s+have\s+(the\s+)?right\s+to\s+work",
    r"must\s+already\s+have\s+(the\s+)?right\s+to\s+work",
    r"require\s+(the\s+)?right\s+to\s+work",
    r"no\s+right\s+to\s+work\s+support",
    r"we\s+are\s+not\s+able\s+to\s+sponsor",
    r"not\s+offering\s+(visa\s+)?sponsorship",
    r"(this|the)\s+role\s+does\s+not\s+offer\s+sponsorship",
    r"sponsorship\s+is\s+not\s+available",
    r"cannot\s+provide\s+(a\s+)?(cos|certificate\s+of\s+sponsorship)",
    r"no\s+cos\s+available",
    r"uk\s+citizens?\s+only",
    r"authori[sz]ed\s+to\s+work\s+in\s+(the\s+)?(uk|united\s+kingdom)",
    r"must\s+be\s+authori[sz]ed\s+to\s+work\s+in\s+(the\s+)?(uk|united\s+kingdom)",
]

POSITIVE_SPONSORSHIP_PATTERNS = [
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
    r"sponsor\s+under\s+the\s+skilled\s+worker\s+route",
    r"skilled\s+worker\s+route\s+available",
    r"transfer\s+(of\s+)?(existing\s+)?skilled\s+worker\s+visa",
    r"we\s+sponsor\s+visas",
]

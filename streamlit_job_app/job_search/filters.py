from __future__ import annotations

import re
from difflib import SequenceMatcher

from .config import (
    IRRELEVANT_TITLE_KEYWORDS,
    NEGATIVE_VISA_PATTERNS,
    POSITIVE_VISA_PATTERNS,
    SENIOR_KEYWORDS,
)


def is_senior_position(job_title: str) -> bool:
    title = job_title.lower().strip()
    return any(keyword in title for keyword in SENIOR_KEYWORDS)


def is_title_relevant(job_title: str, keywords: str) -> tuple[bool, float]:
    title = job_title.lower().strip()
    query = keywords.lower().strip()

    if any(keyword in title for keyword in IRRELEVANT_TITLE_KEYWORDS):
        return False, 0.0

    if not query:
        return True, 0.0

    score = SequenceMatcher(None, title, query).ratio()
    token_overlap = any(token in title for token in query.split() if len(token) > 2)
    return token_overlap or score >= 0.35, score


def infer_visa_signal(text: str) -> tuple[str, str]:
    normalized = text.lower()

    for pattern in NEGATIVE_VISA_PATTERNS:
        match = re.search(pattern, normalized)
        if match:
            return "no", match.group(0)

    for pattern in POSITIVE_VISA_PATTERNS:
        match = re.search(pattern, normalized)
        if match:
            return "yes", match.group(0)

    return "unknown", ""


def extract_visa_snippet(text: str, evidence: str, window: int = 90) -> str:
    if not text:
        return ""
    if not evidence:
        return ""

    pos = text.lower().find(evidence.lower())
    if pos < 0:
        return evidence

    start = max(0, pos - window)
    end = min(len(text), pos + len(evidence) + window)
    snippet = text[start:end].strip()
    return re.sub(r"\s+", " ", snippet)


def is_remote_location(location: str) -> bool:
    return "remote" in (location or "").lower()


def is_hybrid_location(location: str) -> bool:
    return "hybrid" in (location or "").lower()


def classify_work_mode(location: str) -> str:
    if is_remote_location(location):
        return "Remote"
    if is_hybrid_location(location):
        return "Hybrid"
    return "On-site"


def is_allowed_location(location: str) -> bool:
    """Allow only London/nearby geo-filtered jobs, plus explicit remote/hybrid listings."""
    text = (location or "").lower()
    if not text:
        return False

    if "remote" in text or "hybrid" in text:
        return True

    # London and nearby areas typically appear with these tokens.
    if "london" in text:
        return True

    # Keep UK local matches captured through geoId + distance constraints.
    return "united kingdom" in text or "england" in text

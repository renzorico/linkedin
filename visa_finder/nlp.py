from __future__ import annotations

from difflib import SequenceMatcher


def similarity_score(s1: str, s2: str) -> float:
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def is_senior_position(job_title: str) -> bool:
    senior_keywords = [
        "senior ",
        "lead ",
        "principal ",
        "staff ",
        "head of",
        "director",
        "manager",
        "architect",
    ]
    title_lower = job_title.lower().strip()
    return any(kw in title_lower for kw in senior_keywords)


def is_relevant_job(job_title: str) -> tuple[bool, float]:
    core_keywords = {
        "data": ["data", "analytics", "bi", "insight"],
        "ml": ["machine learning", "ml ", "mlops"],
        "ai": ["artificial intelligence", "ai ", "genai", "llm"],
        "roles": [
            "engineer",
            "scientist",
            "analyst",
            "specialist",
            "consultant",
            "coach",
            "trainer",
            "educator",
            "mentor",
        ],
    }
    irrelevant_keywords = [
        "sales",
        "marketing",
        "recruiter",
        "project manager",
        "qa engineer",
    ]

    title = job_title.lower().strip()
    if any(kw in title for kw in irrelevant_keywords):
        return False, 0.0

    has_domain = False
    has_role = False
    scores: list[float] = []

    for group, kws in core_keywords.items():
        if group == "roles":
            has_role = any(kw in title for kw in kws)
        else:
            if any(kw in title for kw in kws):
                has_domain = True
                scores.extend(similarity_score(title, kw) for kw in kws)

    if not (has_domain and has_role):
        return False, 0.0

    return True, max(scores) if scores else 0.5

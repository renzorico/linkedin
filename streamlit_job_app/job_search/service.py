from __future__ import annotations

import time
from typing import Any

from bs4 import BeautifulSoup

from .config import DEFAULT_ROLE_QUERIES, SearchOptions
from .filters import (
    classify_work_mode,
    infer_visa_signal,
    is_allowed_location,
    is_senior_position,
    is_title_relevant,
)
from .linkedin import fetch_job_description, fetch_search_page, parse_job_card


def search_linkedin_jobs(
    location: str,
    exclude_explicit_no_visa: bool,
    max_results: int | None = None,
) -> list[dict[str, Any]]:
    """Search LinkedIn guest job listings and return normalized job rows for UI display.

    By default this runs across the full preset role list used in the previous tool.
    """
    query_list = list(dict.fromkeys(DEFAULT_ROLE_QUERIES))

    collected: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for query in query_list:
        options = SearchOptions(
            keywords=query,
            location=location,
            exclude_explicit_no_visa=exclude_explicit_no_visa,
        )

        for page in range(options.max_pages):
            html = fetch_search_page(options, start=page * 25)
            if not html:
                break

            soup = BeautifulSoup(html, "html.parser")
            cards = soup.find_all("li")
            if not cards:
                break

            for card in cards:
                parsed = parse_job_card(card)
                if not parsed:
                    continue
                if parsed["url"] in seen_urls:
                    continue
                if is_senior_position(parsed["title"]):
                    continue

                relevant, relevance_score = is_title_relevant(parsed["title"], options.keywords)
                if not relevant:
                    continue

                if not is_allowed_location(parsed["location"]):
                    continue

                description = fetch_job_description(parsed["url"])
                visa_signal, evidence = infer_visa_signal(description)
                if options.exclude_explicit_no_visa and visa_signal == "no":
                    continue

                row = {
                    "title": parsed["title"],
                    "company": parsed["company"],
                    "location": parsed["location"],
                    "work_mode": classify_work_mode(parsed["location"]),
                    "posted": parsed["posted"],
                    "relevance": round(relevance_score * 100, 1),
                    "search_query": query,
                    "visa_signal": visa_signal,
                    "job_link": parsed["url"],
                }
                collected.append(row)
                seen_urls.add(parsed["url"])

                if max_results is not None and len(collected) >= max_results:
                    break

                time.sleep(options.request_delay_seconds)

            if max_results is not None and len(collected) >= max_results:
                break

        if max_results is not None and len(collected) >= max_results:
            break

    collected.sort(key=lambda item: item.get("posted", ""), reverse=True)
    return collected

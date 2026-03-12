from __future__ import annotations

import re
import time
import urllib.parse
from typing import Any

import requests
from bs4 import BeautifulSoup

from .config import HEADERS, SearchConfig
from .nlp import is_relevant_job, is_senior_position
from .ui import console


def build_linkedin_url(config: SearchConfig, keywords: str, start: int = 0) -> str:
    params = {
        "keywords": f'"{keywords}"',
        "location": "London Area, United Kingdom",
        "geoId": config.london_geo_id,
        "distance": config.distance,
        "f_WT": config.work_types,
        "f_TPR": config.time_filter,
        "start": start,
        "sortBy": "DD",
    }
    base = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    return f"{base}?{urllib.parse.urlencode(params)}"


def parse_job_card(card: Any, search_title: str) -> dict[str, Any] | None:
    title_el = card.find("h3", class_=re.compile("base-search-card__title|job-search-card__title")) or card.find("h3")
    company_el = card.find("h4", class_=re.compile("base-search-card__subtitle|job-search-card__company")) or card.find("h4")
    location_el = card.find("span", class_=re.compile("job-search-card__location|base-search-card__location"))
    link_el = card.find("a", class_=re.compile("base-card__full-link|job-search-card__list-item"))
    if not link_el:
        link_el = card.find("a", href=re.compile("/jobs/view/"))
    date_el = card.find("time")

    if not (title_el and company_el):
        return None

    job_title = title_el.get_text(strip=True)
    if is_senior_position(job_title):
        return None

    relevant, relevance_score = is_relevant_job(job_title)
    if not relevant:
        return None

    return {
        "search_title": search_title,
        "job_title": job_title,
        "relevance_score": relevance_score,
        "company": company_el.get_text(strip=True),
        "location": location_el.get_text(strip=True) if location_el else "N/A",
        "posted": date_el.get("datetime", "N/A") if date_el else "N/A",
        "url": link_el.get("href", "").split("?")[0] if link_el else "N/A",
        "licensed_sponsor": False,
        "sponsorship_signal": "unknown",
        "sponsorship_evidence": "",
        "hiring_contact_name": "",
        "hiring_contact_title": "",
    }


def scrape_linkedin_jobs(config: SearchConfig, title: str) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    console.print(f"\n[bold yellow]Searching: '{title}'[/bold yellow]")

    for page in range(config.max_pages):
        start = page * 25
        url = build_linkedin_url(config, title, start=start)
        try:
            attempt = 0
            resp = None
            while attempt <= config.max_retries_429:
                resp = requests.get(url, headers=HEADERS, timeout=20)
                if resp.status_code != 429:
                    break
                backoff = config.request_delay_seconds * (attempt + 1)
                console.print(
                    f"  [yellow]HTTP 429 on page {page + 1}; retry {attempt + 1}/{config.max_retries_429 + 1} after {backoff:.1f}s[/yellow]"
                )
                time.sleep(backoff)
                attempt += 1

            if resp is None or resp.status_code != 200:
                status = resp.status_code if resp is not None else "N/A"
                console.print(f"  [red]HTTP {status} on page {page + 1}[/red]")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.find_all("li")
            if not cards:
                break

            page_jobs: list[dict[str, Any]] = []
            for card in cards:
                try:
                    parsed = parse_job_card(card, title)
                    if parsed:
                        page_jobs.append(parsed)
                except Exception:
                    continue

            jobs.extend(page_jobs)
            console.print(f"  [dim]Page {page + 1}: {len(page_jobs)} jobs (total: {len(jobs)})[/dim]")

            # Apply pacing between page requests to reduce rate limiting.
            time.sleep(config.request_delay_seconds)

            if len(page_jobs) < 25:
                break
        except requests.exceptions.RequestException as exc:
            console.print(f"  [red]Request error: {exc}[/red]")
            break

    return jobs


def generate_search_links(config: SearchConfig) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    base = "https://www.linkedin.com/jobs/search/"
    query_variants = ["", "visa sponsorship", "skilled worker visa"]

    for title in config.job_titles:
        for variant in query_variants:
            keywords = f"{title} {variant}".strip()
            params = {
                "keywords": keywords,
                "location": "London Area, United Kingdom",
                "geoId": config.london_geo_id,
                "distance": config.distance,
                "f_WT": config.work_types,
                "f_TPR": config.time_filter,
                "sortBy": "DD",
            }
            links.append(
                {
                    "title": title,
                    "keyword_variant": variant or "broad search",
                    "url": f"{base}?{urllib.parse.urlencode(params)}",
                }
            )
    return links

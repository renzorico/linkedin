from __future__ import annotations

import re
import time
import urllib.parse
from typing import Any

import requests
from bs4 import BeautifulSoup

from .config import HEADERS, SearchOptions


def build_search_url(options: SearchOptions, start: int = 0) -> str:
    params = {
        "keywords": f'"{options.keywords}"',
        "location": options.location,
        "geoId": options.geo_id,
        "distance": options.distance_miles,
        "f_WT": "1,2,3",
        "f_TPR": "r2592000",
        "start": start,
        "sortBy": "DD",
    }
    base = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    return f"{base}?{urllib.parse.urlencode(params)}"


def fetch_search_page(options: SearchOptions, start: int = 0) -> str:
    url = build_search_url(options, start=start)
    attempt = 0

    while attempt <= options.max_retries_429:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            return resp.text

        if resp.status_code == 429 and attempt < options.max_retries_429:
            backoff = options.request_delay_seconds * (attempt + 1)
            time.sleep(backoff)
            attempt += 1
            continue

        return ""

    return ""


def parse_job_card(card: Any) -> dict[str, str] | None:
    title_el = card.find("h3", class_=re.compile("base-search-card__title|job-search-card__title")) or card.find("h3")
    company_el = card.find("h4", class_=re.compile("base-search-card__subtitle|job-search-card__company")) or card.find("h4")
    location_el = card.find("span", class_=re.compile("job-search-card__location|base-search-card__location"))
    link_el = card.find("a", class_=re.compile("base-card__full-link|job-search-card__list-item"))
    if not link_el:
        link_el = card.find("a", href=re.compile("/jobs/view/"))
    date_el = card.find("time")

    if not (title_el and company_el and link_el):
        return None

    return {
        "title": title_el.get_text(strip=True),
        "company": company_el.get_text(strip=True),
        "location": location_el.get_text(strip=True) if location_el else "N/A",
        "posted": date_el.get("datetime", "N/A") if date_el else "N/A",
        "url": link_el.get("href", "").split("?")[0],
    }


def fetch_job_description(job_url: str) -> str:
    match = re.search(r"-(\d+)(?:$|\?)", job_url)
    candidate_text_parts: list[str] = []

    # Source 1: LinkedIn jobPosting API payload.
    if match:
        details_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{match.group(1)}"
        try:
            resp = requests.get(details_url, headers=HEADERS, timeout=20)
            if resp.status_code == 200:
                candidate_text_parts.append(extract_job_page_text(resp.text))
        except requests.RequestException:
            pass

    # Source 2: Public job page often includes "Requirements added by the job poster" text.
    try:
        resp = requests.get(job_url, headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            candidate_text_parts.append(extract_job_page_text(resp.text))
    except requests.RequestException:
        pass

    merged = " ".join(part for part in candidate_text_parts if part)
    return normalize_text(merged)


def normalize_text(raw_text: str) -> str:
    return re.sub(r"\s+", " ", raw_text).strip()


def extract_job_page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Prioritize sections where sponsorship eligibility often appears.
    selectors = [
        "div.show-more-less-html__markup",
        "ul.description__job-criteria-list",
        "section.description__job-criteria",
        "section.core-section-container",
        "main",
    ]

    chunks: list[str] = []
    for selector in selectors:
        for node in soup.select(selector):
            text = node.get_text(" ", strip=True)
            if text:
                chunks.append(text)

    if not chunks:
        chunks.append(soup.get_text(" ", strip=True))

    return normalize_text(" ".join(chunks))

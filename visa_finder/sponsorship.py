from __future__ import annotations

import io
import re
import time
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .config import HEADERS, NEGATIVE_SPONSORSHIP_PATTERNS, POSITIVE_SPONSORSHIP_PATTERNS, SearchConfig
from .ui import console


def fetch_sponsor_list() -> set[str]:
    console.print("\n[bold cyan]Fetching UK Home Office Licensed Sponsor Register...[/bold cyan]")
    gov_page = "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers"

    try:
        resp = requests.get(gov_page, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(resp.text, "html.parser")

        csv_url = None
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if "Sponsor" in href and href.endswith(".csv"):
                csv_url = href if href.startswith("http") else "https://www.gov.uk" + href
                break

        if not csv_url:
            api_url = "https://www.gov.uk/api/content/government/publications/register-of-licensed-sponsors-workers"
            api_resp = requests.get(api_url, timeout=30)
            data = api_resp.json()
            for attachment in data.get("details", {}).get("attachments", []):
                url = attachment.get("url", "")
                if url.endswith(".csv"):
                    csv_url = url
                    break

        if not csv_url:
            console.print("[yellow]Could not find sponsor CSV. Company sponsor matching disabled.[/yellow]")
            return set()

        csv_resp = requests.get(csv_url, headers=HEADERS, timeout=60)
        df = pd.read_csv(io.StringIO(csv_resp.text))
        name_col = [c for c in df.columns if "organisation" in c.lower() or "name" in c.lower()][0]
        sponsors = set(df[name_col].dropna().str.lower().str.strip())
        console.print(f"[green]Loaded {len(sponsors):,} licensed UK sponsors[/green]")
        return sponsors
    except Exception as exc:
        console.print(f"[red]Error fetching sponsor list: {exc}[/red]")
        return set()


def mark_licensed_sponsors(jobs: list[dict[str, Any]], sponsor_set: set[str]) -> None:
    if not sponsor_set:
        return

    for job in jobs:
        company_lower = job["company"].lower().strip()
        if company_lower in sponsor_set:
            job["licensed_sponsor"] = True
            continue
        for sponsor in sponsor_set:
            if len(company_lower) > 3 and (company_lower in sponsor or sponsor in company_lower):
                job["licensed_sponsor"] = True
                break


def extract_job_id(job_url: str) -> str | None:
    match = re.search(r"-(\d+)(?:$|\?)", job_url)
    return match.group(1) if match else None


def fetch_job_details(job_url: str) -> dict[str, str]:
    job_id = extract_job_id(job_url)
    if not job_id:
        return {"description": "", "hiring_contact_name": "", "hiring_contact_title": ""}

    details_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    try:
        resp = requests.get(details_url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            return {"description": "", "hiring_contact_name": "", "hiring_contact_title": ""}

        soup = BeautifulSoup(resp.text, "html.parser")

        description = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))

        # Best-effort extraction: LinkedIn guest markup is not stable, so use broad selectors.
        name = ""
        title = ""
        name_selectors = [
            ".hirer-card__hirer-information h3",
            ".hirer-card__hirer-information a",
            "[class*='hiring-team'] h3",
            "[class*='hirer'] h3",
        ]
        title_selectors = [
            ".hirer-card__hirer-information h4",
            ".hirer-card__hirer-information p",
            "[class*='hiring-team'] p",
            "[class*='hirer'] p",
        ]

        for selector in name_selectors:
            el = soup.select_one(selector)
            if el and el.get_text(strip=True):
                name = el.get_text(strip=True)
                break

        for selector in title_selectors:
            el = soup.select_one(selector)
            if el and el.get_text(strip=True):
                title = el.get_text(strip=True)
                break

        if not name:
            match = re.search(r"Meet\s+the\s+hiring\s+team\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", description)
            if match:
                name = match.group(1)

        return {
            "description": description,
            "hiring_contact_name": name,
            "hiring_contact_title": title,
        }
    except requests.exceptions.RequestException:
        return {"description": "", "hiring_contact_name": "", "hiring_contact_title": ""}


def infer_sponsorship_signal(text: str) -> tuple[str, str]:
    normalized = text.lower()

    for pattern in NEGATIVE_SPONSORSHIP_PATTERNS:
        match = re.search(pattern, normalized)
        if match:
            return "no", match.group(0)

    for pattern in POSITIVE_SPONSORSHIP_PATTERNS:
        match = re.search(pattern, normalized)
        if match:
            return "yes", match.group(0)

    return "unknown", ""


def annotate_sponsorship_signals(config: SearchConfig, jobs: list[dict[str, Any]]) -> None:
    if not config.fetch_descriptions:
        return

    console.print("\n[bold cyan]Analyzing sponsorship wording in job descriptions...[/bold cyan]")
    for idx, job in enumerate(jobs, start=1):
        details = fetch_job_details(job["url"])
        signal, evidence = infer_sponsorship_signal(details["description"])
        job["sponsorship_signal"] = signal
        job["sponsorship_evidence"] = evidence
        job["hiring_contact_name"] = details["hiring_contact_name"]
        job["hiring_contact_title"] = details["hiring_contact_title"]

        if idx % 20 == 0:
            console.print(f"  [dim]Checked {idx}/{len(jobs)} descriptions[/dim]")
        time.sleep(config.request_delay_seconds)


def apply_sponsorship_filter(config: SearchConfig, jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered = [job for job in jobs if job.get("sponsorship_signal") != "no"]
    removed = len(jobs) - len(filtered)
    if removed:
        console.print(f"[yellow]Removed {removed} jobs with explicit no-sponsorship wording[/yellow]")
    elif config.sponsorship_only:
        console.print("[yellow]Sponsorship-only mode active; no explicit no-sponsorship jobs found[/yellow]")
    return filtered

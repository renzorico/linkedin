from __future__ import annotations

import time
from typing import Any

from .config import SearchConfig
from .reporting import save_reports
from .scraper import generate_search_links, scrape_linkedin_jobs
from .sponsorship import (
    annotate_sponsorship_signals,
    apply_sponsorship_filter,
    fetch_sponsor_list,
    mark_licensed_sponsors,
)
from .ui import console


def run_pipeline(config: SearchConfig) -> None:
    console.print("[bold blue]=============================================[/bold blue]")
    console.print("[bold blue] UK Data/ML/AI Visa Job Finder (Modular) [/bold blue]")
    console.print("[bold blue]=============================================[/bold blue]")

    sponsor_set = fetch_sponsor_list()

    all_jobs: list[dict[str, Any]] = []
    for idx, title in enumerate(config.job_titles):
        all_jobs.extend(scrape_linkedin_jobs(config, title))
        if idx < len(config.job_titles) - 1:
            time.sleep(config.request_delay_seconds)

    console.print(f"\n[bold]Raw scraped jobs: {len(all_jobs)}[/bold]")
    mark_licensed_sponsors(all_jobs, sponsor_set)
    annotate_sponsorship_signals(config, all_jobs)
    filtered_jobs = apply_sponsorship_filter(config, all_jobs)
    search_links = generate_search_links(config)
    save_reports(config, filtered_jobs, search_links)

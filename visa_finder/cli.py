from __future__ import annotations

import argparse

from .config import SearchConfig
from .pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find UK data/ML/AI jobs with visa sponsorship signals")
    parser.add_argument(
        "--sponsorship-only",
        action="store_true",
        help="Keep jobs that are not explicitly no-sponsorship (drops explicit no-sponsorship jobs).",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=4,
        help="Max pages per title (25 jobs per page).",
    )
    parser.add_argument(
        "--no-descriptions",
        action="store_true",
        help="Skip fetching full job descriptions (faster, less sponsorship NLP signal).",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=1.2,
        help="Delay between LinkedIn requests to reduce HTTP 429 rate limiting.",
    )
    parser.add_argument(
        "--retry-429",
        type=int,
        default=2,
        help="Retries per page when LinkedIn returns HTTP 429.",
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> SearchConfig:
    return SearchConfig(
        sponsorship_only=args.sponsorship_only,
        max_pages=args.max_pages,
        fetch_descriptions=not args.no_descriptions,
        request_delay_seconds=max(0.1, args.sleep_seconds),
        max_retries_429=max(0, args.retry_429),
    )


def main() -> None:
    args = parse_args()
    config = build_config(args)
    run_pipeline(config)

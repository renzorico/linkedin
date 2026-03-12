from __future__ import annotations

from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st

from job_search import search_linkedin_jobs

LONDON_LOCATION = "London, England, United Kingdom"
ROW_OPTIONS = [10, 25, 50, 100, "All"]
NOISE_PATTERNS = (
    "trainee programmer",
    "realtor",
    "freelance ai trainer",
    "ai trainer",
)
NOISE_COMPANY_PATTERNS = (
    "10x.team",
    "prolific",
    "mindrift",
)


def init_state() -> None:
    defaults = {
        "jobs": [],
        "last_refresh": None,
        "clear_pending": False,
        "rows_to_show": 25,
        "title_keyword_filter": "",
        "search_query_filter": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def dedupe_jobs(rows: list[dict]) -> list[dict]:
    seen: set[str] = set()
    deduped: list[dict] = []
    for row in rows:
        url = str(row.get("job_link", "")).strip()
        if not url or url in seen:
            continue
        deduped.append(row)
        seen.add(url)
    return deduped


def is_noise_row(row: pd.Series) -> bool:
    title = str(row.get("title", "")).lower()
    company = str(row.get("company", "")).lower()
    if any(pattern in title for pattern in NOISE_PATTERNS):
        return True
    return any(pattern in company for pattern in NOISE_COMPANY_PATTERNS)


def build_link_url(url: str, title: str) -> str:
    encoded_title = quote(title, safe="")
    separator = "&" if "#" in url else "#"
    return f"{url}{separator}label={encoded_title}"


def style_visited_links() -> None:
        st.markdown(
            """
            <style>
            a[href*="linkedin.com/jobs/view"]:visited {
                color: #999999 !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )


st.set_page_config(page_title="London JobFinder", page_icon="💼", layout="wide")
init_state()

st.markdown("## London JobFinder")
st.caption(
    "Searches are always fixed to London, England, United Kingdom with a 50-mile radius, including remote and hybrid listings."
)
st.divider()

controls_expanded = st.expander("Search and quality controls", expanded=True)
with controls_expanded:
    control_col_1, control_col_2, control_col_3, control_col_4 = st.columns([1.2, 1, 1, 1.2])

    with control_col_1:
        sort_by = st.selectbox(
            "Sort results by",
            options=["date_desc", "date_asc", "relevance_desc", "company_asc"],
            index=0,
            format_func=lambda x: {
                "date_desc": "Date (newest first)",
                "date_asc": "Date (oldest first)",
                "relevance_desc": "Relevance",
                "company_asc": "Company (A-Z)",
            }[x],
        )
    with control_col_3:
        fetch_jobs = st.button("Fetch / Refresh jobs", type="primary", use_container_width=True)
    with control_col_4:
        clear_results = st.button("Clear current results", use_container_width=True)
        if st.session_state.last_refresh:
            st.markdown(
                f"<span style='font-size:0.85rem;padding:0.25rem 0.5rem;border:1px solid #e2e8f0;border-radius:999px;'>Last refreshed: {st.session_state.last_refresh}</span>",
                unsafe_allow_html=True,
            )

if clear_results:
    st.session_state.clear_pending = True

if st.session_state.clear_pending:
    st.warning("This will remove the current in-memory results. Are you sure?")
    confirm_col, cancel_col = st.columns(2)
    with confirm_col:
        if st.button("Yes, clear results", type="primary", use_container_width=True):
            st.session_state.jobs = []
            st.session_state.last_refresh = None
            st.session_state.clear_pending = False
            st.success("Current results were cleared.")
    with cancel_col:
        if st.button("Cancel", use_container_width=True):
            st.session_state.clear_pending = False

if fetch_jobs:
    today = datetime.now().strftime("%Y-%m-%d")
    last_refresh_date = st.session_state.last_refresh.split(" ")[0] if st.session_state.last_refresh else None

    if last_refresh_date == today and st.session_state.jobs:
        st.info("Results are from today. Displaying cached results.")
    else:
        with st.spinner("Searching jobs..."):
            jobs = search_linkedin_jobs(
                location=LONDON_LOCATION,
                exclude_explicit_no_visa=True,
            )

        st.session_state.jobs = dedupe_jobs(jobs)
        st.session_state.last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.divider()

jobs = dedupe_jobs(st.session_state.jobs)
st.session_state.jobs = jobs

if not jobs:
    st.info("Click Fetch / Refresh jobs to load London-area Data/ML/AI opportunities.")
else:
    table_df = pd.DataFrame(jobs).copy()
    table_df["posted_ts"] = pd.to_datetime(table_df["posted"], errors="coerce")

    filter_col_1, filter_col_2 = st.columns([1.5, 1.2])
    with filter_col_1:
        st.text_input("Title keyword", key="title_keyword_filter", placeholder="e.g. data scientist")
    with filter_col_2:
        search_query_options = sorted([item for item in table_df["search_query"].dropna().unique().tolist() if item])
        st.multiselect("Role category", options=search_query_options, key="search_query_filter")

    filtered_df = table_df.copy()

    title_filter = st.session_state.title_keyword_filter.strip().lower()
    if title_filter:
        filtered_df = filtered_df[filtered_df["title"].astype(str).str.lower().str.contains(title_filter, na=False)]

    if st.session_state.search_query_filter:
        filtered_df = filtered_df[filtered_df["search_query"].isin(st.session_state.search_query_filter)]

    filtered_df = filtered_df[~filtered_df.apply(is_noise_row, axis=1)]

    if sort_by == "date_desc":
        filtered_df = filtered_df.sort_values("posted_ts", ascending=False, na_position="last")
    elif sort_by == "date_asc":
        filtered_df = filtered_df.sort_values("posted_ts", ascending=True, na_position="last")
    elif sort_by == "relevance_desc":
        filtered_df = filtered_df.sort_values("relevance", ascending=False, na_position="last")
    elif sort_by == "company_asc":
        filtered_df = filtered_df.sort_values("company", ascending=True, na_position="last")

    link_df = filtered_df.copy()
    link_df["title"] = link_df["title"].astype(str)
    link_df["title_link"] = link_df.apply(
        lambda row: build_link_url(str(row["job_link"]), str(row["title"])),
        axis=1,
    )
    link_df["posted_display"] = link_df["posted_ts"].dt.date
    visible_limit = st.session_state.rows_to_show
    visible_df = link_df if visible_limit == "All" else link_df.head(int(visible_limit))

    table_top_left, table_top_right = st.columns([4, 1.2])
    with table_top_right:
        st.selectbox("Rows to display", options=ROW_OPTIONS, key="rows_to_show")

    st.dataframe(
        visible_df,
        hide_index=True,
        use_container_width=True,
        column_order=[
            "title_link",
            "company",
            "posted_display",
            "search_query",
            "relevance",
        ],
        column_config={
            "title_link": st.column_config.LinkColumn(
                "Title",
                help="Click to open the LinkedIn listing.",
                display_text=r"label=(.*)$",
                width="large",
            ),
            "company": st.column_config.TextColumn("Company", width="medium"),
            "posted_display": st.column_config.DateColumn("Posted", format="DD-MM", width="small"),
            "search_query": st.column_config.TextColumn("Search Query", width="medium"),
            "relevance": st.column_config.NumberColumn("Relevance", format="%.1f", width="small"),
        },
    )

    st.success(f"Showing {len(visible_df)} of {len(link_df)} matching jobs ({len(table_df)} fetched total).")

    style_visited_links()

    csv_bytes = filtered_df.drop(columns=["posted_ts"], errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download results as CSV",
        data=csv_bytes,
        file_name="linkedin_jobs_results.csv",
        mime="text/csv",
        type="primary",
    )

    export_dir = Path(__file__).parent / "data"
    export_dir.mkdir(exist_ok=True)
    export_path = export_dir / "latest_results.csv"
    filtered_df.drop(columns=["posted_ts"], errors="ignore").to_csv(export_path, index=False)
    st.caption(f"Auto-saved latest filtered results to {export_path}")

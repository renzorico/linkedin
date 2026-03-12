from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import pandas as pd
from rich import box
from rich.table import Table

from .config import SearchConfig
from .ui import console


def to_dataframe(jobs: list[dict[str, Any]]) -> pd.DataFrame:
    if not jobs:
        return pd.DataFrame()

    df = pd.DataFrame(jobs).drop_duplicates(subset=["url"])
    df["licensed_sponsor_sort"] = df["licensed_sponsor"].map({True: 0, False: 1})
    signal_rank = {"yes": 0, "unknown": 1, "no": 2}
    df["sponsorship_signal_sort"] = df["sponsorship_signal"].map(signal_rank).fillna(1)
    df = df.sort_values(
        ["licensed_sponsor_sort", "sponsorship_signal_sort", "relevance_score", "posted"],
        ascending=[True, True, False, False],
    )
    return df.drop(columns=["licensed_sponsor_sort", "sponsorship_signal_sort"])


def _build_html(config: SearchConfig, df: pd.DataFrame, search_links: list[dict[str, str]]) -> str:
    total = len(df)
    licensed_count = int(df["licensed_sponsor"].sum())
    explicit_no_count = int((df["sponsorship_signal"] == "no").sum())
    known_yes_count = int((df["sponsorship_signal"] == "yes").sum())
    unknown_count = int((df["sponsorship_signal"] == "unknown").sum())

    jobs_records: list[dict[str, Any]] = df[
        [
            "job_title",
            "company",
            "location",
            "posted",
            "search_title",
            "relevance_score",
            "sponsorship_signal",
            "sponsorship_evidence",
            "licensed_sponsor",
            "url",
        ]
    ].to_dict(orient="records")

    jobs_json = json.dumps(jobs_records)
    links_json = json.dumps(search_links)
    timestamp = datetime.now().strftime("%d %B %Y, %H:%M")

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>UK Data/ML/AI Visa Jobs | {timestamp}</title>
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
  <link href=\"https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&display=swap\" rel=\"stylesheet\">
  <style>
    :root {{
      --bg: #f3f5f8;
      --panel: #ffffff;
      --ink: #111827;
      --muted: #5b6473;
      --brand: #0a66c2;
      --line: #dbe2ea;
      --ok-bg: #e7f7ee;
      --ok-ink: #146c43;
      --warn-bg: #eef2f7;
      --warn-ink: #4b5563;
      --bad-bg: #fdecec;
      --bad-ink: #b42318;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Manrope", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 0% 0%, rgba(10, 102, 194, 0.12), transparent 34%),
        radial-gradient(circle at 100% 10%, rgba(33, 182, 168, 0.10), transparent 28%),
        var(--bg);
      min-height: 100vh;
    }}
    .wrap {{ max-width: 1200px; margin: 0 auto; padding: 20px 14px 42px; }}
    .hero {{
      background: linear-gradient(120deg, #0a66c2, #145bb3 55%, #0e7490);
      color: white;
      border-radius: 18px;
      padding: 24px;
      box-shadow: 0 12px 35px rgba(17, 24, 39, 0.18);
    }}
    .hero h1 {{ margin: 0; font-size: clamp(1.2rem, 2.3vw, 1.9rem); font-weight: 800; }}
    .hero p {{ margin: 8px 0 0; opacity: 0.95; }}

    .grid {{ display: grid; gap: 14px; margin-top: 16px; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); }}
    .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 16px; }}
    .kpi-value {{ font-size: 1.6rem; font-weight: 800; }}
    .kpi-label {{ color: var(--muted); font-size: 0.84rem; margin-top: 4px; }}

    .toolbar {{
      margin-top: 18px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 10px;
      align-items: end;
    }}
    .field label {{ display: block; font-size: 0.78rem; color: var(--muted); margin-bottom: 5px; }}
    .field input, .field select {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 8px 10px;
      font: inherit;
      background: #fff;
    }}
    .btn-row {{ display: flex; gap: 8px; }}
    button {{
      border: 0;
      border-radius: 10px;
      padding: 9px 12px;
      font-weight: 700;
      cursor: pointer;
      background: var(--brand);
      color: #fff;
    }}
    button.secondary {{ background: #64748b; }}

    .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 14px; margin-top: 14px; }}
    .panel h2 {{ margin: 0 0 10px; font-size: 1rem; }}
    .jobs-meta {{ display: flex; justify-content: space-between; gap: 10px; align-items: center; flex-wrap: wrap; }}
    .pagination {{ display: flex; gap: 8px; align-items: center; }}
    .pagination button {{ padding: 7px 10px; border-radius: 8px; background: #0f172a; }}
    .pagination button:disabled {{ opacity: 0.45; cursor: not-allowed; }}

    .table-wrap {{ overflow: auto; max-height: 640px; border: 1px solid var(--line); border-radius: 12px; width: 100%; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; min-width: 840px; }}
    th, td {{ border-bottom: 1px solid #edf1f5; text-align: left; padding: 9px 10px; vertical-align: top; }}
    th {{ background: #f8fbff; position: sticky; top: 0; z-index: 1; }}
    tr:hover td {{ background: #f8fcff; }}

    .pill {{ padding: 3px 8px; border-radius: 999px; font-size: 0.75rem; font-weight: 700; display: inline-block; }}
    .pill.ok {{ background: var(--ok-bg); color: var(--ok-ink); }}
    .pill.unknown {{ background: var(--warn-bg); color: var(--warn-ink); }}
    .pill.no {{ background: var(--bad-bg); color: var(--bad-ink); }}
    .pill.licensed {{ background: #e8f2ff; color: #0a4e9b; }}
    .muted {{ color: var(--muted); font-size: 0.85rem; }}
    .category-list {{ display: grid; gap: 8px; }}
    .category-item {{ display: flex; justify-content: space-between; border: 1px solid var(--line); border-radius: 10px; padding: 8px 10px; }}

    @media (max-width: 680px) {{
      .wrap {{ padding: 14px 10px 28px; }}
      .hero {{ border-radius: 14px; padding: 18px; }}
      .toolbar {{ grid-template-columns: 1fr; }}
      .grid {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
      table {{ min-width: 720px; }}
    }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"hero\">
      <h1>UK Data, ML & AI Job Dashboard</h1>
      <p>Generated on {timestamp}. Sponsorship-only mode: <strong>{config.sponsorship_only}</strong>.</p>
    </section>

    <section class=\"grid\">
      <div class=\"card\"><div class=\"kpi-value\">{total}</div><div class=\"kpi-label\">Total Jobs</div></div>
      <div class=\"card\"><div class=\"kpi-value\">{licensed_count}</div><div class=\"kpi-label\">Licensed Sponsors</div></div>
      <div class=\"card\"><div class=\"kpi-value\">{known_yes_count}</div><div class=\"kpi-label\">Mentions Sponsorship</div></div>
      <div class=\"card\"><div class=\"kpi-value\">{unknown_count}</div><div class=\"kpi-label\">No Sponsorship Statement</div></div>
      <div class=\"card\"><div class=\"kpi-value\">{explicit_no_count}</div><div class=\"kpi-label\">Explicit No Sponsorship</div></div>
    </section>

    <section class=\"toolbar\">
      <div class=\"field\"><label for=\"search\">Search</label><input id=\"search\" placeholder=\"Title, company, location\"></div>
      <div class=\"field\"><label for=\"categoryFilter\">Category</label><select id=\"categoryFilter\"><option value=\"all\">All</option></select></div>
      <div class=\"field\"><label for=\"sponsorshipFilter\">Sponsorship Wording</label><select id=\"sponsorshipFilter\"><option value=\"all\">All</option><option value=\"yes\">Mentions Sponsorship</option><option value=\"unknown\">No Statement</option><option value=\"no\">Explicitly No Sponsorship</option></select></div>
      <div class=\"field\"><label for=\"licensedFilter\">Licensed Sponsor</label><select id=\"licensedFilter\"><option value=\"all\">All</option><option value=\"yes\">Yes</option><option value=\"no\">No</option></select></div>
      <div class=\"field\"><label for=\"workModeFilter\">Work Mode</label><select id=\"workModeFilter\"><option value=\"all\">All</option><option value=\"remote\">Remote</option><option value=\"hybrid\">Hybrid</option><option value=\"onsite\">On-site/Unknown</option></select></div>
      <div class=\"field\"><label for=\"sortBy\">Sort By</label><select id=\"sortBy\"><option value=\"relevance_desc\">Relevance (High to Low)</option><option value=\"date_desc\">Date (Newest First)</option><option value=\"date_asc\">Date (Oldest First)</option><option value=\"company_asc\">Company (A-Z)</option></select></div>
      <div class=\"field\"><label for=\"pageSize\">Offers Shown</label><select id=\"pageSize\"><option value=\"10\" selected>10</option><option value=\"25\">25</option><option value=\"50\">50</option><option value=\"all\">All</option></select></div>
      <div class=\"btn-row\"><button id=\"resetBtn\" class=\"secondary\">Reset</button></div>
    </section>

    <section class=\"panel\">
      <h2>Jobs</h2>
      <div class=\"jobs-meta\">
        <div class=\"muted\" id=\"resultCount\">0 jobs shown</div>
        <div class=\"pagination\">
          <button id=\"prevPageBtn\" type=\"button\">Prev</button>
          <span class=\"muted\" id=\"pageInfo\">Page 1 / 1</span>
          <button id=\"nextPageBtn\" type=\"button\">Next</button>
        </div>
      </div>
      <div class=\"table-wrap\" style=\"margin-top:10px;\">
        <table>
          <thead>
            <tr>
              <th>Job</th><th>Company</th><th>Location</th><th>Posted</th><th>Category</th><th>Relevance</th><th>Sponsorship</th><th>Licensed</th>
            </tr>
          </thead>
          <tbody id=\"jobsBody\"></tbody>
        </table>
      </div>
    </section>

    <section class=\"panel\">
      <h2>Direct LinkedIn Search Links</h2>
      <div id=\"searchLinks\" class=\"category-list\"></div>
    </section>
  </div>

  <script>
    const JOBS = {jobs_json};
    const SEARCH_LINKS = {links_json};

    function normalizeWorkMode(location) {{
      const text = (location || "").toLowerCase();
      if (text.includes("remote")) return "remote";
      if (text.includes("hybrid")) return "hybrid";
      return "onsite";
    }}

    function fmtDate(d) {{
      if (!d || d === "N/A") return "N/A";
      const date = new Date(d);
      return Number.isNaN(date.getTime()) ? d : date.toISOString().slice(0, 10);
    }}

    function sponsorshipPill(signal, evidence) {{
      if (signal === "yes") return `<span class=\"pill ok\">Mentions sponsorship</span>`;
      if (signal === "no") return `<span class=\"pill no\" title=\"${{(evidence || '').replace(/\"/g, '&quot;')}}\">Explicitly no sponsorship</span>`;
      return `<span class=\"pill unknown\">No statement</span>`;
    }}

    function licensedPill(flag) {{
      return flag ? `<span class=\"pill licensed\">Licensed</span>` : `<span class=\"pill unknown\">Unconfirmed</span>`;
    }}

    const controls = {{
      search: document.getElementById("search"),
      categoryFilter: document.getElementById("categoryFilter"),
      sponsorshipFilter: document.getElementById("sponsorshipFilter"),
      licensedFilter: document.getElementById("licensedFilter"),
      workModeFilter: document.getElementById("workModeFilter"),
      sortBy: document.getElementById("sortBy"),
      pageSize: document.getElementById("pageSize"),
      resultCount: document.getElementById("resultCount"),
      pageInfo: document.getElementById("pageInfo"),
      jobsBody: document.getElementById("jobsBody"),
      prevPageBtn: document.getElementById("prevPageBtn"),
      nextPageBtn: document.getElementById("nextPageBtn"),
      resetBtn: document.getElementById("resetBtn"),
    }};

    let currentPage = 1;
    let currentFilteredRows = [];

    function getPageSizeValue() {{
      return controls.pageSize.value === "all" ? Number.POSITIVE_INFINITY : Number(controls.pageSize.value || 10);
    }}

    const categories = Array.from(new Set(JOBS.map(j => j.search_title))).sort();
    for (const category of categories) {{
      const opt = document.createElement("option");
      opt.value = category;
      opt.textContent = category;
      controls.categoryFilter.appendChild(opt);
    }}

    function applyFilters() {{
      const q = controls.search.value.toLowerCase().trim();
      const category = controls.categoryFilter.value;
      const sponsorship = controls.sponsorshipFilter.value;
      const licensed = controls.licensedFilter.value;
      const workMode = controls.workModeFilter.value;
      const sortBy = controls.sortBy.value;

      let rows = JOBS.filter((j) => {{
        const haystack = [j.job_title, j.company, j.location].join(" ").toLowerCase();
        if (q && !haystack.includes(q)) return false;
        if (category !== "all" && j.search_title !== category) return false;
        if (sponsorship !== "all" && j.sponsorship_signal !== sponsorship) return false;
        if (licensed !== "all" && String(j.licensed_sponsor) !== String(licensed === "yes")) return false;
        if (workMode !== "all" && normalizeWorkMode(j.location) !== workMode) return false;
        return true;
      }});

      rows.sort((a, b) => {{
        if (sortBy === "relevance_desc") return (b.relevance_score || 0) - (a.relevance_score || 0);
        if (sortBy === "date_desc") return new Date(b.posted || 0) - new Date(a.posted || 0);
        if (sortBy === "date_asc") return new Date(a.posted || 0) - new Date(b.posted || 0);
        if (sortBy === "company_asc") return String(a.company).localeCompare(String(b.company));
        return 0;
      }});

      currentFilteredRows = rows;
      const pageSize = getPageSizeValue();
      const totalPages = Number.isFinite(pageSize) ? Math.max(1, Math.ceil(rows.length / pageSize)) : 1;
      if (currentPage > totalPages) currentPage = totalPages;
      renderCurrentPage();
    }}

    function renderCurrentPage() {{
      const pageSize = getPageSizeValue();
      const totalRows = currentFilteredRows.length;
      const totalPages = Number.isFinite(pageSize) ? Math.max(1, Math.ceil(totalRows / pageSize)) : 1;

      if (currentPage < 1) currentPage = 1;
      if (currentPage > totalPages) currentPage = totalPages;

      const start = Number.isFinite(pageSize) ? (currentPage - 1) * pageSize : 0;
      const end = Number.isFinite(pageSize) ? Math.min(start + pageSize, totalRows) : totalRows;
      const pageRows = currentFilteredRows.slice(start, end);

      renderTable(pageRows);

      controls.prevPageBtn.disabled = currentPage <= 1;
      controls.nextPageBtn.disabled = currentPage >= totalPages;
      controls.pageInfo.textContent = `Page ${{currentPage}} / ${{totalPages}}`;
      if (totalRows === 0) {{
        controls.resultCount.textContent = "0 jobs matched";
      }} else {{
        controls.resultCount.textContent = Number.isFinite(pageSize)
          ? `${{totalRows}} jobs matched · showing ${{start + 1}}-${{end}}`
          : `${{totalRows}} jobs matched · showing all`;
      }}
    }}

    function renderTable(rows) {{
      controls.jobsBody.innerHTML = rows.map((j) => `
        <tr>
          <td><a href="${{j.url}}" target="_blank">${{j.job_title}}</a></td>
          <td>${{j.company}}</td>
          <td>${{j.location}}</td>
          <td>${{fmtDate(j.posted)}}</td>
          <td>${{j.search_title}}</td>
          <td>${{Math.round((j.relevance_score || 0) * 100)}}%</td>
          <td>${{sponsorshipPill(j.sponsorship_signal, j.sponsorship_evidence)}}</td>
          <td>${{licensedPill(j.licensed_sponsor)}}</td>
        </tr>
      `).join("");
    }}

    function renderSearchLinks() {{
      const box = document.getElementById("searchLinks");
      box.innerHTML = SEARCH_LINKS.slice(0, 40).map((item) =>
        `<div class=\"category-item\"><span><strong>${{item.title}}</strong> <span class=\"muted\">${{item.keyword_variant}}</span></span><a href=\"${{item.url}}\" target=\"_blank\">Open</a></div>`
      ).join("");
    }}

    for (const element of [
      controls.search,
      controls.categoryFilter,
      controls.sponsorshipFilter,
      controls.licensedFilter,
      controls.workModeFilter,
      controls.sortBy,
      controls.pageSize,
    ]) {{
      const onChange = () => {{
        currentPage = 1;
        applyFilters();
      }};
      element.addEventListener("input", onChange);
      element.addEventListener("change", onChange);
    }}

    controls.prevPageBtn.addEventListener("click", () => {{
      currentPage -= 1;
      renderCurrentPage();
    }});

    controls.nextPageBtn.addEventListener("click", () => {{
      currentPage += 1;
      renderCurrentPage();
    }});

    controls.resetBtn.addEventListener("click", () => {{
      controls.search.value = "";
      controls.categoryFilter.value = "all";
      controls.sponsorshipFilter.value = "all";
      controls.licensedFilter.value = "all";
      controls.workModeFilter.value = "all";
      controls.sortBy.value = "relevance_desc";
      controls.pageSize.value = "10";
      currentPage = 1;
      applyFilters();
    }});

    renderSearchLinks();
    applyFilters();
  </script>
</body>
</html>"""


def save_reports(config: SearchConfig, jobs: list[dict[str, Any]], search_links: list[dict[str, str]]) -> None:
    df = to_dataframe(jobs)
    if df.empty:
        console.print("[red]No jobs found. Try adjusting filters.[/red]")
        return

    df.to_csv(config.output_csv, index=False)
    console.print(f"[green]Saved {len(df)} jobs to {config.output_csv}[/green]")

    payload = {
      "generated_at": datetime.now().isoformat(timespec="seconds"),
      "sponsorship_only": config.sponsorship_only,
      "summary": {
        "total": int(len(df)),
        "licensed_sponsors": int(df["licensed_sponsor"].sum()),
        "mentions_sponsorship": int((df["sponsorship_signal"] == "yes").sum()),
        "unknown_sponsorship": int((df["sponsorship_signal"] == "unknown").sum()),
        "explicit_no_sponsorship": int((df["sponsorship_signal"] == "no").sum()),
      },
      "jobs": df.to_dict(orient="records"),
      "search_links": search_links,
    }

    with open(config.output_json, "w", encoding="utf-8") as file_obj:
      json.dump(payload, file_obj, ensure_ascii=True, indent=2)
    console.print(f"[green]Saved JSON report to {config.output_json}[/green]")

    web_dir = os.path.dirname(config.output_web_json)
    if web_dir:
      os.makedirs(web_dir, exist_ok=True)
      with open(config.output_web_json, "w", encoding="utf-8") as file_obj:
        json.dump(payload, file_obj, ensure_ascii=True, indent=2)
      console.print(f"[green]Updated web data at {config.output_web_json}[/green]")

    html = _build_html(config, df, search_links)
    with open(config.output_html, "w", encoding="utf-8") as file_obj:
        file_obj.write(html)
    console.print(f"[green]Saved HTML report to {config.output_html}[/green]")

    table = Table(title="UK Data/ML/AI Jobs", box=box.ROUNDED, show_lines=True, highlight=True)
    table.add_column("Job", max_width=36)
    table.add_column("Company", max_width=24)
    table.add_column("Signal", max_width=16)
    table.add_column("Licensed", justify="center", max_width=10)

    for _, row in df.head(40).iterrows():
        table.add_row(
            row["job_title"],
            row["company"],
            row["sponsorship_signal"],
            "yes" if row["licensed_sponsor"] else "no",
        )

    console.print("\n")
    console.print(table)

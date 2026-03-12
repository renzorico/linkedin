# Streamlit LinkedIn Job Finder

This is the streamlined Python + Streamlit version of the project.

## What this app does

- Searches across all configured role combinations in `job_search/config.py`.
- Enforces location constraints for:
- London area + 50-mile radius (via LinkedIn geo query)
- Remote roles
- Hybrid roles
- Always excludes jobs that explicitly refuse sponsorship.
- Deduplicates overlapping listings by job URL.
- Hides common irrelevant results with an in-app quality filter.
- Fetches matching jobs once, then applies title, work mode, role category, date, and row-count changes in memory.
- Tracks visited job links for the current session.

## Project structure

- `app.py`: Streamlit UI only
- `job_search/service.py`: orchestration (`search_linkedin_jobs`)
- `job_search/linkedin.py`: LinkedIn request + parsing helpers
- `job_search/filters.py`: title/visa/location filtering logic
- `job_search/config.py`: role combinations and filter patterns
- `requirements.txt`: dependencies

## Run locally

```bash
cd streamlit_job_app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## GitHub repository setup

From `streamlit_job_app/`:

```bash
git init
git add .
git commit -m "Initial Streamlit job finder"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

## Deploy on Streamlit Community Cloud

1. Push this folder to a GitHub repository.
2. Open Streamlit Community Cloud.
3. Create a new app from that repo.
4. Set entrypoint to `app.py`.
5. Deploy.

## Legacy code in parent workspace

The old CLI and web artifacts in the parent folder are kept for reference but are not required for this app:

- `visa_finder/`
- `visa_job_finder.py`
- `web/`
- `visa_jobs_results.*`

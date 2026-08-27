# data-engineering-lab

A portfolio lab of data engineering projects — pipelines, orchestration, and data
movement patterns — from simple ELT jobs to more complete orchestrated workflows.

## Projects

| # | Project | Description | Stack |
|---|---------|-------------|-------|
| 01 | [postgres-elt-pipeline](01-postgres-elt-pipeline/) | Dockerized ELT pipeline moving seed data from a source Postgres database into a destination Postgres database, transformed with dbt and orchestrated with Airflow | Python, PostgreSQL, dbt, Airflow, Docker Compose |
| 02 | [github-analytics-elt](02-github-analytics-elt/) | GitHub repository activity (PRs, issues, commits, reviews) ingested via Airbyte into BigQuery, transformed with dbt into PR merge metrics | Airbyte, BigQuery, dbt |

## How to navigate

Each sub-project lives in its own numbered folder (`0X-project-name/`) and is independent:

- `README.md` — what the project does, why it matters, and how it's built
- its own source tree and run instructions (Docker Compose, scripts, etc. depending on the project)

Projects are ordered by increasing complexity. Each has its own dependencies and can be
run in isolation — see the "How to run" section in each project's README.

## Branch history

Each project was built incrementally on its own feature branch, one per meaningful
chunk of work, merged into `main` via a pull request. Branch names spell out the full
technical stack behind that increment (not just the latest addition), so the branch
list alone tells the story of how each project evolved:

| Branch | What it added |
|---|---|
| `01-script-postgres-dbt` | dbt transformation layer on top of the hand-written `elt_script.py` / Postgres-to-Postgres pipeline |
| `01-script-postgres-dbt-airflow` | Airflow orchestration on top of the above |
| `02-airbyte-bigquery-dbt` | Project 02: GitHub → Airbyte → BigQuery → dbt |

Naming pattern: `<project-number>-<EL-tool>-<destination>-<transformation>[-<orchestrator>]`.

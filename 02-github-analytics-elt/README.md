# 02 — GitHub Analytics ELT

## What

GitHub repository activity (pull requests, issues, commits, reviews) ingested via
Airbyte into BigQuery, transformed with dbt into merge-time and review-time metrics,
orchestrated by a dedicated Airflow instance.

## Why

Where project 01 hand-writes the "EL" step (`elt_script.py`) between two Postgres
databases, this project deliberately uses **Airbyte** instead — a managed connector
that handles pagination, rate limits, and incremental sync state for a real external
API (GitHub), rather than reimplementing that plumbing by hand. The destination is
**BigQuery** (a columnar, serverless warehouse) instead of Postgres, to work with a
genuinely different storage model. dbt and Airflow play the same roles as in project 01
(transformation layer, orchestration), applied to this different stack.

## Architecture

```
 GitHub API
     │
     │ (Airbyte connector: commits, issues, pull_requests, reviews)
     ▼
 Airbyte (local, via abctl — runs in its own "kind" Kubernetes cluster)
     │
     │ incremental sync
     ▼
 BigQuery  (github-analytics-elt.github_analytics)
   raw tables: commits, issues, pull_requests, reviews
     │
     │ dbt (staging → marts)
     ▼
 BigQuery
   stg_commits, stg_issues, stg_pull_requests, stg_reviews   (views)
   pr_metrics, pr_review_metrics                              (tables)

 Airflow DAG "github_analytics_elt"  (airflow/dags/github_analytics_dag.py)
   sync_airbyte (PythonOperator, calls the Airbyte API directly)
        │
        ▼
   dbt_build (DockerOperator, runs `dbt build` in a locally-built dbt-bigquery image)
```

Airflow here is a **separate stack** from project 01's (own `docker-compose.yml`,
own metadata database, UI on port `8082` instead of `8080`) — the two projects stay
independent, at the cost of duplicating the Airflow boilerplate.

`sync_airbyte` doesn't use the official `apache-airflow-providers-airbyte` operator:
that provider sends a malformed OAuth token request against this Airbyte version's
auth endpoint. It's a plain `PythonOperator` that reproduces the same call sequence
(get an OAuth token, trigger the sync, poll until it finishes) that was first
verified by hand with `curl`.

`dbt_build` runs dbt in its own container rather than inside the Airflow image: the
official `dbt-labs/dbt-bigquery` image isn't published for `arm64` (Apple Silicon),
and installing `dbt-bigquery` directly alongside Airflow's own dependencies in one
image doesn't resolve (conflicting pins). `dbt.Dockerfile` builds a small, isolated,
native-arm64 image with just dbt in it.

## Data model

Raw tables landed by Airbyte in `github_analytics` (BigQuery dataset), one per
GitHub API stream, synced incrementally.

dbt models in `dbt_github_analytics/models/`:

| Model | What it does |
|---|---|
| `stg_commits`, `stg_issues`, `stg_pull_requests`, `stg_reviews` | Staging — renamed/typed passthrough of the raw tables. `stg_issues` filters out pull requests (GitHub's `/issues` endpoint returns both). `stg_pull_requests` deduplicates on `pr_id`, keeping the latest `_airbyte_extracted_at` (needed because the Airbyte connection syncs in "Incremental \| Append" mode, which doesn't dedupe on its own) |
| `pr_metrics` | Per pull request: `merge_duration_hours` and a `merge_speed` bucket (Fast/Medium/Slow/Not merged), via a `merge_speed` macro |
| `pr_review_metrics` | Per pull request: time to first review, joining `pull_requests` to the earliest matching row in `reviews` |

Tests: `unique`/`not_null`/`accepted_values` (schema tests) plus a singular test
asserting no PR has a negative merge duration.

## Stack

- Airbyte (self-hosted locally via `abctl`)
- BigQuery
- dbt-bigquery
- Apache Airflow 2.10.3 — dedicated instance, `sync_airbyte` (`PythonOperator`) → `dbt_build` (`DockerOperator`)
- Docker Compose

## How to run

Prerequisites: Airbyte running locally (`abctl local install`, see the root of this
lab for notes), a GCP project with BigQuery enabled, and a service account key saved
as `bigquery-sa-key.json` in this directory (gitignored — never commit it).

```bash
cd 02-github-analytics-elt
docker build -f dbt.Dockerfile -t dbt-bigquery-local:latest .
docker compose up --build -d
```

Open the Airflow UI at [localhost:8082](http://localhost:8082) (`airflow` / `password`).
In **Admin → Connections**, create `airbyte_default` (type `Airbyte`, host
`http://host.docker.internal:8000/api`, Client ID/Secret from `abctl local
credentials`, Token URL set to the *full* URL
`http://host.docker.internal:8000/api/v1/applications/token` — a known provider bug
drops the `/api` prefix otherwise). Then trigger the `github_analytics_elt` DAG.

Verify in BigQuery:

```sql
select * from `github-analytics-elt.github_analytics.pr_metrics`;
```

Tear down with `docker compose down -v`.

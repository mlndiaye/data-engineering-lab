# 01 — Postgres ELT Pipeline

## What

A containerized ELT pipeline: a Python script extracts and loads data between two
PostgreSQL databases, dbt transforms it in place with tested and documented models,
and Airflow orchestrates both steps on a schedule instead of a manual `docker compose up`.

## Why

Each layer demonstrates a distinct, deliberate skill rather than being bolted on for
its own sake:

- **`elt_script.py`** — the "EL" half of ELT written by hand: dump the source
  database and restore it into the destination, with a retry loop while Postgres
  comes up. Shows the raw mechanics before reaching for a framework.
- **dbt** — turns the raw, wholesale-copied tables into a set of named,
  tested, documented models with an explicit dependency graph (`ref()`/`source()`),
  instead of one-off SQL scripts.
- **Airflow** — replaces "run `docker compose up` and hope the ordering is right"
  with a real DAG: scheduled runs, retries, and a UI showing exactly what ran and
  when. It calls the same `elt_script.py` and the same dbt project — nothing was
  rewritten to fit Airflow, it just now owns *when* and *in what order* they run.

## Architecture

```
                        Airflow DAG "elt_and_dbt"  (airflow/dags/elt_dag.py)
                 ┌─────────────────────────────────────────────────────┐
                 │  run_elt_script  ─────────────▶  dbt_run             │
                 │  (PythonOperator)                (DockerOperator,    │
                 │                                   dbt-postgres image)│
                 └───────────┬───────────────────────────┬─────────────┘
                              │                              │
                              ▼                              ▼
                 ┌─────────────────┐  pg_dump/psql  ┌──────────────────────┐  dbt models  ┌───────────────────────┐
                 │ source_postgres  │ ─────────────▶ │ destination_postgres │ ───────────▶ │ destination_postgres   │
                 │  (source_db,     │                │  (destination_db,    │              │  (+ 6 dbt-built tables)│
                 │   seeded on boot)│                │   raw copy)          │              │                        │
                 └─────────────────┘                └──────────────────────┘              └───────────────────────┘

  Airflow control plane: postgres (metadata db) → init-airflow (one-shot: db migrate +
  admin user) → webserver + scheduler, which both wait on init-airflow completing
  before starting.
```

All services share a single `elt_network` Docker bridge network, addressed by their
Compose service names.

`elt_script.py` and dbt used to run as their own Compose services, ordered with
`depends_on`. Both now run as tasks inside the Airflow DAG instead, so those service
definitions were removed.

## Data model

Raw tables seeded into `source_postgres` via `source_db_init/init.sql`: `users`,
`films`, `actors`, `film_actors`, `film_category`.

dbt models in `custom_postgres/models/example/`:

| Model | What it does |
|---|---|
| `actors`, `film_actors`, `films` | Staging — passthrough `select * from {{ source(...) }}`, giving stable, testable names to build on |
| `film_ratings` | Joins films/film_actors/actors, aggregates actor names per film, buckets `user_rating` into a category |
| `film_classification` | Buckets each film's `user_rating` (Excellent/Good/Average/Poor) via the `classify_ratings` macro |
| `specific_movie` | Example of a parametrized, filtered model using a Jinja variable |

Every model has `unique`/`not_null` schema tests defined in `models/example/schema.yml`.

## Stack

- PostgreSQL 13 (source, destination, and Airflow's metadata db)
- Python (`elt_script.py`: `pg_dump`/`psql` wrapper)
- dbt-postgres 1.4.7 — 6 models, 2 macros, schema tests
- Apache Airflow 2.10.3 — webserver + scheduler + one-shot init job
- Docker Compose

## How to run

```bash
cd 01-postgres-elt-pipeline
docker compose up --build -d
```

Open the Airflow UI at [localhost:8080](http://localhost:8080) (`airflow` / `password`),
unpause the `elt_and_dbt` DAG, and trigger it.

Verify the transformed data landed in the destination:

```bash
docker compose exec destination_postgres psql -U postgres -d destination_db -c "select * from film_ratings limit 5;"
```

Tear down with `docker compose down -v` (drops the Postgres volumes, so the next run
starts from a clean source database).

# 01 — Postgres ELT Pipeline

## What

A minimal ELT (Extract, Load, Transform) pipeline between two PostgreSQL databases,
orchestrated with Docker Compose: a source database seeded with sample data (users,
films, categories, actors), a destination database, and a Python script that dumps
the source and restores it into the destination.

## Why

This demonstrates the "EL" half of ELT in its simplest form — moving data wholesale
from a source system into a destination before any transformation happens there —
along with the basic plumbing every data pipeline needs: waiting for dependent
services to become healthy, running inside its own container, and being wired
together declaratively via Compose rather than run by hand.

## Architecture

```
docker-compose up
       │
       ├── source_postgres (seeded via source_db_init/init.sql)
       ├── destination_postgres (empty)
       │
       └── elt_script (depends_on both)
                │
                ├── wait_for_postgres(source_postgres)  — polls pg_isready
                ├── pg_dump source_db  → data_dump.sql
                └── psql  → load data_dump.sql into destination_db
```

The three services communicate over a dedicated `elt_network` Docker bridge network,
addressed by their Compose service names (`source_postgres`, `destination_postgres`).

## Stack

- Python 3.8, `pg_dump`/`psql` (PostgreSQL client tools)
- PostgreSQL 13 (source and destination, via the official `postgres:13-alpine` image)
- Docker Compose

## How to run

```bash
cd 01-postgres-elt-pipeline
docker compose up --build
```

This starts both Postgres containers and runs the ELT script once. To verify the
data landed in the destination:

```bash
docker compose exec destination_postgres psql -U postgres -d destination_db -c "select * from users;"
```

Tear down with `docker compose down -v` (the `-v` also drops the Postgres volumes,
so the next run starts from a clean source database).

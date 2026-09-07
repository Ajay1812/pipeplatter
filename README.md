# Zomato Data Engineering Pipeline

An end-to-end data pipeline for Zomato order/restaurant/review data:
raw CSVs on S3 → Databricks (Unity Catalog) landing tables → dbt medallion
transformations (bronze/silver/gold) → orchestrated by Airflow.

```
S3 (raw CSVs)
   │  COPY INTO
   ▼
zomato.landing.*          (Databricks tables, ingested by Airflow)
   │  dbt: bronze
   ▼
zomato.bronze.*           (views — 1:1 with landing sources)
   │  dbt: silver
   ▼
zomato.silver.*           (views — typed, cleaned, deduped)
   │  dbt: gold
   ▼
zomato.gold.*              (tables — dims, facts, marts)
```

## Repo layout

```
.
├── zomato/                 # dbt project
│   ├── models/
│   │   ├── bronze/         # 1:1 views over landing sources
│   │   ├── silver/         # typed/cleaned views
│   │   └── gold/           # dims, facts, and marts (tables)
│   ├── macros/
│   ├── dbt_project.yml
│   └── ...
└── airflow/                 # local Airflow 3.x (Docker) that orchestrates ingestion + dbt
    ├── Dockerfile
    ├── docker-compose.yml
    ├── dags/
    │   └── zomato_dbt_pipeline.py
    ├── dbt_profiles/
    │   └── profiles.yml     # templated, reads Databricks creds from env
    ├── include/sql/landing/ # COPY INTO statements, one per source table
    └── .env.example
```

## Data model

**Sources** (`zomato.landing`, loaded from S3 via `COPY INTO`): `food`, `users`, `menu`,
`orders`, `order_items`, `reviews`, `restaurants`.

**Bronze** (`zomato.bronze`, views) — `br_*`: a thin `select *` passthrough over each
landing source, giving every downstream layer a stable dbt `ref()` instead of depending
on raw source tables directly.

**Silver** (`zomato.silver`, views) — `sl_*`: type casting (with `try_cast` so malformed
source rows become `NULL` instead of failing the whole model), column renames, and basic
cleaning/filtering.

**Gold** (`zomato.gold`, tables):
- Dimensions: `dim_customers`, `dim_restaurants`, `dim_food`, `dim_dates`
- Facts: `fct_orders`, `fct_order_items` (incremental)
- Marts: `mart_daily_city_revenue`, `mart_delivery_sla`, `mart_restaurant_performance`

Schema placement for every layer is controlled centrally in `zomato/dbt_project.yml`
(`+schema: bronze|silver|gold`), and `zomato/macros/generate_schema_name.sql` overrides
dbt's default `<target_schema>_<custom_schema>` naming so models land in exactly
`bronze`/`silver`/`gold` rather than e.g. `landing_bronze`.

## Prerequisites

- A Databricks workspace with:
  - A SQL warehouse (for dbt + the `COPY INTO` ingestion tasks)
  - A Unity Catalog **external location** with read access to the `s3://<bucket>/raw/...`
    paths used in `airflow/include/sql/landing/*.sql` (Airflow just submits the SQL —
    Databricks needs its own S3 access configured to actually read the files)
  - A personal access token
- Docker + Docker Compose (for running Airflow locally)
- [uv](https://docs.astral.sh/uv/) (for running dbt locally, outside Airflow)

## Running dbt locally (without Airflow)

1. Create `~/.dbt/profiles.yml`:
   ```yaml
   zomato:
     target: dev
     outputs:
       dev:
         type: databricks
         catalog: zomato
         schema: landing
         host: <your-workspace-host>
         http_path: /sql/1.0/warehouses/<warehouse-id>
         token: <your-databricks-token>
         threads: 4
   ```
2. From `zomato/`:
   ```bash
   uv run dbt run     # or: dbt build, dbt run -s bronze/silver/gold, dbt test
   ```

## Running the full pipeline via Airflow

```bash
cd airflow
cp .env.example .env     # fill in DATABRICKS_HOST / DATABRICKS_HTTP_PATH / DATABRICKS_TOKEN,
                          # S3_BUCKET, and generate an AIRFLOW_JWT_SECRET
docker compose build
docker compose up -d
```

Airflow UI: http://localhost:8080 (`admin` / `admin`)

Trigger the `zomato_dbt_pipeline` DAG. It runs, in order:

1. `copy_into_food`, `copy_into_users`, `copy_into_menu`, `copy_into_orders`,
   `copy_into_order_items`, `copy_into_reviews`, `copy_into_restaurants` — in parallel,
   each landing one S3 CSV into `zomato.landing.*` via `COPY INTO`
   (`airflow/include/sql/landing/*.sql`). Idempotent — `COPY INTO` tracks which files
   it already loaded and skips them on retry.
2. `dbt_deps`
3. `dbt_run_bronze` → `dbt_run_silver` → `dbt_run_gold`
4. `dbt_test`

### Configuration

All of this comes from `airflow/.env` (see `airflow/.env.example`):

| Variable | Purpose |
|---|---|
| `DATABRICKS_HOST` / `DATABRICKS_HTTP_PATH` / `DATABRICKS_TOKEN` | Databricks SQL warehouse connection, used by both dbt and the `DatabricksSqlOperator` ingestion tasks |
| `DATABRICKS_CATALOG` / `DATABRICKS_SCHEMA` | dbt's default catalog/schema (per-model schema is overridden in `dbt_project.yml`) |
| `S3_BUCKET` | Bucket the `COPY INTO` statements read raw CSVs from — templated into the SQL files via `{{ var.value.s3_bucket }}`, no hardcoded bucket name or manual file edits needed |
| `AIRFLOW_JWT_SECRET` | Signs Airflow 3's internal execution-API calls |

### Notes / gotchas

- **`COPY INTO` never deletes or replaces rows.** If you swap a source CSV for a smaller/
  different one at the same S3 path, the new rows get appended on top of what's already
  in the landing table — it does not "recreate" the table. If you need a full refresh
  semantics for a table, truncate it before the `COPY INTO` runs.
- dbt itself runs from its own isolated Python venv inside the Airflow image
  (`/opt/airflow/dbt_venv`), installed via `uv`, so its dependencies never conflict with
  Airflow's.
- Credentials are never committed — `airflow/dbt_profiles/profiles.yml` and the landing
  SQL files are templated (`env_var(...)` / `{{ var.value.s3_bucket }}`); real values only
  ever live in your local `airflow/.env` (gitignored).

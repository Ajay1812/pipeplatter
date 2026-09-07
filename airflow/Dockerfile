# Airflow 3.x image + Databricks provider + FAB auth (for admin/admin login) + dbt venv (installed via uv).
# Bump the tag to the newest 3.x if you like (e.g. 3.0.4 / 3.1.x).
FROM apache/airflow:3.0.3

USER root
# uv: fast, reproducible package/venv installs. Grab the static binary straight from its image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
USER airflow

# Providers: databricks (SQL/Jobs operators + connection), fab (classic username/password login).
RUN uv pip install --python "$(which python)" --no-cache-dir \
      apache-airflow-providers-databricks \
      apache-airflow-providers-fab

# dbt in its own venv so it never clashes with Airflow's deps. DAGs call /opt/airflow/dbt_venv/bin/dbt
RUN uv venv /opt/airflow/dbt_venv && \
    uv pip install --python /opt/airflow/dbt_venv/bin/python --no-cache-dir "dbt-databricks>=1.12.5"

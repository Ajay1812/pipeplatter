from datetime import datetime

from airflow.providers.databricks.operators.databricks_sql import DatabricksSqlOperator
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

DBT_BIN = "/opt/airflow/dbt_venv/bin/dbt"
AI_PYTHON = "/opt/airflow/ai_venv/bin/python"
DBT_PROJECT_DIR = "{{ var.value.get('dbt_project_dir', '/opt/airflow/dbt/pipeplatter') }}"
DBT_FLAGS = f"--project-dir {DBT_PROJECT_DIR} --profiles-dir /opt/airflow/dbt_profiles"

LANDING_TABLES = ["food", "users", "menu", "orders", "order_items", "reviews", "restaurants"]

with DAG(
    dag_id="pipeplatter_dbt_pipeline",
    description="Run the pipeplatter dbt project (bronze -> silver -> gold) on Databricks",
    start_date=datetime(2026, 1, 1),
    schedule='@daily',
    catchup=False,
    tags=["dbt", "databricks", "pipeplatter"],
    doc_md=__doc__,
    template_searchpath=["/opt/airflow/include/sql"],
) as dag:

    # Step 1: land the raw S3 CSVs into pipeplatter.landing.* via COPY INTO.
    # COPY INTO tracks which source files it already loaded, so re-running a task
    # only ingests new files - safe to retry.
    landing_tasks = [
        DatabricksSqlOperator(
            task_id=f"copy_into_{table}",
            databricks_conn_id="databricks_default",
            sql=f"landing/{table}.sql",
        )
        for table in LANDING_TABLES
    ]

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"{DBT_BIN} deps {DBT_FLAGS}",
    )

    landing_tasks >> dbt_deps

    dbt_bronze = BashOperator(
        task_id="dbt_run_bronze",
        bash_command=f"{DBT_BIN} run -s bronze {DBT_FLAGS}",
    )

    dbt_silver = BashOperator(
        task_id="dbt_run_silver",
        bash_command=f"{DBT_BIN} run -s silver {DBT_FLAGS}",
    )

    dbt_gold = BashOperator(
        task_id="dbt_run_gold",
        bash_command=f"{DBT_BIN} run -s gold {DBT_FLAGS}",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"{DBT_BIN} test {DBT_FLAGS}",
    )

    enrich_reviews_ai = BashOperator(
        task_id="enrich_reviews",
        bash_command=f"{AI_PYTHON} /opt/airflow/ai/enrich_reviews.py",
    )

    dbt_build_ai = BashOperator(
        task_id="dbt_build_ai",
        bash_command=f"{DBT_BIN} build --select tag:ai {DBT_FLAGS}",
    )

    dbt_deps >> dbt_bronze >> dbt_silver >> dbt_gold >> dbt_test >> enrich_reviews_ai >> dbt_build_ai

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="ecommerce_etl_pipeline",
    default_args=default_args,
    description="E-commerce cart ETL: PostgreSQL → Bronze → Silver → Gold (Azure Blob)",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["etl", "ecommerce"],
) as dag:

    bronze = BashOperator(
        task_id="bronze_extract",
        bash_command="python /opt/airflow/etl/spark/bronze.py",
    )

    silver = BashOperator(
        task_id="silver_transform",
        bash_command="python /opt/airflow/etl/spark/silver.py",
    )

    gold = BashOperator(
        task_id="gold_aggregate",
        bash_command="python /opt/airflow/etl/spark/gold.py",
    )

    bronze >> silver >> gold

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/project"

with DAG(
    dag_id="retail_control_tower",
    start_date=datetime(2026, 11, 1),
    schedule="0 6 * * *",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=5)},
) as dag:
    tasks = []
    for step in ["load_db", "run_queries", "forecast", "alerts"]:
        tasks.append(BashOperator(task_id=step,
                                  bash_command=f"cd {PROJECT_DIR} && python src/{step}.py"))
    for upstream, downstream in zip(tasks, tasks[1:]):
        upstream >> downstream
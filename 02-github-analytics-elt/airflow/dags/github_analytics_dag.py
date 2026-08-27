import time

import requests
from airflow import DAG
from airflow.hooks.base import BaseHook
from airflow.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.utils.dates import days_ago
from docker.types import Mount

CONNECTION_ID = "e5314dca-1d91-4b46-8fe0-b030715349dd"
PROJECT_ROOT_DIR = "/Users/mouhamadoulaminendiaye/workspace/labs/data-engineering-lab/02-github-analytics-elt"
DBT_PROJECT_DIR = f"{PROJECT_ROOT_DIR}/dbt_github_analytics"
DBT_PROFILES_DIR = "/Users/mouhamadoulaminendiaye/.dbt"


def trigger_airbyte_sync(**context):
    conn = BaseHook.get_connection("airbyte_default")
    base_url = conn.host.rstrip("/")
    client_id = conn.login
    client_secret = conn.password

    token_resp = requests.post(
        f"{base_url}/v1/applications/token",
        json={"client_id": client_id, "client_secret": client_secret},
        timeout=30,
    )
    token_resp.raise_for_status()
    token = token_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    job_resp = requests.post(
        f"{base_url}/public/v1/jobs",
        json={"connectionId": CONNECTION_ID, "jobType": "sync"},
        headers=headers,
        timeout=30,
    )
    job_resp.raise_for_status()
    job_id = job_resp.json()["jobId"]

    while True:
        time.sleep(5)
        status_resp = requests.get(
            f"{base_url}/public/v1/jobs/{job_id}",
            headers=headers,
            timeout=30,
        )
        status_resp.raise_for_status()
        status = status_resp.json()["status"]
        if status == "succeeded":
            return job_id
        if status in ("failed", "cancelled"):
            raise Exception(f"Airbyte sync job {job_id} ended with status {status}")


with DAG(
    dag_id="github_analytics_elt",
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
) as dag:

    sync_airbyte = PythonOperator(
        task_id="sync_airbyte",
        python_callable=trigger_airbyte_sync,
    )

    dbt_build = DockerOperator(
        task_id="dbt_build",
        image="dbt-bigquery-local:latest",
        command=f"build --project-dir {DBT_PROJECT_DIR} --profiles-dir /root",
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
        auto_remove="success",
        mount_tmp_dir=False,
        mounts=[
            Mount(source=PROJECT_ROOT_DIR, target=PROJECT_ROOT_DIR, type="bind"),
            Mount(source=DBT_PROFILES_DIR, target="/root", type="bind"),
        ],
    )

    sync_airbyte >> dbt_build

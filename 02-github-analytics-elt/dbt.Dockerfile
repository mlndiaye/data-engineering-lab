FROM python:3.12-slim
RUN pip install dbt-bigquery
ENTRYPOINT ["dbt"]

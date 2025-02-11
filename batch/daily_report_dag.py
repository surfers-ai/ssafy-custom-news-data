import pendulum
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.bash import BashOperator

local_tz = pendulum.timezone("Asia/Seoul")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='daily_report_dag',
    default_args=default_args,
    description='매일 새벽 2시에 Spark를 이용해 뉴스 리포트 생성',
    schedule_interval='0 0 3 * *',  # 한국 시간 기준 새벽 2시
    start_date=datetime(2025, 2, 10, tzinfo=local_tz),
    catchup=False,
    tags=['daily', 'report', 'spark'],
    timezone=local_tz,  # DAG의 타임존을 Asia/Seoul로 지정
) as dag:

    submit_spark_job = SparkSubmitOperator(
        task_id='spark_daily_report',
        application='spark_daily_report.py',
        conn_id='spark_default',
        verbose=True,
        conf={'spark.executor.memory': '2g'},
        application_args=["--date", "{{ ds }}"],
    )

    notify_report_generated = BashOperator(
        task_id='notify_report_generated',
        bash_command=(
            'echo "리포트가 생성되었습니다: '
            'report/daily_report_{{ ds_nodash }}.pdf"'
        )
    )

    submit_spark_job >> notify_report_generated

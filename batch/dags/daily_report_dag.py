import pendulum
from datetime import datetime, timedelta
from airflow import DAG
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
    description='매일 새벽 1시에 Spark를 이용해 뉴스 리포트 생성',
    schedule_interval='0 1 * * *',  # 한국 시간 기준 새벽 1시
    start_date=datetime(2025, 2, 10, tzinfo=local_tz),
    catchup=False,
    tags=['daily', 'report', 'spark']
) as dag:

    submit_spark_job = BashOperator(
        task_id='spark_daily_report',
        bash_command=(
            'echo "Spark 작업 시작" && '
            'python /home/jiwoochris/projects/ssafy-custom-news-data/batch/spark_daily_report.py --date {{ ds }} &&'
            'echo "Spark 작업 완료"'
        )
    )

    notify_report_generated = BashOperator(
        task_id='notify_report_generated',
        bash_command=(
            'echo "리포트가 생성되었습니다: '
            'report/daily_report_{{ ds_nodash }}.pdf"'
        )
    )

    submit_spark_job >> notify_report_generated

if __name__ == "__main__":
    dag.test()
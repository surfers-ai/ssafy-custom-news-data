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
    
    data_sync_job = BashOperator(
        task_id='hourly_data_sync',
        bash_command=(
            'echo "postgresql - es 싱크 시작" && '
            'poetry run python /home/honuuk/ssafy-custom-news-data/batch/posgresql_es_sync.py &&'
            'echo "postgresql - es 싱크 완료"'
        )
    )

    data_sync_job

if __name__ == "__main__":
    dag.test()
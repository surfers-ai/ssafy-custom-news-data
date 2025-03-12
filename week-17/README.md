# 17주차 관통 PJT: 배치처리 워크플로우 파이프라인 구축(Airflow + Spark)


> **목적: Airflow와 Spark 환경을 기반으로 워크플로우에 따른 분기를 나눌 수 있고, 배치 데이터를 처리할 수 있는 능력을 배양한다. 12주차에 배운 머신러닝 알고리즘(Embedding 개념)을 상기한다**
>
> 세부사항:
> - 트래픽이 적은 매일 새벽 1시마다 오늘의 기사, 트렌드, 키워드 분석 등 리포트 발행

## 목차
1. Poetry 라이브러리 설치
2. Spark job 실행 확인
3. Airflow로 배치

## 1. 필요한 라이브러리 설치

```bash
poetry add matplotlib pyspark
```

## 2. Spark job 실행결과 확인
```bash
poetry install
poetry shell

# report 생성할 날짜 입력
poetry run python batch/spark_daily_report.py --date 2025-03-06

# 출력확인
# 리포트가 {현재 파일경로}/report/daily_report_20250306.pdf 에 저장되었습니다.
```

<img width="1072" alt="image" src="https://github.com/user-attachments/assets/d825b1a2-e21e-4bbb-a1fe-34bb936aa31a" />

![image](https://github.com/user-attachments/assets/36696060-eebf-4bb6-94c0-16d1e7d2f961)

<img width="1170" alt="image" src="https://github.com/user-attachments/assets/f4979ea9-1e0f-4008-9e2a-ac126bf754db" />



## 2. Airflow로 배치

Airflow를 사용하여 배치 작업을 설정하는 방법입니다. 자세한 내용은 [Airflow 공식 문서](https://airflow.apache.org/docs/apache-airflow/stable/start.html)를 참고하세요.

### 2.1. Poetry 가상환경 활성화

   ```bash
   poetry shell
   ```

### 2.2. AIRFLOW_HOME 환경 변수 설정
   Airflow 작업 디렉토리를 설정합니다. \*실제 경로를 넣으셔야 합니다.

   ```bash
   echo 'export AIRFLOW_HOME=/home/jiwoochris/projects/ssafy-custom-news-data/batch' >> ~/.bashrc
   source ~/.bashrc
   ```

### 2.3. Airflow 설치

   아래 스크립트는 Airflow 버전 2.10.4를 poetry 환경에서 설치하는 예시입니다.

   ```bash
   AIRFLOW_VERSION=2.10.4

   # 현재 사용 중인 Python 버전 자동 추출 (지원되지 않는 버전을 사용 중이면 직접 설정)
   PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

   CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
   # 예: Python 3.8을 사용하는 경우 constraints URL 예: https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-3.8.txt

   poetry run pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
   ```


### 2.4. Airflow Spark Provider 설치

   Kafka 등과 연동하여 Spark 작업을 수행하기 위해 provider를 설치합니다.

   ```bash
   poetry run pip install apache-airflow-providers-apache-spark
   ```

### 2.5. Airflow 설정 파일 수정

   예제에 제공된 Airflow 설정 파일(batch/airflow.cfg)은 기본적은 2.2. 에서 설정한 AIRFLOW_HOME 환경변수를 참조합니다.
   설정파일에서 에러가 발생하면 {AIRFLOW_HOME} 대신 환경변수에 설정된 경로를 직접 넣어주세요.
   
   ```bash
   예시) sql_alchemy_conn = sqlite:////my/airflow/home/path/airflow.db
   ```

### 2.6. Airflow 실행

   screen을 생성하고 Airflow를 standalone 모드로 실행합니다.

   ```bash
   # screen 생성
   screen -S airflow

   # Airflow 실행
   poetry run airflow standalone

   # screen 세션 분리 (Ctrl+A, D)
   ```

### 2.7. DAG 확인

   Airflow 웹 UI에서 DAG를 확인할 수 있습니다.

   ```bash
   # 기본 접속 정보
   # URL: http://localhost:8080
   # Username: admin
   # Password: 터미널에 출력된 비밀번호 확인
   ```

비밀번호 정보 출력 예시

<img width="846" alt="image" src="https://github.com/user-attachments/assets/f1125832-87d4-442b-831c-b806e4045570" />

웹 UI에서 설정된 DAG 확인

<img width="1569" alt="image" src="https://github.com/user-attachments/assets/474858a4-4a0e-46b6-bb2b-5f190f791193" />

daily_report_dag가 정상적으로 등록되었는지 확인하고, 필요한 경우 활성화합니다.

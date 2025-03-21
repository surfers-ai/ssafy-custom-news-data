# SSAFY 맞춤형 뉴스 데이터 파이프라인 환경 설정 가이드 정리

이 가이드는 **PostgreSQL**, **Kafka**, **Python 라이브러리 관리 (Poetry)**, 그리고 **Airflow**를 이용하여 SSAFY 맞춤형 뉴스 데이터 파이프라인 환경을 단계별로 구축하는 방법을 설명합니다.

> **목차 (원본 README의 목차와 실제 내용의 순서를 모두 반영함)**
>
> 1. PostgreSQL 설치 및 설정
> 2. 필요한 라이브러리 설치
> 3. Kafka 설치 및 실행
> 4. Airflow로 배치

---

## 1. PostgreSQL 설치 및 설정

### 1.1. PostgreSQL 설치 (Linux - Ubuntu)

1. **PostgreSQL 설치**  
   터미널에서 아래 명령어를 실행하여 PostgreSQL과 추가 패키지를 설치합니다.

   ```bash
   sudo apt-get update
   sudo apt-get install postgresql postgresql-contrib
   ```

2. **서비스 상태 확인**  
   PostgreSQL 서비스가 정상 실행 중인지 확인합니다.

   ```bash
   sudo service postgresql status
   ```

### 1.2. PostgreSQL 데이터베이스 설정

1. **PostgreSQL 접속**  
   기본 사용자 `postgres`로 전환한 후 `psql` 셸에 접속합니다.

   ```bash
   sudo -i -u postgres
   psql
   ```

2. **데이터베이스 생성**  
   `news` 데이터베이스를 생성합니다.

   ```sql
   CREATE DATABASE news;
   ```

3. **사용자 생성 및 권한 부여**  
   SSAFY 전용 사용자 `ssafyuser`를 생성하고, `news` 데이터베이스에 대한 모든 권한을 부여합니다.

   ```sql
   CREATE USER ssafyuser WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE news TO ssafyuser;
   ```

4. **테이블 생성**

   1. **데이터베이스 변경**  
      생성한 `news` 데이터베이스로 접속합니다.

      ```bash
      \c news
      ```

   2. **pgvector 확장 설치 (최초 한 번 실행) 및 테이블 생성**  
      아래 SQL 명령어를 실행하여 `pgvector` 확장을 설치하고, `news_article` 테이블을 생성합니다.

      ```sql
      -- pgvector 확장이 필요한 경우 (최초 한 번만 실행)
      CREATE EXTENSION IF NOT EXISTS vector;

      -- news_article 테이블 생성
      CREATE TABLE news_article (
          id SERIAL PRIMARY KEY,
          title VARCHAR(200) NOT NULL,
          writer VARCHAR(255) NOT NULL,
          write_date TIMESTAMP NOT NULL,
          category VARCHAR(50) NOT NULL,
          content TEXT NOT NULL,
          url VARCHAR(200) UNIQUE NOT NULL,
          keywords JSON DEFAULT '[]'::json,
          embedding VECTOR(1536) NOT NULL
      );
      ```

   exit을 통해 터미널을 나올 수 있습니다.

---

## 2. 필요한 라이브러리 설치

프로젝트에서는 [Poetry](https://python-poetry.org/)를 이용하여 파이썬 라이브러리를 관리합니다.

1. **Poetry 설치 (필요한 경우)**

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **의존성 설치**

   ```bash
   poetry install
   ```

3. **가상환경 활성화**

   ```bash
   poetry shell
   ```

---

## 3. Kafka 설치 및 실행

Kafka는 Docker 컨테이너를 이용하여 실행합니다.

### 3.1. Docker 설치

Kafka 실행을 위해 Docker를 설치합니다.  
자세한 내용은 [Docker 설치 가이드 (Ubuntu)](https://docs.docker.com/engine/install/ubuntu/)를 참고하세요.

### 3.2. Kafka 실행

1. **Kafka 디렉토리로 이동**  
   터미널에서 Kafka 관련 파일이 위치한 디렉토리로 이동합니다.

   ```bash
   cd kafka-es
   ```

2. **Docker Compose를 이용해 Kafka 실행**

   ```bash
   sudo docker compose up -d
   ```

3. **Docker 컨테이너 상태 확인**

   ```bash
   sudo docker ps
   ```

### 3.3. Kafka 관련 Python 스크립트 실행

Kafka와 연동되는 파이썬 스크립트를 통해 데이터 파이프라인을 테스트할 수 있습니다.

- **Consumer 실행**  
  Kafka로부터 메시지를 소비하는 스크립트를 실행합니다.

  ```bash
  # Consumer를 위한 screen 생성 및 실행
  screen -S consumer
  python consumer/flink_kafka_consumer.py
  ```

  스크린을 detach하려면 `Ctrl+A+D`를 누르세요.

- **Producer 실행**  
  RSS 피드 데이터를 Kafka로 전송하는 스크립트를 실행합니다.

  ```bash
  # Producer를 위한 screen 생성 및 실행
  screen -S kafka-producer
  python producer/rss_kafka_producer.py
  ```

  스크린을 detach하려면 `Ctrl+A+D`를 누르세요.

### 3.4. Elasticsearch와 Kibana 설정

Elasticsearch와 Kibana는 Kafka와 함께 Docker Compose를 통해 실행됩니다.

1. **환경 변수 설정**  
   `.env` 파일에 Elasticsearch 접속 정보를 추가합니다:

   ```bash
   ES_URL=http://localhost:9200
   ```

2. **Elasticsearch 상태 확인**  
   Elasticsearch가 정상적으로 실행 중인지 확인합니다:

   ```bash
   curl http://localhost:9200
   ```

3. **Kibana 접속**  
   Kibana 대시보드에 접속하여 Elasticsearch 데이터를 시각화할 수 있습니다:

   ```
   http://localhost:5601
   ```

4. **문제 해결**  
   만약 연결 오류가 발생한다면:
   - Docker 컨테이너 상태 확인:
     ```bash
     docker ps | grep elasticsearch
     docker ps | grep kibana
     ```
   - 로그 확인:
     ```bash
     docker logs elasticsearch
     docker logs kibana
     ```
   - 컨테이너 재시작:
     ```bash
     docker restart elasticsearch kibana
     ```
   - 메모리 설정 확인: docker-compose.yml의 ES_JAVA_OPTS가 호스트 시스템의 가용 메모리에 적절한지 확인

---

## 4. Airflow로 배치

Airflow를 사용하여 배치 작업을 설정하는 방법입니다. 자세한 내용은 [Airflow 공식 문서](https://airflow.apache.org/docs/apache-airflow/stable/start.html)를 참고하세요.

1. **Poetry 가상환경 활성화**

   ```bash
   poetry shell
   ```

2. **AIRFLOW_HOME 환경 변수 설정**  
   Airflow 작업 디렉토리를 설정합니다. \*실제 경로를 넣으셔야 합니다.

   ```bash
   echo 'export AIRFLOW_HOME=/home/jiwoochris/projects/ssafy-custom-news-data/batch' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Airflow 설치**

   아래 스크립트는 Airflow 버전 2.10.4를 설치하는 예시입니다.

   ```bash
   AIRFLOW_VERSION=2.10.4

   # 현재 사용 중인 Python 버전 자동 추출 (지원되지 않는 버전을 사용 중이면 직접 설정)
   PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

   CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
   # 예: Python 3.8을 사용하는 경우 constraints URL 예: https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-3.8.txt

   pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
   ```

4. **Airflow Spark Provider 설치**

   Kafka 등과 연동하여 Spark 작업을 수행하기 위해 provider를 설치합니다.

   ```bash
   pip install apache-airflow-providers-apache-spark
   ```

5. **Airflow 설정 파일 수정**

   Airflow 설정 파일(batch/airflow.cfg)을 열어 dags_folder 경로를 수정합니다.

   ```bash
   dags_folder = /home/jiwoochris/projects/ssafy-custom-news-data/batch/dags
   ```

   batch/dags/daily_report_dag.py 파일에서 아래 부분을 찾아서 올바른 경로로 수정합니다.

   ```
   'python /home/jiwoochris/projects/ssafy-custom-news-data/batch/spark_daily_report.py --date {{ ds }} &&'
   ```

   수정 후 저장합니다.

6. **Airflow 실행**

   screen을 생성하고 Airflow를 standalone 모드로 실행합니다.

   ```bash
   # screen 생성
   screen -S airflow

   # Airflow 실행
   airflow standalone

   # screen 세션 분리 (Ctrl+A, D)
   ```

7. **DAG 확인**

   Airflow 웹 UI에서 DAG를 확인할 수 있습니다.

   ```bash
   # 기본 접속 정보
   # URL: http://localhost:8080
   # Username: admin
   # Password: 터미널에 출력된 비밀번호 확인
   ```

   daily_report_dag가 정상적으로 등록되었는지 확인하고, 필요한 경우 활성화합니다.

---

## 마무리

위의 단계들을 차례대로 진행하면 SSAFY 맞춤형 뉴스 데이터 파이프라인 환경이 PostgreSQL, Hadoop, Kafka, Python 라이브러리 관리 (Poetry), 그리고 Airflow를 이용해 성공적으로 구축됩니다.  
문제가 발생하거나 추가적인 도움이 필요하면 관련 문서를 참고하거나 담당자에게 문의하시기 바랍니다.

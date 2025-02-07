# SSAFY 맞춤형 뉴스 데이터 파이프라인 환경 설정 가이드

이 가이드는 **PostgreSQL**과 **Kafka**를 활용하여 SSAFY 맞춤형 뉴스 데이터 파이프라인 환경을 설정하는 방법을 단계별로 설명합니다.

## 목차

1. [PostgreSQL 설치 및 설정](#1-postgresql-설치-및-설정)
   - [1.1. PostgreSQL 설치 (Linux - Ubuntu)](#11-postgresql-설치-linux---ubuntu)
   - [1.2. PostgreSQL 데이터베이스 설정](#12-postgresql-데이터베이스-설정)
2. [필요한 라이브러리 설치](#2-필요한-라이브러리-설치)
3. [Kafka 설치 및 실행](#3-kafka-설치-및-실행)

---

## 1. PostgreSQL 설치 및 설정

### 1.1. PostgreSQL 설치 (Linux - Ubuntu)

1. **PostgreSQL 설치**  
   터미널에서 아래 명령어를 실행합니다.

   ```bash
   sudo apt-get update
   sudo apt-get install postgresql postgresql-contrib
   ```

2. **서비스 상태 확인**

   ```bash
   sudo service postgresql status
   ```

### 1.2. PostgreSQL 데이터베이스 설정

1. **PostgreSQL 접속**  
   PostgreSQL 기본 사용자인 `postgres`로 전환 후 `psql` 셸에 접속합니다.

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
   SSAFY 전용 사용자(`ssafyuser`)를 생성하고, `news` 데이터베이스에 대한 모든 권한을 부여합니다.

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
      아래 SQL 명령어를 통해 `pgvector` 확장을 설치하고, `news_article` 테이블을 생성합니다.

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

---

## 2. 필요한 라이브러리 설치

프로젝트에서는 [Poetry](https://python-poetry.org/)를 이용하여 파이썬 라이브러리를 관리합니다. 아래 명령어를 실행하여 필요한 라이브러리를 설치합니다.

```bash
poetry install
```

---

## 3. Kafka 설치 및 실행

### 3.1. Docker 설치

Kafka는 Docker 컨테이너로 실행됩니다. 우선 Docker를 설치합니다.

- [Docker 설치 가이드 (Ubuntu)](https://docs.docker.com/engine/install/ubuntu/)

### 3.2. Kafka 실행

1. **Kafka 디렉토리로 이동**  
   터미널에서 Kafka 관련 파일이 위치한 디렉토리로 이동합니다.

   ```bash
   cd kafka
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

Kafka와 연동되는 Python 스크립트를 통해 데이터 파이프라인을 테스트할 수 있습니다.

- **Consumer 실행**  
  Kafka로부터 메시지를 소비하는 스크립트를 실행합니다.

  ```bash
  python consumer/flink_kafka_consumer.py
  ```

- **Producer 실행**  
  RSS 피드 데이터를 Kafka로 전송하는 스크립트를 실행합니다.

  ```bash
  python producer/rss_kafka_producer.py
  ```

---

이제 위의 단계들을 차례대로 진행하면 SSAFY 맞춤형 뉴스 데이터 파이프라인 환경이 성공적으로 구축됩니다.  
문제가 발생하거나 추가적인 도움이 필요하면 관련 문서를 참고하거나 담당자에게 문의하시기 바랍니다.

# 14주차 관통 PJT: 실시간 데이터 수집 및 데이터베이스 연동(RSS + Postgresql)

> **목적: 실시간 데이터 적재하는 환경을 직접 구축한다**
>
> 세부사항:
> - 데이터는 뉴스 데이터를 사용한다
> - 뉴스 데이터라는 속성은 관통 PJT 전체에서 계속 유지가 되어야한다
> - 단, 어떤 뉴스 데이터라도 상관은 없다. 조선, 중앙, 한겨례, 혹은 플랫폼에서 데이터를 가져와도 무방하다
> - 14주차 PJT에서는 RSS를 활용해서 ‘라이브’ 데이터를 사용해야 한다.
> - DB는 Postgresql를 사용한다.
>

## 목차
1. PostgreSQL 설치 및 설정
2. Poetry 설치 및 설정
3. 필요한 라이브러리 설치
4. 코드 실행


## 1. PostgreSQL 설치 및 설정
### 1.1. PostgreSQL 설치 (Linux - Ubuntu)

1. **PostgreSQL 설치**  
   터미널에서 아래 명령어를 실행하여 PostgreSQL과 추가 패키지를 설치합니다.

   ```bash
   sudo apt-get update
   sudo apt-get install postgresql postgresql-contrib postgresql-17-pgvector
   ```
   
2. **PostgreSQL 설치**  
   PostgreSQL 서비스를 시작합니다.

   ```bash
   sudo systemctl start postgresql
   ```

3. **서비스 상태 확인**  
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
      CREATE TABLE mynews_article (
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

## 2. Poetry 설치 및 설정
프로젝트에서는 [Poetry](https://python-poetry.org/)를 이용하여 파이썬 라이브러리를 관리하고 코드를 실행합니다.

### 2.1. Poetry 설치 및 환경 세팅
Poetry 설치 후 아래 명령어를 실행하여 필요한 라이브러리를 설치합니다.

```bash
# Poetry 설치 (필요한 경우)
curl -sSL https://install.python-poetry.org | python3 -

# Poetry 프로젝트 초기화
poetry init -n

# 필요한 라이브러리 설치
poetry add dotenv psycopg2-binary requests feedparser bs4 openai tiktoken
```

### 2.2. Poetry로 코드실행
```bash
poetry run python rss_db.py
```
 

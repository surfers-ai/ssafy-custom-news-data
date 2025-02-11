# SSAFY 맞춤형 뉴스 데이터 파이프라인 환경 설정 가이드 정리

이 가이드는 **PostgreSQL**, **Hadoop**, **Kafka**, **Python 라이브러리 관리 (Poetry)**, 그리고 **Airflow**를 이용하여 SSAFY 맞춤형 뉴스 데이터 파이프라인 환경을 단계별로 구축하는 방법을 설명합니다.

> **목차 (원본 README의 목차와 실제 내용의 순서를 모두 반영함)**
>
> 1. PostgreSQL 설치 및 설정
> 2. Hadoop 설치 및 설정
> 3. 필요한 라이브러리 설치
> 4. Kafka 설치 및 실행
> 5. Airflow로 배치

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

---

## 2. Hadoop 설치 및 설정

Hadoop을 통해 HDFS (분산 파일 시스템)를 설정하여 데이터를 저장하고 관리할 수 있습니다.

### 2.1. Java 설치

Hadoop 실행에 필요한 Java를 설치합니다.

```bash
sudo apt-get update
sudo apt-get install default-jdk
```

### 2.2. Hadoop 다운로드 및 설치

1. Hadoop 3.4.0을 다운로드합니다.

   ```bash
   wget https://downloads.apache.org/hadoop/common/hadoop-3.4.0/hadoop-3.4.0.tar.gz
   ```

2. 다운로드한 tar.gz 파일을 압축 해제한 후, `/usr/local/hadoop` 디렉토리로 이동합니다.

   ```bash
   tar -xzvf hadoop-3.4.0.tar.gz
   sudo mv hadoop-3.4.0 /usr/local/hadoop
   ```

### 2.3. Hadoop 환경 변수 설정

사용자 홈 디렉토리의 `~/.bashrc` 파일에 아래 환경 변수를 추가합니다.

```bash
# Hadoop Setting
export HADOOP_HOME=/usr/local/hadoop
export PATH=$PATH:$HADOOP_HOME/bin
export PATH=$PATH:$HADOOP_HOME/sbin
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$PATH:$JAVA_HOME/bin
```

변경 사항을 적용합니다.

```bash
source ~/.bashrc
```

### 2.4. Hadoop 설정 파일 수정

#### (1) core-site.xml 설정

아래 명령어로 파일을 열어 수정합니다.

```bash
nano $HADOOP_HOME/etc/hadoop/core-site.xml
```

파일에 다음 내용을 입력합니다.

```xml
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
</configuration>
```

#### (2) hdfs-site.xml 설정

파일을 열어 아래 내용을 입력합니다.  
**주의:** `dfs.namenode.name.dir`와 `dfs.datanode.data.dir`의 경로에 있는 `사용자이름` 부분은 본인의 리눅스 사용자 이름으로 변경하세요.

```bash
nano $HADOOP_HOME/etc/hadoop/hdfs-site.xml
```

```xml
<configuration>
  <property>
    <name>dfs.replication</name>
    <value>1</value>
  </property>
  <property>
    <name>dfs.namenode.name.dir</name>
    <value>file:///home/사용자이름/hadoopdata/hdfs/namenode</value>
  </property>
  <property>
    <name>dfs.datanode.data.dir</name>
    <value>file:///home/사용자이름/hadoopdata/hdfs/datanode</value>
  </property>
</configuration>
```

### 2.5. SSH 설정

Hadoop 클러스터 환경에서 SSH가 필요하므로 SSH 서버를 설치합니다.

```bash
sudo apt-get install openssh-server
```

### 2.6. JAVA_HOME 설정 (Hadoop용)

Hadoop 환경 설정 파일을 열어 JAVA_HOME 경로를 지정합니다.

```bash
nano $HADOOP_HOME/etc/hadoop/hadoop-env.sh
```

파일 내에 아래 내용을 추가하거나 수정합니다.

```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64/
```

### 2.7. HDFS 데이터 디렉토리 생성

Hadoop이 데이터를 저장할 디렉토리를 생성합니다.

```bash
mkdir -p ~/hadoopdata/hdfs/namenode
mkdir -p ~/hadoopdata/hdfs/datanode
```

### 2.8. HDFS 포맷

이전 단계에서 생성한 이름노드 디렉토리를 포맷합니다.

```bash
hdfs namenode -format
```

### 2.9. HDFS 데몬 시작

HDFS 관련 데몬을 시작합니다.

```bash
start-dfs.sh
```

#### 2.9.1. 데몬 실행 확인

다음 명령어로 실행 중인 Java 프로세스를 확인하여 `NameNode`, `DataNode`, `SecondaryNameNode`가 실행 중인지 확인합니다.

```bash
jps
```

### 2.10. HDFS 사용해보기

#### 2.10.1. 디렉토리 생성

HDFS 내에 사용자 디렉토리를 생성합니다.

```bash
hdfs dfs -mkdir /user
hdfs dfs -mkdir /user/사용자이름
```

#### 2.10.2. 파일 목록 확인

생성한 디렉토리 내의 파일 목록을 확인합니다.

```bash
hdfs dfs -ls /user/사용자이름/
```

### 2.11. HDFS 데몬 종료

HDFS 데몬을 종료합니다.

```bash
stop-dfs.sh
```

---

## 3. 필요한 라이브러리 설치

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

## 4. Kafka 설치 및 실행

Kafka는 Docker 컨테이너를 이용하여 실행합니다.

### 4.1. Docker 설치

Kafka 실행을 위해 Docker를 설치합니다.  
자세한 내용은 [Docker 설치 가이드 (Ubuntu)](https://docs.docker.com/engine/install/ubuntu/)를 참고하세요.

### 4.2. Kafka 실행

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

### 4.3. Kafka 관련 Python 스크립트 실행

Kafka와 연동되는 파이썬 스크립트를 통해 데이터 파이프라인을 테스트할 수 있습니다.

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

## 5. Airflow로 배치

Airflow를 사용하여 배치 작업을 설정하는 방법입니다. 자세한 내용은 [Airflow 공식 문서](https://airflow.apache.org/docs/apache-airflow/stable/start.html)를 참고하세요.

1. **AIRFLOW_HOME 환경 변수 설정**  
   Airflow 작업 디렉토리를 설정합니다.

   ```bash
   export AIRFLOW_HOME=/home/jiwoochris/projects/ssafy-custom-news-data/batch
   ```

2. **Airflow 설치**

   아래 스크립트는 Airflow 버전 2.10.4를 설치하는 예시입니다.

   ```bash
   AIRFLOW_VERSION=2.10.4

   # 현재 사용 중인 Python 버전 자동 추출 (지원되지 않는 버전을 사용 중이면 직접 설정)
   PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

   CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
   # 예: Python 3.8을 사용하는 경우 constraints URL 예: https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-3.8.txt

   pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
   ```

3. **Airflow Spark Provider 설치**

   Kafka 등과 연동하여 Spark 작업을 수행하기 위해 provider를 설치합니다.

   ```bash
   pip install apache-airflow-providers-apache-spark
   ```

4. **Airflow 실행**

   Airflow를 standalone 모드로 실행합니다.

   ```bash
   airflow standalone
   ```

---

## 마무리

위의 단계들을 차례대로 진행하면 SSAFY 맞춤형 뉴스 데이터 파이프라인 환경이 PostgreSQL, Hadoop, Kafka, Python 라이브러리 관리 (Poetry), 그리고 Airflow를 이용해 성공적으로 구축됩니다.  
문제가 발생하거나 추가적인 도움이 필요하면 관련 문서를 참고하거나 담당자에게 문의하시기 바랍니다.

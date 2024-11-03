# SSAFY 맞춤형 뉴스 데이터 파이프라인 환경 설정 가이드

## 1. Hadoop 설치 및 설정

### 1.1 Java 설치

```bash
sudo apt-get update
sudo apt-get install default-jdk
```

### 1.2 Hadoop 다운로드 및 설치

```bash
wget https://downloads.apache.org/hadoop/common/hadoop-3.4.0/hadoop-3.4.0.tar.gz
tar -xzvf hadoop-3.4.0.tar.gz
sudo mv hadoop-3.4.0 /usr/local/hadoop
```

### 1.3 Hadoop 환경 변수 설정

~/.bashrc 파일에 추가:

```bash
# Hadoop Setting
export HADOOP_HOME=/usr/local/hadoop
export PATH=$PATH:$HADOOP_HOME/bin
export PATH=$PATH:$HADOOP_HOME/sbin
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$PATH:$JAVA_HOME/bin
```

변경사항 적용:

```bash
source ~/.bashrc
```

### 1.4 Hadoop 설정 파일 수정

#### core-site.xml 설정

```bash
nano $HADOOP_HOME/etc/hadoop/core-site.xml
```

```xml
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
</configuration>
```

#### hdfs-site.xml 설정

```bash
nano $HADOOP_HOME/etc/hadoop/hdfs-site.xml
```

- 사용자이름 부분에 본인의 리눅스 사용자 이름을 입력하세요.

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

### 1.5 SSH 설정

```bash
sudo apt-get install openssh-server
```

### 1.6 JAVA_HOME 설정

```bash
nano $HADOOP_HOME/etc/hadoop/hadoop-env.sh
```

```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64/
```

### 1.7 HDFS 데이터 디렉토리 생성

```bash
mkdir -p ~/hadoopdata/hdfs/namenode
mkdir -p ~/hadoopdata/hdfs/datanode
```

### 1.8 HDFS 포맷

```bash
hdfs namenode -format
```

### 1.9 HDFS 데몬 시작

```bash
start-dfs.sh
```

#### 1.9.1 데몬 실행 확인

```bash
jps
```

`NameNode`, `DataNode`, `SecondaryNameNode`가 실행 중인지 확인합니다.

### 1.10 HDFS 사용해보기

#### 1.10.1 디렉토리 생성

```bash
hdfs dfs -mkdir /user
hdfs dfs -mkdir /user/사용자이름
```

#### 1.10.2 파일 목록 확인

```bash
hdfs dfs -ls /user/사용자이름/
```

### 1.11 HDFS 데몬 종료

```bash
stop-dfs.sh
```

## 2. Spark 설치 및 설정

### 2.1 Spark 다운로드 및 설치

1. Apache Spark 공식 사이트에서 파일 다운로드
2. 압축 해제 및 설치:

```bash
tar xvzf spark-3.5.3-bin-hadoop3.tgz
sudo mv spark-3.5.3-bin-hadoop3 /usr/local/spark
```

### 2.2 Spark 환경 변수 설정

~/.bashrc 파일에 추가:

```bash
# Spark Setting
export SPARK_HOME=/usr/local/spark
export PATH=$PATH:$SPARK_HOME/bin
```

변경사항 적용:

```bash
source ~/.bashrc
```

## 3. 프로젝트 의존성 관리

Poetry를 사용하여 프로젝트 의존성을 관리합니다.

```bash
# Poetry 설치 (필요한 경우)
curl -sSL https://install.python-poetry.org | python3 -

# 의존성 설치
poetry install

# 가상환경 활성화
poetry shell
```

## 4. 실행 순서

### 4.1 Spark Streaming 서버 실행

# 뉴스 데이터 실시간 ETL 파이프라인

## 전체 데이터 흐름도

```
[Extract]                [Transform]                    [Load]
원본 데이터  →  HDFS  →  Spark Streaming 처리  →  REST API 엔드포인트
(JSON)      (임시저장)   (데이터 정제/가공)        (최종 적재)
                ↓
            아카이브
```

## 1. Extract (데이터 추출)

### crawling.py

- 현재는 기존 제공된 JSON 파일에서 데이터를 읽어오지만, 다음과 같은 다양한 방식으로 데이터 수집이 가능합니다:
  - 웹 크롤링을 통한 실시간 뉴스 수집
  - RSS 피드를 통한 뉴스 구독
  - 뉴스 API 활용 (예: 네이버/카카오 뉴스 API)
  - 외부 뉴스 데이터베이스 연동
  - 실시간 SNS 데이터 수집

#### 데이터 소스

```python
base_directory = 'training_raw_data'
hdfs_path = '/user/news/realtime/'
```

#### 추출 프로세스

1. HDFS 디렉토리 생성 및 권한 부여

```bash
hdfs dfs -mkdir -p /user/news/realtime
hdfs dfs -chmod -R 777 /user/news/realtime
```

2. JSON 파일 읽기

   - 카테고리별 디렉토리 순회
   - 각 카테고리당 최대 10개 파일 처리

3. HDFS 임시 저장
   - 1초 간격으로 데이터 전송
   - 파일명: `news_YYYYMMDD_HHMMSS.json`

## 2. Transform (데이터 변환)

### spark_streaming_server.py

#### 스키마 정의

```python
StructType([
    StructField("title", StringType()),        # 뉴스 제목
    StructField("source_site", StringType()),  # 출처
    StructField("write_date", StringType()),   # 작성일
    StructField("content", StringType()),      # 본문
    StructField("url", StringType())           # 링크
])
```

#### 변환 프로세스

1. **데이터 전처리**

```python
def preprocess_content(content):
    # 텍스트 길이 제한 (5000 토큰)
    # 토큰화 및 디코딩
```

2. **특성 추출**

   - 키워드 추출 (GPT-4)
   - 텍스트 임베딩 생성
   - 카테고리 자동 분류

3. **데이터 정제**
   - 필드명 변경 (source_site → writer)
   - 불필요 필드 제거
   - 누락 데이터 처리

## 3. Load (데이터 적재)

### spark_streaming_server.py

#### HDFS 디렉토리 생성

```bash
# 아카이브용 디렉토리 생성 및 권한 부여
hdfs dfs -mkdir -p /news_archive
hdfs dfs -chmod -R 777 /news_archive
```

#### 데이터베이스 적재

```python
# 전처리된 데이터를 서버 DB에 적재
# TARGET_ENDPOINT는 데이터를 적재할 REST API 엔드포인트를 나타냅니다.
# 주의: 해당 백엔드 서버가 실행 중인 상태여야 합니다.
TARGET_ENDPOINT = "http://localhost:8000/write-article/"
```

#### 적재 프로세스

1. 전처리된 데이터 JSON 변환
2. write-article API 호출하여 DB 저장
3. 원본 데이터는 HDFS의 /news_archive에 보관
4. 적재 상태 모니터링 및 로깅

## 주요 기능 및 특징

### 1. 데이터 저장 및 품질 관리

- 전처리 데이터는 서버 DB에, 원본은 HDFS에 저장
- API 요청/응답 검증 및 DB 적재 상태 모니터링
- 데이터 정합성 검증 및 누락 데이터 처리

### 2. 시스템 안정성

- REST API 기반 확장 가능한 아키텍처
- 체계적인 에러 처리 및 재시도 메커니즘
- 모듈화된 프로세스로 유지보수 용이

### 3. AI 처리 결과 관리

- 키워드 추출, 임베딩, 자동 분류 결과 저장
- AI 모델 결과의 DB 적재 및 품질 관리

## 구성 요소별 연결

```
[crawling.py] → HDFS(/user/news/realtime)
                      ↓
[spark_streaming_server.py] → 데이터 처리
                      ↓
                REST API 엔드포인트
                      ↓
              아카이브(/news_archive)
```

이 ETL 파이프라인은 뉴스 데이터를 실시간으로 추출(Extract), 변환(Transform), 적재(Load)하는 시스템으로, 데이터의 수집부터 최종 저장까지의 전체 과정을 자동화하여 처리합니다.

## ML 파이프라인 구성(archive 하는 이유)

### 1. 데이터 아카이브 활용

#### 저장 위치

- HDFS `/news_archive`

#### 데이터 특징

- 원본 뉴스 데이터
- GPT 기반 레이블링 데이터 (키워드, 카테고리)
- 임베딩 벡터

#### 용도

- 자체 ML 모델 학습을 위한 학습 데이터셋 구축

### 2. Batch 학습 파이프라인

#### 주기적 학습 수행

- 주기적으로 새로운 데이터 반영

#### 학습 대상 모델

1. 키워드 추출 모델

   - GPT 레이블링 데이터 기반
   - 도메인 특화 키워드 추출기 학습

2. 임베딩 모델

   - 뉴스 도메인 특화 임베딩 생성
   - 기존 임베딩 모델 파인튜닝

3. 카테고리 분류 모델
   - GPT 레이블링 기반 지도학습
   - 뉴스 특화 분류체계 적용

### 5. ETL과 ML 파이프라인 통합

```
[ETL 파이프라인]
데이터 수집 → 전처리 → 임시저장 → 변환 → 적재
     │           │                          │
     └→ [아카이브] ←─────────────────────┘
            │
[ML 파이프라인]
            │
     모델 학습 → 평가 → 배포 → 서빙
            ↑                    │
            └──── 피드백 ←──────┘
```

이러한 ML 파이프라인을 통해 초기 GPT 기반의 레이블링 데이터를 활용하여 자체 모델을 발전시키고, 지속적인 학습과 개선이 가능한 시스템을 구축할 수 있습니다.

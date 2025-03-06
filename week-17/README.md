# 17주차 관통 PJT: 배치처리 워크플로우 파이프라인 구축(Airflow + Spark)


> **목적: Airflow와 Spark 환경을 기반으로 워크플로우에 따른 분기를 나눌 수 있고, 배치 데이터를 처리할 수 있는 능력을 배양한다. 12주차에 배운 머신러닝 알고리즘(Embedding 개념)을 상기한다**
>
> 세부사항:
> - 트래픽이 적은 매일 새벽 1시마다 오늘의 기사, 트렌드, 키워드 분석 등 리포트 발행

## 목차
1. Hadoop 설치 및 설정
2. Poetry 라이브러리 설치
3. Airflow로 배치


## 1. Hadoop 설치 및 설정
Hadoop을 통해 HDFS (분산 파일 시스템)를 설정하여 데이터를 저장하고 관리할 수 있습니다.

### 1.1. Java 설치

Hadoop 실행에 필요한 Java를 설치합니다.

```bash
sudo apt-get update
sudo apt-get install default-jdk
```

### 1.2. Hadoop 다운로드 및 설치

1. Hadoop 3.4.0을 다운로드합니다.

   ```bash
   wget https://downloads.apache.org/hadoop/common/hadoop-3.4.0/hadoop-3.4.0.tar.gz
   ```

2. 다운로드한 tar.gz 파일을 압축 해제한 후, `/usr/local/hadoop` 디렉토리로 이동합니다.

   ```bash
   tar -xzvf hadoop-3.4.0.tar.gz
   sudo mv hadoop-3.4.0 /usr/local/hadoop
   ```

### 1.3. Hadoop 환경 변수 설정

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

### 1.4. Hadoop 설정 파일 수정

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

### 1.5. SSH 설정

Hadoop 클러스터 환경에서 SSH가 필요하므로 SSH 서버를 설치합니다.

```bash
sudo apt-get install openssh-server
```

### 1.6. JAVA_HOME 설정 (Hadoop용)

Hadoop 환경 설정 파일을 열어 JAVA_HOME 경로를 지정합니다.

```bash
nano $HADOOP_HOME/etc/hadoop/hadoop-env.sh
```

파일 내에 아래 내용을 추가하거나 수정합니다.

```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64/
```

### 1.7. HDFS 데이터 디렉토리 생성

Hadoop이 데이터를 저장할 디렉토리를 생성합니다.

```bash
mkdir -p ~/hadoopdata/hdfs/namenode
mkdir -p ~/hadoopdata/hdfs/datanode
```

### 1.8. HDFS 포맷

이전 단계에서 생성한 이름노드 디렉토리를 포맷합니다.

```bash
hdfs namenode -format
```

### 1.9. HDFS 데몬 시작

HDFS 관련 데몬을 시작합니다.

```bash
start-dfs.sh
```

#### 1.9.1. 데몬 실행 확인

다음 명령어로 실행 중인 Java 프로세스를 확인하여 `NameNode`, `DataNode`, `SecondaryNameNode`가 실행 중인지 확인합니다.

```bash
jps
```

### 1.10. HDFS 사용해보기

#### 1.10.1. 디렉토리 생성

HDFS 내에 디렉토리를 생성합니다.

```bash
hdfs dfs -mkdir /user
hdfs dfs -mkdir /user/news
hdfs dfs -mkdir /user/news/realtime
hdfs dfs -mkdir /user/news/news_archive
```

#### 1.10.2. 파일 목록 확인

생성한 디렉토리 내의 파일 목록을 확인합니다.

```bash
hdfs dfs -ls /user/news/
```

### 1.11. HDFS 데몬 종료

HDFS 데몬을 종료합니다.

```bash
stop-dfs.sh
```


## 2. 필요한 라이브러리 설치

```bash
poetry add
```

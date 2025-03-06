# 15주차 관통 PJT: 스트리밍 데이터 파이프라인 구축(Kafka + Flink)


> **목적: 카프카와 플링크를 배우고, 실시간 데이터를 핸들링 하는 환경을 직접 구축한다**
>
> 세부사항:
> - 카프카와 플링크가 반드시 사용되어야 한다.
> - 14주차에서 획득한 데이터와 DB를 사용해야 한다.
> - 만약 필요시, RSS에서 새로운 데이터를 땡겨올 수 있어야 한다. 그리고 해당 데이터도 처리가 되어야 한다.

## 목차
1. 카프카, 플링크 개발환경 구축
2. 카프카 producer, consumer 실행


## 1. 카프카, 플링크 개발환경 구축
### 1.1. 패키지 설치
   터미널에서 아래 명령어를 실행하여 producer, consumer 실행에 필요한 패키지를 설치합니다.

   ```bash
   poetry add kafka-python apache-flink pydantic setuptools
   ```

### 1.2. Docker 설치
Kafka 실행을 위해 Docker를 설치합니다.  
자세한 내용은 [Docker 설치 가이드 (Ubuntu)](https://docs.docker.com/engine/install/ubuntu/)를 참고하세요.

### 1.3. Kafka 실행

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
   
## 2. 카프카 Producer, Consumer 실행

Kafka와 연동되는 파이썬 스크립트를 통해 데이터 파이프라인을 테스트할 수 있습니다.

### 2.1 Consumer 실행
  Kafka로부터 메시지를 소비하는 스크립트를 실행합니다.

  ```bash
  # Consumer를 위한 screen 생성 및 실행
  screen -S kafka-consumer
  poetry run python consumer/flink_kafka_consumer.py
  ```

  스크린을 detach하려면 `Ctrl+A+D`를 누르세요.

### 2.2 Producer 실행
  RSS 피드 데이터를 Kafka로 전송하는 스크립트를 실행합니다.

  ```bash
  # Producer를 위한 screen 생성 및 실행
  screen -S kafka-producer
  poetry run python producer/rss_kafka_producer.py
  ```

  스크린을 detach하려면 `Ctrl+A+D`를 누르세요.
  
### 2.3 결과 확인
터미널에서 producing, consuming이 잘 되는지 확인하고 db에 저장이 잘 되는지 확인합니다.


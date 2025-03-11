# flink_kafka_consumer.py

import json
import os
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.connectors import FlinkKafkaConsumer
from pyflink.datastream.functions import MapFunction

import psycopg2
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

from preprocessing import transform_classify_category, transform_extract_keywords, transform_to_embedding

# HDFS 클라이언트 관련 모듈
from hdfs import InsecureClient

# .env 파일에 필요한 설정이 있다면 로드합니다.
load_dotenv()


class NewsArticle(BaseModel):
    """뉴스 기사 데이터를 위한 Pydantic 모델"""
    title: str = Field(description="기사 제목")
    link: str = Field(description="기사 URL")
    summary: str = Field(description="기사 요약")
    published: str = Field(description="발행일")
    author: Optional[str] = Field(default=None, description="기자 이름")
    content: Optional[str] = Field(default=None, description="기사 본문")


def process_message(json_str: str) -> NewsArticle:
    """
    JSON 문자열을 파싱하여 NewsArticle 모델로 변환합니다.
    """
    try:
        data = json.loads(json_str)
        return NewsArticle(**data)
    except Exception as e:
        print(f"메시지 파싱 오류: {e}")
        # 오류 발생 시 기본값으로 빈 기사 반환
        return NewsArticle(
            title="오류 발생",
            link="",
            summary="메시지 파싱 중 오류가 발생했습니다",
            published="",
            author="",
            content=""
        )


class DBInsertionMapFunction(MapFunction):
    """
    DB에 뉴스 기사를 저장하고 HDFS에 파일로 기록하는 함수.
    RichMapFunction을 사용할 수 없는 경우, MapFunction과 lazy initialization을 이용합니다.
    """
    def __init__(self):
        # lazy initialization 플래그
        self._initialized = False

    def _initialize(self):
        """
        DB 연결 및 HDFS 클라이언트를 초기화합니다.
        이 메서드는 워커에서 최초 호출 시 한 번 실행됩니다.
        """
        # PostgreSQL DB 연결
        self._db_conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="news",              # 데이터베이스 이름
            user=os.getenv("DB_USERNAME"),            # 사용자명
            password=os.getenv("DB_PASSWORD")     # 비밀번호
        )
        self._db_conn.autocommit = True

        # HDFS 클라이언트 초기화
        self.hdfs_client = InsecureClient(os.getenv('HDFS_URL'), user=os.getenv('HDFS_USER'))
        self.hdfs_path = '/user/news/realtime/'  # HDFS 내 데이터 저장 경로

        # Elasticsearch 클라이언트 초기화
        self.es = Elasticsearch([os.getenv("ES_URL")])
        if not self.es.ping():
            raise ValueError("Elasticsearch에 연결할 수 없습니다.")

        if not self.es.indices.exists(index="news"):
            self.es.indices.create(index="news")

        self._initialized = True

    def map(self, article: NewsArticle) -> NewsArticle:
        if not self._initialized:
            self._initialize()

        # 작성자: article.author가 없으면 "Unknown" 사용
        writer = article.author if article.author else "Unknown"
        try:
            write_date = datetime.fromisoformat(article.published)
        except Exception as e:
            write_date = datetime.now()

        # 기사 본문이 있으면 content, 없으면 summary 사용
        content = article.content if article.content else article.summary

        try:
            category = transform_classify_category(content)
        except Exception as e:
            print("Category transformation error:", e)
            category = "미분류"

        try:
            keywords = transform_extract_keywords(content)
        except Exception as e:
            print("Keywords transformation error:", e)
            keywords = []

        try:
            embedding = transform_to_embedding(content)
            embedding_str = json.dumps(embedding)
        except Exception as e:
            print("Embedding transformation error:", e)
            embedding_str = json.dumps([])

        # PostgreSQL에 기사 삽입
        # db에 저장된 id를 Elastic Search에도 저장하기 위해 RETURING id 쿼리 추가
        cursor = self._db_conn.cursor()
        db_id = None
        try:
            cursor.execute("""
                INSERT INTO mynews_article (title, writer, write_date, category, content, url, keywords, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
                RETURNING id;
            """, (
                article.title,
                writer,
                write_date,
                category,
                content,
                article.link,
                json.dumps(keywords, ensure_ascii=False),
                embedding_str
            ))
            db_id = cursor.fetchone()[0]
            print(f"Successfully saved article to Postgresql, id: {db_id}")
        except Exception as e:
            print("DB insertion error:", e)
        finally:
            cursor.close()

        # DB에 저장 성공한 경우에만 Elasticsearch에 기사 저장
        if db_id is not None:
            es_data = {
                "id": db_id,
                "title": article.title,
                "writer": writer,
                "write_date": write_date.isoformat(),
                "category": category,
                "content": content,
                "url": article.link,
                "keywords": keywords,
                "embedding": embedding,
            }

            try:
                self.es.index(index="news", document=es_data)
                print(f"Successfully indexed article in Elasticsearch: {article.title}")
            except Exception as e:
                print("Elasticsearch indexing error:", e)

        # HDFS에 파일 저장
        safe_title = "".join(c for c in article.title[:50] if c.isalnum() or c in (' ', '-', '_')).replace(" ", "_")
        filename = f"{write_date.strftime('%Y%m%d')}_{safe_title}.json"
        # hdfs_path가 '/'로 끝나지 않을 경우 보정
        if not self.hdfs_path.endswith("/"):
            hdfs_file_path = self.hdfs_path + "/" + filename
        else:
            hdfs_file_path = self.hdfs_path + filename

        data_to_save = {
            "title": article.title,
            "writer": writer,
            "write_date": write_date.isoformat(),
            "category": category,
            "content": content,
            "link": article.link,
            "keywords": json.dumps(keywords),
            "embedding": embedding_str
        }
        json_data = json.dumps(data_to_save, ensure_ascii=False, indent=2)
        try:
            with self.hdfs_client.write(hdfs_file_path, encoding='utf-8') as writer_obj:
                writer_obj.write(json_data)
            print(f"Successfully saved article to HDFS: {hdfs_file_path}")
        except Exception as e:
            print("HDFS file save error:", e)


        return article  # 체인 연산을 위해 반환


def main():
    # Flink 스트리밍 환경 생성
    env = StreamExecutionEnvironment.get_execution_environment()

    # Kafka connector Jar 파일 경로 설정 (절대 경로, file:// 포함)
    env.add_jars(f"file://{os.getenv("KAFKA_CONNECTOR_PATH")}")

    # Kafka consumer properties 설정
    kafka_props = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'flink_consumer_group'
    }

    # Kafka Consumer 생성 (토픽: "news")
    kafka_consumer = FlinkKafkaConsumer(
        topics="news",
        deserialization_schema=SimpleStringSchema(),  # 문자열 메시지 수신
        properties=kafka_props
    )

    # Kafka에서 메시지 읽어오기
    stream = env.add_source(kafka_consumer)

    # 메시지를 NewsArticle 모델로 변환
    processed_stream = stream.map(process_message)

    # DB 삽입 및 HDFS 저장 로직을 MapFunction으로 실행
    processed_stream = processed_stream.map(DBInsertionMapFunction())

    # 디버그를 위해 처리 결과를 콘솔에 출력 (원하는 경우 주석 처리 가능)
    processed_stream.print()

    print("consumer is running...")
    # Flink Job 실행
    env.execute("Flink Kafka Consumer Job")


if __name__ == "__main__":
    main()

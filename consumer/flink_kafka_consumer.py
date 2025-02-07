# flink_kafka_consumer.py

import json
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.connectors import FlinkKafkaConsumer

import psycopg2
from dotenv import load_dotenv

from preprocessing import transform_classify_category, transform_extract_keywords, transform_to_embedding

# .env 파일에 OpenAI API key 등 필요한 설정이 있다면 로드합니다.
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


# ─────────────────────────────────────────────
# PostgreSQL DB 연결 관련 (각 워커에서 재사용 가능하도록 단일 연결 사용)
# ─────────────────────────────────────────────

_db_conn = None

def get_db_conn():
    """
    워커 내에서 단일 DB 연결을 생성하여 재사용합니다.
    """
    global _db_conn
    if _db_conn is None:
        _db_conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="news",              # 데이터베이스 이름
            user="postgres",            # 사용자명
            password="new_password"     # 비밀번호
        )
        _db_conn.autocommit = True
    return _db_conn


def db_insertion(article: NewsArticle) -> NewsArticle:
    """
    뉴스 기사를 PostgreSQL에 저장합니다.  
    추가 변환(카테고리, 키워드, 임베딩) 후 DB에 삽입합니다.
    """
    writer = article.author if article.author else "Unknown"
    try:
        write_date = datetime.fromisoformat(article.published)
    except Exception as e:
        write_date = datetime.now()

    # 기사 본문이 있다면 content 사용, 없으면 summary 사용
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
        # pgvector 등 확장 모듈을 사용하지 않는 경우 JSON 문자열로 변환
        embedding_str = json.dumps(embedding)
    except Exception as e:
        print("Embedding transformation error:", e)
        embedding_str = json.dumps([])

    conn = get_db_conn()
    cursor = conn.cursor()
    try:
        # 테이블명(news_article) 및 컬럼명은 실제 모델 구조에 맞게 수정하세요.
        cursor.execute("""
            INSERT INTO news_article (title, writer, write_date, category, content, url, keywords, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING
        """, (
            article.title,
            writer,
            write_date,
            category,
            content,
            article.link,
            json.dumps(keywords),
            embedding_str
        ))
    except Exception as e:
        print("DB insertion error:", e)
    finally:
        cursor.close()
    return article  # 반환값은 이후 체인 연산을 위해 그대로 반환합니다.


def main():
    # Flink 스트리밍 환경 생성
    env = StreamExecutionEnvironment.get_execution_environment()

    # 추가 Kafka connector Jar 파일 경로 설정 (절대 경로, file:// 포함)
    env.add_jars("file:///home/jiwoochris/projects/ssafy-custom-news-data/kafka/flink-sql-connector-kafka-3.3.0-1.20.jar")

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

    # DB에 저장하는 로직을 map 연산자로 실행 (side-effect)
    processed_stream = processed_stream.map(db_insertion)

    # 디버그를 위해 처리 결과를 콘솔에 출력 (원하는 경우 주석 처리 가능)
    processed_stream.print()

    # Flink Job 실행
    env.execute("Flink Kafka Consumer Job")


if __name__ == "__main__":
    main()

import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StringType, StructType, StructField
from pyspark.streaming import StreamingContext
import psycopg2
from datetime import datetime

# PostgreSQL 연결 설정
POSTGRESQL_HOST = "localhost"
POSTGRESQL_PORT = "5432"
POSTGRESQL_DB = "news_db"
POSTGRESQL_USER = "postgres_user"
POSTGRESQL_PASSWORD = "postgres_password"
TABLE_NAME = "processed_news"

# Spark 세션 및 StreamingContext 설정
spark = SparkSession.builder.appName("NewsProcessing").getOrCreate()
sc = spark.sparkContext
ssc = StreamingContext(sc, 5)  # 5초마다 데이터를 처리

# HDFS 경로 설정
hdfs_path = "hdfs://localhost:9000/user/jiwoochris"

# PostgreSQL에 데이터 저장 함수
def save_to_postgresql(data):
    print("================================================")
    print("Write to PostgreSQL")
    print(data)
    # try:
    #     conn = psycopg2.connect(
    #         host=POSTGRESQL_HOST,
    #         port=POSTGRESQL_PORT,
    #         dbname=POSTGRESQL_DB,
    #         user=POSTGRESQL_USER,
    #         password=POSTGRESQL_PASSWORD
    #     )
    #     cur = conn.cursor()
    #     insert_query = f"""
    #     INSERT INTO {TABLE_NAME} (title, content, write_date, category, embedding)
    #     VALUES (%s, %s, %s, %s, %s)
    #     """
    #     cur.executemany(insert_query, data)
    #     conn.commit()
    #     cur.close()
    #     conn.close()
    #     print("Data saved to PostgreSQL.")
    # except Exception as e:
    #     print(f"Error saving to PostgreSQL: {e}")

# 샘플 카테고리 분류 함수
def category_classification(title, content):
    # 간단한 키워드 기반 분류 예제
    if "sports" in content.lower():
        return "Sports"
    elif "politics" in content.lower():
        return "Politics"
    else:
        return "General"

# 샘플 임베딩 함수 (여기서는 단순히 문자열 길이 반환으로 예시)
def text_embedding(content):
    return str(len(content))

# UDF로 변환
category_udf = udf(category_classification, StringType())
embedding_udf = udf(text_embedding, StringType())

# 스키마 정의
schema = StructType([
    StructField("title", StringType(), True),
    StructField("content", StringType(), True),
    StructField("write_date", StringType(), True)
])

# 스트리밍 데이터 읽기 및 처리
def process_stream(rdd):
    if not rdd.isEmpty():
        df = spark.read.json(rdd, schema=schema)
        
        # 전처리: 카테고리 분류 및 임베딩 생성
        df = df.withColumn("category", category_udf(col("title"), col("content")))
        df = df.withColumn("embedding", embedding_udf(col("content")))

        # PostgreSQL에 저장할 데이터 준비
        processed_data = df.select("title", "content", "write_date", "category", "embedding").collect()
        rows = [(row['title'], row['content'], row['write_date'], row['category'], row['embedding']) for row in processed_data]

        # PostgreSQL 저장
        save_to_postgresql(rows)

# HDFS 디렉터리로부터 스트리밍 데이터 생성
lines = ssc.textFileStream(hdfs_path)
lines.foreachRDD(lambda rdd: process_stream(rdd))

# 스트리밍 시작
ssc.start()
ssc.awaitTermination()

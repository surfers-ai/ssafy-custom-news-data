import json
from openai import OpenAI
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, lit
from pyspark.sql.types import StringType, ArrayType, FloatType, StructType, StructField
import requests
from dotenv import load_dotenv

load_dotenv()

# 데이터 소스 설정 (HDFS)
SOURCE_DATA_PATH = f"hdfs://localhost:9000/user/news/realtime"
SOURCE_ARCHIVE_PATH = f"hdfs://localhost:9000/news_archive"

# 데이터 적재 대상 설정 (API)
TARGET_ENDPOINT = f"http://localhost:8000/write-article/"

def initialize_spark_session():
    # Spark 처리 엔진 초기화
    # 실시간 뉴스 데이터 ETL 처리를 위한 세션 생성
    return SparkSession.builder \
        .appName("RealTimeNewsETL") \
        .getOrCreate()

def define_source_schema():
    # 원본 데이터 스키마 정의
    # 뉴스 데이터의 구조를 명시하여 데이터 품질 보장
    return StructType([
        StructField("title", StringType(), True),        # 뉴스 제목
        StructField("source_site", StringType(), True),  # 데이터 출처
        StructField("write_date", StringType(), True),   # 생성 일시
        StructField("content", StringType(), True),      # 본문 내용
        StructField("url", StringType(), True)           # 원본 링크
    ])

def create_source_stream(spark, schema):
    # 소스 데이터 스트림 생성
    # HDFS에서 실시간으로 유입되는 JSON 데이터를 읽어오는 스트림 설정
    return spark.readStream \
        .schema(schema) \
        .option("cleanSource", "archive") \
        .option("sourceArchiveDir", SOURCE_ARCHIVE_PATH) \
        .json(SOURCE_DATA_PATH)

def transform_extract_keywords(text):
    """
    (이 부분 자체 모델 학습 시켜 대체 가능)
    텍스트 데이터 변환 - 키워드 추출
    입력 텍스트에서 핵심 키워드를 추출하는 변환 로직
    """
    text = preprocess_content(text)

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 텍스트에서 주요 키워드를 추출하는 전문가입니다. 다음 텍스트에서 가장 중요한 5개의 키워드를 추출해주세요. 키워드는 쉼표로 구분하여 반환해주세요"},
            {"role": "user", "content": text}
        ],
        max_tokens=100
    )
    keywords = response.choices[0].message.content.strip()
    return keywords.split(',')

def transform_to_embedding(text: str) -> list[float]:
    """
    (이 부분 자체 모델 학습 시켜 대체 가능)
    텍스트 데이터 변환 - 벡터 임베딩
    텍스트를 수치형 벡터로 변환하는 변환 로직
    """
    text = preprocess_content(text)

    client = OpenAI()
    response = client.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding

def transform_classify_category(content):
    """
    (이 부분 자체 모델 학습 시켜 대체 가능)
    텍스트 데이터 변환 - 카테고리 분류
    뉴스 내용을 기반으로 적절한 카테고리로 분류하는 변환 로직
    """
    content = preprocess_content(content)
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 뉴스 기사의 카테고리를 분류하는 어시스턴트입니다. No verbose. 카테고리는 [\"IT_과학\", \"건강\", \"경제\", \"교육\", \"국제\", \"라이프스타일\", \"문화\", \"사건사고\", \"사회일반\", \"산업\", \"스포츠\", \"여성복지\", \"여행레저\", \"연예\", \"정치\", \"지역\", \"취미\"] 중 하나입니다. 이외의 카테고리는 없습니다."},
            {"role": "user", "content": content}
        ]
    )
    model_output = response.choices[0].message.content.strip()

    if "카테고리:" in model_output:
        model_output = model_output.split("카테고리:")[1].strip()
    model_output = model_output.replace('"', '').replace("'", "").strip()

    return model_output

def preprocess_content(content):
    """
    데이터 전처리 - 텍스트 길이 제한
    토큰 수를 제한하여 처리 효율성 확보
    """
    import tiktoken
    
    if not content:
        return ""
        
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(content)
    
    if len(tokens) > 5000:
        truncated_tokens = tokens[:5000]
        return encoding.decode(truncated_tokens)
    
    return content

def register_transformation_udfs():
    # 데이터 변환을 위한 UDF 함수 등록
    return {
        "keywords": udf(transform_extract_keywords, ArrayType(StringType())),
        "embedding": udf(transform_to_embedding, ArrayType(FloatType())),
        "category": udf(transform_classify_category, StringType())
    }

def transform_dataframe(source_df, transformation_udfs):
    # 데이터프레임 변환 처리
    # 원본 데이터에 특성 추출 및 분류 결과 추가
    return source_df.withColumn("keywords", transformation_udfs["keywords"](col("content"))) \
             .withColumn("embedding", transformation_udfs["embedding"](col("content"))) \
             .withColumn("category", transformation_udfs["category"](col("content"))) \
             .withColumn("writer", col("source_site")) \
             .drop("source_site")

# def load_to_target(batch_df, epoch_id):
#     # 변환된 데이터를 대상 시스템으로 적재
#     records = batch_df.toJSON().collect()
#     headers = {'Content-Type': 'application/json'}
    
#     for record in records:
#         record_dict = json.loads(record)
#         response = requests.post(
#             TARGET_ENDPOINT,
#             data=record, 
#             headers=headers
#         )
        
#         load_status = f"{'적재 성공' if response.status_code == 200 else '적재 실패'}: {record_dict['title']}"
        
#         print(load_status)
#         if response.status_code != 200:
#             print(response.text)

def load_to_target(batch_df, epoch_id):
    # 변환된 데이터를 대상 시스템으로 적재 (parquet 형식으로 저장)
    batch_df = batch_df.withColumn("keywords", col("keywords").cast(StringType())) \
                       .withColumn("embedding", col("embedding").cast(StringType()))
    batch_df.write.mode("append").parquet("realtime.parquet")


def start_etl_pipeline(transformed_df):
    # ETL 파이프라인 실행
    query = transformed_df.writeStream \
        .foreachBatch(load_to_target) \
        .start()
    return query

def main():
    # ETL 파이프라인 초기화 및 실행
    spark = initialize_spark_session()

    # 소스 데이터 스키마 정의
    source_schema = define_source_schema()
    
    # 소스 데이터 스트림 생성
    source_stream = create_source_stream(spark, source_schema)
    
    # 데이터 변환을 위한 UDF 함수 등록
    transformation_udfs = register_transformation_udfs()
    
    # 데이터프레임 변환 처리
    transformed_df = transform_dataframe(source_stream, transformation_udfs)
    
    # ETL 파이프라인 실행
    query = start_etl_pipeline(transformed_df)
    query.awaitTermination()

if __name__ == "__main__":
    main()

import json
from openai import OpenAI
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, lit
from pyspark.sql.types import StringType, ArrayType, FloatType, StructType, StructField
import requests
from dotenv import load_dotenv

load_dotenv()

def create_spark_session():
    # Spark 세션 생성
    # 애플리케이션 이름을 "RealTimeNewsProcessing"으로 설정하고
    # 새로운 SparkSession을 생성하거나 기존 세션을 가져옴
    return SparkSession.builder \
        .appName("RealTimeNewsProcessing") \
        .getOrCreate()

def get_schema():
    return StructType([
        StructField("title", StringType(), True),
        StructField("source_site", StringType(), True), 
        StructField("write_date", StringType(), True),
        StructField("content", StringType(), True),
        StructField("url", StringType(), True)
    ])

def create_streaming_df(spark, schema):
    return spark.readStream \
        .schema(schema) \
        .option("cleanSource", "archive") \
        .option("sourceArchiveDir", "hdfs://localhost:9000/realtime_archive") \
        .json("hdfs://localhost:9000/user/jiwoochris/realtime")

def extract_keywords(text):
    text = truncate_content(text)

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

def get_embedding(text: str) -> list[float]:
    text = truncate_content(text)

    client = OpenAI()
    response = client.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding

def extract_category(content):
    content = truncate_content(content)
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 뉴스 기사의 카테고리를 분류하는 어시스턴트입니다. No verbose. 카테고리는 [\"IT_과학\", \"건강\", \"경제\", \"교육\", \"국제\", \"라이프스타일\", \"문화\", \"사건사고\", \"사회일반\", \"산업\", \"스포츠\", \"여성복지\", \"여행레저\", \"연예\", \"정치\", \"지역\", \"취미\"] 중 하나입니다. 이외의 카테고리는 없습니다."},
            {"role": "user", "content": content}
        ]
    )
    model_output = response.choices[0].message.content.strip()

    # 모델 출력이 "카테고리: 건강" 형식으로 온 경우 처리
    if "카테고리:" in model_output:
        model_output = model_output.split("카테고리:")[1].strip()
    # 쌍따옴표 및 따옴표 제거 및 전처리
    model_output = model_output.replace('"', '').replace("'", "").strip()

    return model_output

def truncate_content(content):
    import tiktoken
    
    if not content:
        return ""
        
    encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 사용 인코딩
    tokens = encoding.encode(content)
    
    if len(tokens) > 5000:
        truncated_tokens = tokens[:5000]
        return encoding.decode(truncated_tokens)
    
    return content

def create_udfs():
    return {
        "keywords": udf(extract_keywords, ArrayType(StringType())),
        "embedding": udf(get_embedding, ArrayType(FloatType())),
        "category": udf(extract_category, StringType())
    }

def process_dataframe(df, udfs):
    return df.withColumn("keywords", udfs["keywords"](col("content"))) \
             .withColumn("embedding", udfs["embedding"](col("content"))) \
             .withColumn("category", udfs["category"](col("content"))) \
             .withColumn("writer", col("source_site")) \
             .drop("source_site")

def send_to_server(batch_df, epoch_id):
    records = batch_df.toJSON().collect()
    headers = {'Content-Type': 'application/json'}
    
    for record in records:
        record_dict = json.loads(record)
        response = requests.post(
            "http://223.130.135.250:8000/write-article/",   # "http://localhost:8000/write-article/"
            data=record, 
            headers=headers
        )
        
        log_message = f"{'Successfully' if response.status_code == 200 else 'Failed to'} sent data: " + f"{record_dict['title']}"
        
        print(log_message)
        if response.status_code != 200:
            print(response.text)

def start_streaming(processed_df):
    query = processed_df.writeStream \
        .foreachBatch(send_to_server) \
        .start()
    return query

def main():
    # Spark 세션 생성
    spark = create_spark_session()
    
    # 스키마 정의
    schema = get_schema()
    
    # 스트리밍 데이터프레임 생성
    streaming_df = create_streaming_df(spark, schema)
    
    # UDF 함수들 생성
    udfs = create_udfs()
    
    # 데이터프레임 처리 (키워드 추출, 임베딩 생성, 카테고리 분류 등)
    processed_df = process_dataframe(streaming_df, udfs)
    
    # 스트리밍 시작
    query = start_streaming(processed_df)
    
    # 스트리밍이 종료될 때까지 대기
    query.awaitTermination()

if __name__ == "__main__":
    main()

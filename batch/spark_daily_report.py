import sys
import argparse
import os
from datetime import datetime, timedelta

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, count, from_json, to_timestamp
from pyspark.sql.types import ArrayType, StringType
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# HDFS 클라이언트를 이용해 파일 이동 (pyhdfs, hdfs 라이브러리 등 여러가지 방법이 있으나 여기서는 InsecureClient 사용)
from hdfs import InsecureClient

def main(report_date_str):
    print(f"시작 날짜: {report_date_str}")

    # Spark 세션 생성
    spark = SparkSession.builder \
            .appName("DailyNewsReport") \
            .getOrCreate()

    # 보고서 기준 날짜 처리 (YYYY-MM-DD)
    report_date = datetime.strptime(report_date_str, "%Y-%m-%d")
    # 전일 데이터를 분석하도록 함 (report_date의 전날 데이터를 읽음)
    start_date = report_date - timedelta(days=1)
    end_date = report_date

    # HDFS의 /user/news/realtime 디렉터리 내 모든 JSON 파일 읽기
    # Spark가 HDFS와 연동되어 있다면 경로 앞에 hdfs:// 접두어가 필요할 수 있습니다.
    hdfs_input_path = "hdfs://localhost:9000/user/news/realtime/*.json"
    df = spark.read.option("multiLine", True).json(hdfs_input_path)

    # write_date는 ISO 형식의 문자열로 저장되어 있으므로 timestamp로 변환
    df = df.withColumn("write_date_ts", to_timestamp(col("write_date")))
    
    # 지정된 날짜 범위(전일)의 데이터만 필터링
    df = df.filter((col("write_date_ts") >= start_date) & (col("write_date_ts") < end_date))

    if df.rdd.isEmpty():
        print("지정된 날짜 범위에 해당하는 데이터가 없습니다.")
        spark.stop()
        sys.exit(0)

    # keywords 컬럼은 JSON 배열 문자열로 저장되어 있다고 가정
    # 이를 ArrayType(StringType())로 파싱 후 explode하여 각 키워드를 분리
    df = df.withColumn("keywords_array", from_json(col("keywords").cast("string"), ArrayType(StringType())))
    exploded_df = df.withColumn("keyword", explode(col("keywords_array")))

    # 각 키워드의 빈도수 집계
    keyword_counts = exploded_df.groupBy("keyword").agg(count("keyword").alias("count")).orderBy(col("count").desc())

    # 상위 10개 키워드를 Pandas DataFrame으로 변환
    keyword_pd = keyword_counts.limit(10).toPandas()

    # 폰트 설정
    font_path = '/home/honuuk/ssafy-custom-news-data/batch/Pretendard-Bold.ttf'
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()

    # 시각화: 상위 10개 키워드 바 차트 생성
    plt.figure(figsize=(10, 6))
    plt.bar(keyword_pd['keyword'], keyword_pd['count'], color='skyblue')
    plt.xlabel("키워드", fontproperties=font_prop)
    plt.ylabel("빈도수", fontproperties=font_prop)
    plt.title(f"{start_date.strftime('%Y-%m-%d')} 뉴스 리포트 - Top 10 Keywords", fontproperties=font_prop)
    plt.xticks(rotation=45, fontproperties=font_prop)
    plt.tight_layout()

    # 리포트 파일 저장 경로 (Airflow DAG의 EmailOperator 등에서 참조할 경로)
    report_dir = "/home/honuuk/ssafy-custom-news-data/report"
    os.makedirs(report_dir, exist_ok=True)  # 디렉토리가 없으면 생성
    report_file = f"/home/honuuk/ssafy-custom-news-data/report/daily_report_{report_date.strftime('%Y%m%d')}.pdf"
    plt.savefig(report_file)
    plt.close()

    print(f"리포트가 {report_file} 에 저장되었습니다.")

    spark.stop()

    # 리포트 발행 이후, 처리한 파일들을 /news_archive 디렉터리로 이동
    try:
        # HDFS 클라이언트 초기화 (환경에 맞게 URL, user 수정)
        client = InsecureClient('http://localhost:9870', user='hadoop-user')
        source_dir = "/user/news/realtime"
        target_dir = "/news_archive"

        # source 디렉터리 내 파일 목록 조회
        files = client.list(source_dir)
        if not files:
            print(f"{source_dir} 디렉터리에 이동할 파일이 없습니다.")
        else:
            for file in files:
                source_path = f"{source_dir}/{file}"
                target_path = f"{target_dir}/{file}"
                client.rename(source_path, target_path)
                print(f"파일 {source_path} -> {target_path} 로 이동")
            print(f"모든 파일이 {target_dir}로 이동되었습니다.")
    except Exception as e:
        print("파일 이동 중 오류 발생:", e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spark를 이용한 일일 뉴스 리포트 생성")
    parser.add_argument("--date", required=True, help="보고서 기준 날짜 (YYYY-MM-DD)")
    args = parser.parse_args()

    main(args.date)
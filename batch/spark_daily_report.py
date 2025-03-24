import sys
import argparse
import os
import shutil
from datetime import datetime, timedelta

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, count, from_json, to_timestamp
from pyspark.sql.types import ArrayType, StringType
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

def main(report_date_str):
    print(f"시작 날짜: {report_date_str}")

    # Spark 세션 생성
    spark = SparkSession.builder \
            .appName("DailyNewsReport") \
            .getOrCreate()

    # 보고서 기준 날짜 처리
    report_date = datetime.strptime(report_date_str, "%Y-%m-%d")
    start_date = report_date - timedelta(days=1)
    end_date = report_date

    # 로컬 파일 경로 설정
    local_input_path = "/home/jiwoochris/projects/ssafy-custom-news-data/realtime/*.json"
    df = spark.read.option("multiLine", True).json(local_input_path)

    df = df.withColumn("write_date_ts", to_timestamp(col("write_date")))
    df = df.filter((col("write_date_ts") >= start_date) & (col("write_date_ts") < end_date))

    if df.rdd.isEmpty():
        print("지정된 날짜 범위에 해당하는 데이터가 없습니다.")
        spark.stop()
        sys.exit(0)

    df = df.withColumn("keywords_array", from_json(col("keywords").cast("string"), ArrayType(StringType())))
    exploded_df = df.withColumn("keyword", explode(col("keywords_array")))

    # 각 키워드의 빈도수 집계
    keyword_counts = exploded_df.groupBy("keyword").agg(count("keyword").alias("count")).orderBy(col("count").desc())

    # 상위 10개 키워드를 Pandas DataFrame으로 변환
    keyword_pd = keyword_counts.limit(10).toPandas()

    # 폰트 설정
    font_path = '/home/jiwoochris/projects/ssafy-custom-news-data/batch/Pretendard-Bold.ttf'
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
    report_dir = "/home/jiwoochris/projects/ssafy-custom-news-data/report"
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(report_dir, f"daily_report_{report_date.strftime('%Y%m%d')}.pdf")
    plt.savefig(report_file)
    plt.close()

    print(f"리포트가 {report_file} 에 저장되었습니다.")

    spark.stop()

    # 처리 완료된 파일들을 archive 폴더로 이동
    try:
        source_dir = "/home/jiwoochris/projects/ssafy-custom-news-data/realtime"
        target_dir = "/home/jiwoochris/projects/ssafy-custom-news-data/news_archive"
        os.makedirs(target_dir, exist_ok=True)

        files = os.listdir(source_dir)
        if not files:
            print(f"{source_dir} 디렉터리에 이동할 파일이 없습니다.")
        else:
            for file in files:
                source_path = os.path.join(source_dir, file)
                target_path = os.path.join(target_dir, file)
                shutil.move(source_path, target_path)
                print(f"파일 {source_path} -> {target_path} 로 이동")
            print(f"모든 파일이 {target_dir}로 이동되었습니다.")
    except Exception as e:
        print("파일 이동 중 오류 발생:", e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spark를 이용한 일일 뉴스 리포트 생성")
    parser.add_argument("--date", required=True, help="보고서 기준 날짜 (YYYY-MM-DD)")
    args = parser.parse_args()

    main(args.date)
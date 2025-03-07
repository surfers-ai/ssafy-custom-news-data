import sys
import argparse
import os
from datetime import datetime, timedelta

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, count, from_json, to_timestamp
from pyspark.sql.types import ArrayType, StringType
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from dotenv import load_dotenv

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))


def main(report_date_str):
    print(f"시작 날짜: {report_date_str}")

    # Spark 세션 생성
    spark = (
        SparkSession.builder.config(
            "spark.driver.extraClassPath", "./postgresql-42.7.5.jar"
        )
        .appName("DailyNewsReport")
        .getOrCreate()
    )

    # 보고서 기준 날짜 처리 (YYYY-MM-DD)
    report_date = datetime.strptime(report_date_str, "%Y-%m-%d")
    # 전일 데이터를 분석하도록 함 (airflow가 report_date에 전일 날짜를 넣어줍니다.)
    start_date = report_date
    end_date = report_date + timedelta(days=1)

    df = (
        spark.read.format("jdbc")
        .option("url", f"jdbc:postgresql://localhost:5432/news")
        .option("driver", "org.postgresql.Driver")
        .option("dbtable", "mynews_article")
        .option(
            "user",
            os.getenv("DB_USERNAME"),
        )
        .option(
            "password",
            os.getenv("DB_PASSWORD"),
        )
        .load()
    )

    df.show(10)
    # write_date는 ISO 형식의 문자열로 저장되어 있으므로 timestamp로 변환
    df = df.withColumn("write_date_ts", to_timestamp(col("write_date")))

    # 지정된 날짜 범위(전일)의 데이터만 필터링
    df = df.filter(
        (col("write_date_ts") >= start_date) & (col("write_date_ts") < end_date)
    )

    if df.rdd.isEmpty():
        print("지정된 날짜 범위에 해당하는 데이터가 없습니다.")
        spark.stop()
        sys.exit(0)

    # keywords 컬럼은 JSON 배열 문자열로 저장되어 있다고 가정
    # 이를 ArrayType(StringType())로 파싱 후 explode하여 각 키워드를 분리
    df = df.withColumn(
        "keywords_array",
        from_json(col("keywords").cast("string"), ArrayType(StringType())),
    )
    exploded_df = df.withColumn("keyword", explode(col("keywords_array")))

    # 각 키워드의 빈도수 집계
    keyword_counts = (
        exploded_df.groupBy("keyword")
        .agg(count("keyword").alias("count"))
        .orderBy(col("count").desc())
    )

    # 상위 10개 키워드를 Pandas DataFrame으로 변환
    keyword_pd = keyword_counts.limit(10).toPandas()

    # 폰트 설정

    font_path = os.path.join(current_dir, "Pretendard-Bold.ttf")

    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = font_prop.get_name()

    # 시각화: 상위 10개 키워드 바 차트 생성
    plt.figure(figsize=(10, 6))
    plt.bar(keyword_pd["keyword"], keyword_pd["count"], color="skyblue")
    plt.xlabel("키워드", fontproperties=font_prop)
    plt.ylabel("빈도수", fontproperties=font_prop)
    plt.title(
        f"{start_date.strftime('%Y-%m-%d')} 뉴스 리포트 - Top 10 Keywords",
        fontproperties=font_prop,
    )
    plt.xticks(rotation=45, fontproperties=font_prop)
    plt.tight_layout()

    # 리포트 파일 저장 경로 (Airflow DAG의 EmailOperator 등에서 참조할 경로)
    parent_dir = os.path.dirname(current_dir)
    os.path.join(current_dir, "Pretendard-Bold.ttf")
    report_dir = os.path.join(parent_dir, "report")

    os.makedirs(report_dir, exist_ok=True)  # 디렉토리가 없으면 생성
    report_file = os.path.join(
        report_dir, f"daily_report_{report_date.strftime('%Y%m%d')}.pdf"
    )
    plt.savefig(report_file)
    plt.close()

    print(f"리포트가 {report_file} 에 저장되었습니다.")

    spark.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spark를 이용한 일일 뉴스 리포트 생성")
    parser.add_argument("--date", required=True, help="보고서 기준 날짜 (YYYY-MM-DD)")
    args = parser.parse_args()

    main(args.date)

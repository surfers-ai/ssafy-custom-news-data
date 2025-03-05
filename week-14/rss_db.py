import time
import json
import os
from datetime import datetime

import psycopg2
import feedparser
import requests

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from rss_transform import (
    transform_classify_category,
    transform_extract_keywords,
    transform_to_embedding,
)

load_dotenv()


# RSS 피드 URL (예: Khan 뉴스 RSS)
RSS_FEED_URL = "https://www.khan.co.kr/rss/rssdata/total_news.xml"

db_conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="news",  # 데이터베이스 이름
    user=os.getenv("DB_USERNAME"),  # 사용자명
    password=os.getenv("DB_PASSWORD"),  # 비밀번호
)
db_conn.autocommit = True


def fetch_rss_feed():
    """
    RSS 피드를 파싱하여 각 뉴스 항목을 제너레이터로 반환합니다.
    """
    feed = feedparser.parse(RSS_FEED_URL)
    for entry in feed.entries:
        # 각 항목의 필요한 정보를 추출
        news_item = {
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary,
            "published": entry.updated,
            "author": entry.author,
        }
        yield news_item


def crawl_article(url: str) -> str:
    """특정 기사 URL을 크롤링해 기사 본문을 반환합니다."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 예시: 본문 확인
        content_tag = soup.find_all("p", class_="content_text text-l")
        content_text = "\n\n".join([tag.text.strip() for tag in content_tag])

        return content_text

    except requests.exceptions.RequestException as e:
        print(f"오류 발생: {e}")
        return ""


# 크롤링 한 기사를 DB에 저장 가능한 형식으로 변환
def to_db_data(news_item):
    writer = news_item["author"] if news_item["author"] else "Unknown"
    content = news_item["content"] if news_item["content"] else news_item["summary"]

    try:
        write_date = datetime.fromisoformat(news_item["published"])
    except Exception as e:
        write_date = datetime.now()
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
        print('embedding',embedding)
        embedding_str = json.dumps(embedding)
    except Exception as e:
        print("Embedding transformation error:", e)
        embedding_str = json.dumps([])

    return (
        news_item["title"],
        writer,
        write_date,
        category,
        content,
        news_item["link"],
        json.dumps(keywords, ensure_ascii=False),
        embedding_str,
    )


def save(news_item):
    cursor = db_conn.cursor()
    data = to_db_data(news_item)

    try:
        cursor.execute(
            """
            INSERT INTO mynews_article (title, writer, write_date, category, content, url, keywords, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING;
            """,
            data,
        )
        print(f"Successfully saved article to Postgresql, title: {data[0]}")
    except Exception as e:
        print("DB insertion error:", e)
    finally:
        cursor.close()


def main():

    # 중복 저장 방지를 위해 처리한 링크를 저장하는 집합
    saved_links = set()
    while True:
        try:
            for news_item in fetch_rss_feed():
                # 뉴스 링크를 기준으로 중복 체크
                if news_item["link"] not in saved_links:
                    news_item["content"] = crawl_article(news_item["link"])
                    save(news_item)

                    saved_links.add(news_item["link"])
            # 60초 대기 후 다시 피드 확인
            time.sleep(60)
        except Exception as e:
            print("Error:", e)
            time.sleep(60)


if __name__ == "__main__":
    main()

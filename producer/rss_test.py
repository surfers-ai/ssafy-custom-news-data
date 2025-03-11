# producer/rss_kafka_producer.py
import time
import json
import os
import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime

# RSS 피드 URL (예: Khan 뉴스 RSS)
RSS_FEED_URL = "https://www.khan.co.kr/rss/rssdata/total_news.xml"

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

        # Pydantic 모델로 감싸서 반환
        return content_text

    except requests.exceptions.RequestException as e:
        print(f"오류 발생: {e}")
        return ""

def save_article_json(article_data: dict):
    """기사 데이터를 JSON 파일로 저장합니다."""
    # data/raw_articles 디렉토리 생성
    save_dir = "data/raw_articles"
    os.makedirs(save_dir, exist_ok=True)
    
    # 파일명을 timestamp와 제목으로 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in article_data['title'][:30] if c.isalnum() or c in (' ', '-', '_'))
    filename = f"{timestamp}_{safe_title}.json"
    
    filepath = os.path.join(save_dir, filename)
    
    # JSON 파일로 저장
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(article_data, f, ensure_ascii=False, indent=2)
    
    print(f"기사가 저장되었습니다: {filepath}")

def main():
    seen_links = set()
    while True:
        try:
            print("\nRSS 피드를 확인하는 중...")
            for entry in feedparser.parse(RSS_FEED_URL).entries:
                if entry.link not in seen_links:
                    seen_links.add(entry.link)
                    print(f"\n새로운 기사 발견: {entry.title}")
                    print(f"링크: {entry.link}")
                    print(f"요약: {entry.summary}")
                    print(f"발행일: {entry.updated}")
                    print(f"기자: {entry.author}")

                    content = crawl_article(entry.link)
                    print(f"기사 본문: {content}")
                    
                    # 기사 데이터 구성
                    article_data = {
                        "title": entry.title,
                        "link": entry.link,
                        "summary": entry.summary,
                        "published": entry.updated,
                        "author": getattr(entry, 'author', None),
                        "content": content
                    }
                    
                    # JSON 파일로 저장
                    save_article_json(article_data)
            
            print(f"\n처리된 총 기사 수: {len(seen_links)}")
            print("60초 후에 다시 확인합니다...")
            time.sleep(60)
            
        except Exception as e:
            print(f"오류 발생: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()

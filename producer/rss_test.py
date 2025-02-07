# producer/rss_kafka_producer.py
import time

import requests
from bs4 import BeautifulSoup
import feedparser

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
                    # 파일에 제목과 본문만 저장
                    with open('article.md', 'w', encoding='utf-8') as f:
                        f.write(f"# {entry.title}\n\n")
                        f.write(content)
                    exit()
            
            print(f"\n처리된 총 기사 수: {len(seen_links)}")
            print("60초 후에 다시 확인합니다...")
            time.sleep(60)
            
        except Exception as e:
            print(f"오류 발생: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()

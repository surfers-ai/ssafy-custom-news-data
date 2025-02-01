# producer/rss_kafka_producer.py
import time
import feedparser

# RSS 피드 URL (예: Khan 뉴스 RSS)
RSS_FEED_URL = "https://www.khan.co.kr/rss/rssdata/total_news.xml"

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
            
            print(f"\n처리된 총 기사 수: {len(seen_links)}")
            print("60초 후에 다시 확인합니다...")
            time.sleep(60)
            
        except Exception as e:
            print(f"오류 발생: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()

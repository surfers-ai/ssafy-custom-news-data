# producer/rss_kafka_producer.py
import time
import json
import feedparser
from kafka import KafkaProducer

# RSS 피드 URL (예: Khan 뉴스 RSS)
RSS_FEED_URL = "https://www.khan.co.kr/rss/rssdata/total_news.xml"
# Kafka 브로커 주소 (실제 환경에 맞게 수정)
KAFKA_BROKER = "localhost:9092"
# 전송할 Kafka 토픽
TOPIC = "news"

# Kafka Producer 생성 (value는 JSON 직렬화)
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

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
            "published": entry.published
        }
        yield news_item

def main():
    # 중복 전송 방지를 위해 처리한 링크를 저장하는 집합
    seen_links = set()
    while True:
        try:
            for news_item in fetch_rss_feed():
                # 뉴스 링크를 기준으로 중복 체크
                if news_item["link"] not in seen_links:
                    seen_links.add(news_item["link"])
                    producer.send(TOPIC, news_item)
                    print(f"Sent: {news_item['title']}")
            # 60초 대기 후 다시 피드 확인
            time.sleep(60)
        except Exception as e:
            print("Error:", e)
            time.sleep(60)

if __name__ == "__main__":
    main()

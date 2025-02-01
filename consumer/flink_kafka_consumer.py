# consumer/flink_kafka_consumer.py
from pyflink.table import EnvironmentSettings, TableEnvironment

def main():
    # 스트리밍 모드 환경 설정
    env_settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    table_env = TableEnvironment.create(env_settings)

    # Kafka Source 테이블 생성 (Kafka Connector 사용)
    table_env.execute_sql("""
        CREATE TABLE news (
            title STRING,
            link STRING,
            summary STRING,
            published STRING
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'news',
            'properties.bootstrap.servers' = 'localhost:9092',
            'properties.group.id' = 'flink_consumer_group',
            'format' = 'json',
            'scan.startup.mode' = 'earliest-offset'
        )
    """)

    # Sink 테이블 생성 (여기서는 출력용 Print Connector 사용)
    table_env.execute_sql("""
        CREATE TABLE print_sink (
            title STRING,
            link STRING,
            summary STRING,
            published STRING
        ) WITH (
            'connector' = 'print'
        )
    """)

    # Kafka에서 읽은 데이터를 Print Sink로 전송
    table_env.execute_sql("""
        INSERT INTO print_sink
        SELECT * FROM news
    """)

if __name__ == '__main__':
    main()

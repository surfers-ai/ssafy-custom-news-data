# pip install kafka-python
from kafka import KafkaProducer
from kafka import KafkaConsumer

# 1) Producer 테스트
producer = KafkaProducer(bootstrap_servers='localhost:9092')
producer.send('news', b'test-message')
producer.flush()

# 2) Consumer 테스트
consumer = KafkaConsumer('news', bootstrap_servers='localhost:9092', auto_offset_reset='earliest')
for msg in consumer:
    print(msg)
    break

import json
import time
from hdfs import InsecureClient
from datetime import datetime

# HDFS 클라이언트 설정 (URL과 HDFS 경로를 본인 환경에 맞게 수정)
hdfs_client = InsecureClient('http://localhost:9870', user='hadoop-user')  # 'localhost'와 'hadoop-user' 부분을 환경에 맞게 수정하세요.
hdfs_path = '/user/jiwoochris/'  # HDFS 내 데이터 저장 경로

# 샘플 데이터 (title, content, write_date)
def generate_sample_data():
    return {
        "title": "Sample News Title",
        "content": "This is a sample content of the news article.",
        "write_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

# 데이터 전송 루프
try:
    while True:
        data = generate_sample_data()
        json_data = json.dumps(data)
        
        # HDFS에 저장될 파일명 지정
        file_name = f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 데이터 HDFS에 저장
        with hdfs_client.write(hdfs_path + file_name, encoding='utf-8') as writer:
            writer.write(json_data)
        
        print(f"Data sent to HDFS: {data}")
        
        # 5초 대기
        time.sleep(5)

except KeyboardInterrupt:
    print("Data sending stopped.")

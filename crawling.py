import json
import random
import time
from hdfs import InsecureClient
from datetime import datetime
import os
import json
import time

# HDFS 클라이언트 설정 (URL과 HDFS 경로를 본인 환경에 맞게 수정)
hdfs_client = InsecureClient('http://localhost:9870', user='hadoop-user')  # 'localhost'와 'hadoop-user' 부분을 환경에 맞게 수정하세요.
hdfs_path = '/user/news/realtime/'  # HDFS 내 데이터 저장 경로

# 데이터 소스 경로
base_directory = 'training_raw_data'

def load_json_files_and_merge(base_directory, max_files_per_category=10):
    """
    데이터 소스 경로에 있는 모든 JSON 파일을 읽어와서 하나의 리스트로 병합
    """
    all_data = []

    for category in os.listdir(base_directory):
        category_path = os.path.join(base_directory, category)
        
        if os.path.isdir(category_path):
            print(f"카테고리 처리 중: {category}")
            file_count = 0
            for json_file in os.listdir(category_path):
                if json_file.endswith('.json') and file_count < max_files_per_category:
                    file_path = os.path.join(category_path, json_file)
                    
                    with open(file_path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        
                        if 'SJML' in data and 'text' in data['SJML']:
                            for text_item in data['SJML']['text']:
                                text_item['category'] = category
                                all_data.append(text_item)
                    
                    file_count += 1
                
                if file_count >= max_files_per_category:
                    break
    
    return all_data

# 데이터 로드 및 병합 (이 부분을 크롤링으로 대체해도 좋습니다)
merged_data_list = load_json_files_and_merge(base_directory, 1)

# 랜덤으로 데이터 추출
data_list = random.sample(merged_data_list, 200)

# 처리된 데이터 개수 출력
print(f"총 {len(data_list)}개의 뉴스 데이터를 처리합니다.")

# 모든 데이터를 순회하며 1초마다 전송
for data in data_list:
    # 데이터를 JSON 형식으로 변환
    json_data = json.dumps(data, ensure_ascii=False)
    
    # HDFS에 저장될 파일명 생성 
    file_name = f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # HDFS에 데이터 저장
    with hdfs_client.write(hdfs_path + file_name, encoding='utf-8') as writer:
        writer.write(json_data)
    
    # 저장된 파일 경로 출력
    print(f"Data sent to HDFS: {hdfs_path + file_name}")
    
    # 1초 대기 (데이터 전송 간격)
    time.sleep(1)
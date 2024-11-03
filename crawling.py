import json
import time
from hdfs import InsecureClient
from datetime import datetime
import os
import json

# HDFS 클라이언트 설정 (URL과 HDFS 경로를 본인 환경에 맞게 수정)
hdfs_client = InsecureClient('http://localhost:9870', user='hadoop-user')  # 'localhost'와 'hadoop-user' 부분을 환경에 맞게 수정하세요.
hdfs_path = '/user/jiwoochris/realtime/'  # HDFS 내 데이터 저장 경로

def load_json_files_and_merge(base_directory, max_files_per_category=10):
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

base_directory = 'training_raw_data'

data_list = load_json_files_and_merge(base_directory, 1)

print(len(data_list))


import time

# 모든 데이터를 순회하며 1초마다 전송
for data in data_list:
    # 데이터를 JSON 형식으로 변환
    json_data = json.dumps(data, ensure_ascii=False)
    
    # HDFS에 저장될 파일명 생성 
    file_name = f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # HDFS에 데이터 저장
    with hdfs_client.write(hdfs_path + file_name, encoding='utf-8') as writer:
        writer.write(json_data)
        
    print(f"Data sent to HDFS: {json_data}")
    
    # 1초 대기
    time.sleep(1)


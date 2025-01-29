from openai import OpenAI
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

def transform_extract_keywords(text):
    """
    (이 부분 자체 모델 학습 시켜 대체 가능)
    텍스트 데이터 변환 - 키워드 추출
    입력 텍스트에서 핵심 키워드를 추출하는 변환 로직
    """
    text = preprocess_content(text)

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 텍스트에서 주요 키워드를 추출하는 전문가입니다. 다음 텍스트에서 가장 중요한 5개의 키워드를 추출해주세요. 키워드는 쉼표로 구분하여 반환해주세요"},
            {"role": "user", "content": text}
        ],
        max_tokens=100
    )
    keywords = response.choices[0].message.content.strip()
    return keywords.split(',')

def transform_to_embedding(text: str) -> list[float]:
    """
    (이 부분 자체 모델 학습 시켜 대체 가능)
    텍스트 데이터 변환 - 벡터 임베딩
    텍스트를 수치형 벡터로 변환하는 변환 로직
    """
    text = preprocess_content(text)

    client = OpenAI()
    response = client.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding

def transform_classify_category(content):
    """
    (이 부분 자체 모델 학습 시켜 대체 가능)
    텍스트 데이터 변환 - 카테고리 분류
    뉴스 내용을 기반으로 적절한 카테고리로 분류하는 변환 로직
    """
    content = preprocess_content(content)
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 뉴스 기사의 카테고리를 분류하는 어시스턴트입니다. No verbose. 카테고리는 [\"IT_과학\", \"건강\", \"경제\", \"교육\", \"국제\", \"라이프스타일\", \"문화\", \"사건사고\", \"사회일반\", \"산업\", \"스포츠\", \"여성복지\", \"여행레저\", \"연예\", \"정치\", \"지역\", \"취미\"] 중 하나입니다. 이외의 카테고리는 없습니다."},
            {"role": "user", "content": content}
        ]
    )
    model_output = response.choices[0].message.content.strip()

    if "카테고리:" in model_output:
        model_output = model_output.split("카테고리:")[1].strip()
    model_output = model_output.replace('"', '').replace("'", "").strip()

    return model_output

def preprocess_content(content):
    """
    데이터 전처리 - 텍스트 길이 제한
    토큰 수를 제한하여 처리 효율성 확보
    """
    import tiktoken
    
    if not content:
        return ""
        
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(content)
    
    if len(tokens) > 5000:
        truncated_tokens = tokens[:5000]
        return encoding.decode(truncated_tokens)
    
    return content


import pandas as pd

# # CSV 파일 로드
# df = pd.read_csv("ssafy_dataset_news_2024_1st_half.csv", sep="|")

# # 700개 랜덤 추출
# df_sampled = df.sample(n=700, random_state=42)

# # 추출된 데이터 저장
# df_sampled.to_csv("ssafy_dataset_news_2024_1st_half_sampled.csv", sep="|", index=False)

# exit()

# CSV 파일 로드
df = pd.read_csv("ssafy_dataset_news_2024_1st_half_sampled.csv", sep="|")

# 결측치 제거
df = df.dropna()

# 컬럼 이름 변경
df = df.rename(columns={
    'company': 'writer',
    'published': 'write_date',
    'article': 'content',
    'link': 'url'
})



# 행의 수 출력
print(f"총 행의 수: {len(df)}")
print(df.iloc[0])

from concurrent.futures import ThreadPoolExecutor

def process_content(content):
    category = transform_classify_category(content)
    keywords = transform_extract_keywords(content)
    embedding = transform_to_embedding(content)
    return category, keywords, embedding

with ThreadPoolExecutor() as executor:
    results = list(executor.map(process_content, df['content']))

df['category'], df['keywords'], df['embedding'] = zip(*results)


import time
import requests

end_point = "http://223.130.135.250:8000/write-article/"

def send_news_detail(news_data):
    url = end_point
    headers = {
        'Content-Type': 'application/json',
        'Cookie': 'csrftoken=nZ01FLkUwdxQ7HUoV5A9Mzm1Fe0ViOlu; my-app-auth=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzMwMDQxMDQ0LCJpYXQiOjE3Mjk5NTQ2NDQsImp0aSI6IjNkZWI4NTc2N2RjMTQyYTE5NmM4M2Q4NmRkMDUyYzM0IiwidXNlcl9pZCI6MX0.BiJc-9uQCB0SofAGT5JG7LjaXr2k5CclXP6Cnop7JEM; my-refresh-token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTczMDM4NjY0NCwiaWF0IjoxNzI5OTU0NjQ0LCJqdGkiOiJjNjZjNzYzYTk0ZDY0M2M2OGE2N2E1MTIzNTAwMWNiNiIsInVzZXJfaWQiOjF9.yQSgfgxIv7xMC7yzAjwUPdcThwS3oP34JMKGgwFPpWQ; sessionid=l2be4otm6hh9le9wovw8ckjxofc27chk'
    }
    
    response = requests.post(url, headers=headers, json=news_data)
    return response.text

# df를 이용하여 각 뉴스 데이터를 API로 전송
for index, row in df.iloc[1:].iterrows():
    news_data = {
        "title": row['title'],
        "writer": row['writer'],
        "write_date": row['write_date'],
        "category": row['category'],
        "content": row['content'],
        "url": row['url'],
        "keywords": row['keywords'],
        "embedding": row['embedding']
    }
    
    result = send_news_detail(news_data)
    print(f"뉴스 {index + 1} 전송 결과: {result}")
    time.sleep(1)

print("모든 뉴스 데이터 전송 완료")
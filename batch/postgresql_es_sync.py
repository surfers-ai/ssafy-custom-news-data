import psycopg2
from elasticsearch import Elasticsearch

# PostgreSQL 연결 설정
pg_conn = psycopg2.connect(
    host="localhost",
    database="news",
    user="ssafyuser",
    password="ssafyuser"
)

# Elasticsearch 연결 설정
es = Elasticsearch(["http://localhost:9200"])

# PostgreSQL에서 ID 목록 가져오기
pg_cursor = pg_conn.cursor()
pg_cursor.execute("SELECT id FROM mynews_article")
pg_ids = set(row[0] for row in pg_cursor.fetchall())

print("pg_ids: ", pg_ids)

# Elasticsearch에서 모든 문서 가져오기
es_docs = es.search(index="news", body={"query": {"match_all": {}}}, size=10000)

# PostgreSQL ID와 매칭되지 않는 Elasticsearch 문서 삭제
for hit in es_docs['hits']['hits']:
    [es_id, db_id] = [hit['_id'], hit['_source']['id']]
    if db_id not in pg_ids:
        print("delete es documnet id: ", es_id, "db id: ", db_id)
        es.delete(index="news", id=es_id)

# 연결 종료
pg_cursor.close()
pg_conn.close()
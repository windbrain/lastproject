# 이 파일은 MongoDB 연결을 설정하고 컬렉션 객체를 반환하는 유틸리티 모듈입니다.
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import certifi

load_dotenv()
mongo_uri = os.getenv("MONGO_URI") 

def get_mongo_collections():
    if not mongo_uri:
        return None, None
    # SSL/TLS 설정 강화: tls=True, 인증서 검증 무시 -> certifi 사용으로 변경
    # Windows 환경에서 SSL 인증서 오류 해결을 위해 certifi.where() 사용
    client = MongoClient(mongo_uri, tls=True, tlsCAFile=certifi.where())
    db = client["chat_db"]
    return db["login_logs"], db["chat_messages"]

def save_message_to_mongo(collection, role, content):
    if collection is not None:
        collection.insert_one({
            "role": role,
            "content": content
        })
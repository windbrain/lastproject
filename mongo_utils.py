# 이 파일은 MongoDB 연결을 설정하고 컬렉션 객체를 반환하는 유틸리티 모듈입니다.
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI") 

def get_mongo_collections():
    # 임시로 SSL 인증서 검증을 건너뛰도록 설정 (tlsAllowInvalidCertificates=True)
    if not mongo_uri:
        return None, None
    client = MongoClient(mongo_uri, tlsAllowInvalidCertificates=True)
    db = client["chat_db"]
    return db["login_logs"], db["chat_messages"]

def save_message_to_mongo(collection, role, content):
    if collection is not None:
        collection.insert_one({
            "role": role,
            "content": content
        })
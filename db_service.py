# 이 파일은 MongoDB에 사용자 로그인 정보와 채팅 로그를 저장하는 모듈입니다.
from datetime import datetime

def log_user_login(collection, user_info):
    collection.insert_one({
        "email": user_info["email"],
        "name": user_info["name"],
        "provider": "google",
        "login_time": datetime.now()
    })

def log_chat_message(collection, role, content, user_info):
    collection.insert_one({
        "role": role,
        "content": content,
        "email": user_info.get("email", "anonymous"),
        "name": user_info.get("name", "익명"),
        "timestamp": datetime.now()
    })

def get_chat_history(collection, user_email, limit=50):
    """
    특정 이메일의 최근 채팅 기록을 가져옵니다.
    """
    # 시간순 정렬 (오래된 것부터)
    cursor = collection.find({"email": user_email}).sort("timestamp", 1).limit(limit)
    
    messages = []
    for doc in cursor:
        messages.append({
            "role": doc["role"],
            "content": doc["content"]
        })
    return messages

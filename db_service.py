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
    # 시간순 정렬 (최신순으로 가져와서 다시 뒤집기)
    cursor = collection.find({"email": user_email}).sort("timestamp", -1).limit(limit)
    
    messages = []
    for doc in cursor:
        messages.append({
            "role": doc["role"],
            "content": doc["content"]
        })
    
    # 최신순으로 가져왔으므로 다시 시간순(과거->현재)으로 정렬
    return messages[::-1]

def create_chat_session(collection, user_email, title=None):
    """
    새로운 채팅 세션을 생성합니다.
    """
    if not title:
        title = "새로운 대화"
        
    session = {
        "type": "session",
        "email": user_email,
        "title": title,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    result = collection.insert_one(session)
    return str(result.inserted_id)

def get_user_sessions(collection, user_email, limit=20):
    """
    사용자의 채팅 세션 목록을 가져옵니다.
    """
    # type: "session" 인 것만 조회
    cursor = collection.find({"email": user_email, "type": "session"}).sort("updated_at", -1).limit(limit)
    sessions = []
    for doc in cursor:
        sessions.append({
            "id": str(doc["_id"]),
            "title": doc.get("title", "새로운 대화"),
            "created_at": doc["created_at"]
        })
    return sessions

def get_session_messages(collection, session_id):
    """
    특정 세션의 메시지들을 가져옵니다.
    """
    # session_id가 있는 메시지 검색
    cursor = collection.find({"session_id": session_id}).sort("timestamp", 1)
    
    messages = []
    for doc in cursor:
        messages.append({
            "role": doc["role"],
            "content": doc["content"]
        })
    return messages

def update_session_title(collection, session_id, title):
    """
    세션 제목을 업데이트합니다.
    """
    from bson.objectid import ObjectId
    collection.update_one(
        {"_id": ObjectId(session_id)},
        {"$set": {"title": title}}
    )

def log_chat_message(collection, role, content, user_info, session_id=None):
    doc = {
        "type": "message",
        "role": role,
        "content": content,
        "email": user_info.get("email", "anonymous"),
        "name": user_info.get("name", "익명"),
        "timestamp": datetime.now()
    }
    if session_id:
        doc["session_id"] = session_id

    collection.insert_one(doc)
    
    # 세션 업데이트 로직
    if session_id:
        from bson.objectid import ObjectId
        # 세션 문서 찾아서 updated_at 갱신
        collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"updated_at": datetime.now()}}
        )

def delete_chat_session(collection, session_id):
    """
    세션과 해당 세션의 모든 메시지를 삭제합니다.
    """
    from bson.objectid import ObjectId
    # 세션 삭제
    collection.delete_one({"_id": ObjectId(session_id)})
    # 해당 세션의 메시지 삭제
    collection.delete_many({"session_id": session_id})

def create_login_token(collection, user_info):
    """
    로그인 토큰을 생성하고 저장합니다.
    """
    import secrets
    from datetime import timedelta
    
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=1) # 1일 유효
    
    doc = {
        "type": "login_token",
        "token": token,
        "email": user_info["email"],
        "name": user_info["name"],
        "created_at": datetime.now(),
        "expires_at": expires_at
    }
    collection.insert_one(doc)
    return token

def validate_login_token(collection, token):
    """
    토큰을 검증하고 유효하면 사용자 정보를 반환합니다.
    """
    doc = collection.find_one({
        "type": "login_token",
        "token": token,
        "expires_at": {"$gt": datetime.now()}
    })
    
    if doc:
        return {
            "email": doc["email"],
            "name": doc["name"]
        }
    return None

def delete_login_token(collection, token):
    """
    로그인 토큰을 삭제합니다.
    """
    collection.delete_one({"type": "login_token", "token": token})

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
    cursor = collection.find({"email": user_email}).sort("timestamp", -1).limit(limit)
    
    messages = []
    for doc in cursor:
        messages.append({
            "role": doc["role"],
            "content": doc["content"]
        })
    
    return messages[::-1]

def create_chat_session(collection, user_email, title=None):
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
    cursor = collection.find({"session_id": session_id}).sort("timestamp", 1)
    
    messages = []
    for doc in cursor:
        messages.append({
            "role": doc["role"],
            "content": doc["content"]
        })
    return messages

def update_session_title(collection, session_id, title):
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
    
    if session_id:
        from bson.objectid import ObjectId
        collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"updated_at": datetime.now()}}
        )

def delete_chat_session(collection, session_id):
    from bson.objectid import ObjectId
    collection.delete_one({"_id": ObjectId(session_id)})
    collection.delete_many({"session_id": session_id})

def create_login_token(collection, user_info):
    import secrets
    from datetime import timedelta
    
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=1)
    
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
    collection.delete_one({"type": "login_token", "token": token})

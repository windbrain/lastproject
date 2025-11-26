from datetime import datetime
from mongo_utils import get_mongo_collection

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

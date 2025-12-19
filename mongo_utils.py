from pymongo import MongoClient
import os
from dotenv import load_dotenv
import certifi
import platform

load_dotenv()
mongo_uri = os.getenv("MONGO_URI") 

def get_mongo_collections():
    if not mongo_uri:
        return None, None
    
    if platform.system() == "Windows":
        client = MongoClient(mongo_uri, tls=True, tlsCAFile=certifi.where())
    else:
        client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=True)

    db = client["chat_db"]
    return db["login_logs"], db["chat_messages"]

def save_message_to_mongo(collection, role, content):
    if collection is not None:
        collection.insert_one({
            "role": role,
            "content": content
        })
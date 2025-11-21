from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI") 

def get_mongo_collection():
    client = MongoClient(mongo_uri)
    db = client["chat_db"]
    collection = db["messages"]
    return collection

def save_message_to_mongo(collection, role, content):
    collection.insert_one({
        "role": role,
        "content": content
    })
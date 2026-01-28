import certifi
from pymongo import MongoClient
from config import settings

client = MongoClient(
    settings.MONGODB_URL,
    tls=True,
    tlsCAFile=certifi.where()
)

db = client["workspace_ai"]

users_collection = db["users"]
messages_collection = db["messages"]
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "call_quality_db")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is missing in .env file")

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000
)

database = client[DATABASE_NAME]


def check_database_connection():
    client.admin.command("ping")
    return True


def get_database():
    return database

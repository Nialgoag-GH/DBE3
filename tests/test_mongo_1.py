from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

try:
    client.admin.command("ping")
    print("Connected to MongoDB!")
except Exception as e:
    print("Connection failed:")
    print(e)

    
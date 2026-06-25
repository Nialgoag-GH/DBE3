from pymongo import MongoClient
from pprint import pprint

client = MongoClient("mongodb://localhost:27017")

db = client["prueba3"]

print("=== Invitados ===")
for doc in db["invitados"].find():
    pprint(doc)

input('waitput')

print("\n=== Eventos ===")
for doc in db["eventos"].find():
    pprint(doc)
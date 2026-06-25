from pymongo import MongoClient

# Conectamos al servidor local
client = MongoClient("mongodb://localhost:27017/")

print("=== DIAGNÓSTICO DE MONGODB ===")
print("Bases de datos existentes:", client.list_database_names())

# Intentamos entrar a prueba3
db = client["prueba3"]
colecciones = db.list_collection_names()
print(f"\nColecciones dentro de 'prueba3': {colecciones}")

for col in colecciones:
    cantidad = db[col].count_documents({})
    print(f" -> La colección '{col}' tiene {cantidad} documentos.")
    
    # Si hay datos, mostramos cómo se llaman las columnas realmente
    if cantidad > 0:
        ejemplo = db[col].find_one({}, {"_id": 0})
        print(f"    Columnas detectadas: {list(ejemplo.keys())}")
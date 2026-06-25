import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

# ==========================================
# CONEXIÓN Y DETECCIÓN AUTOMÁTICA INFALIBLE
# ==========================================
DB_NAME = "prueba3" #nombre de la base de datos, debe ser igual al nombre de la base de datos que se creo en MongoDB

def conectar_base_datos():
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")  # direccion de la base de datos de MongoBD
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client[DB_NAME]
        
        # MAGIA: Buscar las colecciones que REALMENTE tienen datos
        colecciones_existentes = db.list_collection_names()
        col_eventos = ""
        col_invitados = ""
        
        for c in colecciones_existentes:
            cantidad = db[c].count_documents({})
            if cantidad > 0:  # Solo tomamos las que no están vacías
                if "evento" in c.lower():
                    col_eventos = c
                elif "invitado" in c.lower():
                    col_invitados = c
                    
        if not col_eventos or not col_invitados:
            print("\n[ERROR CRÍTICO] La base de datos no tiene colecciones válidas con datos.")
            print(f"Colecciones detectadas: {colecciones_existentes}")
            sys.exit(1)
            
        print(f"\n[SISTEMA OK] Conectado a '{col_eventos}' y '{col_invitados}' automáticamente.")
        return client, db, col_eventos, col_invitados
        
    except ConnectionFailure:
        print("\n[ERROR] No se pudo conectar a MongoDB.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR INESPERADO] {e}")
        sys.exit(1)

# ==========================================
# FUNCIONALIDADES
# ==========================================

def listar_eventos(db, col_eventos):
    print(f"\n=== LISTADO DE EVENTOS ===")
    try:
        eventos = db[col_eventos].find({}, {"_id": 0, "codigo": 1, "nombre": 1, "fecha": 1, "lugar": 1, "categoria": 1})
        cuenta = 0
        for ev in eventos:
            cuenta += 1
            print(f"\nCódigo:    {ev.get('codigo', 'N/A')}")
            print(f"Nombre:    {ev.get('nombre', 'N/A')}")
            print(f"Fecha:     {ev.get('fecha', 'N/A')}")
            print(f"Lugar:     {ev.get('lugar', 'N/A')}")
            print(f"Categoría: {ev.get('categoria', 'N/A')}")
            print("-" * 30)
            
        if cuenta == 0:
            print(f"No se encontraron registros.")
            input('Presione Enter para continuar...')
    except PyMongoError as e:
        input('Presione Enter para continuar...')
        print(f"[ERROR] {e}")

def buscar_invitados_regex(db, col_invitados):
    print(f"\n=== BUSCAR INVITADOS (REGEX) ===")
    termino = input("Ingrese nombre o correo a buscar: ").strip()
    if not termino:
        return
    try:
        query = {
            "$or": [
                {"nombre": {"$regex": termino, "$options": "i"}},
                {"correo": {"$regex": termino, "$options": "i"}}
            ]
        }
        invitados = db[col_invitados].find(query, {"_id": 0, "nombre": 1, "correo": 1, "estado": 1, "empresa": 1})
        cuenta = 0
        for inv in invitados:
            cuenta += 1
            print(f"- {inv.get('nombre', 'N/A')} ({inv.get('correo', 'N/A')}) | Empresa: {inv.get('empresa', 'N/A')} | Estado: {inv.get('estado', 'N/A')}")
            input('Presione Enter para continuar...')
        if cuenta == 0:
            input('Presione Enter para continuar...')
            print("No se encontraron invitados.")
    except PyMongoError as e:
        print(f"[ERROR] {e}")

def validar_acceso_evento(db, col_eventos, col_invitados):
    print("\n=== VALIDACIÓN DE ACCESO ===")
    correo = input("Ingrese el correo del invitado (ej: ana.martinez@empresa.cl): ").strip()
    codigo_evento = input("Ingrese el código del evento (ej: EVT-2025-001): ").strip()
    
    try:
        pipeline = [
            {"$match": {"correo": {"$regex": f"^{correo}$", "$options": "i"}, "estado": "activo"}},
            {
                "$lookup": {
                    "from": col_eventos,       
                    "localField": "rut",         
                    "foreignField": "invitados.rut",             
                    "as": "evento_info"
                }
            },
            {"$unwind": "$evento_info"},
            {"$match": {"evento_info.codigo": codigo_evento}},
            {"$unwind": "$evento_info.invitados"},
            {"$match": {"evento_info.invitados.rut": "$rut"}}
        ]
        
        resultado = list(db[col_invitados].aggregate(pipeline))
        
        if resultado:
            invitado = resultado[0]
            nombre_usuario = invitado.get("nombre")
            estado_en_evento = invitado["evento_info"]["invitados"].get("estado", "pendiente")
            
            if estado_en_evento == "confirmado":
                print(f"\n[ACCESO PERMITIDO] El invitado '{nombre_usuario}' está CONFIRMADO para este evento.")
                input('Presione Enter para continuar...')
            else:
                print(f"\n[ACCESO DENEGADO] El invitado existe, pero su estado en el evento es: '{estado_en_evento.upper()}'.")
                input('Presione Enter para continuar...')
        else:
            print("\n[ACCESO DENEGADO] No se encontró un invitado activo con ese correo asociado a dicho código de evento.")
            input('Presione Enter para continuar...')
    except PyMongoError as e:
        print(f"[ERROR] {e}")

def top_eventos_confirmados(db, col_eventos):
    print("\n=== TOP 3 EVENTOS CON MÁS CONFIRMADOS ===")
    try:
        pipeline = [
            {"$unwind": "$invitados"},
            {"$match": {"invitados.estado": "confirmado"}},
            {
                "$group": {
                    "_id": {"codigo": "$codigo", "nombre": "$nombre"},
                    "total_confirmados": {"$sum": 1}
                }
            },
            {"$sort": {"total_confirmados": -1}},
            {"$limit": 3}
        ]
        resultados = db[col_eventos].aggregate(pipeline)
        cuenta = 0
        for idx, ev in enumerate(resultados, 1):
            cuenta += 1
            info_evento = ev.get("_id", {})
            print(f"{idx}. Evento: {info_evento.get('nombre')} (Cód: {info_evento.get('codigo')}) - Confirmados: {ev.get('total_confirmados')}")
            input('Presione Enter para continuar...')
        if cuenta == 0:
            print("No hay eventos con asistentes confirmados.")
            input('Presione Enter para continuar...')
    except PyMongoError as e:
        print(f"[ERROR] {e}")

def menu():
    client, db, col_eventos, col_invitados = conectar_base_datos()
    try:
        while True:
            print("\n" + "="*40)
            print("     GESTOR DE EVENTOS E INVITADOS")
            print("="*40)
            print("1. Listar todos los eventos")
            print("2. Buscar invitados (Filtro Regex)")
            print("3. Validación de acceso ($lookup)")
            print("4. Ver Top 3 eventos")
            print("5. Salir")
            print("="*40)
            
            opcion = input("Seleccione una opción (1-5): ").strip()
            
            if opcion == "1":
                listar_eventos(db, col_eventos)
            elif opcion == "2":
                buscar_invitados_regex(db, col_invitados)
            elif opcion == "3":
                validar_acceso_evento(db, col_eventos, col_invitados)
            elif opcion == "4":
                top_eventos_confirmados(db, col_eventos)
            elif opcion == "5":
                print("\nSaliendo del sistema...")
                break
            else:
                print("\n[AVISO] Opción inválida.")
            input('Presione Enter para continuar...')
    except KeyboardInterrupt:
        print("\n\nCerrando...")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    menu()
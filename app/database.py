from motor.motor_asyncio import AsyncIOMotorClient

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_to_mongo(uri: str, db_name: str):
    # IMPORTANTE: Usar la uri que viene del .env
    db_instance.client = AsyncIOMotorClient(uri)
    db_instance.db = db_instance.client[db_name]
    print(f"✅ Conectado a MongoDB: {db_name}")

def get_db():
    # Esta función debe retornar el objeto db de la instancia global
    return db_instance.db

async def get_next_sequence_value(sequence_name: str):
    db = get_db()
    # Busca el contador, lo incrementa en 1 y lo devuelve
    result = await db.counters.find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=True
    )
    return result["sequence_value"]
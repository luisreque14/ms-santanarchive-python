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

async def setup_database_indexes(db: AsyncIOMotorClient):
    """
    Crea los índices necesarios para optimizar los pipelines del Executive Summary.
    """
    try:
        print("Ensuring MongoDB indexes...")

        # --- Colección: concert_songs ---
        await db.concert_songs.create_index("track_ids", background=True)
        await db.concert_songs.create_index([("song_number", 1), ("song_name", 1)], background=True)
        
        # --- Colección: concerts ---
        await db.concerts.create_index([("concert_year", -1)], background=True)
        await db.concerts.create_index("country_id", background=True)
        await db.concerts.create_index("concert_date", background=True)

        # --- Colección: tracks ---
        await db.tracks.create_index([("metadata.is_live", 1), ("id", 1)], background=True)
        await db.tracks.create_index("album_id", background=True)

        # --- Colección: tracks ---
        # Para _get_top_lead_singer y _get_general_track_stats
        await db.tracks.create_index("lead_vocal_ids", background=True)

        # Para get_total_guest_artists
        await db.tracks.create_index("guest_artist_ids", background=True)

        # Para get_total_by_composer
        await db.tracks.create_index("composer_ids", background=True)

        print("✅ All indexes ensured successfully.")
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
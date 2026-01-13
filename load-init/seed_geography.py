import asyncio
from app.database import connect_to_mongo, get_db, db_instance  # Importa db_instance


async def seed_continents():
    await connect_to_mongo()
    db = get_db()

    continents = [
        {"id": 1, "code": "AM", "name": "Americas"},
        {"id": 2, "code": "EU", "name": "Europe"},
        {"id": 3, "code": "AF", "name": "Africa"},
        {"id": 4, "code": "AS", "name": "Asia"},
        {"id": 5, "code": "OC", "name": "Oceania"}
    ]

    for continent in continents:
        result = await db.continents.update_one(
            {"id": continent["id"]},
            {"$set": continent},
            upsert=True
        )
        print(f"Procesando {continent['name']}: {result.modified_count} actualizados, {result.upserted_id} creados")

    # Cerramos la conexión manualmente al terminar
    db_instance.client.close()
    print("Conexión cerrada.")


if __name__ == "__main__":
    asyncio.run(seed_continents())
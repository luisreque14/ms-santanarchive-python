import asyncio
from scripts.common.db_utils import db_manager


async def seed_continents():
    db = await db_manager.connect()

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
    await db_manager.close()
    print("Conexión cerrada.")


if __name__ == "__main__":
    asyncio.run(seed_continents())
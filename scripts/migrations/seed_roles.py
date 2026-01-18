import asyncio
from dotenv import load_dotenv
from scripts.common.db_utils import db_manager

load_dotenv()


async def seed_roles():
    # 2. Conectar
    db = await db_manager.connect()

    # 3. Lista de roles basada en nuestra investigación previa
    roles_data = [
        {"id": 1, "name": "Guitar", "category": "Strings"},
        {"id": 2, "name": "Vocals", "category": "Vocals"},
        {"id": 3, "name": "Percussion", "category": "Percussion"},
        {"id": 4, "name": "Keyboards", "category": "Keys"},
        {"id": 5, "name": "Bass", "category": "Strings"},
        {"id": 6, "name": "Congas", "category": "Percussion"},
        {"id": 7, "name": "Drums", "category": "Percussion"},
        {"id": 8, "name": "Timbales", "category": "Percussion"},
        {"id": 9, "name": "Bongos", "category": "Percussion"},
        {"id": 10, "name": "Trumpet", "category": "Winds"},
        {"id": 11, "name": "Trombone", "category": "Winds"}
    ]

    print("🚀 Iniciando carga de roles...")

    stats = {"nuevos": 0, "actualizados": 0}

    for role in roles_data:
        # Usamos update_one con upsert para que sea seguro repetir el proceso
        result = await db.roles.update_one(
            {"id": role["id"]},
            {"$set": role},
            upsert=True
        )

        if result.upserted_id:
            stats["nuevos"] += 1
        else:
            stats["actualizados"] += 1

    print(f"\n✅ Proceso completado:")
    print(f"   - Roles creados: {stats['nuevos']}")
    print(f"   - Roles actualizados: {stats['actualizados']}")

    await db_manager.close()
    print("🔌 Conexión cerrada.")


if __name__ == "__main__":
    asyncio.run(seed_roles())
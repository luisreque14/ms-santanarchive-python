# python -m scripts.maintenance.fix_vocal_ids
import asyncio
from scripts.common.db_utils import db_manager

async def update_vocal_id():
    # 1. Conectar a la base de datos
    db = await db_manager.connect()
    
    old_id = 48
    new_id = 24

    print(f"🔄 Iniciando actualización: reemplazando ID {old_id} por {new_id} en tracks...")

    try:
        # 2. Ejecutar la actualización masiva
        # Usamos un pipeline de agregación dentro del update para transformar el array
        result = await db.tracks.update_many(
            {"lead_vocal_ids": old_id},  # Filtro: solo tracks que tengan el ID 48
            [
                {
                    "$set": {
                        "lead_vocal_ids": {
                            "$map": {
                                "input": "$lead_vocal_ids",
                                "as": "id",
                                "in": {
                                    "$cond": [
                                        {"$eq": ["$$id", old_id]}, 
                                        new_id, 
                                        "$$id"
                                    ]
                                }
                            }
                        }
                    }
                }
            ]
        )

        print(f"✅ Proceso completado.")
        print(f"📊 Tracks encontrados con el ID {old_id}: {result.matched_count}")
        print(f"📝 Tracks actualizados: {result.modified_count}")

    except Exception as e:
        print(f"❌ Error durante la actualización: {e}")
    
    finally:
        # 3. Cerrar conexión
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(update_vocal_id())
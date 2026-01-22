# python -m scripts.cleanup.cleanup_musicians_fields
import asyncio
from scripts.common.db_utils import db_manager

async def cleanup_musicians_fields():
    # 1. Conectar a la base de datos
    db = await db_manager.connect()
    
    print("🧹 Iniciando limpieza de campos en la colección 'musicians'...")

    # 2. Definir los campos a eliminar
    fields_to_remove = {
        "start_date": "",
        "end_date": "",
        "activeFrom": "",
        "activeTo": ""
    }

    try:
        # 3. Ejecutar update_many con $unset
        # El primer {} indica que se aplique a TODOS los documentos
        result = await db.musicians.update_many(
            {}, 
            {"$unset": fields_to_remove}
        )

        print(f"✅ Limpieza completada.")
        print(f"📊 Documentos analizados: {result.matched_count}")
        print(f"🗑️ Documentos modificados: {result.modified_count}")

    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")
    
    finally:
        # 4. Cerrar conexión
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(cleanup_musicians_fields())
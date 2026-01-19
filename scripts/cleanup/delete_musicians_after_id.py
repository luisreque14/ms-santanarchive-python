#python -m scripts.cleanup.delete_musicians_after_id
import asyncio
from scripts.common.db_utils import db_manager

async def delete_musicians_high_id(threshold: int):
    # 1. Conexión a la base de datos
    db = await db_manager.connect()
    
    try:
        # Filtro: id numérico mayor a 45
        query = {"id": {"$gt": threshold}}
        
        # 2. Contar registros afectados
        count = await db.musicians.count_documents(query)
        
        if count == 0:
            print(f"ℹ️ No se encontraron músicos con ID mayor a {threshold}.")
            return

        print(f"⚠️ Se han encontrado {count} músicos con ID > {threshold}.")
        confirm = input(f"¿Estás seguro de que deseas ELIMINAR estos {count} músicos de la colección 'musicians'? (s/n): ")
        
        if confirm.lower() == 's':
            # 3. Ejecutar la eliminación masiva
            result = await db.musicians.delete_many(query)
            print(f"✅ Éxito: Se han eliminado {result.deleted_count} músicos.")
        else:
            print("❌ Operación cancelada.")

    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")
    finally:
        await db_manager.close()

if __name__ == "__main__":
    # Umbral de 45 según tu corrección
    asyncio.run(delete_musicians_high_id(100045))
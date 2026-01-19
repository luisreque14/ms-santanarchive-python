#python -m scripts.cleanup.clean_tracks_attributes

import asyncio
from scripts.common.db_utils import db_manager

async def remove_attributes():
    # 1. Conexión a la base de datos
    db = await db_manager.connect()
    
    # 2. Definir los atributos a eliminar
    attributes_to_remove = {
        "lead_vocal_ids": "",
        #"release_date": "",
        "guests_lead_vocal_ids": ""
    }
    
    # Confirmación de seguridad
    print("⚠️  PREPARANDO LIMPIEZA DE ATRIBUTOS")
    print(f"Se eliminarán: {list(attributes_to_remove.keys())} de TODA la colección Tracks.")
    
    # 3. Ejecutar el $unset
    # El operador $unset elimina el campo por completo del documento
    try:
        result = await db.tracks.update_many(
            {}, # Filtro vacío para afectar a todos los documentos
            {"$unset": attributes_to_remove}
        )
        
        print(f"\n✅ PROCESO COMPLETADO")
        print(f"🔎 Tracks encontrados: {result.matched_count}")
        print(f"🗑️  Tracks modificados: {result.modified_count}")
        
    except Exception as e:
        print(f"❌ Error durante la eliminación: {e}")
    finally:
        await db_manager.close()

if __name__ == "__main__":
    # Usamos un pequeño delay o confirmación manual por seguridad
    confirm = input("¿Estás seguro de eliminar estos campos en MongoDB Cloud? (y/n): ")
    if confirm.lower() == 'y':
        asyncio.run(remove_attributes())
    else:
        print("Operación cancelada.")
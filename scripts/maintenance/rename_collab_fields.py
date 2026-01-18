import asyncio
from scripts.common.db_utils import db_manager

async def run_migration():
    db = await db_manager.connect()
    
    # En Motor (Python), la sintaxis es igual a la de Atlas
    result = await db.tracks.update_many(
        {}, 
        {"$rename": {"collaborator_ids": "guest_artist_ids"}}
    )
    
    print(f"✅ Proceso completado.")
    print(f"🔎 Documentos encontrados: {result.matched_count}")
    print(f"✏️  Documentos modificados: {result.modified_count}")
    
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
# python -m scripts.check_data.check_orphaned_lead_vocals
import asyncio
from scripts.common.db_utils import db_manager

async def check_orphaned_lead_vocals():
    db = await db_manager.connect()
    
    print("🔍 Iniciando validación de IDs entre tracks y musicians...")

    try:
        # 1. Obtener todos los IDs únicos presentes en tracks.lead_vocal_ids
        pipeline = [
            {"$unwind": "$lead_vocal_ids"},
            {"$group": {"_id": None, "unique_ids": {"$addToSet": "$lead_vocal_ids"}}}
        ]
        
        cursor = db.tracks.aggregate(pipeline)
        tracks_result = await cursor.to_list(length=1)
        
        if not tracks_result:
            print("ℹ️ No se encontraron lead_vocal_ids en la colección tracks.")
            return

        ids_in_tracks = set(tracks_result[0]["unique_ids"])
        print(f"📡 IDs únicos encontrados en tracks: {len(ids_in_tracks)}")

        # 2. Obtener todos los IDs existentes en la colección musicians
        musicians_cursor = db.musicians.find({}, {"id": 1, "_id": 0})
        ids_in_musicians = {m["id"] async for m in musicians_cursor if "id" in m}
        print(f"🎸 IDs existentes en musicians: {len(ids_in_musicians)}")

        # 3. Encontrar la diferencia (IDs en tracks que no están en musicians)
        orphaned_ids = ids_in_tracks - ids_in_musicians

        if not orphaned_ids:
            print("✅ ¡Integridad perfecta! Todos los vocalistas existen en la colección musicians.")
        else:
            print(f"❌ Se encontraron {len(orphaned_ids)} IDs huérfanos (no existen en musicians):")
            print(sorted(list(orphaned_ids)))
            
            # Opcional: Mostrar qué tracks tienen estos IDs
            print("\n📋 Ejemplo de tracks afectados:")
            sample_tracks = db.tracks.find(
                {"lead_vocal_ids": {"$in": list(orphaned_ids)}},
                {"title": 1, "lead_vocal_ids": 1, "_id": 0}
            ).limit(5)
            
            async for track in sample_tracks:
                print(f"- Track: '{track['title']}' | IDs: {track['lead_vocal_ids']}")

    except Exception as e:
        print(f"❌ Error durante la validación: {e}")
    
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(check_orphaned_lead_vocals())
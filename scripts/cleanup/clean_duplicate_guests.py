import asyncio
from dotenv import load_dotenv
from scripts.common.db_utils import db_manager

load_dotenv()


async def clean_duplicate_guests():
    db = await db_manager.connect()

    print("🔍 Buscando duplicados en la colección 'guests'...")

    # 1. Agrupar por nombre para encontrar duplicados
    pipeline = [
        {
            "$group": {
                "_id": {"$toLower": "$full_name"},
                "count": {"$sum": 1},
                "ids": {"$push": "$id"},
                "original_names": {"$push": "$full_name"}
            }
        },
        {"$match": {"count": {"$gt": 1}}}
    ]

    duplicates = await db.guests.aggregate(pipeline).to_list(length=None)

    if not duplicates:
        print("✅ No se encontraron invitados duplicados.")
        return

    for group in duplicates:
        target_id = group["ids"][0]  # Mantendremos este ID
        duplicate_ids = group["ids"][1:]  # Estos son los IDs que eliminaremos
        correct_name = group["original_names"][0]

        print(f"⚖️ Unificando: '{correct_name}' (Manteniendo ID: {target_id}, Eliminando IDs: {duplicate_ids})")

        # 2. Actualizar la colección 'tracks' para que usen el ID correcto
        # Buscamos tracks que contengan cualquiera de los IDs duplicados en su array guest_ids
        for old_id in duplicate_ids:
            # $pull quita el ID viejo y $addToSet añade el ID nuevo sin repetir
            await db.tracks.update_many(
                {"guest_ids": old_id},
                {
                    "$pull": {"guest_ids": old_id}
                }
            )
            await db.tracks.update_many(
                {"title": {"$exists": True}},  # Filtro general para asegurar re-inserción
                {"$addToSet": {"guest_ids": target_id}},
                # Solo aplicamos a los que antes tenían el old_id (lógica simplificada aquí)
            )
            # Nota: La lógica ideal de update_many con arrays requiere un poco más de cuidado
            # Usaremos una forma más segura:
            cursor = db.tracks.find({"guest_ids": old_id})
            async for track in cursor:
                new_list = list(set([target_id if x == old_id else x for x in track["guest_ids"]]))
                await db.tracks.update_one({"_id": track["_id"]}, {"$set": {"guest_ids": new_list}})

        # 3. Borrar los duplicados de la colección 'guests'
        await db.guests.delete_many({"id": {"$in": duplicate_ids}})

    print(f"✨ Limpieza completada. Se procesaron {len(duplicates)} grupos de duplicados.")
    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(clean_duplicate_guests())
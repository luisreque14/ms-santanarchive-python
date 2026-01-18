import pandas as pd
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import re
from scripts.common.db_utils import db_manager

async def get_next_sequence_value(db, sequence_name):
    """Genera IDs incrementales para la colección guest_artists"""
    result = await db.counters.find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=True
    )
    return result["sequence_value"]

async def get_or_create_guest_artist(db, full_name: str):
    """Busca un colaborador o lo crea si no existe (Case Insensitive)"""
    name_clean = full_name.strip()
    if not name_clean: return None

    # Buscar existente en la colección 'guest_artists'
    guest_artist = await db.guest_artists.find_one({"full_name": {"$regex": f"^{name_clean}$", "$options": "i"}})

    if guest_artist:
        return guest_artist["id"]

    # Crear nuevo colaborador
    new_id = await get_next_sequence_value(db, "guest_artist_id")
    await db.guest_artists.insert_one({"id": new_id, "full_name": name_clean})
    print(f"🆕 Colaborador Creado: {name_clean} (ID: {new_id})")
    return new_id

async def process_excel_to_mongo(file_path: str):
    db = await db_manager.connect()
    # Leer Excel
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()

    print(f"🚀 Procesando {len(df)} filas...")

    for _, row in df.iterrows():
        song_title = str(row['Canción']).strip()
        album_name = str(row['Album']).strip()
        guest_artist_str = str(row['Colaboradores']).strip()

        guest_artist_ids = []

        song_escaped = re.escape(song_title)
        album_escaped = re.escape(album_name)

        # 1. Obtener ID del álbum (necesario para identificar la canción correcta)

        album_doc = await db.albums.find_one({
            "title": {"$regex": f"^{album_escaped}$", "$options": "i"}
        })

        if album_doc:
            await db.tracks.update_one(
                {
                    "title": {"$regex": f"^{song_escaped}$", "$options": "i"},
                    "album_id": album_doc["id"]
                },
                {"$set": {"guest_artist_ids": guest_artist_ids}}
            )

        # 2. Verificar si hay colaboradores en el Excel
        if guest_artist_str.lower() not in ['nan', '', 'none']:
            # Procesar colaboradores uno por uno
            guest_artist_names = [n for n in guest_artist_str.split(',') if n.strip()]
            for name in guest_artist_names:
                cid = await get_or_create_guest_artist(db, name)
                if cid:
                    guest_artist_ids.append(cid)

        # 3. Actualizar Track por Nombre e ID de Álbum
        # Siempre se actualizará 'guest_artist_ids', ya sea con IDs o como lista vacía []
        result = await db.tracks.update_one(
            {
                "title": {"$regex": f"^{song_title}$", "$options": "i"},
                "album_id": album_doc["id"]
            },
            {"$set": {"guest_artist_ids": guest_artist_ids}}
        )

        if result.modified_count > 0:
            status = f"con {len(guest_artist_ids)} IDs" if guest_artist_ids else "como lista vacía"
            print(f"✅ Track '{song_title}' actualizado {status}.")
        else:
            print(f"ℹ️ Track '{song_title}' no requirió cambios o no fue encontrado.")

    await db_manager.close()

if __name__ == "__main__":
    # Asegúrate de que el archivo Excel existe en la ruta
    asyncio.run(process_excel_to_mongo("update_santana_guests.xlsx"))
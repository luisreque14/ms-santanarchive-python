import asyncio
import os
import pandas as pd
from dotenv import load_dotenv
from app.database import connect_to_mongo, get_db, db_instance

load_dotenv()

async def sync_master_data(file_path: str):
    await connect_to_mongo(os.getenv("MONGODB_URL"), os.getenv("DB_NAME"))
    db = get_db()

    # 1. Mapas de referencia
    genre_map = {g["name"].lower().strip(): g["id"] for g in await db.genres.find().to_list(length=None)}
    composer_map = {c["full_name"].lower().strip(): c["id"] for c in await db.composers.find().to_list(length=None)}

    # 2. Leer Excel
    df = pd.read_excel(file_path)
    df.columns = [c.strip() for c in df.columns]

    print(f"🔄 Sincronizando {len(df)} filas...")
    stats = {"nuevos": 0, "actualizados": 0}

    for _, row in df.iterrows():
        album_name = str(row['Album']).strip()
        track_title = str(row['Canción']).strip()

        # --- A. OBTENER O CREAR ÁLBUM (Lógica de Upsert manual para el álbum) ---
        album = await db.albums.find_one({"title": album_name})
        if not album:
            last_album = await db.albums.find_one(sort=[("id", -1)])
            album_id = (last_album["id"] + 1) if last_album else 1
            await db.albums.insert_one({
                "id": album_id,
                "title": album_name,
                "release_year": int(row['Año Lanzamiento'])
            })
        else:
            album_id = album["id"]

        # --- B. PROCESAR GÉNEROS Y COMPOSITORES ---
        def get_ids(text, mapping):
            parts = [p.strip().lower() for p in str(text).replace('/', ',').replace(';', ',').split(',')]
            return [mapping[p] for p in parts if p in mapping]

        genre_ids = get_ids(row['Género'], genre_map)
        comp_ids = get_ids(row['Compositores'], composer_map)

        # --- C. PREPARAR DATOS DEL TRACK ---
        track_data = {
            "track_number": int(row['Nro Pista']) if pd.notna(row['Nro Pista']) else 0,
            "side": str(row['Lado']) if pd.notna(row['Lado']) else "N/A",
            "duration": str(row['Duración']),
            "genre_ids": genre_ids,
            "composer_ids": comp_ids,
            "metadata": {
                "key": str(row['Tono de la canción']),
                "is_instrumental": str(row['Es instrumental?']).strip().upper() == 'SÍ',
                "is_live": str(row['Canción en vivo?']).strip().upper() == 'SÍ',
                "is_love_song": str(row['Es canción de amor?']).strip().upper() == 'SÍ'
            }
        }

        # --- D. UPDATE_ONE CON UPSERT ---
        # Filtro: misma canción en el mismo álbum
        result = await db.tracks.update_one(
            {"title": track_title, "album_id": album_id},
            {"$set": track_data},
            upsert=True
        )

        if result.matched_count > 0:
            stats["actualizados"] += 1
        else:
            stats["nuevos"] += 1

    print(f"\n📊 Resumen de sincronización:")
    print(f"✨ Registros nuevos creados: {stats['nuevos']}")
    print(f"🆙 Registros existentes actualizados: {stats['actualizados']}")

    if db_instance.client:
        db_instance.client.close()

if __name__ == "__main__":
    asyncio.run(sync_master_data("../santana_master.xlsx"))
#Este script lee el archivo santana_master_v2 y SOLAMENTE CREA los tracks que no existen (incluido el álbum, en caso no exista).
#Además de crear el track, verifica si existe el género, compositor, vocalista principal/invitado y artista invitado. Si no existe, lo crea.
#Útil para agregar más tracks/álbumes a la BD. Para actualizar los datos del track, usar otro script.

# python -m scripts.maintenance.load_master_data

import asyncio
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from scripts.common.db_utils import db_manager

# Caché global
cache = {
    "genres": {},
    "composers": {},
    "guest_artists": {},
    "musicians": {},
    "albums": {}
}

def clean_str(value):
    return str(value).strip() if pd.notna(value) else ""

def to_bool(value):
    clean_val = clean_str(value).upper()
    return True if clean_val == "SI" else False

def format_cover_name(album_name):
    name_processed = album_name.lower().replace(" ", "-")
    return f"santana-{name_processed}.jpg"

async def get_next_sequence_value(db, counter_id):
    """Obtiene el siguiente ID atómico de la colección counters."""
    counter = await db.counters.find_one_and_update(
        {"_id": counter_id},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=True
    )
    return int(counter["sequence_value"])

async def preload_caches(db):
    """Carga TODO de una sola vez para evitar find_one durante el bucle."""
    print("⏳ Sincronizando maestros en memoria (Zero-DB-Query Mode)...")
    
    # Maestros estándar
    for coll in ["genres", "composers", "guest_artists", "albums", "tracks"]:
        field = "title" if coll in ["albums", "tracks"] else ("name" if coll == "genres" else "full_name")
        cursor = db[coll].find({}, {"id": 1, field: 1})
        async for doc in cursor:
            if doc.get(field):
                key = f"{doc[field].lower().strip()}"
                # Para tracks, la llave debe ser (titulo + album_id) para ser única
                if coll == "tracks":
                    key = f"{key}_{doc.get('album_id')}"
                cache[coll][key] = int(doc["id"])
    
    # Músicos (Especial: sin full_name)
    cursor = db.musicians.find({}, {"id": 1, "first_name": 1, "last_name": 1})
    async for doc in cursor:
        fname = doc.get("first_name", "").strip()
        lname = doc.get("last_name", "").strip()
        key = f"{fname} {lname}".strip().lower()
        if key:
            cache["musicians"][key] = int(doc["id"])

    print(f"🚀 Memoria lista: {sum(len(v) for v in cache.values())} registros cargados.")

async def get_next_id(db, collection_name):
    # Solo consultamos el ID más alto para autoincrementar
    last_doc = await db[collection_name].find_one(sort=[("id", -1)])
    return (int(last_doc["id"]) + 1) if last_doc else 1

async def get_or_create_id_with_status(db, collection, field, name):
    if not name or str(name).lower() == "nan": 
        return None, False
    
    name_clean = str(name).strip()
    name_key = name_clean.lower()
    
    # 1. BÚSQUEDA EXCLUSIVA EN CACHÉ (Súper rápido)
    if name_key in cache[collection]:
        return int(cache[collection][name_key]), False
    
    # 2. SI NO ESTÁ EN CACHÉ, ES NUEVO (Solo una inserción)
    new_id = await get_next_id(db, collection)
    if collection == "musicians":
        parts = name_clean.split()
        first_name = parts[0] if len(parts) > 0 else name_clean
        last_name = parts[-1] if len(parts) > 1 else ""
        await db.musicians.insert_one({
            "id": int(new_id),
            "first_name": first_name,
            "last_name": last_name
        })
    else:
        await db[collection].insert_one({"id": int(new_id), field: name_clean})
    
    # Actualizamos caché para no re-insertar si aparece de nuevo en el Excel
    cache[collection][name_key] = int(new_id)
    return int(new_id), True

async def process_list_with_logs(db, collection, field, raw_value, label):
    if not raw_value or pd.isna(raw_value):
        return [], []
    
    names = [n.strip() for n in re.split(r'[/,]', str(raw_value)) if n.strip()]
    ids, logs = [], []
    for name in names:
        id_found, is_new = await get_or_create_id_with_status(db, collection, field, name)
        if id_found is not None:
            ids.append(id_found)
            if is_new:
                logs.append(f"{label}: {name} ✅")
    return ids, logs

async def run_import():
    confirm = input("⚠️ ¿Ejecutar carga OPTIMIZADA (Cache Full)? (SI/NO): ")
    if confirm.upper() != "SI": return

    db = await db_manager.connect()
    file_path = Path(__file__).parent.parent / "data_sources" / "santana_master_v2.xlsx"

    try:
        await preload_caches(db)
        df = pd.read_excel(file_path, dtype={'Fecha lanzamiento': str})
        print(f"\n📈 Procesando {len(df)} filas...\n" + "—"*120)

        for index, row in df.iterrows():
            song_title = clean_str(row["Canción"])
            album_title = clean_str(row["Album"])
            
            # 1. Álbum (Caché)
            album_key = album_title.lower().strip()
            is_new_alb = False
            if album_key in cache["albums"]:
                curr_alb_id = cache["albums"][album_key]
            else:
                curr_alb_id = await get_next_id(db, "albums")
                await db.albums.insert_one({
                    "id": int(curr_alb_id), "title": album_title, "is_live": False,
                    "release_year": int(row["Año Lanzamiento"]) if pd.notna(row.get("Año Lanzamiento")) else None,
                    "cover": format_cover_name(album_title)
                })
                cache["albums"][album_key] = curr_alb_id
                is_new_alb = True

            # 2. Maestros (Caché + Inserción si no existen)
            c_ids, c_logs = await process_list_with_logs(db, "composers", "full_name", row.get("Compositores"), "Comp")
            g_ids, g_logs = await process_list_with_logs(db, "genres", "name", row.get("Género"), "Gen")
            inv_ids, inv_logs = await process_list_with_logs(db, "guest_artists", "full_name", row.get("Artistas invitados"), "Guest")
            vi_ids, vi_logs = await process_list_with_logs(db, "guest_artists", "full_name", row.get("Cantantes invitados"), "VocG")
            vp_ids, vp_logs = await process_list_with_logs(db, "musicians", "N/A", row.get("Cantantes principales"), "Lead")

            # 3. Track (Sincronización)
            track_key = f"{song_title.lower().strip()}_{curr_alb_id}"
            
            if track_key in cache["tracks"]:
                curr_track_id = cache["tracks"][track_key]
            else:
                # Si es nuevo, pedimos un ID al contador de tracks
                curr_track_id = await get_next_sequence_value(db, "track_id")
                cache["tracks"][track_key] = curr_track_id
            
            track_data = {
                "id": curr_track_id,
                "album_id": curr_alb_id, "title": song_title, "composer_ids": c_ids,
                "duration": clean_str(row.get("Duración")), "genre_ids": g_ids,
                "duration_seconds": int(row.get("Duración en Segundos")) if pd.notna(row.get("Duración en Segundos")) else 0,
                "metadata": {
                    "key": clean_str(row.get("Tono de la canción")), "is_instrumental": to_bool(row.get("Es instrumental?")),
                    "is_live": to_bool(row.get("Canción en vivo?")), "is_love_song": to_bool(row.get("Es canción de amor?"))
                },
                "track_number": int(row["Nro Pista"]) if pd.notna(row.get("Nro Pista")) else 0,
                "guest_artist_ids": inv_ids, "guest_lead_vocal_ids": vi_ids, "lead_vocal_ids": vp_ids
            }

            res = await db.tracks.update_one(
                {"title": re.compile(f"^{re.escape(song_title)}$", re.IGNORECASE), "album_id": curr_alb_id},
                {"$set": track_data}, upsert=True
            )

            # Log minimalista y eficiente
            masters_status = " | ".join(c_logs + g_logs + inv_logs + vi_logs + vp_logs)
            alb_status = f"{album_title}{' ✅' if is_new_alb else ''}"
            track_icon = "✨" if res.upserted_id else "🔄"
            
            print(f"L{index+1:03d} | {track_icon} {song_title[:20]:<20} | {alb_status[:25]:<25} | {masters_status}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(run_import())
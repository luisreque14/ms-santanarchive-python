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

# Diccionario global para evitar consultas repetitivas a la nube
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

async def preload_caches(db):
    """Carga los datos maestros en memoria al iniciar."""
    print("⏳ Cargando datos maestros en caché...")
    for coll in ["genres", "composers", "guest_artists", "musicians", "albums"]:
        projection = {"id": 1, "name": 1, "full_name": 1, "title": 1}
        cursor = db[coll].find({}, projection)
        async for doc in cursor:
            name = doc.get("name") or doc.get("full_name") or doc.get("title")
            if name:
                cache[coll][name.lower().strip()] = doc["id"]
    print(f"🚀 Caché lista ({sum(len(v) for v in cache.values())} registros)")

async def get_next_id(db, collection_name):
    last_doc = await db[collection_name].find_one(sort=[("id", -1)])
    return (last_doc["id"] + 1) if last_doc else 1

async def get_or_create_id_with_status(db, collection, field, name):
    if not name or str(name).lower() == "nan": 
        return None, False
    
    name_clean = str(name).strip()
    name_key = name_clean.lower()
    
    if name_key in cache[collection]:
        return cache[collection][name_key], False
    
    regex = re.compile(f"^{re.escape(name_clean)}$", re.IGNORECASE)
    doc = await db[collection].find_one({field: regex})
    
    if doc:
        cache[collection][name_key] = doc["id"]
        return doc["id"], False
    
    new_id = await get_next_id(db, collection)
    await db[collection].insert_one({"id": new_id, field: name_clean})
    cache[collection][name_key] = new_id
    return new_id, True

async def process_list_with_logs(db, collection, field, raw_value, label):
    """
    Divide por '/' o ',' usando regex para manejar múltiples separadores.
    """
    if not raw_value or pd.isna(raw_value):
        return [], []
    
    # Regex split: divide por '/' o ',' (y limpia espacios alrededor)
    names = [n.strip() for n in re.split(r'[/,]', str(raw_value)) if n.strip()]
    
    ids = []
    logs = []
    
    for name in names:
        id_found, is_new = await get_or_create_id_with_status(db, collection, field, name)
        if id_found:
            ids.append(id_found)
            status_icon = " ✅" if is_new else ""
            logs.append(f"{label}: {name}{status_icon}")
            
    return ids, logs

async def run_import():
    confirm = input("⚠️ ¿Ejecutar importación (Soporta '/' y ',')? (SI/NO): ")
    if confirm.upper() != "SI": return

    current_dir = Path(__file__).parent
    file_path = current_dir.parent / "data_sources" / "santana_master_v2.xlsx"
    
    db = await db_manager.connect()

    try:
        await preload_caches(db)
        df = pd.read_excel(file_path, dtype={'Fecha lanzamiento': str})
        print(f"\n📈 Procesando {len(df)} filas...\n" + "—"*115)

        for index, row in df.iterrows():
            song_title = clean_str(row["Canción"])
            album_title = clean_str(row["Album"])
            row_logs = []

            # --- 1. ÁLBUM ---
            album_key = album_title.lower().strip()
            if album_key in cache["albums"]:
                current_album_id = cache["albums"][album_key]
                row_logs.append(f"ALBUM: {album_title}")
            else:
                new_album_id = await get_next_id(db, "albums")
                raw_date = row.get("Fecha lanzamiento")
                release_date_obj = None
                try: 
                    if pd.notna(raw_date) and clean_str(raw_date):
                        release_date_obj = datetime.strptime(clean_str(raw_date), '%Y-%m-%d')
                except: pass
                
                await db.albums.insert_one({
                    "id": new_album_id, "title": album_title, "is_live": False,
                    "release_year": int(row["Año Lanzamiento"]) if pd.notna(row.get("Año Lanzamiento")) else None,
                    "cover": format_cover_name(album_title), "release_date": release_date_obj
                })
                
                current_album_id = new_album_id
                cache["albums"][album_key] = new_album_id
                row_logs.append(f"ALBUM: {album_title} ✅")

            # --- 2. MAESTROS (Separación inteligente / ,) ---
            c_ids, c_logs = await process_list_with_logs(db, "composers", "full_name", row.get("Compositores"), "Comp")
            g_ids, g_logs = await process_list_with_logs(db, "genres", "name", row.get("Género"), "Gen")
            inv_ids, inv_logs = await process_list_with_logs(db, "guest_artists", "full_name", row.get("Artistas invitados"), "Guest")
            vi_ids, vi_logs = await process_list_with_logs(db, "guest_artists", "full_name", row.get("Cantantes invitados"), "GuestVoc")
            vp_ids, vp_logs = await process_list_with_logs(db, "musicians", "full_name", row.get("Cantantes principales"), "LeadVoc")

            row_logs.extend(c_logs + g_logs + inv_logs + vi_logs + vp_logs)

            # --- 3. TRACK ---
            track_exists = await db.tracks.find_one({"title": re.compile(f"^{re.escape(song_title)}$", re.IGNORECASE), "album_id": current_album_id})

            if not track_exists:
                
                await db.tracks.insert_one({
                    "album_id": current_album_id, "title": song_title, "composer_ids": c_ids,
                    "duration": clean_str(row.get("Duración")), "genre_ids": g_ids,
                    "duration_seconds": int(row.get("Duración Segundos")) if pd.notna(row.get("Duración Segundos")) else 0,
                    "metadata": {
                        "key": clean_str(row.get("Tono de la canción")), "is_instrumental": to_bool(row.get("Es instrumental?")),
                        "is_live": to_bool(row.get("Canción en vivo?")), "is_love_song": to_bool(row.get("Es canción de amor?"))
                    },
                    "track_number": int(row["Nro Pista"]) if pd.notna(row.get("Nro Pista")) else 0,
                    "guest_artist_ids": inv_ids, "guest_lead_vocal_ids": vi_ids, "lead_vocal_ids": vp_ids
                })
                
                row_logs.append(f"TRACK: {song_title} ✅")
            else:
                row_logs.append(f"TRACK: {song_title}")

            print(f"L{index + 1:03d} | " + " | ".join(row_logs))

        print("—"*115 + "\n🏁 Proceso completado exitosamente.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(run_import())
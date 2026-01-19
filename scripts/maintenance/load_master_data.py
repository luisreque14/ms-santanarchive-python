#python -m scripts.maintenance.load_master_data

import asyncio
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from scripts.common.db_utils import db_manager

def clean_str(value):
    return str(value).strip() if pd.notna(value) else ""

def to_bool(value):
    clean_val = clean_str(value).upper()
    return True if clean_val == "SI" else False

def format_cover_name(album_name):
    # santana-[nombre].jpg en minúsculas y con guiones
    name_processed = album_name.lower().replace(" ", "-")
    return f"santana-{name_processed}.jpg"

async def get_next_id(db, collection_name):
    """Obtiene el siguiente ID autoincremental."""
    last_doc = await db[collection_name].find_one(sort=[("id", -1)])
    return (last_doc["id"] + 1) if last_doc else 1

async def get_id_by_name(db, collection, field, name):
    if not name or name.lower() == "nan": return None
    regex = re.compile(f"^{re.escape(name.strip())}$", re.IGNORECASE)
    doc = await db[collection].find_one({field: regex})
    return doc["id"] if doc else None

async def process_list_column(db, collection, field, raw_value):
    if not raw_value or pd.isna(raw_value):
        return []
    names = [n.strip() for n in str(raw_value).split(",") if n.strip()]
    ids = []
    for name in names:
        id_found = await get_id_by_name(db, collection, field, name)
        if id_found is not None:
            ids.append(id_found)
    return ids

async def run_import():
    # 0. Confirmación de seguridad
    confirm = input("⚠️ ¿Estás seguro de ejecutar la creación de Álbumes y Tracks? (SI/NO): ")
    if confirm.upper() != "SI":
        print("Operación cancelada.")
        return

    # 1. Localizar archivo
    current_dir = Path(__file__).parent
    # Ajuste de ruta según tu estructura: scripts/data_sources/
    file_path = current_dir.parent / "data_sources" / "santana_master_v2.xlsx"
    
    db = await db_manager.connect()

    try:
        df = pd.read_excel(file_path, dtype={'Fecha lanzamiento': str})
        
        # 2. Validar columnas críticas
        if "Canción" not in df.columns or "Album" not in df.columns:
            print("❌ Error: Faltan las columnas 'Canción' o 'Album'. Ejecución detenida.")
            return

        print(f"🚀 Procesando {len(df)} filas...")

        for _, row in df.iterrows():
            song_title = clean_str(row["Canción"])
            album_title = clean_str(row["Album"])
            
            # --- SECCIÓN ÁLBUM ---
            album_regex = re.compile(f"^{re.escape(album_title)}$", re.IGNORECASE)
            album_doc = await db.albums.find_one({"title": album_regex})
            
            # Procesar Fecha lanzamiento (yyyy-mm-dd)
            raw_date = row.get("Fecha lanzamiento")
            release_date_obj = None
            if pd.notna(raw_date) and clean_str(raw_date) != "":
                try:
                    release_date_obj = datetime.strptime(clean_str(raw_date).strip(), '%Y-%m-%d')
                except ValueError:
                    print(f"⚠️ Formato de fecha inválido en álbum '{album_title}': {raw_date}")

            if not album_doc:
                # CREAR ÁLBUM si no existe
                new_id = await get_next_id(db, "albums")
                album_payload = {
                    "id": new_id,
                    "title": album_title,
                    "release_year": int(row["Año Lanzamiento"]) if pd.notna(row.get("Año Lanzamiento")) else None,
                    "cover": format_cover_name(album_title),
                    "release_date": release_date_obj
                }
                await db.albums.insert_one(album_payload)
                current_album_id = new_id
                print(f"🆕 Álbum creado: {album_title}")
            else:
                # Si existe, solo agregar release_date si no existe el atributo
                current_album_id = album_doc["id"]
                if "release_date" not in album_doc and release_date_obj:
                    await db.albums.update_one(
                        {"id": current_album_id},
                        {"$set": {"release_date": release_date_obj}}
                    )

            # --- SECCIÓN TRACK ---
            # Verificar si el track ya existe para este álbum
            track_exists = await db.tracks.find_one({
                "title": re.compile(f"^{re.escape(song_title)}$", re.IGNORECASE),
                "album_id": current_album_id
            })

            if not track_exists:
                # Obtener IDs de colecciones relacionadas
                composer_ids = await process_list_column(db, "composers", "full_name", row.get("Compositores"))
                genre_ids = await process_list_column(db, "genres", "name", row.get("Género"))
                guest_artist_ids = await process_list_column(db, "guest_artists", "full_name", row.get("Artistas invitados"))
                guest_vocal_ids = await process_list_column(db, "guest_artists", "full_name", row.get("Cantantes invitados"))
                lead_vocal_ids = await process_list_column(db, "musicians", "full_name", row.get("Cantantes principales"))

                track_payload = {
                    "album_id": current_album_id,
                    "title": song_title,
                    "composer_ids": composer_ids,
                    "duration": clean_str(row.get("Duración")),
                    "genre_ids": genre_ids,
                    "metadata": {
                        "key": clean_str(row.get("Tono de la canción")),
                        "is_instrumental": to_bool(row.get("Es instrumental?")),
                        "is_live": to_bool(row.get("Canción en vivo?")),
                        "is_love_song": to_bool(row.get("Es canción de amor?"))
                    },
                    "side": clean_str(row.get("Lado")),
                    "track_number": int(row["Nro Pista"]) if pd.notna(row.get("Nro Pista")) else 0,
                    "guest_artist_ids": guest_artist_ids,
                    "guest_lead_vocal_ids": guest_vocal_ids,
                    "lead_vocal_ids": lead_vocal_ids
                }
                await db.tracks.insert_one(track_payload)
                print(f"✅ Track creado: {song_title}")
            else:
                print(f"ℹ️ El track '{song_title}' ya existe. Omitiendo creación.")

        print("\n🏁 Proceso finalizado.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(run_import())